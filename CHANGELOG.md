# Changelog

All notable changes to **RevenueShield** will be documented in this file.
The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-05

### Added
- **Core Architecture**: Dual-layer AI recovery estimation + Deterministic Safety & Economic Policy Gate.
- **Machine Learning**: Integrated pre-trained ML models for success probability estimation (`retry`, `reminder`, `escalation`).
- **Policy Engine**: Dynamic Expected Net Recovery calculation with configurable costs and safety thresholds.
- **Razorpay Integration**: Official Razorpay Test Mode client for test order creation and webhook signature validation.
- **Persistence Layer**: SQLite database schema with state machine lifecycle tracking.
- **Cryptographic Webhooks**: HMAC-SHA256 signature verification and event idempotency (`payment.captured`, `order.paid`, `payment.failed`).
- **Audit Logging**: Machine-readable immutable audit log with automatic secret redaction.
- **FastAPI Backend**: Full REST API with health check, metrics, evaluation, and execution endpoints.
- **Streamlit Dashboard**: Live interactive UI with KPI cards, pipeline diagram, transaction inspector, and recovery sandbox.
- **Automated Tests**: Comprehensive 21-test pytest suite covering all modules.
