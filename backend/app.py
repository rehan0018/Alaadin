"""
Alaadin - FastAPI Backend Application
Exposes REST and WebSocket endpoints for Executive Dashboard, 3-Way Benchmark Experiment,
Agent Failure Lab, Webhook Ingestion with Idempotency, and Real-time WebSocket Stream.
"""

import os
import io
import csv
import json
import asyncio
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

try:
    from backend.agent_brain import get_recovery_agent
    from backend.guardrails import get_policy_engine
    from backend.simulator import get_simulator
    from backend.ml_model import get_scorer
    from backend.agent_tools import get_tool_registry, PAYMENT_STATE_STORE
except ImportError:
    from .agent_brain import get_recovery_agent
    from .guardrails import get_policy_engine
    from .simulator import get_simulator
    from .ml_model import get_scorer
    from .agent_tools import get_tool_registry, PAYMENT_STATE_STORE

app = FastAPI(
    title="Alaadin - Autonomous Payment Recovery Agent API",
    description="Backend service powering Alaadin payment recovery, ERV decision optimization, and 3-way benchmarks.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = get_recovery_agent()
policy_engine = get_policy_engine()
simulator = get_simulator()
scorer = get_scorer()
tool_registry = get_tool_registry()

_cached_benchmark = None
PROCESSED_IDEMPOTENCY_KEYS: Dict[str, Dict[str, Any]] = {}

class WebhookPaymentEvent(BaseModel):
    event_id: str
    payment_id: str
    idempotency_key: Optional[str] = None
    status: str = "failed"
    amount: float = 2499.0
    payment_method: str = "UPI"
    failure_code: str = "BANK_SERVER_ERROR"
    customer_id: Optional[str] = "CUST_7821"
    customer_age_days: int = 180
    previous_transactions: int = 8
    previous_success_rate: float = 0.90
    retry_count: int = 0
    fraud_risk_score: float = 0.04
    timestamp: Optional[str] = None

class CustomPaymentRequest(BaseModel):
    payment_id: Optional[str] = None
    amount: float = 2499.0
    payment_method: str = "UPI"
    failure_code: str = "BANK_SERVER_ERROR"
    customer_age_days: int = 180
    previous_transactions: int = 8
    previous_success_rate: float = 0.90
    previous_failures: int = 1
    previous_recovery_rate: float = 0.65
    retry_count: int = 0
    notification_count: int = 0
    time_since_failure_mins: int = 0
    fraud_risk_score: float = 0.05
    customer_value: float = 0.70
    is_opted_out: int = 0
    is_already_succeeded: int = 0
    subscription_type: str = "ONE_TIME"
    merchant_category: str = "ECOMMERCE"

class BatchSimulateRequest(BaseModel):
    sample_size: int = 1000

class PolicyUpdateRequest(BaseModel):
    max_retries: Optional[int] = None
    max_notifications: Optional[int] = None
    max_recovery_window_hours: Optional[int] = None
    fraud_risk_threshold: Optional[float] = None
    enforce_quiet_hours: Optional[bool] = None
    high_ticket_approval_amount: Optional[float] = None

class FailureLabTestRequest(BaseModel):
    scenario_id: str

class ManualOverrideRequest(BaseModel):
    payment_id: str
    action: str
    note: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Alaadin Autonomous Agent Engine",
        "ml_model_loaded": scorer.calibrated_model is not None,
        "dataset_loaded": len(simulator.df) > 0,
        "razorpay_api_configured": bool(tool_registry.razorpay_key_id and tool_registry.razorpay_key_secret),
        "environment": "PRODUCTION" if tool_registry.razorpay_key_id else "SANDBOX_SIMULATED"
    }

@app.post("/api/webhooks/payment-failed")
def ingest_payment_failed_webhook(event: WebhookPaymentEvent):
    """
    Webhook Ingestion with Idempotency Protection.
    Guarantees duplicate webhook deliveries never trigger duplicate money movement.
    Note: In-memory store used for demo; production uses Redis/Postgres.
    """
    idem_key = event.idempotency_key or event.event_id or event.payment_id
    if idem_key in PROCESSED_IDEMPOTENCY_KEYS:
        return {
            "status": "DUPLICATE_IGNORED",
            "message": f"Event with idempotency key '{idem_key}' was already processed. Duplicate action suppressed.",
            "cached_result": PROCESSED_IDEMPOTENCY_KEYS[idem_key]
        }

    payment_dict = event.model_dump()
    result = agent.process_failed_payment(payment_dict)
    PROCESSED_IDEMPOTENCY_KEYS[idem_key] = result
    return {
        "status": "PROCESSED",
        "event_id": event.event_id,
        "payment_id": event.payment_id,
        "result": result
    }

