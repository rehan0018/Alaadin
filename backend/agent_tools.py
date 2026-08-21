"""
RecoverAI - Autonomous Agent Tool Registry
Provides the standard suite of recovery tools that the Agent Brain can invoke.
Each tool returns a structured execution result with timestamp and audit metadata.
"""

import time
import random
from typing import Dict, Any, List
from datetime import datetime

class ToolRegistry:
    def __init__(self):
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
                "description": "Invokes the ML model to compute P(Recovery), expected recovered INR value, and optimal recovery route.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "schedule_smart_retry",
                "description": "Schedules an automated gateway retry after a calculated cooldown period via optimal routing.",
                "parameters": {"payment_id": "string", "delay_minutes": "integer", "route_override": "string"}
            },
            {
                "name": "send_customer_notification",
                "description": "Dispatches an intelligent interactive message via WhatsApp, SMS, or Email with dynamic action prompts.",
                "parameters": {"payment_id": "string", "channel": "string", "template": "string"}
            },
            {
                "name": "create_payment_link",
                "description": "Generates a secure 1-click Razorpay-style recovery payment link with optional instant incentives.",
                "parameters": {"payment_id": "string", "validity_hours": "integer", "discount_pct": "float"}
            },
            {
                "name": "retry_payment",
                "description": "Triggers an immediate transaction execution attempt against the primary gateway.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "check_payment_status",
                "description": "Queries the banking rails / NPCI / Card switch to verify whether the payment has already settled.",
                "parameters": {"payment_id": "string"}
            },
            {
                "name": "escalate_to_merchant",
                "description": "Hands off complex, high-value, or repeated failures to merchant operations queue with diagnostic briefing.",
                "parameters": {"payment_id": "string", "reason": "string", "priority": "string"}
            },
            {
                "name": "stop_recovery",
                "description": "Halts all active recovery workflows, cancels pending retries, and marks ticket as closed or unrecoverable.",
                "parameters": {"payment_id": "string", "reason": "string"}
            }
        ]

    def get_definitions(self) -> List[Dict[str, Any]]:
        return self.tool_definitions

    def execute_tool(self, tool_name: str, args: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes the specified tool with arguments and returns a structured audit output."""
        context = context or {}
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if tool_name == "get_payment_context":
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "payment_id": args.get("payment_id"),
                    "amount": context.get("amount", 2499.0),
                    "method": context.get("payment_method", "UPI"),
                    "failure_code": context.get("failure_code", "BANK_SERVER_ERROR"),
                    "failure_category": context.get("failure_category", "TEMPORARY_SYSTEM"),
                    "retry_count": context.get("retry_count", 0),
                    "notification_count": context.get("notification_count", 0)
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
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "recovery_probability": prob,
                    "expected_recovered_value": round(amount * prob, 2),
                    "recommended_action": context.get("ml_recommended_action", "RETRY_DELAYED"),
                    "risk_tier": "LOW" if prob > 0.7 else ("MEDIUM" if prob > 0.4 else "HIGH")
                }
            }

        elif tool_name == "schedule_smart_retry":
            delay = args.get("delay_minutes", 30)
            return {
                "tool": tool_name,
                "status": "SCHEDULED",
                "timestamp": timestamp,
                "output": {
                    "scheduled_delay_minutes": delay,
                    "target_route": args.get("route_override", "SECONDARY_FAST_UPI_SWITCH"),
                    "action_summary": f"Automated smart retry queued for execution in {delay} minutes."
                }
            }

        elif tool_name == "send_customer_notification":
            channel = args.get("channel", "WHATSAPP")
            template = args.get("template", "PAYMENT_RETRY_ONE_CLICK")
            return {
                "tool": tool_name,
                "status": "DELIVERED",
                "timestamp": timestamp,
                "output": {
                    "channel": channel,
                    "template": template,
                    "action_summary": f"Dispatched recovery notification via {channel} with template '{template}'."
                }
            }

        elif tool_name == "create_payment_link":
            pay_id = args.get("payment_id", "PAY_TEMP")
            link_id = f"plink_recov_{pay_id[-6:]}"
            url = f"https://pay.recoverai.io/{link_id}"
            return {
                "tool": tool_name,
                "status": "CREATED",
                "timestamp": timestamp,
                "output": {
                    "link_id": link_id,
                    "payment_url": url,
                    "validity_hours": args.get("validity_hours", 24),
                    "action_summary": f"Smart payment link created: {url}"
                }
            }

        elif tool_name == "retry_payment":
            # Simulate execution result based on ML recovery score
            prob = context.get("ml_recovery_probability", 0.75)
            succeeded = random.random() < prob
            return {
                "tool": tool_name,
                "status": "EXECUTED",
                "timestamp": timestamp,
                "output": {
                    "result": "PAYMENT_SUCCESS" if succeeded else "PAYMENT_FAILED_AGAIN",
                    "settled": succeeded,
                    "action_summary": "Direct retry processed on banking switch."
                }
            }

        elif tool_name == "check_payment_status":
            return {
                "tool": tool_name,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "output": {
                    "status": "PENDING_FAILED",
                    "settled": False,
                    "action_summary": "Status verified with banking switch: Payment remains pending/failed."
                }
            }

        elif tool_name == "escalate_to_merchant":
            return {
                "tool": tool_name,
                "status": "ESCALATED",
                "timestamp": timestamp,
                "output": {
                    "ticket_id": f"ESC_{random.randint(10000, 99999)}",
                    "priority": args.get("priority", "HIGH"),
                    "reason": args.get("reason", "Multiple recovery attempts exhausted"),
                    "action_summary": "Incident logged to merchant dashboard queue."
                }
            }

        elif tool_name == "stop_recovery":
            return {
                "tool": tool_name,
                "status": "HALTED",
                "timestamp": timestamp,
                "output": {
                    "reason": args.get("reason", "Guardrail policy limit reached or unrecoverable error"),
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
