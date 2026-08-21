"""
RecoverAI - Merchant-Configurable Financial Safety Guardrails (Hard Policy Engine)
Enforces non-negotiable boundaries over autonomous agent actions.
Inspired by the principles of controlled agentic payment operations.
The Decision Engine proposes actions, but the Policy Engine has the final, absolute veto.
"""

from typing import Dict, Any, Tuple, List
from datetime import datetime, timezone
import zoneinfo

class MerchantPolicyConfig:
    def __init__(
        self,
        max_retries: int = 3,
        max_notifications: int = 2,
        max_recovery_window_hours: int = 72,
        fraud_risk_threshold: float = 0.65,
        enforce_quiet_hours: bool = True,
        quiet_hours_start: int = 22, # 10 PM
        quiet_hours_end: int = 8,    # 8 AM
        default_timezone: str = "Asia/Kolkata",
        high_ticket_approval_amount: float = 100000.0, # ₹1,00,000
        allow_automated_discounts: bool = True
    ):
        self.max_retries = max_retries
        self.max_notifications = max_notifications
        self.max_recovery_window_hours = max_recovery_window_hours
        self.fraud_risk_threshold = fraud_risk_threshold
        self.enforce_quiet_hours = enforce_quiet_hours
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        self.default_timezone = default_timezone
        self.high_ticket_approval_amount = high_ticket_approval_amount
        self.allow_automated_discounts = allow_automated_discounts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "max_notifications": self.max_notifications,
            "max_recovery_window_hours": self.max_recovery_window_hours,
            "fraud_risk_threshold": self.fraud_risk_threshold,
            "enforce_quiet_hours": self.enforce_quiet_hours,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "default_timezone": self.default_timezone,
            "high_ticket_approval_amount": self.high_ticket_approval_amount,
            "allow_automated_discounts": self.allow_automated_discounts
        }

