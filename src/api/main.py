"""FastAPI Backend and Razorpay Webhook Service for RevenueShield."""
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings
from database import init_db, get_db
from models.db_models import (
    RecoveryCase,
    RecoveryDecisionRecord,
    RecoveryActionRecord,
    AuditLogRecord,
    WebhookEventRecord,
    RecoveryState,
)
from recovery_workflow import recovery_workflow
from audit_logger import audit_logger
from razorpay_client import razorpay_client

# Initialize database
init_db()

app = FastAPI(
    title="RevenueShield API",
    description="AI-Assisted Revenue Recovery Platform with Deterministic Safety Policy & Razorpay Integration",
    version="1.0.0",
)

# Enable CORS for dashboard and frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("RevenueShield.API")

# -------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------

class TransactionEvaluationRequest(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID")
    amount: float = Field(..., gt=0, description="Transaction amount")
    customer_id: Optional[str] = Field(default=None)
    currency: str = Field(default="INR")
    payment_method: str = Field(default="card")
    status: str = Field(default="failed")
    failure_reason: Optional[str] = Field(default="gateway_timeout")
    failure_source: Optional[str] = Field(default="bank")
    failure_step: Optional[str] = Field(default="authorization")
    attempt_number: int = Field(default=1)
    account_age_days: int = Field(default=180)
    total_transactions: int = Field(default=10)
    successful_transactions: int = Field(default=8)
    historical_success_rate: float = Field(default=0.8)
    customer_segment: str = Field(default="regular")
    is_subscription: bool = Field(default=False)
    proposed_action: Optional[str] = Field(default=None)

class ExecuteRecoveryRequest(BaseModel):
    transaction_id: str
    proposed_action: Optional[str] = None

class SimulatePaymentRequest(BaseModel):
    amount: Optional[float] = None
    status: str = Field(default="captured", description="captured or failed")

# -------------------------------------------------------------
# Core API Routes
# -------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """System health check and runtime status."""
    return {
        "status": "healthy",
        "service": "RevenueShield",
        "version": "1.0.0",
        "mode": settings.app_mode,
        "is_test_mode": settings.is_test_mode,
        "is_simulation": settings.is_demo_simulation,
        "has_razorpay_credentials": settings.has_razorpay_credentials,
    }

@app.get("/api/config", tags=["System"])
def get_configuration():
    """Retrieve safe system configuration parameters."""
    return settings.safe_dict()

@app.get("/api/metrics", tags=["Metrics"])
def get_metrics(db: Session = Depends(get_db)):
    """Compute live, dynamically aggregated revenue recovery metrics from the database."""
    total_cases = db.query(RecoveryCase).count()
    if total_cases == 0:
        return {
            "total_cases": 0,
            "revenue_at_risk": 0.0,
            "recovered_revenue": 0.0,
            "net_recovered_revenue": 0.0,
            "recovery_rate_pct": 0.0,
            "pending_recoveries": 0,
            "failed_recoveries": 0,
            "policy_blocked_actions": 0,
            "actions_by_type": {"retry": 0, "reminder": 0, "escalation": 0},
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
        }

    revenue_at_risk = db.query(func.sum(RecoveryCase.amount)).scalar() or 0.0
    recovered_revenue = db.query(func.sum(RecoveryCase.amount_recovered)).scalar() or 0.0
    net_recovered = db.query(func.sum(RecoveryCase.net_recovered)).scalar() or 0.0
    recovered_count = db.query(RecoveryCase).filter(RecoveryCase.recovered == True).count()
    
    pending_count = db.query(RecoveryCase).filter(
        RecoveryCase.status.in_([RecoveryState.PAYMENT_PENDING.value, RecoveryState.ACTION_EXECUTED.value, RecoveryState.AT_RISK.value])
    ).count()

    failed_count = db.query(RecoveryCase).filter(
        RecoveryCase.status.in_([RecoveryState.RECOVERY_FAILED.value, RecoveryState.PAYMENT_FAILED.value])
    ).count()

    blocked_count = db.query(RecoveryCase).filter(
        RecoveryCase.status == RecoveryState.POLICY_BLOCKED.value
    ).count()

    # Action counts
    retry_count = db.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "retry").count()
    reminder_count = db.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "reminder").count()
    escalation_count = db.query(RecoveryActionRecord).filter(RecoveryActionRecord.action_type == "escalation").count()

    # Risk level distribution
    low_risk = db.query(RecoveryCase).filter(RecoveryCase.risk_level == "low").count()
    med_risk = db.query(RecoveryCase).filter(RecoveryCase.risk_level == "medium").count()
    high_risk = db.query(RecoveryCase).filter(RecoveryCase.risk_level == "high").count()

    recovery_rate = (recovered_count / total_cases * 100.0) if total_cases > 0 else 0.0

    return {
        "total_cases": total_cases,
        "revenue_at_risk": round(revenue_at_risk, 2),
        "recovered_revenue": round(recovered_revenue, 2),
        "net_recovered_revenue": round(net_recovered, 2),
        "recovery_rate_pct": round(recovery_rate, 2),
        "recovered_count": recovered_count,
        "pending_recoveries": pending_count,
        "failed_recoveries": failed_count,
        "policy_blocked_actions": blocked_count,
        "actions_by_type": {
            "retry": retry_count,
            "reminder": reminder_count,
            "escalation": escalation_count,
        },
        "risk_distribution": {
            "low": low_risk,
            "medium": med_risk,
            "high": high_risk,
        },
    }

