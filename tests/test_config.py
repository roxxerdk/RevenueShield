"""Tests for Central Configuration."""
import os
import pytest
from config import Settings, settings

def test_default_settings():
    assert settings.app_env in ["development", "test", "production"]
    assert settings.policy_max_transaction_amount == 500000.0
    assert settings.policy_min_expected_value == 0.0
    assert settings.policy_max_escalation_amount == 100000.0
    assert settings.action_costs == {"retry": 2.0, "reminder": 1.0, "escalation": 15.0}

def test_settings_safe_dict_redaction():
    safe = settings.safe_dict()
    assert "razorpay_key_secret" not in safe
    assert "razorpay_webhook_secret" not in safe
    assert "policy" in safe
    assert "action_costs" in safe["policy"]

def test_custom_settings_override(monkeypatch):
    monkeypatch.setenv("APP_MODE", "DEMO_SIMULATION")
    monkeypatch.setenv("POLICY_MAX_TRANSACTION_AMOUNT", "250000.0")
    monkeypatch.setenv("COST_RETRY", "5.0")
    
    custom_settings = Settings()
    assert custom_settings.is_demo_simulation is True
    assert custom_settings.is_test_mode is False
    assert custom_settings.policy_max_transaction_amount == 250000.0
    assert custom_settings.action_costs["retry"] == 5.0
