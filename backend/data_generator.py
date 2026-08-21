"""
RecoverAI - Synthetic Payment Dataset Generator
Generates 50,000 realistic payment records across UPI, Cards, NetBanking, and Mandates.
Includes realistic failure causes, customer history, fraud indicators, and ground-truth recovery labels.
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
        "base_recovery_prob": 0.84,
        "ideal_action": "RETRY_DELAYED",
        "methods": ["UPI", "NETBANKING", "CREDIT_CARD", "DEBIT_CARD"],
    },
    "INSUFFICIENT_FUNDS": {
        "category": "CUSTOMER_FUNDS",
        "description": "Account or card balance below transaction amount",
        "base_recovery_prob": 0.58,
        "ideal_action": "SEND_PAYMENT_LINK",
        "methods": ["UPI", "DEBIT_CARD", "NETBANKING", "MANDATE"],
    },
    "CARD_EXPIRED": {
        "category": "PERMANENT_INSTRUMENT",
        "description": "Credit/Debit card past expiration date",
        "base_recovery_prob": 0.22,
        "ideal_action": "REQUEST_PAYMENT_UPDATE",
        "methods": ["CREDIT_CARD", "DEBIT_CARD"],
    },
    "UPI_TRANSACTION_LIMIT": {
        "category": "CUSTOMER_LIMIT",
        "description": "Exceeded daily UPI limit or single transaction limit",
        "base_recovery_prob": 0.65,
        "ideal_action": "SEND_PAYMENT_LINK_ALT_METHOD",
        "methods": ["UPI"],
    },
    "AUTH_FAILED_OTP_TIMEOUT": {
        "category": "AUTHENTICATION_FRICTION",
        "description": "3DS / OTP verification timed out or abandoned",
        "base_recovery_prob": 0.72,
        "ideal_action": "SEND_WHATSAPP_REMINDER",
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "NETWORK_TIMEOUT": {
        "category": "TEMPORARY_SYSTEM",
        "description": "Gateway network timeout during processing",
        "base_recovery_prob": 0.88,
        "ideal_action": "RETRY_SMART_ROUTE",
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "MANDATE_EXECUTION_FAILED": {
        "category": "SUBSCRIPTION_MANDATE",
        "description": "Recurring mandate rejected by customer bank",
        "base_recovery_prob": 0.49,
        "ideal_action": "SCHEDULE_RETRY_NOTIFY",
        "methods": ["MANDATE", "CREDIT_CARD"],
    },
    "CHECKOUT_ABANDONED": {
        "category": "CUSTOMER_FRICTION",
        "description": "Customer dropped off before completing payment flow",
        "base_recovery_prob": 0.41,
        "ideal_action": "SEND_SMART_DISCOUNT_LINK",
        "methods": ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING"],
    },
    "FRAUD_SUSPECTED": {
        "category": "HIGH_RISK",
        "description": "High velocity or abnormal geolocation mismatch",
        "base_recovery_prob": 0.05,
        "ideal_action": "STOP_AND_FLAG",
        "methods": ["CREDIT_CARD", "DEBIT_CARD", "UPI"],
    },
    "INVALID_CVV_DETAILS": {
        "category": "PERMANENT_INSTRUMENT",
        "description": "Incorrect card details entered repeatedly",
        "base_recovery_prob": 0.28,
        "ideal_action": "REQUEST_PAYMENT_UPDATE",
        "methods": ["CREDIT_CARD", "DEBIT_CARD"],
    }
}

MERCHANT_CATEGORIES = ["ECOMMERCE", "SAAS_SUBSCRIPTION", "EDTECH", "TRAVEL_HOSPITALITY", "FINTECH_LENDING", "FOOD_DELIVERY"]
PAYMENT_METHODS = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NETBANKING", "MANDATE"]

def generate_synthetic_dataset(num_records: int = 50000) -> pd.DataFrame:
    """Generate 50,000 realistic payment records with realistic recovery outcomes."""
    print(f"[*] Generating {num_records} synthetic payment records...")
    
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
        
        # Payment Method distribution (UPI is very dominant in India)
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
        
        # Transaction Amount (Realistic INR distribution)
        if merchant_category == "SAAS_SUBSCRIPTION":
            amount = float(random.choice([499, 999, 1499, 2499, 4999, 9999]))
        elif merchant_category == "ECOMMERCE":
            amount = float(np.random.lognormal(mean=6.8, sigma=0.9)) # ~₹400 - ₹15,000
            amount = round(max(99.0, min(amount, 75000.0)), 2)
        elif merchant_category == "TRAVEL_HOSPITALITY":
            amount = float(random.randint(2500, 45000))
        elif merchant_category == "EDTECH":
            amount = float(random.choice([1999, 4999, 8999, 14999, 24999]))
        else:
            amount = float(round(random.uniform(199, 12000), 2))

        # Customer History profile
        customer_age_days = random.randint(1, 1200)
        previous_transactions = random.randint(0, 45)
        
        if previous_transactions == 0:
            previous_success_rate = 0.0
            previous_failures = 0
            customer_value = random.uniform(0.1, 0.4)
        else:
            previous_success_rate = round(random.betavariate(8, 2), 3) # Skewed towards high success
            previous_failures = max(0, int(previous_transactions * (1.0 - previous_success_rate)))
            customer_value = round(min(1.0, (previous_transactions * 0.03) + (previous_success_rate * 0.5)), 3)

        # Retry and timing features
        retry_count = random.choices([0, 1, 2, 3, 4], weights=[0.55, 0.25, 0.12, 0.05, 0.03])[0]
        notification_count = min(retry_count, random.choices([0, 1, 2, 3], weights=[0.50, 0.30, 0.15, 0.05])[0])
        
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
            fraud_risk_score = round(random.betavariate(1, 9), 3) # skewed low

        is_opted_out = (random.random() < 0.04) # 4% opt-out rate
        is_already_succeeded = (random.random() < 0.01) # 1% race-condition check
        subscription_type = "RECURRING" if (merchant_category == "SAAS_SUBSCRIPTION" or payment_method == "MANDATE") else "ONE_TIME"

        # Calculate true recovery probability based on features
        base_prob = failure_info["base_recovery_prob"]
        
        # Modulate by customer success rate
        if previous_transactions > 0:
            base_prob += (previous_success_rate - 0.7) * 0.25
            
        # Modulate by retry count (decaying returns)
        base_prob -= (retry_count * 0.16)
        
        # Modulate by amount (larger amounts are harder to recover if insufficient funds)
        if amount > 15000:
            base_prob -= 0.08
            
        # Modulate by fraud risk
        if fraud_risk_score > 0.60:
            base_prob -= 0.55
            
        # Modulate by time of day (daytime recovery is higher for notification actions)
        if 9 <= hour <= 21:
            base_prob += 0.05
        else:
            base_prob -= 0.05

        true_prob = float(np.clip(base_prob, 0.01, 0.96))
        
        # Simulate outcome
        recovery_success = 1 if (random.random() < true_prob and not is_opted_out and fraud_risk_score <= 0.65) else 0
        
        # Recovery action executed
        recovery_action = failure_info["ideal_action"]
        if retry_count >= 3:
            recovery_action = "ESCALATE_MERCHANT" if amount > 5000 else "STOP_RECOVERY"
        if fraud_risk_score > 0.65:
            recovery_action = "STOP_AND_FLAG"
            recovery_success = 0
            
        recovered_amount = amount if recovery_success == 1 else 0.0
        
        # Time to recovery (in hours)
        if recovery_success == 1:
            if failure_category == "TEMPORARY_SYSTEM":
                time_to_recovery = round(random.uniform(0.1, 2.5), 2)
            elif failure_category in ["CUSTOMER_FUNDS", "CUSTOMER_LIMIT"]:
                time_to_recovery = round(random.uniform(1.0, 14.0), 2)
            elif failure_category == "AUTHENTICATION_FRICTION":
                time_to_recovery = round(random.uniform(0.2, 5.0), 2)
            else:
                time_to_recovery = round(random.uniform(2.0, 36.0), 2)
        else:
            time_to_recovery = 0.0

        records.append({
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
            "customer_value": customer_value,
            "retry_count": retry_count,
            "notification_count": notification_count,
            "fraud_risk_score": fraud_risk_score,
            "is_opted_out": int(is_opted_out),
            "is_already_succeeded": int(is_already_succeeded),
            "subscription_type": subscription_type,
            "hour": hour,
            "day": day,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "recovery_action": recovery_action,
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
