# 🗺️ RevenueShield Product Roadmap

This document outlines the development milestones, technical objectives, and future feature releases for **RevenueShield**.

---

## 📍 Phase 1: MVP Core Engine (Current — v1.0.0) ✅
- [x] **Dual-Layer Architecture**: ML Success Probability Estimation + Deterministic Policy Engine.
- [x] **Machine Learning Models**: Pre-trained classifiers for `retry`, `reminder`, and `escalation`.
- [x] **Expected Net Recovery Optimization**: EV formula factoring in dynamic intervention costs.
- [x] **Deterministic Policy & Safety Gate**: Configurable bounds, caps, and negative ROI rejection.
- [x] **Razorpay Test Mode Integration**: Automated Test Mode order creation and status tracking.
- [x] **Cryptographic Webhooks**: HMAC-SHA256 signature verification and event idempotency.
- [x] **SQLite Persistence & State Machine**: Full recovery case tracking through final settlement.
- [x] **Live Interactive Streamlit Dashboard**: Metrics KPI cards, transaction drilldown, and interactive sandbox.
- [x] **Immutable Audit Trail**: Structured JSON logs with automated credential sanitization.
- [x] **Automated Test Suite**: 100% passing pytest suite.

---

## 📍 Phase 2: Advanced Subscriptions & Smart Routing (Q4 2026) 🚀
- [ ] **Razorpay Subscriptions Auto-Dunning**: Dynamic smart dunning retry schedules based on customer salary cycles.
- [ ] **Multi-Channel Personalized Reminders**: Automated WhatsApp & SMS integration with Razorpay Payment Links API.
- [ ] **Adaptive Intervention Costing**: Real-time fee adjustments based on card network Interchange and merchant processing tiers.
- [ ] **LLM Explainability Agent**: Natural language rationale summaries for merchant finance executives.

---

## 📍 Phase 3: Multi-Merchant & Global Gateway Mesh (2027) 🌐
- [ ] **Cross-Gateway Intelligent Routing**: Dynamic failover across Razorpay, UPI Rails, and international merchant accounts.
- [ ] **Reinforcement Learning from Merchant Feedback (RLHF)**: Online policy optimization based on settlement outcomes.
- [ ] **Enterprise SSO & Role-Based Access Control (RBAC)**: Fine-grained permissions for finance and support agents.
