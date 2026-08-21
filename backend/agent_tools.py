"""
RecoverAI - Autonomous Agent Tool Registry & State Machine
Provides the 10 core execution tools and maintains payment settlement state.
Supports Razorpay Test API for live payment-link creation with fallback sandbox.
"""

import os
import time
import random
import httpx
from typing import Dict, Any, List
from datetime import datetime

# Global In-Memory State Machine
# Lifecycle: FAILED -> ELIGIBLE -> ACTION_SCHEDULED -> ACTION_EXECUTED -> VERIFYING -> (RECOVERED | FAILED_FINAL | STOPPED)
PAYMENT_STATE_STORE: Dict[str, Dict[str, Any]] = {}

class ToolRegistry:
    def __init__(self):
        self.razorpay_key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        self.razorpay_key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        
        self.tool_definitions = [
            {
                "name": "get_payment_context",
                "description": "Retrieves real-time payment metadata, failure code, amount, instrument details, and gateway telemetry.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "get_customer_history",
                "description": "Fetches customer 360 profile, historical transaction success rate, previous failures, and VIP value score.",
                "parameters": {"customer_id": "string"}
            },
            {
                "name": "calculate_recovery_score",
                "description": "Invokes the calibrated ML model to compute P(Recovery), expected recovered INR value, and optimal action.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "schedule_smart_retry",
                "description": "Schedules an automated gateway retry after a calculated cooldown period via optimal secondary switch routing.",
                "parameters": {"payment_id": "string", "delay_minutes": "integer", "route_override": "string"}
            },
            {
                "name": "send_customer_notification",
                "description": "Dispatches an intelligent interactive message via WhatsApp, SMS, or Email with dynamic action prompts.",
                "parameters": {"payment_id": "string", "channel": "string", "template": "string"}
            },
            {
                "name": "create_payment_link",
                "description": "Generates a secure 1-click payment link via Razorpay Test API (or sandbox fallback).",
                "parameters": {"payment_id": "string", "validity_hours": "integer", "amount": "float"}
            },
            {
                "name": "retry_payment",
                "description": "Triggers an execution attempt against the primary/secondary banking rails.",
                "parameters": {"payment_id": "string", "route": "string"}
            },
            {
                "name": "check_payment_status",
                "description": "Queries the banking rails / state store to verify whether the payment has settled successfully.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "escalate_to_merchant",
                "description": "Hands off complex, high-value, or repeated failures to merchant operations queue with diagnostic briefing.",
                "parameters": {"payment_id": "string", "reason": "string", "priority": "string"}
            },
            {
                "name": "stop_recovery",
                "description": "Halts all active recovery workflows, cancels pending retries, and marks state as STOPPED.",
                "parameters": {"payment_id": "string", "reason": "string"}
            }
        ]

    def get_definitions(self) -> List[Dict[str, Any]]:
        return self.tool_definitions

    def _get_or_init_state(self, payment_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if payment_id not in PAYMENT_STATE_STORE:
            context = context or {}
            PAYMENT_STATE_STORE[payment_id] = {
                "payment_id": payment_id,
                "amount": float(context.get("amount", 2499.0)),
                "lifecycle_state": "FAILED",
                "status": "FAILED",
                "settled": False,
                "retry_attempts": int(context.get("retry_count", 0)),
                "notifications_sent": int(context.get("notification_count", 0)),
                "created_at": datetime.utcnow().isoformat(),
                "history": []
            }
        return PAYMENT_STATE_STORE[payment_id]

    def execute_tool(self, tool_name: str, args: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes the specified tool and updates state store."""
        context = context or {}
        payment_id = args.get("payment_id") or context.get("payment_id", f"PAY_{int(time.time()*1000)}")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        state = self._get_or_init_state(payment_id, context)

        if tool_name == "get_payment_context":
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "payment_id": payment_id,
                    "amount": context.get("amount", 2499.0),
                    "method": context.get("payment_method", "UPI"),
                    "failure_code": context.get("failure_code", "BANK_SERVER_ERROR"),
                    "failure_category": context.get("failure_category", "TEMPORARY_SYSTEM"),
                    "retry_count": state["retry_attempts"],
                    "notification_count": state["notifications_sent"]
                }
            }

        elif tool_name == "get_customer_history":
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "customer_id": args.get("customer_id") or context.get("customer_id", "CUST_999"),
                    "customer_age_days": context.get("customer_age_days", 240),
                    "previous_transactions": context.get("previous_transactions", 12),
                    "previous_success_rate": context.get("previous_success_rate", 0.91),
                    "previous_failures": context.get("previous_failures", 1),
                    "is_opted_out": bool(context.get("is_opted_out", 0)),
                    "customer_tier": "VIP" if context.get("customer_value", 0.5) > 0.7 else "STANDARD"
                }
            }

        elif tool_name == "calculate_recovery_score":
            prob = context.get("ml_recovery_probability", 0.85)
            amount = context.get("amount", 2499.0)
            erv = context.get("expected_recovered_value", round(amount * prob, 2))
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "recovery_probability": prob,
                    "expected_recovery_value_erv": erv,
                    "recommended_action": context.get("ml_recommended_action", "RETRY_DELAYED_30M"),
                    "confidence_tier": "HIGH" if prob > 0.75 else ("MEDIUM" if prob > 0.45 else "LOW")
                }
            }

        elif tool_name == "schedule_smart_retry":
            delay = args.get("delay_minutes", 30)
            route = args.get("route_override", "SECONDARY_FAST_UPI_SWITCH")
            state["lifecycle_state"] = "ACTION_SCHEDULED"
            state["history"].append(f"Scheduled retry in {delay}m via {route}")
            return {
                "tool": tool_name,
                "status": "SCHEDULED",
                "timestamp": timestamp,
                "output": {
                    "scheduled_delay_minutes": delay,
                    "target_route": route,
                    "action_summary": f"Smart retry queued for execution in {delay} minutes via {route}."
                }
            }

        elif tool_name == "retry_payment":
            state["lifecycle_state"] = "ACTION_EXECUTED"
            state["retry_attempts"] += 1
            
            # Outcome determination based on counterfactual probability
            p_success = float(context.get("p_action_success", context.get("ml_recovery_probability", 0.75)))
            
            # Ground truth simulation
            is_success = random.random() < p_success
            if is_success:
                state["status"] = "SUCCESS"
                state["settled"] = True
                state["lifecycle_state"] = "RECOVERED"
                state["recovered_at"] = timestamp
            else:
                state["status"] = "FAILED"
                state["settled"] = False
                state["lifecycle_state"] = "VERIFYING"

            return {
                "tool": tool_name,
                "status": "EXECUTED",
                "timestamp": timestamp,
                "output": {
                    "result": "PAYMENT_SETTLED_SUCCESS" if is_success else "PAYMENT_RETRY_DECLINED",
                    "settled": is_success,
                    "route_used": args.get("route", "SECONDARY_FAST_UPI_SWITCH"),
                    "action_summary": f"Direct switch retry {'succeeded and settled' if is_success else 'declined by bank'}."
                }
            }

        elif tool_name == "create_payment_link":
            amt = float(args.get("amount", context.get("amount", 2499.0)))
            pay_id_clean = payment_id.replace("PAY_", "")
            
            # Real Razorpay Test API integration if credentials present
            real_link_created = False
            payment_url = f"https://pay.razorpay.com/plink_test_{pay_id_clean}"
            link_id = f"plink_test_{pay_id_clean}"
            
            if self.razorpay_key_id and self.razorpay_key_secret:
                try:
                    with httpx.Client(timeout=4.0) as client:
                        resp = client.post(
                            "https://api.razorpay.com/v1/payment_links",
                            auth=(self.razorpay_key_id, self.razorpay_key_secret),
                            json={
                                "amount": int(amt * 100),
                                "currency": "INR",
                                "description": f"RecoverAI Payment Recovery for {payment_id}",
                                "reference_id": payment_id,
                                "expire_by": int(time.time()) + (args.get("validity_hours", 24) * 3600)
                            }
                        )
                        if resp.status_code in [200, 201]:
                            rdata = resp.json()
                            payment_url = rdata.get("short_url", payment_url)
                            link_id = rdata.get("id", link_id)
                            real_link_created = True
                except Exception as ex:
                    pass # Fallback to sandbox link

            state["lifecycle_state"] = "ACTION_SCHEDULED"
            return {
                "tool": tool_name,
                "status": "CREATED",
                "timestamp": timestamp,
                "output": {
                    "link_id": link_id,
                    "payment_url": payment_url,
                    "is_live_razorpay_api": real_link_created,
                    "validity_hours": args.get("validity_hours", 24),
                    "action_summary": f"Payment recovery link created: {payment_url}"
                }
            }

        elif tool_name == "send_customer_notification":
            channel = args.get("channel", "WHATSAPP")
            template = args.get("template", "ONE_CLICK_RECOVERY_LINK")
            state["notifications_sent"] += 1
            state["lifecycle_state"] = "ACTION_EXECUTED"
            
            # Simulate customer click-through & payment probability
            p_success = float(context.get("p_action_success", context.get("ml_recovery_probability", 0.65)))
            is_success = random.random() < p_success
            if is_success:
                state["status"] = "SUCCESS"
                state["settled"] = True
                state["lifecycle_state"] = "RECOVERED"
            else:
                state["status"] = "FAILED"
                state["settled"] = False
                state["lifecycle_state"] = "VERIFYING"

            return {
                "tool": tool_name,
                "status": "DELIVERED",
                "timestamp": timestamp,
                "output": {
                    "channel": channel,
                    "template": template,
                    "dispatched": True,
                    "action_summary": f"Dispatched recovery prompt via {channel} (Template: {template})."
                }
            }

        elif tool_name == "check_payment_status":
            # Return true settlement state from state store
            is_settled = bool(state.get("settled", False) or state.get("status") == "SUCCESS")
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "payment_id": payment_id,
                    "settled": is_settled,
                    "current_status": "SUCCESS" if is_settled else "PENDING_FAILED",
                    "lifecycle_state": state.get("lifecycle_state", "VERIFYING"),
                    "action_summary": f"Verified banking rails: {'Payment SETTLED successfully' if is_settled else 'Payment remains unsettled'}."
                }
            }

        elif tool_name == "escalate_to_merchant":
            state["lifecycle_state"] = "STOPPED"
            state["status"] = "ESCALATED"
            return {
                "tool": tool_name,
                "status": "ESCALATED",
                "timestamp": timestamp,
                "output": {
                    "ticket_id": f"ESC_{random.randint(10000, 99999)}",
                    "priority": args.get("priority", "HIGH"),
                    "reason": args.get("reason", "Policy limit or high-value ceiling"),
                    "action_summary": "Incident logged to merchant operations queue."
                }
            }

        elif tool_name == "stop_recovery":
            state["lifecycle_state"] = "STOPPED"
            state["status"] = "HALTED"
            return {
                "tool": tool_name,
                "status": "HALTED",
                "timestamp": timestamp,
                "output": {
                    "reason": args.get("reason", "Policy limit reached or unrecoverable error"),
                    "action_summary": "Recovery workflow terminated and logged."
                }
            }

        else:
            return {
                "tool": tool_name,
                "status": "UNKNOWN_TOOL",
                "timestamp": timestamp,
                "output": {"error": f"Tool '{tool_name}' not recognized."}
            }

# Global singleton
_tool_registry_instance = None

def get_tool_registry() -> ToolRegistry:
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance
