"""
RecoverAI - Machine Learning Recovery Scorer
Trains an XGBoost / Gradient Boosted Model on synthetic payment data.
Predicts Recovery Probability P(Recovery) and Expected Recovered Value (ERV).
Provides feature importances and action recommendations.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FEATURE_COLS = [
    "amount",
    "customer_age_days",
    "previous_transactions",
    "previous_success_rate",
    "previous_failures",
    "retry_count",
    "notification_count",
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
NUMERIC_COLS = [c for c in FEATURE_COLS if c not in CATEGORICAL_COLS]

class RecoveryScorerModel:
    def __init__(self):
        self.model = None
        self.columns = []
        self.metrics = {}
        self.feature_importances = {}
        self.categories_map = {}

    def prepare_features(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        """One-hot encodes categoricals and aligns with trained columns."""
        df_encoded = pd.get_dummies(df[FEATURE_COLS], columns=CATEGORICAL_COLS, drop_first=False)
        
        if is_training:
            self.columns = list(df_encoded.columns)
            return df_encoded
        else:
            # Reindex to match training columns
            for col in self.columns:
                if col not in df_encoded.columns:
                    df_encoded[col] = 0
            df_encoded = df_encoded[self.columns]
            return df_encoded

    def train(self, train_path: str = None, val_path: str = None, test_path: str = None):
        """Train XGBoost model on train dataset and evaluate on test dataset."""
        train_path = train_path or os.path.join(DATA_DIR, "payments_train.csv")
        test_path = test_path or os.path.join(DATA_DIR, "payments_test.csv")
        
        print(f"[*] Loading training data from {train_path}...")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        X_train = self.prepare_features(train_df, is_training=True)
        y_train = train_df["recovery_success"].values
        
        X_test = self.prepare_features(test_df, is_training=False)
        y_test = test_df["recovery_success"].values
        
        print(f"[*] Training XGBoost Classifier on {len(X_train)} samples with {X_train.shape[1]} features...")
        self.model = xgb.XGBClassifier(
            n_estimators=160,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        # Predict on Test set
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        roc = roc_auc_score(y_test, y_pred_proba)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        self.metrics = {
            "roc_auc": round(float(roc), 4),
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "test_samples": len(test_df),
            "confusion_matrix": cm
        }
        
        # Feature Importance
        importances = self.model.feature_importances_
        feat_imp = sorted(
            [{"feature": col, "importance": round(float(imp), 4)} 
             for col, imp in zip(self.columns, importances)],
            key=lambda x: x["importance"],
            reverse=True
        )
        self.feature_importances = feat_imp[:15]
        
        print(f"[OK] Training complete!")
        print(f"     - ROC-AUC: {self.metrics['roc_auc']}")
        print(f"     - Accuracy: {self.metrics['accuracy']}")
        print(f"     - Precision: {self.metrics['precision']}")
        print(f"     - Recall: {self.metrics['recall']}")
        
        self.save()

    def save(self, model_dir: str = MODEL_DIR):
        """Save model and metadata to disk."""
        os.makedirs(model_dir, exist_ok=True)
        model_file = os.path.join(model_dir, "xgboost_recovery_model.joblib")
        meta_file = os.path.join(model_dir, "model_metadata.json")
        
        joblib.dump({
            "model": self.model,
            "columns": self.columns,
            "metrics": self.metrics,
            "feature_importances": self.feature_importances
        }, model_file)
        
        with open(meta_file, "w") as f:
            json.dump({
                "metrics": self.metrics,
                "feature_importances": self.feature_importances,
                "feature_count": len(self.columns)
            }, f, indent=2)
            
        print(f"[OK] Model artifacts saved to {model_file}")

    def load(self, model_dir: str = MODEL_DIR):
        """Load trained model and metadata."""
        model_file = os.path.join(model_dir, "xgboost_recovery_model.joblib")
        if not os.path.exists(model_file):
            print(f"[!] Model file not found at {model_file}. Training new model...")
            self.train()
            return
            
        data = joblib.load(model_file)
        self.model = data["model"]
        self.columns = data["columns"]
        self.metrics = data["metrics"]
        self.feature_importances = data["feature_importances"]
        print(f"[OK] Loaded pre-trained model with ROC-AUC {self.metrics.get('roc_auc')}")

    def predict_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time inference for a single payment event."""
        # Convert dictionary to DataFrame
        row = {
            "amount": float(payment.get("amount", 1000.0)),
            "customer_age_days": int(payment.get("customer_age_days", 180)),
            "previous_transactions": int(payment.get("previous_transactions", 5)),
            "previous_success_rate": float(payment.get("previous_success_rate", 0.85)),
            "previous_failures": int(payment.get("previous_failures", 1)),
            "retry_count": int(payment.get("retry_count", 0)),
            "notification_count": int(payment.get("notification_count", 0)),
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
        
        prob = float(self.model.predict_proba(X)[0, 1])
        # Add slight rule adjustment if fraud is detected or hard limits exceeded
        if row["fraud_risk_score"] > 0.65:
            prob = min(prob, 0.05)
            
        prob = round(float(np.clip(prob, 0.02, 0.98)), 3)
        amount = row["amount"]
        expected_recovered_value = round(amount * prob, 2)
        
        # Determine confidence tier
        if prob >= 0.75:
            confidence_tier = "HIGH"
        elif prob >= 0.45:
            confidence_tier = "MEDIUM"
        else:
            confidence_tier = "LOW"
            
        # Determine recommended action based on failure code and ML score
        code = row["failure_code"]
        retries = row["retry_count"]
        fraud = row["fraud_risk_score"]
        
        if fraud > 0.65:
            recommended_action = "STOP_AND_FLAG"
            recommended_delay_mins = 0
            explanation = f"High fraud risk detected ({fraud:.2f}). Cease automated retries and flag."
        elif retries >= 3:
            recommended_action = "ESCALATE_MERCHANT" if amount > 5000 else "STOP_RECOVERY"
            recommended_delay_mins = 0
            explanation = f"Maximum automated retries reached ({retries}). Escalate to merchant team."
        elif "BANK" in code or "TIMEOUT" in code:
            recommended_action = "RETRY_DELAYED"
            recommended_delay_mins = 30
            explanation = f"Temporary bank outage detected. Retrying in 30 mins has a {int(prob*100)}% recovery chance."
        elif "INSUFFICIENT" in code:
            recommended_action = "SEND_PAYMENT_LINK"
            recommended_delay_mins = 120
            explanation = f"Insufficient balance. Send smart payment link via WhatsApp/SMS."
        elif "EXPIRED" in code or "INVALID" in code:
            recommended_action = "REQUEST_PAYMENT_UPDATE"
            recommended_delay_mins = 0
            explanation = f"Invalid card details. Request customer to update payment instrument."
        elif "LIMIT" in code:
            recommended_action = "SEND_PAYMENT_LINK_ALT_METHOD"
            recommended_delay_mins = 60
            explanation = f"UPI limit exceeded. Prompt customer to complete with NetBanking/Card."
        elif "AUTH" in code or "ABANDONED" in code:
            recommended_action = "SEND_WHATSAPP_REMINDER"
            recommended_delay_mins = 15
            explanation = f"Authentication drop-off. Send 1-click checkout recovery link."
        else:
            recommended_action = "RETRY_DELAYED"
            recommended_delay_mins = 30
            explanation = f"General transient error. Schedule automated smart retry."

        return {
            "recovery_probability": prob,
            "expected_recovered_value": expected_recovered_value,
            "confidence_tier": confidence_tier,
            "recommended_action": recommended_action,
            "recommended_delay_minutes": recommended_delay_mins,
            "explanation": explanation
        }

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
    
    # Test sample inference
    sample_payment = {
        "payment_id": "PAY_TEST_01",
        "amount": 2499,
        "payment_method": "UPI",
        "failure_code": "BANK_SERVER_ERROR",
        "previous_success_rate": 0.91,
        "previous_failures": 1,
        "retry_count": 0,
        "fraud_risk_score": 0.03
    }
    result = scorer.predict_payment(sample_payment)
    print("\n[Sample Inference Result]:")
    print(json.dumps(result, indent=2))
