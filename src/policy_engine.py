"""Deterministic safety and economic policy engine for RevenueShield.

The ML models recommend recovery probabilities.
The Policy Engine is the final, deterministic safety authority that decides
whether the proposed action is permitted to execute, enforcing economic viability
and safety thresholds loaded dynamically from configuration.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Set
from config import settings

@dataclass
class PolicyDecision:
    allowed: bool
    action: Optional[str]
    reason: str
    expected_value: float
    risk_level: str
    expected_values: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "reason": self.reason,
            "expected_value": self.expected_value,
            "risk_level": self.risk_level,
            "expected_values": self.expected_values,
        }

class RecoveryPolicy:
    """Deterministic safety and economic policy engine for RevenueShield."""

    ALLOWED_ACTIONS: Set[str] = {"retry", "reminder", "escalation"}

    def __init__(
        self,
        action_costs: Optional[Dict[str, float]] = None,
        max_transaction_amount: Optional[float] = None,
        min_expected_value: Optional[float] = None,
        max_escalation_amount: Optional[float] = None,
        high_risk_ev_threshold: Optional[float] = None,
        low_risk_ev_threshold: Optional[float] = None,
    ):
        # Load parameters dynamically from central configuration if not overridden
        self.action_costs = (
            action_costs if action_costs is not None else settings.action_costs
        )
        self.max_transaction_amount = (
            max_transaction_amount
            if max_transaction_amount is not None
            else settings.policy_max_transaction_amount
        )
        self.min_expected_value = (
            min_expected_value
            if min_expected_value is not None
            else settings.policy_min_expected_value
        )
        self.max_escalation_amount = (
            max_escalation_amount
            if max_escalation_amount is not None
            else settings.policy_max_escalation_amount
        )
        self.high_risk_ev_threshold = (
            high_risk_ev_threshold
            if high_risk_ev_threshold is not None
            else settings.policy_high_risk_ev_threshold
        )
        self.low_risk_ev_threshold = (
            low_risk_ev_threshold
            if low_risk_ev_threshold is not None
            else settings.policy_low_risk_ev_threshold
        )

    def calculate_expected_value(
        self,
        amount: float,
        probability: float,
        action: str,
    ) -> float:
        """Calculate expected net recovery for a specific action.
        Expected Value = P(success) * transaction_amount - intervention_cost
        """
        cost = self.action_costs.get(action, 0.0)
        return (probability * amount) - cost

    def evaluate(
        self,
        amount: float,
        probabilities: Dict[str, float],
        proposed_action: Optional[str] = None,
    ) -> PolicyDecision:
        """Evaluate recovery viability through deterministic rules."""
        # 1. Validate amount
        if amount is None or amount <= 0:
            return PolicyDecision(
                allowed=False,
                action=None,
                reason="Invalid transaction amount: Amount must be greater than zero",
                expected_value=0.0,
                risk_level="high",
                expected_values={},
            )

        if amount > self.max_transaction_amount:
            return PolicyDecision(
                allowed=False,
                action=None,
                reason=f"Transaction amount ({amount}) exceeds maximum automated recovery limit ({self.max_transaction_amount})",
                expected_value=0.0,
                risk_level="high",
                expected_values={},
            )

        # 2. Validate probabilities
        for action in self.ALLOWED_ACTIONS:
            prob = probabilities.get(action)
            if prob is None:
                return PolicyDecision(
                    allowed=False,
                    action=None,
                    reason=f"Missing recovery probability for '{action}'",
                    expected_value=0.0,
                    risk_level="high",
                    expected_values={},
                )
            if not (0.0 <= prob <= 1.0):
                return PolicyDecision(
                    allowed=False,
                    action=None,
                    reason=f"Invalid probability value for '{action}': {prob} (must be between 0.0 and 1.0)",
                    expected_value=0.0,
                    risk_level="high",
                    expected_values={},
                )

        # 3. Calculate expected values for all actions
        expected_values: Dict[str, float] = {}
        for action in self.ALLOWED_ACTIONS:
            expected_values[action] = self.calculate_expected_value(
                amount=amount,
                probability=probabilities[action],
                action=action,
            )

        # 4. Select economically optimal action
        best_action = max(expected_values, key=expected_values.get)
        best_expected_value = expected_values[best_action]

        # 5. Respect explicitly proposed action if supplied
        if proposed_action is not None:
            if proposed_action not in self.ALLOWED_ACTIONS:
                return PolicyDecision(
                    allowed=False,
                    action=None,
                    reason=f"Proposed action '{proposed_action}' is not in allowed actions: {list(self.ALLOWED_ACTIONS)}",
                    expected_value=0.0,
                    risk_level="high",
                    expected_values=expected_values,
                )
            best_action = proposed_action
            best_expected_value = expected_values[proposed_action]

        # 6. Reject sub-threshold / negative expected recovery
        if best_expected_value < self.min_expected_value:
            return PolicyDecision(
                allowed=False,
                action=best_action,
                reason=f"Expected net recovery ({best_expected_value:.2f}) does not meet minimum threshold ({self.min_expected_value})",
                expected_value=best_expected_value,
                risk_level="medium",
                expected_values=expected_values,
            )

        # 7. Escalation safety rule
        if best_action == "escalation" and amount > self.max_escalation_amount:
            return PolicyDecision(
                allowed=False,
                action=best_action,
                reason=f"Automated escalation blocked for high-value transaction exceeding cap ({self.max_escalation_amount})",
                expected_value=best_expected_value,
                risk_level="high",
                expected_values=expected_values,
            )

        # 8. Determine dynamic risk level
        if best_expected_value >= self.low_risk_ev_threshold:
            risk_level = "low"
        elif best_expected_value >= self.high_risk_ev_threshold:
            risk_level = "medium"
        else:
            risk_level = "high"

        return PolicyDecision(
            allowed=True,
            action=best_action,
            reason="Action passed deterministic economic and safety checks",
            expected_value=best_expected_value,
            risk_level=risk_level,
            expected_values=expected_values,
        )