class PolicyEngine:
    def __init__(self, config: MerchantPolicyConfig = None):
        self.config = config or MerchantPolicyConfig()

    def update_config(self, new_config_dict: Dict[str, Any]):
        for k, v in new_config_dict.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)

    def _get_local_hour(self, payment: Dict[str, Any], current_time: datetime = None) -> Tuple[int, str]:
        tz_name = payment.get("timezone") or self.config.default_timezone
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
            now = current_time or datetime.now(timezone.utc)
            local_time = now.astimezone(tz)
            return local_time.hour, tz_name
        except Exception:
            # Fallback to payment record hour or IST
            return int(payment.get("hour", 14)), tz_name

    def evaluate_action(
        self,
        payment: Dict[str, Any],
        proposed_action: str,
        current_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Hard Safety Boundary Gatekeeper.
        Evaluates proposed agent action against itemized merchant safety policies.
        Returns:
            {
                "is_allowed": bool,
                "status": "APPROVED" | "BLOCKED" | "MODIFIED" | "HUMAN_APPROVAL_REQUIRED",
                "final_action": str,
                "itemized_checks": List[Dict[str, Any]],
                "reason": str
            }
        """
        itemized_checks = []
        retry_count = int(payment.get("retry_count", 0))
        notif_count = int(payment.get("notification_count", 0))
        fraud_score = float(payment.get("fraud_risk_score", 0.0))
        amount = float(payment.get("amount", 0.0))
        is_opted_out = bool(payment.get("is_opted_out", 0) == 1 or payment.get("is_opted_out", False))
        is_already_succeeded = bool(payment.get("is_already_succeeded", 0) == 1 or payment.get("status") == "SUCCESS" or payment.get("is_settled", False))
        
        # 1. Recovery Window Calculation from time_since_failure_mins
        time_since_failure_mins = float(payment.get("time_since_failure_mins", 0.0))
        elapsed_hours = time_since_failure_mins / 60.0
        
        # 2. Timezone-aware quiet hours
        local_hour, tz_name = self._get_local_hour(payment, current_time)
        is_quiet = self.config.enforce_quiet_hours and (local_hour >= self.config.quiet_hours_start or local_hour < self.config.quiet_hours_end)

        # -------------------------------------------------------------
        # CHECK 1: State Lock (Already Succeeded Payment)
        # -------------------------------------------------------------
        if is_already_succeeded:
            itemized_checks.append({
                "rule": "Payment State Lock",
                "status": "FAIL",
                "display": "Settled as SUCCESS",
                "passed": False
            })
            return {
                "is_allowed": False,
                "status": "BLOCKED",
                "final_action": "STOP",
                "itemized_checks": itemized_checks,
                "reason": "Payment already settled successfully. All automated recovery actions blocked by State Lock guardrail."
            }
        itemized_checks.append({
            "rule": "Payment State Lock",
            "status": "PASS",
            "display": "Pending / Unsettled",
            "passed": True
        })

        # -------------------------------------------------------------
        # CHECK 2: Recovery Time Window (<= 72 Hours)
        # -------------------------------------------------------------
        if elapsed_hours > self.config.max_recovery_window_hours:
            itemized_checks.append({
                "rule": "Recovery Window",
                "status": "FAIL",
                "display": f"{elapsed_hours:.1f}h > {self.config.max_recovery_window_hours}h Exceeded",
                "passed": False
            })
            return {
                "is_allowed": False,
                "status": "BLOCKED",
                "final_action": "STOP",
                "itemized_checks": itemized_checks,
                "reason": f"Recovery time window exceeded ({elapsed_hours:.1f}h > {self.config.max_recovery_window_hours}h). Automated recovery halted."
            }
        itemized_checks.append({
            "rule": "Recovery Window",
            "status": "PASS",
            "display": f"{elapsed_hours:.1f}h / {self.config.max_recovery_window_hours}h Active",
            "passed": True
        })

        # -------------------------------------------------------------
        # CHECK 3: High-Ticket Hard Boundary (> ₹1,00,000)
        # -------------------------------------------------------------
        if amount >= self.config.high_ticket_approval_amount and proposed_action not in ["STOP", "ESCALATE_MERCHANT"]:
            itemized_checks.append({
                "rule": "High-Value Ceiling",
                "status": "MANUAL",
                "display": f"\u20b9{amount:,.0f} >= \u20b9{self.config.high_ticket_approval_amount:,.0f}",
                "passed": False
            })
            return {
                "is_allowed": False,
                "status": "HUMAN_APPROVAL_REQUIRED",
                "final_action": "ESCALATE_MERCHANT",
                "itemized_checks": itemized_checks,
                "reason": f"High-ticket transaction (\u20b9{amount:,.2f}) exceeds autonomous limit. Routed to human operations queue for review."
            }
        itemized_checks.append({
            "rule": "High-Value Ceiling",
            "status": "PASS",
            "display": f"\u20b9{amount:,.0f} < \u20b9{self.config.high_ticket_approval_amount:,.0f}",
            "passed": True
        })

        # -------------------------------------------------------------
        # CHECK 4: Fraud Risk Gate
        # -------------------------------------------------------------
        if fraud_score > self.config.fraud_risk_threshold:
            itemized_checks.append({
                "rule": "Fraud Risk Gate",
                "status": "FAIL",
                "display": f"{fraud_score:.2f} > {self.config.fraud_risk_threshold}",
                "passed": False
            })
            return {
                "is_allowed": False,
                "status": "BLOCKED",
                "final_action": "STOP",
                "itemized_checks": itemized_checks,
                "reason": f"Fraud risk score ({fraud_score:.2f}) exceeds merchant safety threshold ({self.config.fraud_risk_threshold}). Intercepted and frozen."
            }
        itemized_checks.append({
            "rule": "Fraud Risk Gate",
            "status": "PASS",
            "display": f"{fraud_score:.2f} <= {self.config.fraud_risk_threshold}",
            "passed": True
        })

        # -------------------------------------------------------------
        # CHECK 5: Retry Limits
        # -------------------------------------------------------------
        if "RETRY" in proposed_action:
            if retry_count >= self.config.max_retries:
                itemized_checks.append({
                    "rule": "Max Retry Limit",
                    "status": "FAIL",
                    "display": f"{retry_count} / {self.config.max_retries} Retries",
                    "passed": False
                })
                fallback = "ESCALATE_MERCHANT" if amount > 5000.0 else "STOP"
                return {
                    "is_allowed": False,
                    "status": "BLOCKED",
                    "final_action": fallback,
                    "itemized_checks": itemized_checks,
                    "reason": f"Maximum automated retry limit ({self.config.max_retries}) reached. Modifying action to {fallback}."
                }
            itemized_checks.append({
                "rule": "Max Retry Limit",
                "status": "PASS",
                "display": f"{retry_count} / {self.config.max_retries} Retries",
                "passed": True
            })

        # -------------------------------------------------------------
        # CHECK 6: Customer Outreach Limits, Opt-Out, & Quiet Hours
        # -------------------------------------------------------------
        if proposed_action in ["SEND_PAYMENT_LINK", "SEND_WHATSAPP"]:
            if is_opted_out:
                itemized_checks.append({
                    "rule": "Customer Opt-Out",
                    "status": "FAIL",
                    "display": "Opted Out",
                    "passed": False
                })
                fallback = "RETRY_DELAYED_30M" if retry_count < self.config.max_retries else "STOP"
                return {
                    "is_allowed": False,
                    "status": "BLOCKED",
                    "final_action": fallback,
                    "itemized_checks": itemized_checks,
                    "reason": "Customer opted out of communications. Outbound notifications blocked by merchant policy."
                }
            itemized_checks.append({
                "rule": "Customer Opt-Out",
                "status": "PASS",
                "display": "Opted In",
                "passed": True
            })

            if notif_count >= self.config.max_notifications:
                itemized_checks.append({
                    "rule": "Max Contact Limit",
                    "status": "FAIL",
                    "display": f"{notif_count} / {self.config.max_notifications} Contacts",
                    "passed": False
                })
                fallback = "RETRY_DELAYED_30M" if retry_count < self.config.max_retries else "STOP"
                return {
                    "is_allowed": False,
                    "status": "BLOCKED",
                    "final_action": fallback,
                    "itemized_checks": itemized_checks,
                    "reason": f"Maximum customer contacts ({self.config.max_notifications}) reached. Suppressing further outbound messages."
                }
            itemized_checks.append({
                "rule": "Max Contact Limit",
                "status": "PASS",
                "display": f"{notif_count} / {self.config.max_notifications} Contacts",
                "passed": True
            })

            # Timezone Quiet Hours
            if is_quiet:
                itemized_checks.append({
                    "rule": f"Quiet Hours ({tz_name})",
                    "status": "PASS_DELAYED",
                    "display": "Queued for 8:00 AM",
                    "passed": True
                })
            else:
                itemized_checks.append({
                    "rule": f"Quiet Hours ({tz_name})",
                    "status": "PASS",
                    "display": "Active Hours Allowed",
                    "passed": True
                })

        return {
            "is_allowed": True,
            "status": "APPROVED",
            "final_action": proposed_action,
            "itemized_checks": itemized_checks,
            "reason": "All merchant safety guardrails satisfied. Action approved for execution."
        }

# Global singleton policy engine
_policy_engine_instance = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine_instance
    if _policy_engine_instance is None:
        _policy_engine_instance = PolicyEngine()
    return _policy_engine_instance