@app.get("/api/stats")
@app.get("/api/benchmark")
def get_stats(sample_size: int = Query(default=10000, le=50000)):
    global _cached_benchmark
    if _cached_benchmark is None or sample_size != 10000:
        _cached_benchmark = simulator.run_3way_benchmark(sample_size=sample_size)
    return _cached_benchmark

@app.post("/api/simulate/batch")
def run_batch_simulation(req: BatchSimulateRequest):
    """Executes a genuine batch simulation across requested cohort size."""
    size = max(10, min(req.sample_size, 50000))
    res = simulator.run_3way_benchmark(sample_size=size)
    return res

@app.get("/api/payments")
def get_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    method: Optional[str] = None,
    failure_code: Optional[str] = None,
    search: Optional[str] = None
):
    if simulator.df.empty:
        simulator._load_dataset()
    df = simulator.df.copy()
    if method and method != "ALL":
        df = df[df["payment_method"] == method]
    if failure_code and failure_code != "ALL":
        df = df[df["failure_code"] == failure_code]
    if search:
        s = search.strip().upper()
        df = df[df["payment_id"].str.contains(s, na=False) | df["customer_id"].str.contains(s, na=False)]

    total_count = len(df)
    start_idx = (page - 1) * page_size
    subset = df.iloc[start_idx:start_idx + page_size]
    
    payments_list = [agent.process_failed_payment(row.to_dict()) for _, row in subset.iterrows()]
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size,
        "data": payments_list
    }

@app.get("/api/payments/export/csv")
def export_payments_csv(count: int = Query(default=500, le=5000)):
    """Exports payment audit log as a downloadable CSV."""
    if simulator.df.empty:
        simulator._load_dataset()
    subset = simulator.df.head(count).copy()
    batch_probs = scorer.predict_batch_probabilities(subset)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["payment_id", "amount", "method", "failure_code", "recovery_probability", "recommended_action", "policy_verdict", "final_action", "outcome", "recovered_amount"])
    
    for idx_pos, (_, row) in enumerate(subset.iterrows()):
        p_dict = row.to_dict()
        prob = float(batch_probs[idx_pos])
        best_action, _, _ = scorer.evaluate_candidate_actions(p_dict, prob)
        pol = policy_engine.evaluate_action(p_dict, best_action)
        is_rec = pol["is_allowed"] and prob >= 0.5
        writer.writerow([
            p_dict.get("payment_id"),
            p_dict.get("amount"),
            p_dict.get("payment_method"),
            p_dict.get("failure_code"),
            round(prob, 2),
            best_action,
            pol["status"],
            pol["final_action"],
            "RECOVERED" if is_rec else "UNSETTLED",
            p_dict.get("amount") if is_rec else 0.0
        ])
        
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alaadin_audit_export.csv"}
    )

@app.get("/api/payments/{payment_id}")
def get_payment_detail(payment_id: str):
    if simulator.df.empty:
        simulator._load_dataset()
    match = simulator.df[simulator.df["payment_id"] == payment_id]
    if match.empty:
        fallback = {
            "payment_id": payment_id,
            "amount": 2499.0,
            "payment_method": "UPI",
            "failure_code": "BANK_SERVER_ERROR",
            "customer_id": "CUST_7821",
            "previous_success_rate": 0.88,
            "previous_transactions": 14,
            "retry_count": 0,
            "fraud_risk_score": 0.04
        }
        return agent.process_failed_payment(fallback)
    return agent.process_failed_payment(match.iloc[0].to_dict())

@app.post("/api/agent/decide")
def test_agent_decision(req: CustomPaymentRequest):
    p_dict = req.model_dump()
    if not p_dict.get("payment_id"):
        p_dict["payment_id"] = f"PAY_TEST_{random.randint(10000, 99999)}"
    return agent.process_failed_payment(p_dict)

