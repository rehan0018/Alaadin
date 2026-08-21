"""
Alaadin - Autonomous Agent Brain & Decision Engine
Implements the full lifecycle:
Detect -> Understand -> Decide (ERV) -> Policy Engine (Hard Veto) -> Tool Execution -> Verification -> Measure & Audit.
Outcome is verified directly from tool execution, not from synthetic labels.
"""

import time
import json
from typing import Dict, Any, List
from datetime import datetime

try:
    from backend.ml_model import get_scorer
    from backend.guardrails import get_policy_engine
    from backend.agent_tools import get_tool_registry
except ImportError:
    from .ml_model import get_scorer
    from .guardrails import get_policy_engine
    from .agent_tools import get_tool_registry

class PaymentRecoveryAgent:
    def __init__(self):
        self.scorer = get_scorer()
        self.policy_engine = get_policy_engine()
        self.tool_registry = get_tool_registry()

    def decide(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure Decision Phase: Calculates calibrated P(Recovery) and optimizes Expected Recovery Value (ERV).
        Decoupled from execution for benchmark evaluations.
        """
        ml_prediction = self.scorer.predict_payment(payment)
        return {
            "recovery_probability": ml_prediction["recovery_probability"],
            "expected_recovered_value": ml_prediction["expected_recovered_value"],
            "confidence_tier": ml_prediction["confidence_tier"],
            "proposed_action": ml_prediction["recommended_action"],
            "action_evaluations": ml_prediction["action_evaluations"],
            "decision_rationale_why": ml_prediction["decision_rationale_why"],
            "recommended_delay_minutes": ml_prediction["recommended_delay_minutes"]
        }

    def process_failed_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full autonomous lifecycle execution:
        Detect -> Understand -> Decide (ERV) -> Policy Boundary -> Act (Tool) -> Verify -> Measure & Audit.
        """
        payment_id = payment.get("payment_id", f"PAY_{int(time.time()*1000)}")
        amount = float(payment.get("amount", 2499.0))
        customer_id = payment.get("customer_id", "CUST_UNKNOWN")
        failure_code = payment.get("failure_code", "BANK_SERVER_ERROR")
        method = payment.get("payment_method", "UPI")
        
        # 1. State / Context Builder Tools
        context_res = self.tool_registry.execute_tool("get_payment_context", {"payment_id": payment_id}, context=payment)
        cust_res = self.tool_registry.execute_tool("get_customer_history", {"customer_id": customer_id}, context=payment)
        
        # 2. ML Prediction & ERV Optimization (Decide)
        decision = self.decide(payment)
        recovery_prob = decision["recovery_probability"]
        proposed_action = decision["proposed_action"]
        erv_value = decision["expected_recovered_value"]
        action_evals = decision["action_evaluations"]
        rationale_why = decision["decision_rationale_why"]
        delay_mins = decision["recommended_delay_minutes"]
        p_action_success = action_evals.get(proposed_action, {}).get("p_success", recovery_prob)

        # Invoke actual recovery score tool for audit completeness
        score_res = self.tool_registry.execute_tool(
            "calculate_recovery_score", 
            {"payment_id": payment_id}, 
            context={
                **payment, 
                "ml_recovery_probability": recovery_prob,
                "expected_recovered_value": erv_value,
                "ml_recommended_action": proposed_action
            }
        )

        # 3. Policy Engine (HARD SAFETY BOUNDARY)
        policy_verdict = self.policy_engine.evaluate_action(
            payment=payment,
            proposed_action=proposed_action,
            current_time=datetime.utcnow()
        )
        
        is_approved = policy_verdict["is_allowed"]
        final_action = policy_verdict["final_action"]
        policy_status = policy_verdict["status"]
        
        # 4. Tool Execution & Outcome Verification
        action_summary = ""
        tool_invoked = None
        tool_output = None
        
        payment_context = {
            **payment,
            "ml_recovery_probability": recovery_prob,
            "ml_recommended_action": proposed_action,
            "p_action_success": p_action_success
        }

        if is_approved and final_action == "RETRY_DELAYED_30M":
            # Flow: schedule_smart_retry -> retry_payment -> check_payment_status
            tool_invoked = "retry_payment"
            sched_res = self.tool_registry.execute_tool("schedule_smart_retry", {"payment_id": payment_id, "delay_minutes": delay_mins, "route_override": "SECONDARY_FAST_UPI_SWITCH"}, context=payment_context)
            retry_res = self.tool_registry.execute_tool("retry_payment", {"payment_id": payment_id, "route": "SECONDARY_FAST_UPI_SWITCH"}, context=payment_context)
            verify_res = self.tool_registry.execute_tool("check_payment_status", {"payment_id": payment_id}, context=payment_context)
            
            tool_output = retry_res["output"]
            action_summary = f"RETRY EXECUTED via Secondary Switch ({'Settled Successfully' if verify_res['output']['settled'] else 'Declined'})"

        elif is_approved and final_action in ["SEND_PAYMENT_LINK", "SEND_WHATSAPP"]:
            # Flow: create_payment_link -> send_customer_notification -> simulate_customer_payment_action -> check_payment_status
            tool_invoked = "send_customer_notification"
            link_res = self.tool_registry.execute_tool("create_payment_link", {"payment_id": payment_id, "validity_hours": 24, "amount": amount}, context=payment_context)
            notif_res = self.tool_registry.execute_tool("send_customer_notification", {"payment_id": payment_id, "channel": "WHATSAPP" if "WHATSAPP" in final_action else "SMS", "template": "ONE_CLICK_RECOVERY_LINK"}, context=payment_context)
            cust_action_res = self.tool_registry.execute_tool("simulate_customer_payment_action", {"payment_id": payment_id, "link_id": link_res["output"]["link_id"]}, context=payment_context)
            verify_res = self.tool_registry.execute_tool("check_payment_status", {"payment_id": payment_id}, context=payment_context)
            
            tool_output = notif_res["output"]
            action_summary = f"Dispatched link via {'WhatsApp' if 'WHATSAPP' in final_action else 'SMS'} ({'Customer Completed Payment' if verify_res['output']['settled'] else 'No Customer Action'})"

        elif final_action == "ESCALATE_MERCHANT" or policy_status == "HUMAN_APPROVAL_REQUIRED":
            tool_invoked = "escalate_to_merchant"
            res = self.tool_registry.execute_tool("escalate_to_merchant", {"payment_id": payment_id, "reason": policy_verdict["reason"], "priority": "HIGH"}, context=payment_context)
            verify_res = self.tool_registry.execute_tool("check_payment_status", {"payment_id": payment_id}, context=payment_context)
            tool_output = res["output"]
            action_summary = "ESCALATED TO MERCHANT (Human Supervisor Routing)"

        else: # STOP / BLOCKED
            tool_invoked = "stop_recovery"
            res = self.tool_registry.execute_tool("stop_recovery", {"payment_id": payment_id, "reason": policy_verdict["reason"]}, context=payment_context)
            verify_res = self.tool_registry.execute_tool("check_payment_status", {"payment_id": payment_id}, context=payment_context)
            tool_output = res["output"]
            action_summary = f"RECOVERY HALTED: {policy_verdict['reason']}"

        # 5. Outcome Verification from check_payment_status Tool
        is_recovered = bool(verify_res["output"]["settled"] and is_approved)
        recovered_amount = amount if is_recovered else 0.0
        elapsed_recovery_hours = 0.5 if "30M" in final_action else (1.2 if "LINK" in final_action or "WHATSAPP" in final_action else 0.0)

        # 6. Structured Decision Rationale
        decision_rationale = {
            "payment_id": payment_id,
            "failure_code": failure_code,
            "failure_description": payment.get("failure_category", "TEMPORARY_SYSTEM"),
            "recovery_probability_pct": int(recovery_prob * 100),
            "expected_recovery_value_inr": erv_value,
            "recommended_action": proposed_action,
            "why_bullets": rationale_why,
            "policy_checks": policy_verdict["itemized_checks"],
            "policy_verdict": policy_status,
            "action_executed": action_summary,
            "verified_outcome": "SETTLED_SUCCESS" if is_recovered else "UNSETTLED"
        }

        # 7. Audit Trail steps
        audit_trail = [
            {
                "step": "DETECT_CONTEXT",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "title": f"Payment Event Ingested ({payment_id})",
                "details": f"\u20b9{amount:,.2f} {method} | Failure: {failure_code} | Customer History: {cust_res['output']['previous_success_rate']*100:.0f}% ({cust_res['output']['previous_transactions']} txns)",
                "status": "INFO"
            },
            {
                "step": "ML_ERV_DECISION",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "title": f"ML Scorer & ERV Optimization",
                "details": f"P(Recovery): {int(recovery_prob*100)}% | ERV: \u20b9{erv_value:,.2f} | Selected Optimal Action: {proposed_action}",
                "status": "SUCCESS",
                "tool_call": "calculate_recovery_score"
            },
            {
                "step": "POLICY_HARD_BOUNDARY",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "title": f"Policy Safety Gate: {policy_status}",
                "details": policy_verdict["reason"],
                "status": "SUCCESS" if is_approved else "WARNING",
                "itemized_checks": policy_verdict["itemized_checks"]
            },
            {
                "step": "EXECUTE_TOOL",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "title": f"Tool Execution: {tool_invoked}",
                "details": action_summary,
                "status": "SUCCESS" if is_approved else "BLOCKED",
                "tool_call": tool_invoked,
                "tool_output": tool_output
            },
            {
                "step": "VERIFY_STATUS",
                "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "title": f"Status Verification: {verify_res['output']['current_status']}",
                "details": verify_res["output"]["action_summary"],
                "status": "SUCCESS" if is_recovered else "INFO",
                "tool_call": "check_payment_status"
            }
        ]

        return {
            "payment_id": payment_id,
            "customer_id": customer_id,
            "amount": amount,
            "payment_method": method,
            "failure_code": failure_code,
            "failure_category": payment.get("failure_category", "TEMPORARY_SYSTEM"),
            "recovery_probability": recovery_prob,
            "expected_recovered_value": erv_value,
            "confidence_tier": decision["confidence_tier"],
            "proposed_action": proposed_action,
            "final_action": final_action,
            "action_evaluations": action_evals,
            "policy_verdict": policy_status,
            "policy_reason": policy_verdict["reason"],
            "itemized_policy_checks": policy_verdict["itemized_checks"],
            "decision_rationale": decision_rationale,
            "tool_executed": tool_invoked,
            "action_summary": action_summary,
            "is_recovered": is_recovered,
            "recovered_amount": recovered_amount,
            "time_to_recovery_hours": elapsed_recovery_hours if is_recovered else 0.0,
            "audit_trail": audit_trail,
            "processed_at": datetime.utcnow().isoformat()
        }

# Global singleton agent
_agent_instance = None

def get_recovery_agent() -> PaymentRecoveryAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PaymentRecoveryAgent()
    return _agent_instance
