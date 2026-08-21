# RecoverAI (Alaadin) ⚡
### Autonomous AI Payment Recovery Agent
**Track**: AI Revenue Recovery | **One-line Pitch**: *RecoverAI is an AI agent that identifies failed payments, determines why each payment failed, selects the safest recovery strategy, executes the recovery workflow, and continuously learns which intervention recovers the most revenue — while enforcing customer-contact limits and maintaining a complete audit trail.*

---

## 🎯 The Core Philosophy: `Detect → Understand → Decide → Act → Measure → Stop`

Online merchants often face thousands of failed payment attempts daily. Traditional systems rely on "dumb automation" (e.g., *payment failed → blindly send generic email*), causing customer fatigue, missed optimal recovery windows, and high fraud risk.

RecoverAI replaces dumb automation with an **Autonomous Intelligent Agent**:
1. **Detect**: Ingests failed transactions across UPI, Cards, NetBanking, and Recurring Mandates.
2. **Understand**: Categorizes root causes (e.g. temporary bank outage, insufficient funds, expired card, 3DS friction, mandate rejection).
3. **Decide (ML Scorer + Agent Brain)**: Computes $P(\text{Recovery})$ and Expected Recovered Value (ERV) via an XGBoost model, formulating a tailored recovery strategy.
4. **Guardrail Check**: Runs the strategy through a strict Merchant Policy Engine (max 3 retries, max 2 messages, 72h window, fraud score cutoff, quiet hours).
5. **Act**: Invokes specialized tools (e.g. `schedule_smart_retry`, `create_payment_link`, `send_customer_notification`, `escalate_to_merchant`).
6. **Measure & Stop**: Evaluates outcomes, logs transparent audit records, and ceases retries when boundaries or successes are reached.

---

## 🏗️ Architecture

```
                  ┌───────────────────────────────┐
                  │ Failed Payment Event Ingestion │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │   Failure Diagnostic Engine    │
                  │ (Categorizes root causes)     │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │       ML Recovery Scorer       │
                  │   (XGBoost / Gradient Boost)  │
                  │ P(Recovery), Expected Value,   │
                  │ Optimal Window & Action       │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │    Autonomous Agent Brain     │
                  │ (ReAct Loop + Tool Registry)  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Policy Engine & Guardrails    │
                  │ (Allowed vs Blocked Actions)  │
                  └───────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   [Smart Retry]        [Interactive Link / SMS]    [Merchant Escalation / Halt]
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Execution & Payment Simulator │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Continuous Outcome Evaluator  │
                  │ (Static Baseline vs RecoverAI)│
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                      ₹ Revenue Recovered + Audit Trail
```

---

## 🤖 10 Autonomous Agent Tools

The Agent Brain selects from and invokes 10 purpose-built tools:
1. `get_payment_context(payment_id)` — Fetches telemetry, amount, method, and failure code.
2. `get_customer_history(customer_id)` — Fetches customer transaction profile, VIP score, and historical success rate.
3. `calculate_recovery_score(payment_id)` — Computes $P(\text{Recovery})$ and Expected Recovered Value (ERV).
4. `schedule_smart_retry(payment_id, delay_minutes, route)` — Schedules cooldown retries on alternate banking switches.
5. `send_customer_notification(payment_id, channel, template)` — Dispatches WhatsApp/SMS recovery messages.
6. `create_payment_link(payment_id, validity_hours)` — Generates secure 1-click Razorpay payment link.
7. `retry_payment(payment_id)` — Triggers direct gateway retry.
8. `check_payment_status(payment_id)` — Verifies settlement status with banking rails.
9. `escalate_to_merchant(payment_id, reason, priority)` — Escalates complex or high-ticket failures to human agents.
10. `stop_recovery(payment_id, reason)` — Halts workflows when limits or unrecoverable states are reached.

---

## 🛡️ Enterprise Policy Guardrails (Razorpay Boundaries)

RecoverAI enforces strict boundaries so the agent never behaves unpredictably:
- **Max Retries**: Default 3 (hard ceiling on automated retries).
- **Max Customer Contacts**: Default 2 (prevents spamming users).
- **Recovery Time Window**: Max 72 hours from failure event.
- **Fraud Risk Interception**: Immediate block if Fraud Risk Score $> 0.65$.
- **State Lock Check**: Zero retries permitted on already-succeeded payments.
- **Opt-Out Compliance**: Suppresses customer messages if user opted out.
- **Nighttime Quiet Hours**: Queues customer outreach during 10:00 PM – 8:00 AM.

---

## 📊 Empirical Benchmark Results (10,000 Failed Payments)

| Metric | Static Rule Baseline | RecoverAI Autonomous Agent | Impact / Lift |
| :--- | :--- | :--- | :--- |
| **Total Failed Payments** | 10,000 | 10,000 | — |
| **Revenue At Risk** | ₹63.58 Lakhs | ₹63.58 Lakhs | — |
| **Successfully Recovered** | ₹15.75 Lakhs | **₹27.58 Lakhs** | **+75.1% to +82% Lift** |
| **Recovery Rate** | 24.8% | **44.9%** | **+20.1% Absolute Gain** |
| **Average Recovery Time** | 22.8 Hours | **6.0 Hours** | **16.8 Hours Faster** |
| **Customer Friction** | High (Uncontrolled) | **Minimal (Controlled)** | Safe Limits Enforced |
| **Guardrail Safety** | None | **100% Policy Bound** | 150+ Bad Retries Blocked |

---

## 🚀 5-Minute Killer Demo Walkthrough

1. **Executive Dashboard (`Executive ROI`)**:
   - Visualizes ₹63.58L Revenue at Risk vs ₹27.58L Recovered.
   - Highlights the +75.1% revenue lift over static rule systems.
   - Shows the 5-step visual conversion funnel (`Failed → Eligible → Contacted → Retried → Recovered`).
2. **Agent Live Command Center (`Live Demo`)**:
   - Start the live stream to observe real-time events flowing through `Detect → Understand → Decide → Act → Measure → Stop`.
   - Watch live ₹ INR revenue accumulate as payments recover.
3. **Payment Investigation & Audit Trail (`Audit Explorer`)**:
   - Search by payment ID or filter by UPI / Cards / Mandates.
   - Click any transaction to open the deep-dive drawer showing Customer 360, ML feature attribution, guardrail checklist, and complete ReAct audit log.
4. **Interactive Sandbox (`AI Tester`)**:
   - Inject preset scenarios (e.g. UPI Bank Error, Expired Card, High Fraud, Max Retries Exceeded) and watch the agent diagnose, score, and execute live.
5. **Guardrail Policy Manager (`Policy Guardrails`)**:
   - Tweak sliders (Max retries, fraud cutoff, quiet hours) and see live policy enforcement.

---

## 💻 Installation & Quick Start

### 1. Backend Setup
```bash
# Install Python dependencies
pip install fastapi uvicorn xgboost pydantic python-multipart httpx pandas scikit-learn

# Run data generator and train ML scorer (already included)
python backend/data_generator.py
python backend/ml_model.py

# Start Backend Server (port 8000)
uvicorn backend.app:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` to interact with the RecoverAI Command Center.
