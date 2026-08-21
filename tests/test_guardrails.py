"""
Unit Tests for RecoverAI Policy Engine & Guardrails
Tests all 8 financial safety boundaries.
"""

import pytest
from datetime import datetime
from backend.guardrails import PolicyEngine, MerchantPolicyConfig

def test_state_lock_guardrail():
    policy = PolicyEngine()
    payment = {"amount": 2499.0, "is_already_succeeded": 1, "retry_count": 0}
    verdict = policy.evaluate_action(payment, "RETRY_DELAYED_30M")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"
    assert verdict["final_action"] == "STOP"

def test_fraud_risk_cutoff_guardrail():
    policy = PolicyEngine(MerchantPolicyConfig(fraud_risk_threshold=0.65))
    payment = {"amount": 5000.0, "fraud_risk_score": 0.91, "retry_count": 0}
    verdict = policy.evaluate_action(payment, "SEND_PAYMENT_LINK")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"
    assert verdict["final_action"] == "STOP"

def test_max_retries_guardrail():
    policy = PolicyEngine(MerchantPolicyConfig(max_retries=3))
    payment = {"amount": 2500.0, "retry_count": 3, "fraud_risk_score": 0.04}
    verdict = policy.evaluate_action(payment, "RETRY_DELAYED_30M")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"

def test_max_contacts_guardrail():
    policy = PolicyEngine(MerchantPolicyConfig(max_notifications=2))
    payment = {"amount": 1999.0, "notification_count": 2, "is_opted_out": 0}
    verdict = policy.evaluate_action(payment, "SEND_WHATSAPP")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"

def test_customer_opt_out_guardrail():
    policy = PolicyEngine()
    payment = {"amount": 999.0, "is_opted_out": 1, "notification_count": 0}
    verdict = policy.evaluate_action(payment, "SEND_WHATSAPP")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"

def test_recovery_window_72h_guardrail():
    policy = PolicyEngine(MerchantPolicyConfig(max_recovery_window_hours=72))
    # 76 hours elapsed = 4560 minutes
    payment = {"amount": 3499.0, "time_since_failure_mins": 4560, "retry_count": 0}
    verdict = policy.evaluate_action(payment, "RETRY_DELAYED_30M")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "BLOCKED"
    assert "Recovery time window exceeded" in verdict["reason"]

def test_high_ticket_approval_ceiling():
    policy = PolicyEngine(MerchantPolicyConfig(high_ticket_approval_amount=100000.0))
    payment = {"amount": 200000.0, "retry_count": 0, "fraud_risk_score": 0.02}
    verdict = policy.evaluate_action(payment, "RETRY_DELAYED_30M")
    assert verdict["is_allowed"] is False
    assert verdict["status"] == "HUMAN_APPROVAL_REQUIRED"
    assert verdict["final_action"] == "ESCALATE_MERCHANT"

def test_approved_action_within_policy():
    policy = PolicyEngine()
    payment = {
        "amount": 2499.0,
        "retry_count": 0,
        "notification_count": 0,
        "time_since_failure_mins": 15,
        "fraud_risk_score": 0.03,
        "is_opted_out": 0,
        "is_already_succeeded": 0
    }
    verdict = policy.evaluate_action(payment, "RETRY_DELAYED_30M")
    assert verdict["is_allowed"] is True
    assert verdict["status"] == "APPROVED"
    assert verdict["final_action"] == "RETRY_DELAYED_30M"
