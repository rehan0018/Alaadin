"""
RecoverAI - Autonomous Agent Brain
Executes the ReAct reasoning cycle: Detect -> Understand -> Decide -> Act -> Measure -> Stop.
Integrates ML Recovery Scoring, Agent Tool Invocation, Policy Guardrails, and Full Audit Trail Generation.
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

    def process_failed_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full autonomous pipeline execution for a failed payment.
        Returns complete agent decision, policy evaluation, tool execution, and audit trail.
        """
        start_time = datetime.utcnow()
        payment_id = payment.get("payment_id", f"PAY_{int(time.time()*1000)}")
        amount = float(payment.get("amount", 2499.0))
        customer_id = payment.get("customer_id", "CUST_UNKNOWN")
        failure_code = payment.get("failure_code", "BANK_SERVER_ERROR")
        method = payment.get("payment_method", "UPI")
        
        audit_trail: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # STEP 1: DETECT & UNDERSTAND
        # -------------------------------------------------------------
        audit_trail.append({
            "step": "DETECT",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": f"Payment Failure Event Ingested ({payment_id})",
            "details": f"Amount: \u20b9{amount:,.2f} | Method: {method} | Gateway Failure Code: {failure_code}",
            "status": "INFO"
        })

        # Tool 1: Context retrieval
        context_res = self.tool_registry.execute_tool(
            "get_payment_context", 
            {"payment_id": payment_id}, 
            context=payment
        )
        # Tool 2: Customer 360
        cust_res = self.tool_registry.execute_tool(
            "get_customer_history", 
            {"customer_id": customer_id}, 
            context=payment
        )
        
        audit_trail.append({
            "step": "UNDERSTAND",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": "Analyzed Payment & Customer Profile",
            "details": f"Customer Success Rate: {cust_res['output']['previous_success_rate']*100:.1f}% ({cust_res['output']['previous_transactions']} previous txns). Tier: {cust_res['output']['customer_tier']}.",
            "status": "SUCCESS",
            "tool_call": "get_customer_history"
        })

        # -------------------------------------------------------------
        # STEP 2: ML RECOVERY SCORING (DECIDE)
        # -------------------------------------------------------------
        ml_prediction = self.scorer.predict_payment(payment)
        recovery_prob = ml_prediction["recovery_probability"]
        expected_recovered_value = ml_prediction["expected_recovered_value"]
        recommended_action = ml_prediction["recommended_action"]
        delay_mins = ml_prediction["recommended_delay_minutes"]
        
        # Inject ML prediction into context for tools
        payment_context = {
            **payment,
            "ml_recovery_probability": recovery_prob,
            "ml_recommended_action": recommended_action
        }

        audit_trail.append({
            "step": "DECIDE_ML_SCORER",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": f"ML Recovery Probability: {int(recovery_prob * 100)}%",
            "details": f"Expected Recovered Value: \u20b9{expected_recovered_value:,.2f}. Confidence: {ml_prediction['confidence_tier']}. Recommended Action: {recommended_action} (delay: {delay_mins}m).",
            "status": "SUCCESS",
            "tool_call": "calculate_recovery_score"
        })

        # -------------------------------------------------------------
        # STEP 3: GUARDRAIL & POLICY ENGINE VERIFICATION
        # -------------------------------------------------------------
        policy_verdict = self.policy_engine.evaluate_action(
            payment=payment,
            proposed_action=recommended_action,
            current_time=datetime.utcnow()
        )
        
        action_allowed = policy_verdict["is_allowed"]
        final_action = policy_verdict["final_action"]
        
        policy_status = "ALLOWED" if action_allowed and policy_verdict["status"] == "ALLOWED" else ("MODIFIED" if policy_verdict["status"] == "MODIFIED" else "BLOCKED")
        
        audit_trail.append({
            "step": "POLICY_CHECK",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": f"Merchant Guardrails Evaluation: {policy_status}",
            "details": policy_verdict["reason"],
            "status": "SUCCESS" if action_allowed else "WARNING",
            "passed_checks": policy_verdict["passed_checks"],
            "failed_checks": policy_verdict["failed_checks"],
            "verdict": policy_status
        })

        # -------------------------------------------------------------
        # STEP 4: ACTION EXECUTION (ACT)
        # -------------------------------------------------------------
        action_result = {}
        tool_invoked = None
        
        if final_action in ["RETRY_DELAYED", "RETRY_SMART_ROUTE"]:
            tool_invoked = "schedule_smart_retry"
            action_result = self.tool_registry.execute_tool(
                "schedule_smart_retry",
                {"payment_id": payment_id, "delay_minutes": delay_mins, "route_override": "SECONDARY_FAST_UPI_SWITCH"},
                context=payment_context
            )
            act_summary = f"Smart retry queued for execution in {delay_mins} minutes via optimal secondary route."

        elif final_action in ["SEND_PAYMENT_LINK", "SEND_PAYMENT_LINK_ALT_METHOD", "SEND_SMART_DISCOUNT_LINK"]:
            # First generate link
            link_res = self.tool_registry.execute_tool("create_payment_link", {"payment_id": payment_id, "validity_hours": 24}, context=payment_context)
            # Then dispatch notification
            tool_invoked = "send_customer_notification"
            action_result = self.tool_registry.execute_tool(
                "send_customer_notification",
                {"payment_id": payment_id, "channel": "WHATSAPP", "template": "INSTANT_PAYMENT_RECOVERY_LINK"},
                context=payment_context
            )
            act_summary = f"Generated smart payment link ({link_res['output']['payment_url']}) and dispatched via WhatsApp."

        elif final_action in ["SEND_WHATSAPP_REMINDER", "REQUEST_PAYMENT_UPDATE"]:
            tool_invoked = "send_customer_notification"
            action_result = self.tool_registry.execute_tool(
                "send_customer_notification",
                {"payment_id": payment_id, "channel": "WHATSAPP", "template": "UPDATE_PAYMENT_METHOD_PROMPT"},
                context=payment_context
            )
            act_summary = f"Sent interactive WhatsApp payment method update request to customer."

        elif final_action == "RETRY_IMMEDIATE":
            tool_invoked = "retry_payment"
            action_result = self.tool_registry.execute_tool("retry_payment", {"payment_id": payment_id}, context=payment_context)
            act_summary = "Triggered immediate bank switch retry."

        elif final_action == "ESCALATE_MERCHANT":
            tool_invoked = "escalate_to_merchant"
            action_result = self.tool_registry.execute_tool(
                "escalate_to_merchant",
                {"payment_id": payment_id, "reason": policy_verdict["reason"], "priority": "HIGH"},
                context=payment_context
            )
            act_summary = f"Escalated high-value failure (\u20b9{amount:,.2f}) to Merchant Operations Queue."

        else: # STOP_RECOVERY or STOP_AND_FLAG
            tool_invoked = "stop_recovery"
            action_result = self.tool_registry.execute_tool(
                "stop_recovery",
                {"payment_id": payment_id, "reason": policy_verdict["reason"]},
                context=payment_context
            )
            act_summary = f"Workflow halted: {policy_verdict['reason']}"

        audit_trail.append({
            "step": "ACT",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": f"Executed Action: {final_action}",
            "details": act_summary,
            "status": "SUCCESS" if action_allowed else "BLOCKED",
            "tool_call": tool_invoked,
            "tool_output": action_result.get("output")
        })

        # -------------------------------------------------------------
        # STEP 5: OUTCOME EVALUATION & STOP
        # -------------------------------------------------------------
        # Ground truth recovery determination for this event
        simulated_recovery_success = bool(payment.get("recovery_success", 0) == 1 and action_allowed)
        recovered_val = amount if simulated_recovery_success else 0.0
        
        audit_trail.append({
            "step": "MEASURE_STOP",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "title": f"Outcome: {'SUCCESSFULLY RECOVERED' if simulated_recovery_success else 'PENDING / HALTED'}",
            "details": f"Recovered Amount: \u20b9{recovered_val:,.2f} | Execution Completed safely within policy bounds.",
            "status": "SUCCESS" if simulated_recovery_success else "INFO"
        })

        return {
            "payment_id": payment_id,
            "customer_id": customer_id,
            "amount": amount,
            "payment_method": method,
            "failure_code": failure_code,
            "failure_category": payment.get("failure_category", "TEMPORARY_SYSTEM"),
            "recovery_probability": recovery_prob,
            "expected_recovered_value": expected_recovered_value,
            "confidence_tier": ml_prediction["confidence_tier"],
            "proposed_action": recommended_action,
            "final_action": final_action,
            "policy_verdict": policy_status,
            "policy_reason": policy_verdict["reason"],
            "passed_checks": policy_verdict["passed_checks"],
            "failed_checks": policy_verdict["failed_checks"],
            "tool_executed": tool_invoked,
            "action_summary": act_summary,
            "is_recovered": simulated_recovery_success,
            "recovered_amount": recovered_val,
            "time_to_recovery_hours": payment.get("time_to_recovery_hours", 1.5) if simulated_recovery_success else 0.0,
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
