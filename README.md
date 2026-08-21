# Alaadin ⚡
### Autonomous AI Payment Recovery Agent
**Track**: AI Revenue Recovery | **Repository**: [https://github.com/rehan0018/Alaadin](https://github.com/rehan0018/Alaadin)

> **One-line Pitch**: *Alaadin is an autonomous AI payment recovery agent that identifies failed payments, determines why each payment failed, calculates multi-action Expected Recovery Value (ERV), selects the safest intervention within merchant-configurable safety policies, verifies the outcome via direct banking status checks, and proves how much revenue it recovered.*

---

## 🎯 Architecture: `Detect → Understand → Decide (ERV) → Policy Boundary → Act → Verify → Stop`

Alaadin closes the loop between prediction and action while keeping the final authority with **merchant-defined safety policies**.

```
                 PAYMENT FAILURE EVENT
                          │
                          ▼
                ┌───────────────────┐
                │ Idempotency Layer │ (In-Memory for Demo / Redis in Prod)
                └─────────┬─────────┘
                          ▼
                ┌───────────────────┐
                │  Context Builder  │
                │(Payment + Customer│
                └─────────┬─────────┘
                          ▼
          ┌───────────────┴────────────────┐
          │                                │
          ▼                                ▼
 Failure Classifier                 Risk/Fraud Signal
          │                                │
          └───────────────┬────────────────┘
                          ▼
                ┌───────────────────┐
                │   Calibrated ML   │
                │    P(Recovery)    │
                │ Brier / ECE / PR  │
                └─────────┬─────────┘
                          ▼
                ┌───────────────────┐
                │   ERV Decision    │
                │ Action Selection  │
                └─────────┬─────────┘
                          ▼
                ┌───────────────────┐
                │   POLICY ENGINE   │
                │     HARD VETO     │
                └─────────┬─────────┘
                          ▼
                 APPROVE / BLOCKED /
                 MODIFY / HUMAN APPR
                          │
                          ▼
                ┌───────────────────┐
                │  Tool Execution   │
                └─────────┬─────────┘
                          ▼
                ┌───────────────────┐
                │Status Verification│
                └─────────┬─────────┘
                          ▼
                RECOVERED / UNSETTLED
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
      Decision Rationale        3-Way Benchmark
         Audit Trail              Evaluation
```

---

## 🛡️ The Hard Safety Boundary (Policy Engine)

Autonomous ML models and LLMs must **never have unchecked authority over money movement or customer outreach**. In Alaadin, the Agent Decision Engine proposes optimal interventions, but the **Policy Engine has the final, absolute veto**.

*Alaadin implements a merchant-configurable guardrail framework inspired by the principles of controlled agentic payment operations.*

### Core Financial Safety Guardrails:
1. **Payment State Lock**: Blocks all automated actions if the transaction has already settled (prevents race-condition double charges).
2. **72-Hour Recovery Window**: Calculates `time_since_failure_mins / 60.0` and immediately blocks any transaction older than 72 hours (`✗ 76.2h > 72h`).
3. **High-Ticket Ceiling (> ₹1,00,000)**: Mandates human supervisor authorization before executing actions on enterprise-tier amounts.
4. **Fraud Risk Gate**: Intercepts and freezes recovery workflows if fraud risk score exceeds `0.65`.
5. **Max Retry Ceiling**: Strict limit (3/3 retries) to prevent merchant gateway health score degradation.
6. **Customer Opt-Out & Contact Limits**: Strictly suppresses notifications if a customer has opted out or reached contact limits (2/2).
7. **Timezone-Aware Quiet Hours**: Delays outbound messaging during customer local quiet hours (`Asia/Kolkata` IST 10 PM - 8 AM).

---

## 📐 Expected Recovery Value (ERV) Action Optimization

Instead of static action mapping, Alaadin calculates multi-action ERV mathematically:

$$\text{ERV}(a) = P(\text{success} \mid \text{features}, a) \times \text{Amount} - \text{InterventionCost}(a) - \text{ContactCost}(a)$$

$$\text{Optimal Action} = \arg\max_{a} \text{ERV}(a) \quad \text{subject to Policy Engine Guardrails}$$

| Candidate Action | Base Cost | Contact Cost | Action Description |
| :--- | :--- | :--- | :--- |
| **`RETRY_DELAYED_30M`** | ₹0.00 | ₹0.00 | Cooldown retry over optimal secondary banking switch |
| **`SEND_WHATSAPP`** | ₹1.00 | ₹0.50 | Interactive 1-click WhatsApp payment prompt |
| **`SEND_PAYMENT_LINK`** | ₹2.00 | ₹1.00 | Dynamic SMS / Web payment link with alternate rails |
| **`ESCALATE_MERCHANT`** | ₹5.00 | ₹0.00 | Routing to human support operations with briefing |
| **`STOP`** | ₹0.00 | ₹0.00 | Cease recovery to prevent fraud / policy violation |

---

## 🔬 Calibrated ML Scorer (Zero Target-Leakage)

Trained with 5-fold cross-validation calibration (`CalibratedClassifierCV`) and validation-split threshold optimization.

### Holdout Test Metrics (7,500 Samples):
- **PR-AUC**: `0.7515` (Precision-Recall Area Under Curve for imbalanced recovery)
- **ROC-AUC**: `0.8133` (High discriminative separation)
- **Brier Score**: `0.1755` (Optimal probability sharpness)
- **Expected Calibration Error (ECE)**: `0.0283` ($< 3\%$ calibration divergence)
- **Precision**: `57.44%` | **Recall**: `95.97%`

*Note on Retraining: Alaadin measures intervention outcomes and uses them as evaluation signals for future model retraining.*

---

## 📊 Scientific 3-Way Benchmark Experiment (Identical 10,000 Cohort)

All three recovery architectures evaluated across the **exact same 10,000-payment test cohort against a Common Counterfactual Outcome Environment**:

| Evaluation Metric | Baseline A: Static Retry | Baseline B: Rule-Based | Alaadin Autonomous Agent | Measured Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Revenue Recovered** | ₹15.75 Lakhs | ₹19.40 Lakhs | **₹27.58 Lakhs** | **+75.1% vs Static / +42.1% vs Rules** |
| **Recovery Rate (%)** | 24.8% | 31.2% | **44.9%** | **+20.1% Absolute Gain** |
| **Average Recovery Time** | 22.8 Hours | 16.0 Hours | **5.2 Hours** | **17.6 Hours Faster** |
| **Customer Contacts** | 4,200 (Blind) | 3,100 (Heuristic) | **1,850 (Controlled)** | **56% Less Customer Spam** |
| **Unnecessary Retries** | 4,500 Wasted | 2,800 Wasted | **0 Wasted (Measured)** | **100% Efficient** |
| **Disallowed Actions Executed** | 185 Disallowed | 92 Disallowed | **0 Disallowed** | **100% Policy Bound** |
| **Cost per Recovery** | ₹14.50 | ₹8.20 | **₹2.80** | **Cost-Optimal** |

*Note: Simulated human-review recovery probability for enterprise escalations is evaluated at 35%.*

---

## 🧪 Agent Failure Lab: "What if the Agent is Wrong?"

Judges can stress-test edge cases in the dedicated **Failure Lab** in the dashboard:
1. **Payment Already Succeeded** → Agent attempts retry → Policy Engine: `✗ BLOCKED - State Lock Guardrail`
2. **Fraud Risk Score = 0.91** → Agent proposes payment link → Policy Engine: `✗ BLOCKED - Fraud Gate`
3. **3 Previous Retries Exhausted** → Agent wants to retry again → Policy Engine: `✗ BLOCKED - Max Retries Reached`
4. **Customer Opted Out** → Agent wants to send WhatsApp message → Policy Engine: `✗ BLOCKED - Opt-out Compliance`
5. **High-Value Transaction (₹2,00,000)** → Agent wants autonomous action → Policy Engine: `→ HUMAN SUPERVISOR APPROVAL REQUIRED`

---

## 📋 Decision Rationale Card Format

```
DECISION RATIONALE:
Payment: PAY_10291 (₹2,499 UPI)
Failure: BANK_SERVER_ERROR (Temporary Bank Outage)
Recovery Probability: 87% (ERV: ₹2,174)
Recommended Action: RETRY_DELAYED_30M

Why:
• Temporary gateway/bank outage detected
• Customer has 91% historical success rate
• 0 previous retries on active transaction
• Recovery window active (0.2h / 72h)

Policy Safety Checks:
✓ State Lock: Pending / Unsettled
✓ Recovery Window: 0.2h / 72.0h Active
✓ High-Value Ceiling: ₹2,499 < ₹1,00,000
✓ Fraud Risk: 0.03 <= 0.65
✓ Max Retries: 0 / 3 Retries

Enforced Action: RETRY EXECUTED via Secondary Switch
Verified Status: SETTLED_SUCCESS (₹2,499 Recovered)
```

---

## 🚀 Quick Start Guide

### 1. Run with Docker Compose:
```bash
docker compose up --build
```
Open `http://localhost:8000`.

### 2. Or Run Locally:
```bash
# Backend Setup
pip install -r requirements.txt
python backend/data_generator.py
python backend/ml_model.py
uvicorn backend.app:app --port 8000 --reload

# Frontend Setup
cd frontend
npm install
npm run dev
```

### 3. Run Automated Pytest Suite:
```bash
python -m pytest tests/ -v
```

---

## 🧭 5-Minute Judge Demo Script

1. **Minute 0–1 | Executive Dashboard**: Highlight Revenue at Risk, Recovered Revenue, and the **3-Way Benchmark Experiment Table**. Highlight: *"These numbers come from an apples-to-apples counterfactual benchmark, not hardcoded demo values."*
2. **Minute 1–2 | Interactive Sandbox**: Select `BANK_SERVER_ERROR`, inspect $P(\text{recovery}) = 87\%$, optimal action `RETRY_DELAYED_30M`, ERV, itemized policy checklist, and click **Execute**.
3. **Minute 2–3 | Agent Failure Lab**: Stress-test `Fraud Risk 0.91` (`✗ BLOCKED - Fraud Gate`) and `Already Succeeded` (`✗ BLOCKED - State Lock`).
4. **Minute 3–4 | Live Command Center**: Click **Run Live (WS)** or **Batch 1k** to stream transactions via WebSocket through `Detect → Understand → Decide (ERV) → Policy Boundary → Act → Verify → Stop`.
5. **Minute 4–5 | Audit Explorer**: Inspect the 5-step Decision Rationale and click **Export CSV** to demonstrate complete audit compliance.
