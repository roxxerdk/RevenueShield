"""Tests for Razorpay Client and Audit Logger."""
import hmac
import hashlib
import pytest
from razorpay_client import RazorpayTestClient
from audit_logger import AuditLogger

def test_razorpay_simulation_order_creation():
    client = RazorpayTestClient(is_simulation=True)
    order = client.create_order(
        amount=2500.50,
        currency="INR",
        receipt="rcpt_test_01",
        notes={"original_transaction_id": "TXN_SIM_01"}
    )
    assert order["entity"] == "order"
    assert order["amount"] == 250050  # Paise conversion
    assert order["currency"] == "INR"
    assert order["receipt"] == "rcpt_test_01"
    assert order["is_simulation"] is True

def test_razorpay_webhook_signature_verification():
    secret = "my_test_webhook_secret_123"
    client = RazorpayTestClient(webhook_secret=secret, is_simulation=False)
    
    payload = b'{"event":"payment.captured","id":"evt_123"}'
    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    
    # Valid signature
    assert client.verify_webhook_signature(body=payload, signature=valid_sig, secret=secret) is True
    
    # Invalid signature
    assert client.verify_webhook_signature(body=payload, signature="invalid_tampered_sig", secret=secret) is False
    
    # Empty signature
    assert client.verify_webhook_signature(body=payload, signature="", secret=secret) is False

def test_audit_logger_sanitization():
    raw_data = {
        "user_id": "user_123",
        "api_secret": "rzp_secret_topsecret",
        "nested": {
            "password": "supersecretpassword",
            "webhook_secret": "whsec_xyz",
            "amount": 5000,
        }
    }
    sanitized = AuditLogger.sanitize(raw_data)
    assert sanitized["user_id"] == "user_123"
    assert sanitized["api_secret"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["webhook_secret"] == "[REDACTED]"
    assert sanitized["nested"]["amount"] == 5000
