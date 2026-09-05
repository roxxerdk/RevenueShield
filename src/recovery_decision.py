"""Revenue recovery decision service combining ML predictions and Policy Engine."""
from typing import Dict, Any, Optional
from recovery_predictor import RecoveryPredictor
from policy_engine import RecoveryPolicy, PolicyDecision

class RecoveryDecisionService:
    """Evaluates failed transactions using ML predictions + Policy Engine checks."""

    def __init__(
        self,
        predictor: Optional[RecoveryPredictor] = None,
        policy: Optional[RecoveryPolicy] = None,
    ):
        self.predictor = predictor or RecoveryPredictor()
        self.policy = policy or RecoveryPolicy()

    def decide(
        self,
        transaction: Dict[str, Any],
        proposed_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate ML prediction and run through deterministic policy gate."""
        # 1. Predict recovery probabilities with ML model
        probabilities = self.predictor.predict(transaction)

        amount = float(transaction.get("amount", 0.0))

        # 2. Evaluate against deterministic policy engine
        decision: PolicyDecision = self.policy.evaluate(
            amount=amount,
            probabilities=probabilities,
            proposed_action=proposed_action,
        )

        # 3. Return structured recovery decision payload
        return {
            "transaction_id": transaction.get("transaction_id"),
            "customer_id": transaction.get("customer_id"),
            "amount": amount,
            "currency": transaction.get("currency", "INR"),
            "probabilities": probabilities,
            "selected_action": decision.action,
            "allowed": decision.allowed,
            "expected_value": round(decision.expected_value, 2),
            "risk_level": decision.risk_level,
            "reason": decision.reason,
            "expected_values": {k: round(v, 2) for k, v in decision.expected_values.items()},
        }
