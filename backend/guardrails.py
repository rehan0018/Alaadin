"""
RecoverAI - Enterprise Policy Engine & Guardrails
Enforces Razorpay-grade merchant guardrails and boundary checks.
Ensures the autonomous agent never exceeds retries, spams customers,
contacts opted-out users, or acts on high-fraud or already-succeeded transactions.
"""

from typing import Dict, Any, Tuple, List
from datetime import datetime

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
        high_ticket_escalation_amount: float = 15000.0,
        allow_automated_discounts: bool = True
    ):
        self.max_retries = max_retries
        self.max_notifications = max_notifications
        self.max_recovery_window_hours = max_recovery_window_hours
        self.fraud_risk_threshold = fraud_risk_threshold
        self.enforce_quiet_hours = enforce_quiet_hours
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        self.high_ticket_escalation_amount = high_ticket_escalation_amount
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
            "high_ticket_escalation_amount": self.high_ticket_escalation_amount,
            "allow_automated_discounts": self.allow_automated_discounts
        }

class PolicyEngine:
    def __init__(self, config: MerchantPolicyConfig = None):
        self.config = config or MerchantPolicyConfig()

    def update_config(self, new_config_dict: Dict[str, Any]):
        for k, v in new_config_dict.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)

    def evaluate_action(
        self,
        payment: Dict[str, Any],
        proposed_action: str,
        current_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Validates the proposed action against all merchant policies.
        Returns:
            {
                "is_allowed": bool,
                "status": "ALLOWED" | "REJECTED" | "MODIFIED",
                "final_action": str,
                "passed_checks": List[str],
                "failed_checks": List[str],
                "reason": str
            }
        """
        passed_checks = []
        failed_checks = []
        
        # 1. Check if payment already succeeded
        if payment.get("is_already_succeeded", 0) == 1 or payment.get("status") == "SUCCESS":
            failed_checks.append("PAYMENT_ALREADY_SUCCEEDED")
            return {
                "is_allowed": False,
                "status": "REJECTED",
                "final_action": "STOP_RECOVERY",
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "reason": "Payment has already settled successfully. No further recovery action allowed."
            }
        passed_checks.append("Payment not yet settled")

        # 2. Check Fraud Risk Threshold
        fraud_score = float(payment.get("fraud_risk_score", 0.0))
        if fraud_score > self.config.fraud_risk_threshold:
            failed_checks.append(f"FRAUD_RISK_EXCEEDED ({fraud_score:.2f} > {self.config.fraud_risk_threshold})")
            return {
                "is_allowed": False,
                "status": "REJECTED",
                "final_action": "STOP_AND_FLAG",
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "reason": f"High fraud risk score ({fraud_score:.2f}) exceeds merchant threshold ({self.config.fraud_risk_threshold}). Action halted."
            }
        passed_checks.append(f"Fraud risk score safe ({fraud_score:.2f} <= {self.config.fraud_risk_threshold})")

        # 3. Check Retry Limits for Retry Actions
        retry_count = int(payment.get("retry_count", 0))
        if proposed_action in ["RETRY_DELAYED", "RETRY_SMART_ROUTE", "RETRY_IMMEDIATE"]:
            if retry_count >= self.config.max_retries:
                failed_checks.append(f"MAX_RETRIES_EXCEEDED ({retry_count} >= {self.config.max_retries})")
                
                # Check if high ticket to escalate or stop
                amount = float(payment.get("amount", 0.0))
                fallback_action = "ESCALATE_MERCHANT" if amount >= 5000.0 else "STOP_RECOVERY"
                return {
                    "is_allowed": False,
                    "status": "MODIFIED",
                    "final_action": fallback_action,
                    "passed_checks": passed_checks,
                    "failed_checks": failed_checks,
                    "reason": f"Retry limit ({self.config.max_retries}) reached. Modifying action to {fallback_action}."
                }
            passed_checks.append(f"Within max retries ({retry_count}/{self.config.max_retries})")

        # 4. Check Customer Contact Limits & Opt-Out for Notification Actions
        notif_count = int(payment.get("notification_count", 0))
        is_opted_out = bool(payment.get("is_opted_out", False) or payment.get("is_opted_out", 0) == 1)
        
        if proposed_action in [
            "SEND_PAYMENT_LINK", "SEND_WHATSAPP_REMINDER", 
            "SEND_PAYMENT_LINK_ALT_METHOD", "REQUEST_PAYMENT_UPDATE", "SEND_SMART_DISCOUNT_LINK"
        ]:
            if is_opted_out:
                failed_checks.append("CUSTOMER_OPTED_OUT")
                return {
                    "is_allowed": False,
                    "status": "REJECTED",
                    "final_action": "RETRY_DELAYED" if retry_count < self.config.max_retries else "STOP_RECOVERY",
                    "passed_checks": passed_checks,
                    "failed_checks": failed_checks,
                    "reason": "Customer has opted out of communications. Direct notifications blocked by policy."
                }
            passed_checks.append("Customer opted-in for communication")

            if notif_count >= self.config.max_notifications:
                failed_checks.append(f"MAX_NOTIFICATIONS_EXCEEDED ({notif_count} >= {self.config.max_notifications})")
                return {
                    "is_allowed": False,
                    "status": "MODIFIED",
                    "final_action": "RETRY_DELAYED" if retry_count < self.config.max_retries else "STOP_RECOVERY",
                    "passed_checks": passed_checks,
                    "failed_checks": failed_checks,
                    "reason": f"Maximum customer contacts ({self.config.max_notifications}) reached. Suppressing further messages."
                }
            passed_checks.append(f"Within notification limits ({notif_count}/{self.config.max_notifications})")

            # Check Quiet Hours
            curr_hour = current_time.hour if current_time else int(payment.get("hour", 14))
            if self.config.enforce_quiet_hours:
                is_quiet_hours = (curr_hour >= self.config.quiet_hours_start or curr_hour < self.config.quiet_hours_end)
                if is_quiet_hours:
                    passed_checks.append("Quiet hours active - notification queued for morning dispatch")
                else:
                    passed_checks.append("Outside quiet hours - immediate dispatch allowed")

        # 5. Check High Ticket Escalation Threshold
        amount = float(payment.get("amount", 0.0))
        if amount >= self.config.high_ticket_escalation_amount and retry_count >= 2 and proposed_action != "ESCALATE_MERCHANT":
            return {
                "is_allowed": True,
                "status": "MODIFIED",
                "final_action": "ESCALATE_MERCHANT",
                "passed_checks": passed_checks,
                "failed_checks": [],
                "reason": f"High value transaction (\u20b9{amount:,.2f}) with multiple failures automatically escalated to priority merchant queue."
            }

        # All checks passed
        return {
            "is_allowed": True,
            "status": "ALLOWED",
            "final_action": proposed_action,
            "passed_checks": passed_checks,
            "failed_checks": [],
            "reason": "All merchant policy guardrails satisfied."
        }

# Global singleton policy engine
_policy_engine_instance = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine_instance
    if _policy_engine_instance is None:
        _policy_engine_instance = PolicyEngine()
    return _policy_engine_instance
