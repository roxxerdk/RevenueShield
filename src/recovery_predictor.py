"""Revenue recovery probability predictor using pre-trained ML models."""
import os
from pathlib import Path
from typing import Dict, Any
import joblib
import pandas as pd
from config import settings

class RecoveryPredictor:
    """Loads RevenueShield recovery models and predicts success probabilities."""

    ACTIONS = ["retry", "reminder", "escalation"]

    # Default feature values for runtime transactions
    DEFAULT_FEATURES = {
        "amount": 1000.0,
        "attempt_number": 1,
        "checkout_duration_sec": 60.0,
        "hour_of_day": 12,
        "day_of_week": 2,
        "account_age_days": 180,
        "total_transactions": 10,
        "successful_transactions": 8,
        "failed_transactions": 2,
        "historical_success_rate": 0.8,
        "average_transaction_value": 1000.0,
        "median_transaction_value": 1000.0,
        "total_spend": 8000.0,
        "days_since_last_success": 5,
        "previous_recovery_attempts": 0,
        "previous_recoveries": 0,
        "currency": "INR",
        "payment_method": "card",
        "status": "failed",
        "failure_reason": "payment_gateway_error",
        "failure_source": "bank",
        "failure_step": "authorization",
        "subscription_status": None,
        "device_type": "mobile",
        "customer_segment": "regular",
        "checkout_started": True,
        "is_subscription": False,
        "is_new_device": False,
    }

    def __init__(self, models_dir: Path = None):
        self.models_dir = Path(models_dir) if models_dir else settings.resolved_models_dir
        
        preprocessor_path = self.models_dir / "recovery_preprocessor.joblib"
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Recovery preprocessor not found at {preprocessor_path}")
        
        self.preprocessor = joblib.load(preprocessor_path)
        
        self.models = {}
        for action in self.ACTIONS:
            model_path = self.models_dir / f"{action}_model.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"Model artifact not found for action '{action}' at {model_path}")
            self.models[action] = joblib.load(model_path)

    def prepare_features(self, transaction: Dict[str, Any]) -> pd.DataFrame:
        """Merge incoming transaction data with safe defaults for missing fields."""
        features = self.DEFAULT_FEATURES.copy()
        features.update(transaction)
        
        df = pd.DataFrame([features])
        
        # Ensure boolean features are encoded as integers
        boolean_features = ["checkout_started", "is_subscription", "is_new_device"]
        for col in boolean_features:
            if col in df.columns:
                df[col] = df[col].astype(int)
                
        return df

    def predict(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """Predict recovery probabilities for retry, reminder, and escalation."""
        df = self.prepare_features(transaction)
        X = self.preprocessor.transform(df)

        probabilities: Dict[str, float] = {}
        for action in self.ACTIONS:
            prob = self.models[action].predict_proba(X)[0][1]
            probabilities[action] = float(prob)

        return probabilities
