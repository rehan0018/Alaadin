"""
Alaadin - Synthetic Payment Dataset Generator (Zero-Leakage Design)
Generates 50,000 realistic payment records across UPI, Cards, NetBanking, and Mandates.
Strictly separates decision-time features from downstream execution outcomes.
"""

import os
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

FAILURE_REASONS = {
    "BANK_SERVER_ERROR": {
        "category": "TEMPORARY_SYSTEM",
        "description": "Issuer or acquirer bank server timeout/error",
        "base_recovery_prob": 0.82,
        "action_probs": {"RETRY_DELAYED_30M": 0.82, "SEND_PAYMENT_LINK": 0.50, "SEND_WHATSAPP": 0.55, "ESCALATE_MERCHANT": 0.30, "STOP": 0.0},
        "methods": ["UPI", "NETBANKING", "CREDIT_CARD", "DEBIT_CARD"],
    },
    "INSUFFICIENT_FUNDS": {
        "category": "CUSTOMER_FUNDS",
        "description": "Account or card balance below transaction amount",
        "base_recovery_prob": 0.56,
        "action_probs": {"RETRY_DELAYED_30M": 0.25, "SEND_PAYMENT_LINK": 0.62, "SEND_WHATSAPP": 0.58, "ESCALATE_MERCHANT": 0.20, "STOP": 0.0},
        "methods": ["UPI", "DEBIT_CARD", "NETBANKING", "MANDATE"],
    },
    "CARD_EXPIRED": {
        "category": "PERMANENT_INSTRUMENT",
        "description": "Credit/Debit card past expiration date",
        "base_recovery_prob": 0.22,
        "action_probs": {"RETRY_DELAYED_30M": 0.02, "SEND_PAYMENT_LINK": 0.45, "SEND_WHATSAPP": 0.48, "ESCALATE_MERCHANT": 0.15, "STOP": 0.0},
        "methods": ["CREDIT_CARD", "DEBIT_CARD"],
    },
    "UPI_TRANSACTION_LIMIT": {
        "category": "CUSTOMER_LIMIT",
        "description": "Exceeded daily UPI limit or single transaction limit",
        "base_recovery_prob": 0.64,
        "action_probs": {"RETRY_DELAYED_30M": 0.15, "SEND_PAYMENT_LINK": 0.68, "SEND_WHATSAPP": 0.64, "ESCALATE_MERCHANT": 0.25, "STOP": 0.0},
        "methods": ["UPI"],
    },
    "AUTH_FAILED_OTP_TIMEOUT": {
        "category": "AUTHENTICATION_FRICTION",
        "description": "3DS / OTP verification timed out or abandoned",
        "base_recovery_prob": 0.70,
        "action_probs": {"RETRY_DELAYED_30M": 0.35, "SEND_PAYMENT_LINK": 0.72, "SEND_WHATSAPP": 0.75, "ESCALATE_MERCHANT": 0.20, "STOP": 0.0},
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "NETWORK_TIMEOUT": {
        "category": "TEMPORARY_SYSTEM",
        "description": "Gateway network timeout during processing",
        "base_recovery_prob": 0.86,
        "action_probs": {"RETRY_DELAYED_30M": 0.86, "SEND_PAYMENT_LINK": 0.48, "SEND_WHATSAPP": 0.52, "ESCALATE_MERCHANT": 0.35, "STOP": 0.0},
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "MANDATE_EXECUTION_FAILED": {
        "category": "SUBSCRIPTION_MANDATE",
        "description": "Recurring mandate rejected by customer bank",
        "base_recovery_prob": 0.48,
        "action_probs": {"RETRY_DELAYED_30M": 0.42, "SEND_PAYMENT_LINK": 0.55, "SEND_WHATSAPP": 0.58, "ESCALATE_MERCHANT": 0.30, "STOP": 0.0},
        "methods": ["MANDATE", "CREDIT_CARD"],
    },
    "CHECKOUT_ABANDONED": {
        "category": "CUSTOMER_FRICTION",
        "description": "Customer dropped off before completing payment flow",
        "base_recovery_prob": 0.42,
        "action_probs": {"RETRY_DELAYED_30M": 0.10, "SEND_PAYMENT_LINK": 0.52, "SEND_WHATSAPP": 0.60, "ESCALATE_MERCHANT": 0.15, "STOP": 0.0},
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "FRAUD_SUSPECTED": {
        "category": "HIGH_RISK",
        "description": "High velocity or abnormal geolocation mismatch",
        "base_recovery_prob": 0.04,
        "action_probs": {"RETRY_DELAYED_30M": 0.01, "SEND_PAYMENT_LINK": 0.02, "SEND_WHATSAPP": 0.01, "ESCALATE_MERCHANT": 0.05, "STOP": 0.0},
        "methods": ["CREDIT_CARD", "DEBIT_CARD", "UPI"],
    },
    "INVALID_CVV_DETAILS": {
        "category": "PERMANENT_INSTRUMENT",
        "description": "Incorrect card details entered repeatedly",
        "base_recovery_prob": 0.26,
        "action_probs": {"RETRY_DELAYED_30M": 0.02, "SEND_PAYMENT_LINK": 0.48, "SEND_WHATSAPP": 0.52, "ESCALATE_MERCHANT": 0.18, "STOP": 0.0},
        "methods": ["CREDIT_CARD", "DEBIT_CARD"],
    }
}

ACTION_COSTS = {
    "RETRY_DELAYED_30M": 0.0,    # Zero direct gateway cost
    "SEND_PAYMENT_LINK": 2.0,    # SMS / Link generation fee ₹2
    "SEND_WHATSAPP": 1.0,        # WhatsApp business message fee ₹1
    "ESCALATE_MERCHANT": 5.0,    # Ops support handling cost ₹5
    "STOP": 0.0
}

MERCHANT_CATEGORIES = ["ECOMMERCE", "SAAS_SUBSCRIPTION", "EDTECH", "TRAVEL_HOSPITALITY", "FINTECH_LENDING", "FOOD_DELIVERY"]
PAYMENT_METHODS = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING", "MANDATE"]

def generate_synthetic_dataset(num_records: int = 50000) -> pd.DataFrame:
    """Generate 50,000 realistic payment records with strict decision-time features."""
    print(f"[*] Generating {num_records} synthetic payment records for Alaadin...")
    
    records = []
    base_time = datetime(2026, 8, 1, 0, 0, 0)
    
    for i in range(num_records):
        payment_id = f"PAY_{100000 + i}"
        customer_id = f"CUST_{random.randint(1000, 9999)}"
        merchant_id = f"MERCH_{random.randint(100, 999)}"
        merchant_category = random.choices(
            MERCHANT_CATEGORIES, 
            weights=[0.35, 0.25, 0.15, 0.10, 0.10, 0.05]
        )[0]
        
        # Payment Method
        payment_method = random.choices(
            PAYMENT_METHODS, 
            weights=[0.55, 0.20, 0.12, 0.08, 0.05]
        )[0]
        
        # Select compatible failure code
        compatible_failures = [
            code for code, data in FAILURE_REASONS.items()
            if payment_method in data["methods"]
        ]
        failure_code = random.choice(compatible_failures)
        failure_info = FAILURE_REASONS[failure_code]
        failure_category = failure_info["category"]
        
        # Amount in INR
        if merchant_category == "SAAS_SUBSCRIPTION":
            amount = float(random.choice([499, 999, 1499, 2499, 4999, 9999]))
        elif merchant_category == "ECOMMERCE":
            amount = float(np.random.lognormal(mean=6.8, sigma=0.9))
            amount = round(max(99.0, min(amount, 75000.0)), 2)
        elif merchant_category == "TRAVEL_HOSPITALITY":
            amount = float(random.randint(2500, 45000))
        elif merchant_category == "EDTECH":
            amount = float(random.choice([1999, 4999, 8999, 14999, 24999]))
        else:
            amount = float(round(random.uniform(199, 12000), 2))

        # Customer Transaction History
        customer_age_days = random.randint(1, 1200)
        previous_transactions = random.randint(0, 45)
        
        if previous_transactions == 0:
            previous_success_rate = 0.0
            previous_failures = 0
            previous_recovery_rate = 0.0
            customer_value = random.uniform(0.1, 0.4)
        else:
            previous_success_rate = round(random.betavariate(8, 2), 3)
            previous_failures = max(0, int(previous_transactions * (1.0 - previous_success_rate)))
            previous_recovery_rate = round(random.uniform(0.3, 0.9), 3)
            customer_value = round(min(1.0, (previous_transactions * 0.03) + (previous_success_rate * 0.5)), 3)

        # Retry and timing features available at decision time
        retry_count = random.choices([0, 1, 2, 3, 4], weights=[0.55, 0.25, 0.12, 0.05, 0.03])[0]
        notification_count = min(retry_count, random.choices([0, 1, 2, 3], weights=[0.50, 0.30, 0.15, 0.05])[0])
        time_since_failure_mins = random.randint(1, 180) if retry_count > 0 else 0
        
        hour = random.randint(0, 23)
        day = random.randint(0, 6)
        created_at = base_time + timedelta(
            days=random.randint(0, 20),
            hours=hour,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # Fraud risk score (0.00 to 1.00)
        if failure_category == "HIGH_RISK":
            fraud_risk_score = round(random.uniform(0.70, 0.98), 3)
        else:
            fraud_risk_score = round(random.betavariate(1, 9), 3)

        is_opted_out = int(random.random() < 0.04) # 4% opt-out
        is_already_succeeded = int(random.random() < 0.01) # 1% already succeeded
        subscription_type = "RECURRING" if (merchant_category == "SAAS_SUBSCRIPTION" or payment_method == "MANDATE") else "ONE_TIME"

        # Calculate True P(Recovery) for ground truth simulation
        base_prob = failure_info["base_recovery_prob"]
        if previous_transactions > 0:
            base_prob += (previous_success_rate - 0.7) * 0.22
        base_prob -= (retry_count * 0.15)
        if amount > 15000:
            base_prob -= 0.08
        if fraud_risk_score > 0.60:
            base_prob -= 0.55
        if 9 <= hour <= 21:
            base_prob += 0.05
        else:
            base_prob -= 0.05

        true_prob = float(np.clip(base_prob, 0.01, 0.96))
        
        # Determine Ground Truth outcome (1 = Recovered, 0 = Failed)
        recovery_success = 1 if (random.random() < true_prob and not is_opted_out and fraud_risk_score <= 0.65 and not is_already_succeeded) else 0
        
        # Optimal action selection via ERV logic
        action_ervs = {}
        for action_name, action_p in failure_info["action_probs"].items():
            mod_p = float(np.clip(action_p * (true_prob / (failure_info["base_recovery_prob"] + 1e-6)), 0.0, 0.98))
            cost = ACTION_COSTS[action_name]
            erv = (mod_p * amount) - cost
            action_ervs[action_name] = {"prob": round(mod_p, 3), "erv": round(erv, 2)}

        best_action = max(action_ervs.keys(), key=lambda a: action_ervs[a]["erv"])
        if retry_count >= 3:
            best_action = "ESCALATE_MERCHANT" if amount > 5000 else "STOP"
        if fraud_risk_score > 0.65 or is_already_succeeded:
            best_action = "STOP"

        recovered_amount = amount if recovery_success == 1 else 0.0
        time_to_recovery = round(random.uniform(0.2, 8.5), 2) if recovery_success == 1 else 0.0

        records.append({
            # Decision-time features (Features for ML model)
            "payment_id": payment_id,
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "merchant_category": merchant_category,
            "amount": amount,
            "payment_method": payment_method,
            "failure_code": failure_code,
            "failure_category": failure_category,
            "customer_age_days": customer_age_days,
            "previous_transactions": previous_transactions,
            "previous_success_rate": previous_success_rate,
            "previous_failures": previous_failures,
            "previous_recovery_rate": previous_recovery_rate,
            "customer_value": customer_value,
            "retry_count": retry_count,
            "notification_count": notification_count,
            "time_since_failure_mins": time_since_failure_mins,
            "fraud_risk_score": fraud_risk_score,
            "is_opted_out": is_opted_out,
            "is_already_succeeded": is_already_succeeded,
            "subscription_type": subscription_type,
            "hour": hour,
            "day": day,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            
            # Ground-truth labels & outcomes (NOT used as ML input features)
            "optimal_action": best_action,
            "action_prob_retry": action_ervs["RETRY_DELAYED_30M"]["prob"],
            "action_prob_link": action_ervs["SEND_PAYMENT_LINK"]["prob"],
            "action_prob_whatsapp": action_ervs["SEND_WHATSAPP"]["prob"],
            "true_recovery_probability": round(true_prob, 3),
            "recovery_success": recovery_success,
            "recovered_amount": recovered_amount,
            "time_to_recovery_hours": time_to_recovery
        })

    df = pd.DataFrame(records)
    print(f"[OK] Generated {len(df)} records. Overall recovery rate: {(df['recovery_success'].mean() * 100):.2f}%")
    return df

def save_and_split_dataset(df: pd.DataFrame, output_dir: str = "backend/data"):
    """Splits dataset into 70% train, 15% validation, and 15% test, saving CSVs."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Shuffle
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    n = len(df)
    train_end = int(0.70 * n)
    val_end = int(0.85 * n)
    
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]
    
    full_path = os.path.join(output_dir, "payments_50k_full.csv")
    train_path = os.path.join(output_dir, "payments_train.csv")
    val_path = os.path.join(output_dir, "payments_val.csv")
    test_path = os.path.join(output_dir, "payments_test.csv")
    
    df.to_csv(full_path, index=False)
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"[OK] Datasets saved successfully:")
    print(f"    - Full: {full_path} ({len(df)} rows)")
    print(f"    - Train: {train_path} ({len(train_df)} rows)")
    print(f"    - Val:   {val_path} ({len(val_df)} rows)")
    print(f"    - Test:  {test_path} ({len(test_df)} rows)")

if __name__ == "__main__":
    df = generate_synthetic_dataset(50000)
    save_and_split_dataset(df, output_dir="backend/data")
