"""
Unit Tests for RecoverAI Agent Decision Lifecycle
"""

import pytest
from backend.agent_brain import get_recovery_agent

def test_agent_bank_error_decision():
    agent = get_recovery_agent()
    payment = {
        "payment_id": "PAY_TEST_BANK_01",
        "amount": 2499.0,
        "payment_method": "UPI",
        "failure_code": "BANK_SERVER_ERROR",
        "customer_age_days": 180,
        "previous_transactions": 10,
        "previous_success_rate": 0.92,
        "retry_count": 0,
        "fraud_risk_score": 0.03
    }
    result = agent.process_failed_payment(payment)
    assert result["payment_id"] == "PAY_TEST_BANK_01"
    assert result["proposed_action"] == "RETRY_DELAYED_30M"
    assert result["policy_verdict"] == "APPROVED"
    assert result["expected_recovered_value"] > 0
    assert "why_bullets" in result["decision_rationale"]
    assert len(result["audit_trail"]) == 5

def test_agent_fraud_interception():
    agent = get_recovery_agent()
    payment = {
        "payment_id": "PAY_TEST_FRAUD_01",
        "amount": 45000.0,
        "payment_method": "CREDIT_CARD",
        "failure_code": "FRAUD_SUSPECTED",
        "retry_count": 0,
        "fraud_risk_score": 0.89
    }
    result = agent.process_failed_payment(payment)
    assert result["policy_verdict"] == "BLOCKED"
    assert result["final_action"] == "STOP"
    assert result["is_recovered"] is False

def test_agent_card_expired_decision():
    agent = get_recovery_agent()
    payment = {
        "payment_id": "PAY_TEST_EXPIRED_01",
        "amount": 899.0,
        "payment_method": "CREDIT_CARD",
        "failure_code": "CARD_EXPIRED",
        "retry_count": 0,
        "fraud_risk_score": 0.02
    }
    result = agent.process_failed_payment(payment)
    assert result["proposed_action"] in ["SEND_PAYMENT_LINK", "SEND_WHATSAPP"]
    assert result["policy_verdict"] == "APPROVED"
