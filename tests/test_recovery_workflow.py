"""Tests for Recovery Workflow and Webhook Processing."""
import json
import pytest
from recovery_workflow import RevenueRecoveryWorkflow
from models.db_models import RecoveryState
from database import get_db_session
from models.db_models import RecoveryCase

def test_workflow_risk_detection():
    wf = RevenueRecoveryWorkflow()
    assert wf.detect_revenue_risk({"status": "failed"}) is True
    assert wf.detect_revenue_risk({"status": "subscription_failed"}) is True
    assert wf.detect_revenue_risk({"status": "abandoned"}) is True
    assert wf.detect_revenue_risk({"status": "captured", "failure_reason": None}) is False

def test_workflow_run_and_execution():
    wf = RevenueRecoveryWorkflow()
    txn = {
        "transaction_id": "TEST_WF_TXN_999",
        "amount": 3500.0,
        "currency": "INR",
        "status": "failed",
        "failure_reason": "network_error",
        "failure_source": "network",
    }
    
    res = wf.run(txn)
    assert res["risk_detected"] is True
    assert res["status"] in [
        RecoveryState.PAYMENT_PENDING.value,
        RecoveryState.REMINDER_SENT.value,
        RecoveryState.ESCALATED.value,
        RecoveryState.POLICY_BLOCKED.value,
    ]
    assert "diagnosis" in res
    assert "decision" in res
    assert "execution" in res

def test_webhook_idempotency_and_recovery_verification():
    wf = RevenueRecoveryWorkflow()
    tx_id = "TEST_WF_RECOVER_01"
    
    # Initialize a case
    wf.run({
        "transaction_id": tx_id,
        "amount": 2500.0,
        "currency": "INR",
        "status": "failed",
        "failure_reason": "bank_error",
    })

    # Webhook payload for payment.captured
    event_id = "evt_test_unique_1001"
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_recov_1001",
                    "order_id": "order_test_recov_1001",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {"original_transaction_id": tx_id},
                }
            }
        }
    }

    # Process first time in simulation mode
    res1 = wf.process_webhook_event(
        event_id=event_id,
        event_type="payment.captured",
        payload=payload,
        signature="sim_sig",
        raw_body=json.dumps(payload).encode("utf-8")
    )
    assert res1["status"] == "processed"
    assert res1["recovered"] is True
    assert res1["amount_recovered"] == 2500.0

    # Verify case status in DB
    with get_db_session() as session:
        case = session.query(RecoveryCase).filter(RecoveryCase.transaction_id == tx_id).first()
        assert case is not None
        assert case.recovered is True
        assert case.amount_recovered == 2500.0
        assert case.status == RecoveryState.RECOVERED.value

    # Process duplicate event (Idempotency test)
    res2 = wf.process_webhook_event(
        event_id=event_id,
        event_type="payment.captured",
        payload=payload,
        signature="sim_sig",
        raw_body=json.dumps(payload).encode("utf-8")
    )
    assert res2["status"] == "ignored"
    assert "Duplicate" in res2["reason"]
