# 🛡️ RevenueShield: AI Revenue Recovery Engine
**Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery**

[![RevenueShield CI](https://github.com/roxxerdk/RevenueShield/actions/workflows/ci.yml/badge.svg)](https://github.com/roxxerdk/RevenueShield/actions/workflows/ci.yml)
[![CodeQL Security](https://github.com/roxxerdk/RevenueShield/actions/workflows/codeql.yml/badge.svg)](https://github.com/roxxerdk/RevenueShield/actions/workflows/codeql.yml)
[![Latest Release](https://img.shields.io/github/v/release/roxxerdk/RevenueShield?color=blue&label=release)](https://github.com/roxxerdk/RevenueShield/releases)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Test Suite](https://img.shields.io/badge/tests-23%20passed%20%2F%20100%25-success.svg)](tests/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)

RevenueShield is an AI-assisted, policy-governed revenue recovery system engineered for Razorpay payment failures and subscription involuntary churn. It combines machine learning predictive models with a deterministic economic and safety policy gate, executing bounded recovery actions via **Razorpay Test Mode** and verifying real revenue recovery through cryptographic webhook events.

---

## 📌 Problem Statement & Context

Payment failures in digital commerce and SaaS subscriptions cause substantial involuntary churn:
- **False Declines & Transient Failures**: Network timeouts, temporary bank outages, and velocity thresholds cause otherwise legitimate customer payments to fail.
- **Suboptimal Interventions**: Blindly retrying every failed transaction leads to wasted gateway fees, customer fatigue, and payment gateway velocity blocks. Conversely, manually escalating low-value transactions results in negative economic return.
- **Lack of Governance & Verification**: Pure AI/LLM systems lack deterministic safety bounds and cannot be trusted to execute financial transactions without strict policy constraints. Furthermore, creating a payment order does *not* constitute recovered revenue until cryptographic settlement is verified.

### The RevenueShield Solution
RevenueShield introduces a **Dual-Layer Architecture**:
1. **AI / ML Layer**: Recommends success probabilities across multiple recovery interventions (`retry`, `reminder`, `escalation`).
2. **Deterministic Policy Gate**: Has final decision authority, computing Expected Net Recovery ($\text{EV} = P(\text{success}) \times \text{amount} - \text{cost}$) and enforcing maximum recovery limits, minimum return thresholds, and escalation safety caps.
3. **Razorpay Test Mode Execution**: For retries, creates a new Razorpay Test Mode order for customer checkout.
4. **Cryptographic Webhook Verification**: Verifies HMAC-SHA256 signatures, enforces event idempotency, and confirms settlement before marking revenue as recovered.

---

## 🏛️ System Architecture & Workflow

```mermaid
flowchart TD
    A[Payment Failure / Risk Detected] --> B[Diagnostic Extraction]
    B --> C[ML Recovery Models]
    C -->|P(Retry), P(Reminder), P(Escalation)| D[Expected Value Calculator]
    D --> E{Deterministic Policy Gate}
    E -->|BLOCKED| F[Log Blocked Reason & Audit Trail]
    E -->|APPROVED| G{Action Dispatcher}
    G -->|Retry| H[Create Razorpay Test Mode Order]
    G -->|Reminder| I[Dispatch Internal Recovery Reminder]
    G -->|Escalation| J[Create High-Priority Escalation Task]
    H --> K[Customer Completes Checkout]
    K --> L[Razorpay Webhook: payment.captured]
    L --> M[HMAC-SHA256 Signature Verification]
    M --> N[Idempotency Check]
    N --> O[Verified Recovery State Transition]
    O --> P[Immutable Audit Trail & SQLite Persistence]
    P --> Q[Live Dynamic Streamlit Dashboard & API]
```

---

## ⚙️ Key Technical Features

### 1. Zero Hardcoded Values & Centralized Configuration
- All parameters (API credentials, webhook secrets, database URLs, action costs, policy thresholds, ports) are managed dynamically via `src/config.py` using `pydantic-settings`.
- Secrets are read exclusively from environment variables or `.env`. `.env` is protected in `.gitignore`.
- `.env.example` provides complete configuration documentation without exposing secrets.

### 2. Machine Learning Predictive Layer
- Uses pre-trained scikit-learn models (`models/retry_model.joblib`, `models/reminder_model.joblib`, `models/escalation_model.joblib`, and `models/recovery_preprocessor.joblib`).
- Predicts individual success probabilities: $P(\text{retry})$, $P(\text{reminder})$, $P(\text{escalation})$.
- Dynamically fills default values for unseen transaction features to prevent runtime prediction errors.

### 3. Deterministic Safety & Economic Policy Gate (`src/policy_engine.py`)
- Calculates Expected Net Recovery for each candidate intervention:
  $$\text{Expected Value} = P(\text{action}) \times \text{Transaction Amount} - \text{Intervention Cost}$$
- **Policy Invariants**:
  - `amount > 0` and `amount <= POLICY_MAX_TRANSACTION_AMOUNT` (e.g. ₹500,000 max).
  - Probabilities strictly bounded in $[0.0, 1.0]$.
  - Minimum Expected Value threshold (rejects negative or sub-threshold economic recovery).
  - Automated Escalation safety cap (blocks high-value automated escalation above `POLICY_MAX_ESCALATION_AMOUNT`, e.g. ₹100,000).
  - Risk Level classification: `low`, `medium`, `high`.

### 4. Official Razorpay Integration (Test Mode Only)
- Client implementation (`src/razorpay_client.py`) uses official `razorpay` SDK in Test Mode (`rzp_test_...`).
- Handles integer paise conversions (`amount_paise = int(round(amount * 100))`).
- Supports `DEMO_SIMULATION` mode when offline or without active test keys.
- **No fake APIs**: Does not pretend Razorpay has an arbitrary `retry_failed_payment()` API. For retries, creates a new Razorpay Test Mode order (`order_...`) for customer checkout.

### 5. Cryptographic Webhooks & Idempotency (`POST /webhooks/razorpay`)
- Cryptographically validates the `X-Razorpay-Signature` header using HMAC-SHA256 against `RAZORPAY_WEBHOOK_SECRET`.
- Enforces event idempotency: `event_id` is tracked in `WebhookEventRecord` to prevent duplicate processing or double-counting revenue.
- Updates recovery status and verifies recovered amount upon receiving `payment.captured` or `order.paid`.

### 6. SQLite Persistence & Lifecycle State Machine
- Lifecycle states: `AT_RISK` $\to$ `DIAGNOSED` $\to$ `DECISION_MADE` $\to$ `POLICY_APPROVED` / `POLICY_BLOCKED` $\to$ `ACTION_EXECUTED` $\to$ `PAYMENT_PENDING` $\to$ `PAYMENT_CAPTURED` $\to$ `RECOVERED` / `RECOVERY_FAILED`.
- Persists recovery cases, decisions, dispatched actions, webhook events, and audit logs.

### 7. Immutable Machine-Readable Audit Trail
- Structured audit logs record timestamps, transaction IDs, ML probabilities, policy decisions, execution payloads, and verification outcomes.
- Sensitive credentials (`api_secret`, `key_secret`, `password`, `token`, `webhook_secret`) are automatically redacted before logging or DB persistence.

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Virtual environment (recommended)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/roxxerdk/RevenueShield.git
cd RevenueShield

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```
Edit `.env` to configure your settings:
```ini
RAZORPAY_KEY_ID=rzp_test_your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
RAZORPAY_WEBHOOK_SECRET=your_test_webhook_secret

APP_ENV=development
APP_MODE=TEST_MODE

API_HOST=127.0.0.1
API_PORT=8000
DASHBOARD_PORT=8501

DATABASE_URL=sqlite:///./revenueshield.db
POLICY_MAX_TRANSACTION_AMOUNT=500000.0
POLICY_MIN_EXPECTED_VALUE=0.0
POLICY_MAX_ESCALATION_AMOUNT=100000.0
COST_RETRY=2.0
COST_REMINDER=1.0
COST_ESCALATION=15.0
```

---

## 💻 Running the Services

### 1. Start the FastAPI REST & Webhook Backend
```bash
# Set PYTHONPATH to include src
$env:PYTHONPATH="src"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### 2. Start the Interactive Streamlit Dashboard
```bash
$env:PYTHONPATH="src"
python -m streamlit run dashboard/app.py --server.port 8501
```
Dashboard UI: `http://localhost:8501`

### 3. Run the Automated Test Suite & Benchmarks
```bash
$env:PYTHONPATH="src"
python -m pytest tests/ -v
```

---

## 🎯 Step-by-Step Buildathon Demonstration

Follow this exact demonstration workflow:

1. **Open the Live Dashboard** at `http://localhost:8501`.
2. **View Executive KPIs**:
   - Inspect dynamically computed metrics: *Revenue at Risk*, *Recovered Revenue*, *Net Economic Gain*, *Recovery Rate %*, and *Action Breakdown*.
3. **Inspect Persisted Recovery Cases (Tab 2)**:
   - Filter by status (`PAYMENT_PENDING`, `RECOVERED`, `POLICY_BLOCKED`).
   - Select any transaction (e.g. `TXN1000043`) to view its failure diagnosis, ML probabilities ($P(\text{retry}), P(\text{reminder}), P(\text{escalation})$), Expected Net Recovery, Policy Gate approval, and full audit trail.
4. **Run Live Interactive Recovery Sandbox (Tab 3)**:
   - Enter a new failed transaction (e.g., `TXN_DEMO_2026`, Amount: ₹4,500, Reason: `network_error`).
   - Click **🚀 Run Recovery Pipeline**:
     - Step 1: Model estimates success probabilities ($P(\text{retry}) = 0.62$, etc.).
     - Step 2: Policy Gate validates economics and safety $\to$ `ALLOWED`.
     - Step 3: Executes action $\to$ creates Razorpay Test Mode Order (`order_...`). Status becomes `PAYMENT_PENDING`.
   - Click **Simulate Successful Payment (`payment.captured`)**:
     - Razorpay webhook event is received with HMAC verification and idempotency check.
     - State transitions to `RECOVERED`.
     - Metrics update dynamically!
5. **Inspect Machine-Readable Audit Logs (Tab 4)**:
   - Review immutable structured JSON audit events with all credentials safely redacted.

---

## 🔒 Security & Compliance Checklist

- [x] **No Hardcoded Secrets**: Zero credentials, API keys, or secrets in source code or git history.
- [x] **`.env` Protected**: `.env` is excluded in `.gitignore`; `.env.example` provides variable documentation only.
- [x] **Cryptographic Webhook Verification**: HMAC-SHA256 signature verification on all incoming webhook payloads.
- [x] **Idempotency Safeguard**: Webhook event IDs are tracked to eliminate duplicate event processing or double counting.
- [x] **Audit Log Redaction**: Sensitive keys are automatically sanitized prior to log recording.
- [x] **Bounded Action Execution**: AI recommendations are strictly constrained by the deterministic policy layer.
- [x] **Test Mode Only**: Explicitly restricted to Razorpay Test Mode (`rzp_test_...`) or Simulation Mode.

---

## 🗺️ Product Roadmap & Releases
- See [ROADMAP.md](ROADMAP.md) for future release milestones.
- See [CHANGELOG.md](CHANGELOG.md) for version history.
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute.

---

## 👥 Contributors & Acknowledgements
- Developed for the **Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery**.