@app.get("/api/recoveries", tags=["Recoveries"])
def list_recoveries(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List recovery cases with optional status filter and pagination."""
    query = db.query(RecoveryCase)
    if status_filter:
        query = query.filter(RecoveryCase.status == status_filter)

    cases = query.order_by(RecoveryCase.updated_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "transaction_id": c.transaction_id,
            "customer_id": c.customer_id,
            "amount": c.amount,
            "currency": c.currency,
            "status": c.status,
            "failure_reason": c.failure_reason,
            "failure_source": c.failure_source,
            "risk_level": c.risk_level,
            "recovered": c.recovered,
            "amount_recovered": c.amount_recovered,
            "net_recovered": c.net_recovered,
            "razorpay_order_id": c.razorpay_order_id,
            "razorpay_payment_id": c.razorpay_payment_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in cases
    ]

@app.get("/api/recoveries/{transaction_id}", tags=["Recoveries"])
def get_recovery_detail(transaction_id: str, db: Session = Depends(get_db)):
    """Get complete drill-down detail for a specific transaction including decisions, actions, and audit logs."""
    case = db.query(RecoveryCase).filter(RecoveryCase.transaction_id == transaction_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case '{transaction_id}' not found")

    decisions = [
        {
            "id": d.id,
            "p_retry": d.p_retry,
            "p_reminder": d.p_reminder,
            "p_escalation": d.p_escalation,
            "selected_action": d.selected_action,
            "expected_value": d.expected_value,
            "risk_level": d.risk_level,
            "allowed": d.allowed,
            "policy_reason": d.policy_reason,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in case.decisions
    ]

    actions = [
        {
            "id": a.id,
            "action_type": a.action_type,
            "status": a.status,
            "razorpay_order_id": a.razorpay_order_id,
            "razorpay_payment_id": a.razorpay_payment_id,
            "details": a.details_json,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in case.actions
    ]

    audit_logs = [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "event_type": l.event_type,
            "severity": l.severity,
            "details": l.details_json,
        }
        for l in case.audit_logs
    ]

    return {
        "case": {
            "transaction_id": case.transaction_id,
            "customer_id": case.customer_id,
            "amount": case.amount,
            "currency": case.currency,
            "status": case.status,
            "failure_reason": case.failure_reason,
            "failure_source": case.failure_source,
            "failure_step": case.failure_step,
            "risk_level": case.risk_level,
            "recovered": case.recovered,
            "amount_recovered": case.amount_recovered,
            "net_recovered": case.net_recovered,
            "razorpay_order_id": case.razorpay_order_id,
            "razorpay_payment_id": case.razorpay_payment_id,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        },
        "decisions": decisions,
        "actions": actions,
        "audit_logs": audit_logs,
    }

@app.post("/api/recoveries/evaluate", tags=["Recovery Actions"])
def evaluate_transaction(req: TransactionEvaluationRequest, db: Session = Depends(get_db)):
    """Evaluate a transaction with ML models and Deterministic Policy Engine."""
    decision = recovery_workflow.evaluate_and_record(
        transaction=req.model_dump(),
        proposed_action=req.proposed_action,
        db_session=db,
    )
    return decision

@app.post("/api/recoveries/execute", tags=["Recovery Actions"])
def execute_recovery(req: ExecuteRecoveryRequest, db: Session = Depends(get_db)):
    """Execute policy-approved recovery intervention for a transaction."""
    case = db.query(RecoveryCase).filter(RecoveryCase.transaction_id == req.transaction_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Transaction not found. Please evaluate first.")

    txn_dict = {
        "transaction_id": case.transaction_id,
        "customer_id": case.customer_id,
        "amount": case.amount,
        "currency": case.currency,
        "failure_reason": case.failure_reason,
    }

    # Retrieve or evaluate decision
    decision = recovery_workflow.evaluate_and_record(
        transaction=txn_dict,
        proposed_action=req.proposed_action,
        db_session=db
    )

    execution = recovery_workflow.execute_recovery(
        transaction=txn_dict,
        decision=decision,
        db_session=db
    )

    return {
        "decision": decision,
        "execution": execution,
    }

@app.post("/api/recoveries/{transaction_id}/simulate-payment", tags=["Demo & Testing"])
def simulate_customer_payment(
    transaction_id: str,
    req: SimulatePaymentRequest,
    db: Session = Depends(get_db)
):
    """Simulate customer checkout payment to test recovery verification and webhook lifecycle."""
    case = db.query(RecoveryCase).filter(RecoveryCase.transaction_id == transaction_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    amount = req.amount or case.amount
    simulated_event_id = f"evt_sim_{transaction_id}_{int(amount)}"
    simulated_payment_id = f"pay_sim_{transaction_id}"
    order_id = case.razorpay_order_id or f"order_sim_{transaction_id}"

    event_type = "payment.captured" if req.status == "captured" else "payment.failed"

    simulated_payload = {
        "event": event_type,
        "payload": {
            "payment": {
                "entity": {
                    "id": simulated_payment_id,
                    "order_id": order_id,
                    "amount": int(round(amount * 100)),
                    "currency": case.currency,
                    "status": req.status,
                    "notes": {
                        "original_transaction_id": transaction_id,
                    }
                }
            }
        }
    }

    result = recovery_workflow.process_webhook_event(
        event_id=simulated_event_id,
        event_type=event_type,
        payload=simulated_payload,
        signature="simulated_valid_signature",
        raw_body=json.dumps(simulated_payload).encode("utf-8")
    )

    return {
        "message": f"Simulated {event_type} processed successfully",
        "result": result,
    }

# -------------------------------------------------------------
# Razorpay Webhook Endpoint
# -------------------------------------------------------------

@app.post("/webhooks/razorpay", tags=["Webhooks"])
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """Receive and cryptographically verify incoming Razorpay Test Mode webhooks.
    Enforces signature verification, idempotency, and updates recovery states.
    """
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON webhook payload")

    event_id = payload.get("event_id") or payload.get("id") or f"evt_{hash(raw_body)}"
    event_type = payload.get("event")

    if not event_type:
        raise HTTPException(status_code=400, detail="Missing event type in webhook payload")

    result = recovery_workflow.process_webhook_event(
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature=x_razorpay_signature,
        raw_body=raw_body,
    )

    if result.get("status") == "rejected":
        raise HTTPException(status_code=400, detail=result.get("reason"))

    return result