@app.post("/api/failure-lab")
def run_failure_lab_test(req: FailureLabTestRequest):
    scenarios = {
        "ALREADY_SUCCEEDED": {
            "title": "Payment Already Succeeded (Race Condition)",
            "description": "Payment was already settled as SUCCESS via bank webhook, but a delayed async retry arrives.",
            "payment": {
                "payment_id": "FAIL_LAB_01",
                "amount": 4999.0,
                "payment_method": "UPI",
                "failure_code": "BANK_SERVER_ERROR",
                "is_already_succeeded": 1,
                "retry_count": 0,
                "fraud_risk_score": 0.02
            }
        },
        "HIGH_FRAUD": {
            "title": "High Fraud Risk Velocity (Score 0.91)",
            "description": "ML identifies high recovery potential on amount, but fraud risk score is 0.91.",
            "payment": {
                "payment_id": "FAIL_LAB_02",
                "amount": 38000.0,
                "payment_method": "CREDIT_CARD",
                "failure_code": "FRAUD_SUSPECTED",
                "is_already_succeeded": 0,
                "retry_count": 0,
                "fraud_risk_score": 0.91
            }
        },
        "MAX_RETRIES": {
            "title": "3 Previous Retries Exhausted",
            "description": "Payment already attempted 3 automated retries. Agent wants to retry again.",
            "payment": {
                "payment_id": "FAIL_LAB_03",
                "amount": 1899.0,
                "payment_method": "UPI",
                "failure_code": "BANK_SERVER_ERROR",
                "is_already_succeeded": 0,
                "retry_count": 3,
                "fraud_risk_score": 0.03
            }
        },
        "OPTED_OUT": {
            "title": "Customer Opted Out of Messages",
            "description": "Payment failed due to card expiry. Agent wants to dispatch WhatsApp link, but customer opted out.",
            "payment": {
                "payment_id": "FAIL_LAB_04",
                "amount": 1499.0,
                "payment_method": "CREDIT_CARD",
                "failure_code": "CARD_EXPIRED",
                "is_opted_out": 1,
                "retry_count": 0,
                "fraud_risk_score": 0.02
            }
        },
        "HIGH_TICKET": {
            "title": "High-Value Transaction (\u20b92,00,000)",
            "description": "Payment of \u20b92,00,000 failed. Policy requires mandatory human supervisor authorization.",
            "payment": {
                "payment_id": "FAIL_LAB_05",
                "amount": 200000.0,
                "payment_method": "NETBANKING",
                "failure_code": "BANK_SERVER_ERROR",
                "is_already_succeeded": 0,
                "retry_count": 0,
                "fraud_risk_score": 0.04
            }
        }
    }
    
    selected = scenarios.get(req.scenario_id, scenarios["HIGH_FRAUD"])
    result = agent.process_failed_payment(selected["payment"])
    return {
        "scenario_id": req.scenario_id,
        "title": selected["title"],
        "description": selected["description"],
        "agent_result": result
    }

@app.get("/api/policy")
def get_policy():
    return policy_engine.config.to_dict()

@app.post("/api/policy")
def update_policy(req: PolicyUpdateRequest):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    policy_engine.update_config(update_data)
    global _cached_benchmark
    _cached_benchmark = None
    return {
        "status": "SUCCESS",
        "message": "Merchant safety guardrails updated successfully.",
        "active_policy": policy_engine.config.to_dict()
    }

@app.get("/api/model/info")
@app.get("/api/model/calibration")
def get_model_info():
    return {
        "model_type": "Calibrated XGBoost Classifier + ERV Decision Policy",
        "metrics": scorer.metrics,
        "calibration_data": scorer.calibration_data,
        "feature_importances": scorer.feature_importances,
        "feature_count": len(scorer.columns)
    }

@app.get("/api/tools")
def get_tools():
    return tool_registry.get_definitions()

@app.post("/api/override")
def manual_override(req: ManualOverrideRequest):
    """Updates the actual in-memory Payment State Store upon merchant manual override."""
    payment_id = req.payment_id
    if payment_id not in PAYMENT_STATE_STORE:
        PAYMENT_STATE_STORE[payment_id] = {
            "payment_id": payment_id,
            "status": "FAILED",
            "lifecycle_state": "FAILED",
            "history": []
        }
    
    state = PAYMENT_STATE_STORE[payment_id]
    if req.action == "HALT_RECOVERY":
        state["status"] = "HALTED"
        state["lifecycle_state"] = "STOPPED"
    elif req.action == "FORCE_RETRY":
        state["status"] = "SUCCESS"
        state["settled"] = True
        state["lifecycle_state"] = "RECOVERED"
    elif req.action == "SEND_CUSTOM_LINK":
        state["status"] = "LINK_DISPATCHED"
        state["lifecycle_state"] = "ACTION_EXECUTED"
        
    state["history"].append(f"Merchant override: {req.action} ({req.note or 'No notes'}) at {datetime.utcnow().isoformat()}")
    
    return {
        "status": "OVERRIDDEN",
        "payment_id": payment_id,
        "override_action": req.action,
        "updated_state": state["lifecycle_state"],
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Merchant manual override dispatched: '{req.action}' for {payment_id}."
    }

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """Real-time live stream WebSocket powering the Live Command Center."""
    await websocket.accept()
    try:
        if simulator.df.empty:
            simulator._load_dataset()
        indices = list(range(len(simulator.df)))
        random.shuffle(indices)
        idx = 0
        while True:
            row = simulator.df.iloc[indices[idx % len(indices)]].to_dict()
            idx += 1
            result = agent.process_failed_payment(row)
            await websocket.send_json({"type": "PAYMENT_EVENT", "data": result})
            await asyncio.sleep(1.2)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[!] WebSocket stream disconnected: {e}")

# Mount frontend dist static assets
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend build not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
