"""
Integration Tests for FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["ml_model_loaded"] is True

def test_api_benchmark_cohort():
    res = client.get("/api/benchmark?sample_size=200")
    assert res.status_code == 200
    data = res.json()
    assert "three_way_comparison" in data
    assert "static_retry" in data["three_way_comparison"]
    assert "rule_based" in data["three_way_comparison"]
    assert "alaadin_agent" in data["three_way_comparison"]

def test_api_webhook_idempotency():
    webhook_payload = {
        "event_id": "evt_test_idem_999",
        "payment_id": "PAY_IDEM_999",
        "idempotency_key": "idem_token_abc_123",
        "amount": 1999.0,
        "payment_method": "UPI",
        "failure_code": "BANK_SERVER_ERROR",
        "retry_count": 0
    }
    
    # First delivery: Processed
    res1 = client.post("/api/webhooks/payment-failed", json=webhook_payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "PROCESSED"

    # Second delivery: Duplicate Ignored
    res2 = client.post("/api/webhooks/payment-failed", json=webhook_payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "DUPLICATE_IGNORED"

def test_api_failure_lab():
    res = client.post("/api/failure-lab", json={"scenario_id": "HIGH_FRAUD"})
    assert res.status_code == 200
    assert res.json()["agent_result"]["policy_verdict"] == "BLOCKED"

def test_api_csv_export():
    res = client.get("/api/payments/export/csv?count=50")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "payment_id,amount" in res.text
