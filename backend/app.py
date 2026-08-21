"""
RecoverAI - FastAPI Backend Application
Exposes REST and WebSocket endpoints for Executive Dashboard, Live Demo Simulation,
Payment Investigation & Audit Explorer, Interactive Sandbox, and Policy Guardrail Management.
"""

import os
import json
import asyncio
import random
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    from backend.agent_brain import get_recovery_agent
    from backend.guardrails import get_policy_engine
    from backend.simulator import get_simulator
    from backend.ml_model import get_scorer
    from backend.agent_tools import get_tool_registry
except ImportError:
    from .agent_brain import get_recovery_agent
    from .guardrails import get_policy_engine
    from .simulator import get_simulator
    from .ml_model import get_scorer
    from .agent_tools import get_tool_registry

app = FastAPI(
    title="RecoverAI - Autonomous Payment Recovery Agent API",
    description="Backend service powering RecoverAI payment recovery, ML inference, and live streaming.",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
agent = get_recovery_agent()
policy_engine = get_policy_engine()
simulator = get_simulator()
scorer = get_scorer()
tool_registry = get_tool_registry()

# Cached benchmark results
_cached_benchmark = None

class CustomPaymentRequest(BaseModel):
    payment_id: Optional[str] = None
    amount: float = 2499.0
    payment_method: str = "UPI"
    failure_code: str = "BANK_SERVER_ERROR"
    customer_age_days: int = 180
    previous_transactions: int = 8
    previous_success_rate: float = 0.90
    previous_failures: int = 1
    retry_count: int = 0
    notification_count: int = 0
    fraud_risk_score: float = 0.05
    customer_value: float = 0.70
    is_opted_out: int = 0
    is_already_succeeded: int = 0
    subscription_type: str = "ONE_TIME"
    merchant_category: str = "ECOMMERCE"

class PolicyUpdateRequest(BaseModel):
    max_retries: Optional[int] = None
    max_notifications: Optional[int] = None
    max_recovery_window_hours: Optional[int] = None
    fraud_risk_threshold: Optional[float] = None
    enforce_quiet_hours: Optional[bool] = None
    high_ticket_escalation_amount: Optional[float] = None

class ManualOverrideRequest(BaseModel):
    payment_id: str
    action: str # "FORCE_RETRY", "SEND_CUSTOM_LINK", "HALT_RECOVERY", "ESCALATE"
    note: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "RecoverAI Agent Engine",
        "ml_model_loaded": scorer.model is not None,
        "dataset_loaded": len(simulator.df) > 0
    }

@app.get("/api/stats")
def get_stats(sample_size: int = Query(default=10000, le=50000)):
    """Returns Executive Dashboard KPIs, Comparison, and Funnel."""
    global _cached_benchmark
    if _cached_benchmark is None or sample_size != 10000:
        _cached_benchmark = simulator.run_benchmark(sample_size=sample_size)
    return _cached_benchmark

@app.get("/api/payments")
def get_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    method: Optional[str] = None,
    failure_code: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """Paginated list of payments with real-time agent decisions."""
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
    end_idx = start_idx + page_size
    
    subset = df.iloc[start_idx:end_idx]
    
    payments_list = []
    for _, row in subset.iterrows():
        res = agent.process_failed_payment(row.to_dict())
        payments_list.append(res)
        
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size,
        "data": payments_list
    }

@app.get("/api/payments/{payment_id}")
def get_payment_detail(payment_id: str):
    """Detailed diagnosis and full audit trail for a specific payment."""
    if simulator.df.empty:
        simulator._load_dataset()
        
    match = simulator.df[simulator.df["payment_id"] == payment_id]
    if match.empty:
        # Fallback to simulated payment with given ID
        fallback_payment = {
            "payment_id": payment_id,
            "amount": 2499.0,
            "payment_method": "UPI",
            "failure_code": "BANK_SERVER_ERROR",
            "customer_id": "CUST_7821",
            "previous_success_rate": 0.88,
            "previous_transactions": 14,
            "previous_failures": 1,
            "retry_count": 0,
            "fraud_risk_score": 0.04
        }
        return agent.process_failed_payment(fallback_payment)
        
    row_dict = match.iloc[0].to_dict()
    return agent.process_failed_payment(row_dict)

@app.post("/api/agent/decide")
def test_agent_decision(req: CustomPaymentRequest):
    """Sandbox endpoint: Test any custom payment input against Agent Brain & Policy Guardrails."""
    payment_dict = req.model_dump()
    if not payment_dict.get("payment_id"):
        payment_dict["payment_id"] = f"PAY_SIM_{random.randint(10000, 99999)}"
        
    result = agent.process_failed_payment(payment_dict)
    return result

@app.get("/api/policy")
def get_policy():
    """Returns current active merchant policy guardrails."""
    return policy_engine.config.to_dict()

@app.post("/api/policy")
def update_policy(req: PolicyUpdateRequest):
    """Updates active merchant policy guardrails."""
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    policy_engine.update_config(update_data)
    
    # Invalidate cache so stats reflect updated policy
    global _cached_benchmark
    _cached_benchmark = None
    
    return {
        "status": "SUCCESS",
        "message": "Policy guardrails updated successfully.",
        "active_policy": policy_engine.config.to_dict()
    }

@app.get("/api/model/info")
def get_model_info():
    """Returns ML recovery model metrics, ROC-AUC, accuracy, and feature importances."""
    return {
        "model_type": "XGBoost Classifier + Calibrated Decision Engine",
        "metrics": scorer.metrics,
        "feature_importances": scorer.feature_importances,
        "feature_count": len(scorer.columns)
    }

@app.get("/api/tools")
def get_tools():
    """Returns list of all available agent tools and specs."""
    return tool_registry.get_definitions()

@app.post("/api/override")
def manual_override(req: ManualOverrideRequest):
    """Merchant manual override for a specific payment."""
    return {
        "status": "OVERRIDDEN",
        "payment_id": req.payment_id,
        "override_action": req.action,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Merchant manually dispatched override action '{req.action}' for {req.payment_id}."
    }

# -------------------------------------------------------------
# WebSocket Live Stream for Killer Demo
# -------------------------------------------------------------
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        if simulator.df.empty:
            simulator._load_dataset()
            
        sample_indices = list(range(len(simulator.df)))
        random.shuffle(sample_indices)
        
        idx = 0
        while True:
            row_dict = simulator.df.iloc[sample_indices[idx % len(sample_indices)]].to_dict()
            idx += 1
            
            # Process via Agent Brain
            result = agent.process_failed_payment(row_dict)
            
            # Send real-time event to connected UI
            await websocket.send_json({
                "type": "PAYMENT_EVENT",
                "data": result
            })
            
            # Realistic pause between stream events (configurable)
            await asyncio.sleep(1.2)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[!] WebSocket error: {e}")

# Mount frontend dist static assets if available
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Avoid intercepting API / WS
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend build not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
