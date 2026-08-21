"""
RecoverAI - Machine Learning Recovery Scorer & Probability Calibration Engine
Trains XGBoost model with CalibratedClassifierCV on validation split.
Determines optimal decision threshold and computes Brier Score, ECE, PR-AUC, ROC-AUC.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.metrics import (
    roc_auc_score, 
    precision_recall_curve, 
    auc, 
    brier_score_loss, 
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    confusion_matrix
)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import xgboost as xgb

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FEATURE_COLS = [
    "amount",
    "customer_age_days",
    "previous_transactions",
    "previous_success_rate",
    "previous_failures",
    "previous_recovery_rate",
    "retry_count",
    "notification_count",
    "time_since_failure_mins",
    "fraud_risk_score",
    "customer_value",
    "hour",
    "day",
    # Categoricals to one-hot encode
    "payment_method",
    "failure_code",
    "merchant_category",
    "subscription_type"
]

CATEGORICAL_COLS = ["payment_method", "failure_code", "merchant_category", "subscription_type"]

ACTION_COSTS = {
    "RETRY_DELAYED_30M": {"cost": 0.0, "contact_cost": 0.0, "desc": "Secondary switch retry after 30 min cooldown"},
    "SEND_PAYMENT_LINK": {"cost": 2.0, "contact_cost": 1.0, "desc": "1-click recovery payment link via SMS"},
    "SEND_WHATSAPP": {"cost": 1.0, "contact_cost": 0.5, "desc": "Interactive WhatsApp recovery prompt"},
    "ESCALATE_MERCHANT": {"cost": 5.0, "contact_cost": 0.0, "desc": "Route to Merchant Operations support queue"},
    "STOP": {"cost": 0.0, "contact_cost": 0.0, "desc": "Halt further recovery workflows"}
}

class RecoveryScorerModel:
    def __init__(self):
        self.base_model = None
        self.calibrated_model = None
        self.columns = []
        self.optimal_threshold = 0.50
        self.metrics = {}
        self.feature_importances = {}
        self.calibration_data = {}

    def prepare_features(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        """One-hot encodes categorical features and aligns schema."""
        df_clean = df.copy()
        if "previous_recovery_rate" not in df_clean.columns:
            df_clean["previous_recovery_rate"] = 0.5
        if "time_since_failure_mins" not in df_clean.columns:
            df_clean["time_since_failure_mins"] = 0
            
        df_encoded = pd.get_dummies(df_clean[FEATURE_COLS], columns=CATEGORICAL_COLS, drop_first=False)
        
        if is_training:
            self.columns = list(df_encoded.columns)
            return df_encoded
        else:
            for col in self.columns:
                if col not in df_encoded.columns:
                    df_encoded[col] = 0
            return df_encoded[self.columns]

    def calculate_ece(self, y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
        """Calculates Expected Calibration Error (ECE)."""
        bin_limits = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n = len(y_true)
        
        for i in range(n_bins):
            bin_mask = (y_prob > bin_limits[i]) & (y_prob <= bin_limits[i+1])
            bin_size = np.sum(bin_mask)
            if bin_size > 0:
                bin_acc = np.mean(y_true[bin_mask])
                bin_conf = np.mean(y_prob[bin_mask])
                ece += (bin_size / n) * np.abs(bin_acc - bin_conf)
        return float(ece)

    def optimize_threshold_on_validation(self, X_val: pd.DataFrame, y_val: np.ndarray, amounts: np.ndarray) -> float:
        """Finds decision threshold maximizing net expected recovered value on validation split."""
        probs = self.calibrated_model.predict_proba(X_val)[:, 1]
        thresholds = np.linspace(0.2, 0.8, 31)
        best_thresh = 0.50
        best_net_rev = -1e9
        
        for t in thresholds:
            preds = (probs >= t).astype(int)
            # Net recovery: True Positives recover amount, False Positives incur ₹3 contact friction
            tp_mask = (preds == 1) & (y_val == 1)
            fp_mask = (preds == 1) & (y_val == 0)
            net_rev = np.sum(amounts[tp_mask]) - (np.sum(fp_mask) * 3.0)
            if net_rev > best_net_rev:
                best_net_rev = net_rev
                best_thresh = float(t)
                
        return round(best_thresh, 2)

    def train(self, train_path: str = None, val_path: str = None, test_path: str = None):
        """Train XGBoost on Train split, calibrate on Val split, evaluate on Test split."""
        train_path = train_path or os.path.join(DATA_DIR, "payments_train.csv")
        val_path = val_path or os.path.join(DATA_DIR, "payments_val.csv")
        test_path = test_path or os.path.join(DATA_DIR, "payments_test.csv")
        
        print(f"[*] Training RecoverAI Scorer on {train_path} (Train: 35k)...")
        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)
        
        X_train = self.prepare_features(train_df, is_training=True)
        y_train = train_df["recovery_success"].values
        
        X_val = self.prepare_features(val_df, is_training=False)
        y_val = val_df["recovery_success"].values
        val_amounts = val_df["amount"].values
        
        X_test = self.prepare_features(test_df, is_training=False)
        y_test = test_df["recovery_success"].values
        
        # 1. Base XGBoost Estimator
        self.base_model = xgb.XGBClassifier(
            n_estimators=180,
            max_depth=5,
            learning_rate=0.07,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=42
        )
        self.base_model.fit(X_train, y_train)
        
        # 2. Probability Calibration via CalibratedClassifierCV (5-Fold CV)
        print(f"[*] Calibrating probability outputs with 5-fold cross-validation...")
        self.calibrated_model = CalibratedClassifierCV(
            estimator=self.base_model,
            method="sigmoid",
            cv=5
        )
        self.calibrated_model.fit(X_train, y_train)
        
        # 3. Decision Threshold Optimization
        self.optimal_threshold = self.optimize_threshold_on_validation(X_val, y_val, val_amounts)
        print(f"[OK] Calibrated Model. Optimal Decision Threshold: {self.optimal_threshold}")
        
        # 4. Final Evaluation on Holdout Test Split (7,500 records)
        y_pred_proba = self.calibrated_model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= self.optimal_threshold).astype(int)
        
        roc = roc_auc_score(y_test, y_pred_proba)
        precision_arr, recall_arr, _ = precision_recall_curve(y_test, y_pred_proba)
        pr_auc = auc(recall_arr, precision_arr)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        brier = brier_score_loss(y_test, y_pred_proba)
        ece = self.calculate_ece(y_test, y_pred_proba, n_bins=10)
        
        prob_true, prob_pred = calibration_curve(y_test, y_pred_proba, n_bins=10, strategy='uniform')
        calibration_points = [
            {"predicted_prob": round(float(p), 3), "empirical_prob": round(float(t), 3)}
            for p, t in zip(prob_pred, prob_true)
        ]
        
        self.metrics = {
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "brier_score": round(float(brier), 4),
            "expected_calibration_error_ece": round(float(ece), 4),
            "optimal_threshold": self.optimal_threshold,
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "test_samples": len(test_df),
            "confusion_matrix": cm
        }
        
        self.calibration_data = {
            "brier_score": round(float(brier), 4),
            "ece": round(float(ece), 4),
            "optimal_threshold": self.optimal_threshold,
            "curve": calibration_points
        }
        
        # Feature Importances from Base Model
        importances = self.base_model.feature_importances_
        feat_imp = sorted(
            [{"feature": col, "importance": round(float(imp), 4)} 
             for col, imp in zip(self.columns, importances)],
            key=lambda x: x["importance"],
            reverse=True
        )
        self.feature_importances = feat_imp[:15]
        
        print(f"[OK] Test Holdout Metrics:")
        print(f"     - ROC-AUC:    {self.metrics['roc_auc']}")
        print(f"     - PR-AUC:     {self.metrics['pr_auc']}")
        print(f"     - Brier:      {self.metrics['brier_score']}")
        print(f"     - ECE:        {self.metrics['expected_calibration_error_ece']}")
        print(f"     - Precision:  {self.metrics['precision']}")
        print(f"     - Recall:     {self.metrics['recall']}")
        
        self.save()

    def save(self, model_dir: str = MODEL_DIR):
        os.makedirs(model_dir, exist_ok=True)
        model_file = os.path.join(model_dir, "xgboost_recovery_model.joblib")
        meta_file = os.path.join(model_dir, "model_metadata.json")
        
        joblib.dump({
            "base_model": self.base_model,
            "calibrated_model": self.calibrated_model,
            "columns": self.columns,
            "optimal_threshold": self.optimal_threshold,
            "metrics": self.metrics,
            "feature_importances": self.feature_importances,
            "calibration_data": self.calibration_data
        }, model_file)
        
        with open(meta_file, "w") as f:
            json.dump({
                "metrics": self.metrics,
                "feature_importances": self.feature_importances,
                "calibration_data": self.calibration_data,
                "feature_count": len(self.columns)
            }, f, indent=2)
            
        print(f"[OK] Model artifacts saved to {model_file}")

    def load(self, model_dir: str = MODEL_DIR):
        model_file = os.path.join(model_dir, "xgboost_recovery_model.joblib")
        if not os.path.exists(model_file):
            print(f"[!] Model file not found. Training new calibrated model...")
            self.train()
            return
            
        data = joblib.load(model_file)
        self.base_model = data["base_model"]
        self.calibrated_model = data["calibrated_model"]
        self.columns = data["columns"]
        self.optimal_threshold = data.get("optimal_threshold", 0.50)
        self.metrics = data["metrics"]
        self.feature_importances = data["feature_importances"]
        self.calibration_data = data.get("calibration_data", {})
        print(f"[OK] Loaded pre-trained calibrated model (ROC-AUC {self.metrics.get('roc_auc')}, Brier {self.metrics.get('brier_score')})")

    def evaluate_candidate_actions(self, payment: Dict[str, Any], base_prob: float) -> Tuple[str, Dict[str, Any], List[str]]:
        """
        Calculates Expected Recovery Value (ERV) for candidate actions:
        ERV(action) = P(success | action) * Amount - InterventionCost - ContactCost
        """
        amount = float(payment.get("amount", 1000.0))
        code = str(payment.get("failure_code", "BANK_SERVER_ERROR"))
        retries = int(payment.get("retry_count", 0))
        fraud = float(payment.get("fraud_risk_score", 0.05))
        is_opted_out = bool(payment.get("is_opted_out", 0) == 1)
        already_succeeded = bool(payment.get("is_already_succeeded", 0) == 1)
        elapsed_hours = float(payment.get("time_since_failure_mins", 0.0)) / 60.0
        
        action_results = {}
        rationale_bullets = []

        if "BANK" in code or "TIMEOUT" in code:
            p_retry = min(0.96, base_prob * 1.08)
            p_link = base_prob * 0.65
            p_whatsapp = base_prob * 0.70
            p_escalate = 0.35
            rationale_bullets.append("Temporary gateway/bank outage detected")
        elif "INSUFFICIENT" in code or "LIMIT" in code:
            p_retry = base_prob * 0.35
            p_link = min(0.92, base_prob * 1.15)
            p_whatsapp = min(0.90, base_prob * 1.10)
            p_escalate = 0.25
            rationale_bullets.append("Customer balance/limit friction: direct link/notification yields higher success")
        elif "EXPIRED" in code or "INVALID" in code:
            p_retry = 0.02 # Direct retry on expired card is useless
            p_link = min(0.85, base_prob * 1.25)
            p_whatsapp = min(0.88, base_prob * 1.30)
            p_escalate = 0.20
            rationale_bullets.append("Permanent card defect: instrument update required")
        elif "AUTH" in code or "ABANDONED" in code:
            p_retry = base_prob * 0.40
            p_link = min(0.94, base_prob * 1.10)
            p_whatsapp = min(0.95, base_prob * 1.15)
            p_escalate = 0.20
            rationale_bullets.append("Authentication drop-off: 1-click WhatsApp prompt is optimal")
        else:
            p_retry = base_prob * 0.80
            p_link = base_prob * 0.75
            p_whatsapp = base_prob * 0.75
            p_escalate = 0.30
            rationale_bullets.append("General payment failure")

        decay = max(0.2, 1.0 - (retries * 0.25))
        p_retry *= decay
        p_link *= max(0.4, 1.0 - (retries * 0.15))
        p_whatsapp *= max(0.4, 1.0 - (retries * 0.15))

        if is_opted_out:
            p_link = 0.0
            p_whatsapp = 0.0
            rationale_bullets.append("Customer opted out of direct messages")

        if fraud > 0.65 or already_succeeded or elapsed_hours > 72:
            p_retry = 0.0
            p_link = 0.0
            p_whatsapp = 0.0
            p_escalate = 0.0
            rationale_bullets.append("Safety policy threshold or state lock triggered")

        candidates = {
            "RETRY_DELAYED_30M": p_retry,
            "SEND_PAYMENT_LINK": p_link,
            "SEND_WHATSAPP": p_whatsapp,
            "ESCALATE_MERCHANT": p_escalate,
            "STOP": 0.0
        }

        for act_name, p_act in candidates.items():
            cost_info = ACTION_COSTS[act_name]
            total_cost = cost_info["cost"] + cost_info["contact_cost"]
            erv = (p_act * amount) - total_cost
            action_results[act_name] = {
                "action": act_name,
                "p_success": round(float(p_act), 3),
                "cost_inr": total_cost,
                "expected_recovery_value_erv": round(float(erv), 2),
                "description": cost_info["desc"]
            }

        best_action = max(action_results.keys(), key=lambda a: action_results[a]["expected_recovery_value_erv"])
        if action_results[best_action]["expected_recovery_value_erv"] <= 0 and best_action != "STOP":
            best_action = "STOP"

        hist_rate = float(payment.get("previous_success_rate", 0.0))
        if hist_rate > 0.8:
            rationale_bullets.append(f"Customer has strong historical success rate ({int(hist_rate*100)}%)")
        if retries == 0:
            rationale_bullets.append("First failure occurrence (0 previous retries)")
        else:
            rationale_bullets.append(f"Previous retry count: {retries}")

        return best_action, action_results, rationale_bullets

    def predict_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time inference calculating calibrated P(Recovery) and ERV."""
        row = {
            "amount": float(payment.get("amount", 1000.0)),
            "customer_age_days": int(payment.get("customer_age_days", 180)),
            "previous_transactions": int(payment.get("previous_transactions", 5)),
            "previous_success_rate": float(payment.get("previous_success_rate", 0.85)),
            "previous_failures": int(payment.get("previous_failures", 1)),
            "previous_recovery_rate": float(payment.get("previous_recovery_rate", 0.60)),
            "retry_count": int(payment.get("retry_count", 0)),
            "notification_count": int(payment.get("notification_count", 0)),
            "time_since_failure_mins": int(payment.get("time_since_failure_mins", 0)),
            "fraud_risk_score": float(payment.get("fraud_risk_score", 0.05)),
            "customer_value": float(payment.get("customer_value", 0.65)),
            "hour": int(payment.get("hour", 14)),
            "day": int(payment.get("day", 2)),
            "payment_method": str(payment.get("payment_method", "UPI")),
            "failure_code": str(payment.get("failure_code", "BANK_SERVER_ERROR")),
            "merchant_category": str(payment.get("merchant_category", "ECOMMERCE")),
            "subscription_type": str(payment.get("subscription_type", "ONE_TIME"))
        }
        
        df_single = pd.DataFrame([row])
        X = self.prepare_features(df_single, is_training=False)
        
        prob = float(self.calibrated_model.predict_proba(X)[0, 1])
        if row["fraud_risk_score"] > 0.65:
            prob = min(prob, 0.03)
            
        prob = round(float(np.clip(prob, 0.01, 0.98)), 3)
        amount = row["amount"]
        
        best_action, action_evals, rationale_bullets = self.evaluate_candidate_actions(payment, prob)
        erv = action_evals[best_action]["expected_recovery_value_erv"]
        confidence_tier = "HIGH" if prob >= 0.75 else ("MEDIUM" if prob >= 0.45 else "LOW")

        return {
            "recovery_probability": prob,
            "expected_recovered_value": erv,
            "confidence_tier": confidence_tier,
            "recommended_action": best_action,
            "action_evaluations": action_evals,
            "decision_rationale_why": rationale_bullets,
            "recommended_delay_minutes": 30 if "30M" in best_action else (15 if "WHATSAPP" in best_action else 0)
        }

    def predict_batch_probabilities(self, df: pd.DataFrame) -> np.ndarray:
        """Vectorized batch inference for instant benchmark evaluations."""
        X = self.prepare_features(df, is_training=False)
        probs = self.calibrated_model.predict_proba(X)[:, 1]
        if "fraud_risk_score" in df.columns:
            fraud_mask = df["fraud_risk_score"] > 0.65
            probs[fraud_mask] = np.minimum(probs[fraud_mask], 0.03)
        return np.clip(probs, 0.01, 0.98)

# Global singleton
_scorer_instance = None

def get_scorer() -> RecoveryScorerModel:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RecoveryScorerModel()
        _scorer_instance.load()
    return _scorer_instance

if __name__ == "__main__":
    scorer = RecoveryScorerModel()
    scorer.train()
