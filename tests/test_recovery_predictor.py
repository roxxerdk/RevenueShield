"""Tests for Recovery Predictor and Decision Service."""
import pytest
from recovery_predictor import RecoveryPredictor
from recovery_decision import RecoveryDecisionService

def test_recovery_predictor_output():
    predictor = RecoveryPredictor()
    txn = {
        "amount": 5000.0,
        "attempt_number": 1,
        "checkout_duration_sec": 120.0,
        "hour_of_day": 14,
        "day_of_week": 2,
        "account_age_days": 300,
        "total_transactions": 20,
        "successful_transactions": 15,
        "failed_transactions": 5,
        "historical_success_rate": 0.75,
        "average_transaction_value": 4500.0,
        "median_transaction_value": 4200.0,
        "total_spend": 90000.0,
        "days_since_last_success": 3,
        "previous_recovery_attempts": 0,
        "previous_recoveries": 0,
        "currency": "INR",
        "payment_method": "upi",
        "status": "failed",
        "failure_reason": "network_error",
        "failure_source": "network",
        "failure_step": "authorization",
        "device_type": "mobile",
        "customer_segment": "regular",
        "checkout_started": True,
        "is_subscription": False,
        "is_new_device": False,
    }

    probabilities = predictor.predict(txn)
    assert set(probabilities.keys()) == {"retry", "reminder", "escalation"}
    for act, prob in probabilities.items():
        assert 0.0 <= prob <= 1.0

def test_recovery_decision_service():
    service = RecoveryDecisionService()
    txn = {
        "transaction_id": "TEST_TXN_DEC_01",
        "amount": 5000.0,
        "payment_method": "card",
        "status": "failed",
        "failure_reason": "gateway_timeout",
    }
    decision = service.decide(txn)
    assert decision["transaction_id"] == "TEST_TXN_DEC_01"
    assert decision["amount"] == 5000.0
    assert "probabilities" in decision
    assert decision["selected_action"] in ["retry", "reminder", "escalation"]
    assert isinstance(decision["allowed"], bool)
    assert isinstance(decision["expected_value"], float)
