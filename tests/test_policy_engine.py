"""Tests for Deterministic Policy Engine."""
import pytest
from policy_engine import RecoveryPolicy, PolicyDecision

def test_policy_normal_approval():
    policy = RecoveryPolicy()
    decision = policy.evaluate(
        amount=5000.0,
        probabilities={"retry": 0.70, "reminder": 0.50, "escalation": 0.40}
    )
    assert decision.allowed is True
    assert decision.action == "retry"
    # EV = 0.70 * 5000 - 2.0 = 3498.0
    assert decision.expected_value == pytest.approx(3498.0)
    assert decision.risk_level == "low"

def test_policy_invalid_amount_zero_or_negative():
    policy = RecoveryPolicy()
    decision_zero = policy.evaluate(
        amount=0.0,
        probabilities={"retry": 0.70, "reminder": 0.50, "escalation": 0.40}
    )
    assert decision_zero.allowed is False
    assert "greater than zero" in decision_zero.reason

    decision_neg = policy.evaluate(
        amount=-100.0,
        probabilities={"retry": 0.70, "reminder": 0.50, "escalation": 0.40}
    )
    assert decision_neg.allowed is False

def test_policy_amount_exceeds_max():
    policy = RecoveryPolicy(max_transaction_amount=500000.0)
    decision = policy.evaluate(
        amount=600000.0,
        probabilities={"retry": 0.90, "reminder": 0.80, "escalation": 0.95}
    )
    assert decision.allowed is False
    assert "exceeds maximum automated recovery limit" in decision.reason

def test_policy_invalid_probability():
    policy = RecoveryPolicy()
    # Missing action
    decision_missing = policy.evaluate(
        amount=5000.0,
        probabilities={"retry": 0.70, "reminder": 0.50}
    )
    assert decision_missing.allowed is False
    assert "Missing recovery probability" in decision_missing.reason

    # Out of range
    decision_out_of_range = policy.evaluate(
        amount=5000.0,
        probabilities={"retry": 1.25, "reminder": 0.50, "escalation": 0.40}
    )
    assert decision_out_of_range.allowed is False
    assert "Invalid probability" in decision_out_of_range.reason

def test_policy_negative_expected_value():
    policy = RecoveryPolicy(min_expected_value=0.0)
    # Amount 5, costs: retry 2, reminder 1, escalation 15
    # Retry EV = 0.01 * 5 - 2 = -1.95
    # Reminder EV = 0.01 * 5 - 1 = -0.95
    # Escalation EV = 0.01 * 5 - 15 = -14.95
    decision = policy.evaluate(
        amount=5.0,
        probabilities={"retry": 0.01, "reminder": 0.01, "escalation": 0.01}
    )
    assert decision.allowed is False
    assert "minimum threshold" in decision.reason

def test_policy_escalation_cap():
    policy = RecoveryPolicy(max_escalation_amount=100000.0)
    decision = policy.evaluate(
        amount=150000.0,
        probabilities={"retry": 0.10, "reminder": 0.10, "escalation": 0.90},
        proposed_action="escalation"
    )
    assert decision.allowed is False
    assert "Escalation blocked" in decision.reason or "escalation blocked" in decision.reason.lower()
