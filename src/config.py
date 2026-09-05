"""Central Configuration Management for RevenueShield.
All configurations are dynamically loaded from environment variables.
No hardcoded secrets or environment-specific thresholds are present in code.
"""
from pathlib import Path
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Razorpay Credentials (TEST MODE ONLY)
    razorpay_key_id: Optional[str] = Field(default=None, alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(default=None, alias="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: Optional[str] = Field(default=None, alias="RAZORPAY_WEBHOOK_SECRET")

    # Application Environment & Mode
    app_env: str = Field(default="development", alias="APP_ENV")
    app_mode: str = Field(default="TEST_MODE", alias="APP_MODE")

    # Network Configuration
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    dashboard_port: int = Field(default=8501, alias="DASHBOARD_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Persistence & Paths
    database_url: str = Field(default="sqlite:///./revenueshield.db", alias="DATABASE_URL")
    models_dir: str = Field(default="models", alias="MODELS_DIR")
    data_dir: str = Field(default="data", alias="DATA_DIR")

    # Deterministic Policy Engine Settings
    policy_max_transaction_amount: float = Field(default=500000.0, alias="POLICY_MAX_TRANSACTION_AMOUNT")
    policy_min_expected_value: float = Field(default=0.0, alias="POLICY_MIN_EXPECTED_VALUE")
    policy_max_escalation_amount: float = Field(default=100000.0, alias="POLICY_MAX_ESCALATION_AMOUNT")
    policy_high_risk_ev_threshold: float = Field(default=100.0, alias="POLICY_HIGH_RISK_EV_THRESHOLD")
    policy_low_risk_ev_threshold: float = Field(default=1000.0, alias="POLICY_LOW_RISK_EV_THRESHOLD")

    # Intervention Action Costs (INR)
    cost_retry: float = Field(default=2.0, alias="COST_RETRY")
    cost_reminder: float = Field(default=1.0, alias="COST_REMINDER")
    cost_escalation: float = Field(default=15.0, alias="COST_ESCALATION")

    @computed_field
    @property
    def action_costs(self) -> Dict[str, float]:
        return {
            "retry": float(self.cost_retry),
            "reminder": float(self.cost_reminder),
            "escalation": float(self.cost_escalation)
        }

    @computed_field
    @property
    def is_demo_simulation(self) -> bool:
        return str(self.app_mode).strip().upper() == "DEMO_SIMULATION"

    @computed_field
    @property
    def is_test_mode(self) -> bool:
        return not self.is_demo_simulation

    @computed_field
    @property
    def resolved_models_dir(self) -> Path:
        p = Path(self.models_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @computed_field
    @property
    def resolved_data_dir(self) -> Path:
        p = Path(self.data_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @computed_field
    @property
    def has_razorpay_credentials(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    def safe_dict(self) -> dict:
        """Return safe configuration dictionary without exposing secrets."""
        return {
            "app_env": self.app_env,
            "app_mode": self.app_mode,
            "is_test_mode": self.is_test_mode,
            "is_demo_simulation": self.is_demo_simulation,
            "has_razorpay_credentials": self.has_razorpay_credentials,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "dashboard_port": self.dashboard_port,
            "database_url": self.database_url,
            "policy": {
                "max_transaction_amount": self.policy_max_transaction_amount,
                "min_expected_value": self.policy_min_expected_value,
                "max_escalation_amount": self.policy_max_escalation_amount,
                "high_risk_ev_threshold": self.policy_high_risk_ev_threshold,
                "low_risk_ev_threshold": self.policy_low_risk_ev_threshold,
                "action_costs": self.action_costs,
            }
        }

settings = Settings()
