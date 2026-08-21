"""
Unit Tests for Machine Learning Scorer & Calibration
"""

import pytest
from backend.ml_model import get_scorer

def test_ml_scorer_metrics_and_calibration():
    scorer = get_scorer()
    assert scorer.calibrated_model is not None
    assert "roc_auc" in scorer.metrics
    assert "pr_auc" in scorer.metrics
    assert "brier_score" in scorer.metrics
    assert "expected_calibration_error_ece" in scorer.metrics
    
    # Verify probability calibration quality
    assert scorer.metrics["brier_score"] < 0.25
    assert scorer.metrics["expected_calibration_error_ece"] < 0.10
    assert len(scorer.feature_importances) > 0

def test_ml_scorer_candidate_action_erv():
    scorer = get_scorer()
    payment = {
        "amount": 3000.0,
        "payment_method": "UPI",
        "failure_code": "BANK_SERVER_ERROR",
        "previous_success_rate": 0.88,
        "retry_count": 0,
        "fraud_risk_score": 0.04
    }
    pred = scorer.predict_payment(payment)
    assert 0.0 <= pred["recovery_probability"] <= 1.0
    assert pred["expected_recovered_value"] > 0
    assert "action_evaluations" in pred
    assert "RETRY_DELAYED_30M" in pred["action_evaluations"]
    assert "SEND_PAYMENT_LINK" in pred["action_evaluations"]
