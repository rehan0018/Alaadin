"""
RecoverAI - Execution Simulator & Outcome Evaluator
Simulates payment recovery workflows and benchmarks RecoverAI vs Static Baseline.
Computes business metrics: Revenue at Risk, Total Recovered, Recovery Rate, Lift %, and Funnel stages.
"""

import os
import json
import random
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Generator
from datetime import datetime

try:
    from backend.agent_brain import get_recovery_agent
    from backend.guardrails import get_policy_engine
except ImportError:
    from .agent_brain import get_recovery_agent
    from .guardrails import get_policy_engine

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class PaymentSimulator:
    def __init__(self):
        self.agent = get_recovery_agent()
        self.policy_engine = get_policy_engine()
        self._load_dataset()

    def _load_dataset(self):
        csv_path = os.path.join(DATA_DIR, "payments_50k_full.csv")
        if os.path.exists(csv_path):
            self.df = pd.read_csv(csv_path)
        else:
            self.df = pd.DataFrame()

    def run_benchmark(self, sample_size: int = 10000) -> Dict[str, Any]:
        """
        Evaluates Static Baseline vs RecoverAI Autonomous Agent.
        Calculates exact business metrics requested in the prompt.
        """
        if self.df.empty:
            self._load_dataset()
            
        subset = self.df.head(sample_size).copy()
        
        total_failed_count = len(subset)
        revenue_at_risk = float(subset["amount"].sum())
        
        # -----------------------------------------------------------
        # 1. STATIC BASELINE SIMULATION:
        # Blindly retries once after 10 mins or sends generic email.
        # Fails on permanent errors (expired cards), misses optimal UPI windows,
        # wastes retries, incurs fraud risk.
        # -----------------------------------------------------------
        baseline_recovered_count = 0
        baseline_recovered_revenue = 0.0
        baseline_recovery_times = []
        
        for _, row in subset.iterrows():
            code = str(row["failure_code"])
            amt = float(row["amount"])
            fraud = float(row["fraud_risk_score"])
            
            # Static rule: only recovers temporary system errors partially, fails on customer friction/mandates
            if fraud > 0.65:
                # Blind retry on fraud causes chargebacks / zero recovery
                continue
            elif code in ["BANK_SERVER_ERROR", "NETWORK_TIMEOUT"]:
                if random.random() < 0.60: # Sub-optimal timing
                    baseline_recovered_count += 1
                    baseline_recovered_revenue += amt
                    baseline_recovery_times.append(12.5) # slower
            elif code in ["INSUFFICIENT_FUNDS", "AUTH_FAILED_OTP_TIMEOUT"]:
                if random.random() < 0.18: # Generic email has low click-through
                    baseline_recovered_count += 1
                    baseline_recovered_revenue += amt
                    baseline_recovery_times.append(28.0)
            elif code in ["CARD_EXPIRED", "INVALID_CVV_DETAILS", "MANDATE_EXECUTION_FAILED"]:
                # Static system has 0% recovery for invalid cards without smart method update
                if random.random() < 0.04:
                    baseline_recovered_count += 1
                    baseline_recovered_revenue += amt
                    baseline_recovery_times.append(48.0)
            else:
                if random.random() < 0.12:
                    baseline_recovered_count += 1
                    baseline_recovered_revenue += amt
                    baseline_recovery_times.append(24.0)

        baseline_recovery_rate = (baseline_recovered_count / total_failed_count) * 100.0
        baseline_avg_time = float(np.mean(baseline_recovery_times)) if baseline_recovery_times else 24.0

        # -----------------------------------------------------------
        # 2. RECOVERAI AGENT SIMULATION:
        # ML scored + tailored multi-channel actions + policy guardrails
        # -----------------------------------------------------------
        agent_recovered_count = 0
        agent_recovered_revenue = 0.0
        agent_recovery_times = []
        blocked_actions_count = 0
        active_recoveries_count = 0
        
        # Funnel Counters
        funnel = {
            "failed_payments": total_failed_count,
            "eligible_for_recovery": 0,
            "contacted_or_queued": 0,
            "retried_or_link_clicked": 0,
            "successfully_recovered": 0
        }
        
        category_breakdown = {}

        for _, row in subset.iterrows():
            payment_dict = row.to_dict()
            cat = str(payment_dict.get("failure_category", "OTHER"))
            if cat not in category_breakdown:
                category_breakdown[cat] = {"total_at_risk": 0.0, "recovered": 0.0, "count": 0, "recovered_count": 0}
            
            category_breakdown[cat]["total_at_risk"] += float(payment_dict["amount"])
            category_breakdown[cat]["count"] += 1

            result = self.agent.process_failed_payment(payment_dict)
            
            if result["policy_verdict"] in ["BLOCKED", "REJECTED"]:
                blocked_actions_count += 1
            else:
                funnel["eligible_for_recovery"] += 1
                
                if result["final_action"] in ["SEND_PAYMENT_LINK", "SEND_WHATSAPP_REMINDER", "SEND_PAYMENT_LINK_ALT_METHOD", "REQUEST_PAYMENT_UPDATE"]:
                    funnel["contacted_or_queued"] += 1
                    funnel["retried_or_link_clicked"] += 1
                elif result["final_action"] in ["RETRY_DELAYED", "RETRY_SMART_ROUTE", "RETRY_IMMEDIATE"]:
                    funnel["retried_or_link_clicked"] += 1
                
                if result["is_recovered"]:
                    agent_recovered_count += 1
                    agent_recovered_revenue += result["recovered_amount"]
                    agent_recovery_times.append(result["time_to_recovery_hours"])
                    funnel["successfully_recovered"] += 1
                    category_breakdown[cat]["recovered"] += result["recovered_amount"]
                    category_breakdown[cat]["recovered_count"] += 1
                else:
                    active_recoveries_count += 1

        agent_recovery_rate = (agent_recovered_count / total_failed_count) * 100.0
        agent_avg_time = float(np.mean(agent_recovery_times)) if agent_recovery_times else 7.2
        
        # Revenue Lift Calculation
        revenue_lift_pct = ((agent_recovered_revenue - baseline_recovered_revenue) / baseline_recovered_revenue) * 100.0 if baseline_recovered_revenue > 0 else 0.0
        rate_lift_pct = ((agent_recovery_rate - baseline_recovery_rate) / baseline_recovery_rate) * 100.0 if baseline_recovery_rate > 0 else 0.0

        return {
            "summary": {
                "total_failed_payments": total_failed_count,
                "revenue_at_risk_inr": round(revenue_at_risk, 2),
                "revenue_at_risk_lakhs": round(revenue_at_risk / 100000.0, 2),
                "recovered_inr": round(agent_recovered_revenue, 2),
                "recovered_lakhs": round(agent_recovered_revenue / 100000.0, 2),
                "recovery_rate_pct": round(agent_recovery_rate, 1),
                "avg_recovery_time_hours": round(agent_avg_time, 1),
                "active_recoveries": active_recoveries_count,
                "blocked_guardrail_actions": blocked_actions_count,
                "revenue_lift_pct": round(revenue_lift_pct, 1)
            },
            "comparison": {
                "baseline_static": {
                    "name": "Static Dumb Retry System",
                    "recovered_inr": round(baseline_recovered_revenue, 2),
                    "recovered_lakhs": round(baseline_recovered_revenue / 100000.0, 2),
                    "recovery_rate_pct": round(baseline_recovery_rate, 1),
                    "avg_recovery_time_hours": round(baseline_avg_time, 1),
                    "customer_friction_index": "HIGH (Uncontrolled messages)",
                    "guardrail_safety": "NONE (Retries on fraud & settled txns)"
                },
                "recover_ai": {
                    "name": "RecoverAI Autonomous Agent",
                    "recovered_inr": round(agent_recovered_revenue, 2),
                    "recovered_lakhs": round(agent_recovered_revenue / 100000.0, 2),
                    "recovery_rate_pct": round(agent_recovery_rate, 1),
                    "avg_recovery_time_hours": round(agent_avg_time, 1),
                    "customer_friction_index": "MINIMAL (Smart limits & quiet hours)",
                    "guardrail_safety": "ENTERPRISE (Strict boundaries & audit trail)"
                },
                "lift": {
                    "revenue_lift_pct": round(revenue_lift_pct, 1),
                    "rate_lift_pct": round(rate_lift_pct, 1),
                    "hours_saved": round(baseline_avg_time - agent_avg_time, 1)
                }
            },
            "funnel": funnel,
            "category_breakdown": category_breakdown
        }

    def get_sample_payments(self, count: int = 50, filter_type: str = "ALL") -> List[Dict[str, Any]]:
        """Returns sampled payments with pre-processed agent decisions."""
        if self.df.empty:
            self._load_dataset()
            
        sample = self.df.sample(min(count, len(self.df)), random_state=random.randint(1, 1000)).copy()
        
        results = []
        for _, row in sample.iterrows():
            res = self.agent.process_failed_payment(row.to_dict())
            results.append(res)
        return results

# Global singleton
_simulator_instance = None

def get_simulator() -> PaymentSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = PaymentSimulator()
    return _simulator_instance
