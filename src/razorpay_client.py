"""Razorpay Test Mode Client Service for RevenueShield.

Handles test orders, payments, and cryptographic webhook signature verification.
Never uses live mode. Falls back cleanly to DEMO_SIMULATION when credentials are not configured.
"""
import hmac
import hashlib
import uuid
from typing import Dict, Any, Optional
import razorpay
from config import settings
from audit_logger import audit_logger

class RazorpayTestClient:
    """Service wrapper for Razorpay Test Mode operations."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        is_simulation: Optional[bool] = None,
    ):
        self.key_id = key_id or settings.razorpay_key_id
        self.key_secret = key_secret or settings.razorpay_key_secret
        self.webhook_secret = webhook_secret or settings.razorpay_webhook_secret
        
        # Decide if running in pure simulation or live test API
        if is_simulation is not None:
            self.is_simulation = is_simulation
        else:
            self.is_simulation = settings.is_demo_simulation or not bool(self.key_id and self.key_secret)

        self._client: Optional[razorpay.Client] = None
        if not self.is_simulation and self.key_id and self.key_secret:
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new Razorpay Test Mode order for a recovery retry attempt.
        Amounts in Razorpay API are represented in the smallest currency sub-unit (paise for INR).
        """
        amount_paise = int(round(amount * 100))
        receipt_id = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"
        order_payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt_id,
            "notes": notes or {},
        }

        if self.is_simulation or self._client is None:
            # Deterministic simulation mode for offline demo
            simulated_order_id = f"order_sim_{uuid.uuid4().hex[:14]}"
            return {
                "id": simulated_order_id,
                "entity": "order",
                "amount": amount_paise,
                "amount_paid": 0,
                "amount_due": amount_paise,
                "currency": currency,
                "receipt": receipt_id,
                "status": "created",
                "notes": notes or {},
                "is_simulation": True,
            }

        try:
            order = self._client.order.create(data=order_payload)
            order["is_simulation"] = False
            return order
        except Exception as e:
            audit_logger.log_event(
                event_type="RAZORPAY_API_ERROR",
                details={"operation": "create_order", "error": str(e)},
                severity="ERROR"
            )
            raise RuntimeError(f"Razorpay Test Order creation failed: {e}")

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details from Razorpay Test API or simulation."""
        if self.is_simulation or self._client is None or order_id.startswith("order_sim_"):
            return {
                "id": order_id,
                "entity": "order",
                "status": "created",
                "is_simulation": True,
            }

        try:
            return self._client.order.fetch(order_id)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch order '{order_id}': {e}")

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from Razorpay Test API or simulation."""
        if self.is_simulation or self._client is None or payment_id.startswith("pay_sim_"):
            return {
                "id": payment_id,
                "entity": "payment",
                "status": "captured",
                "is_simulation": True,
            }

        try:
            return self._client.payment.fetch(payment_id)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch payment '{payment_id}': {e}")

    def verify_webhook_signature(
        self,
        body: bytes,
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """Cryptographically verify HMAC SHA256 webhook signature.
        Rejects any request where the signature does not match the computed digest.
        """
        webhook_secret = secret or self.webhook_secret
        if not webhook_secret:
            # If no secret configured, fail closed for security
            return False

        if not signature:
            return False

        try:
            expected_signature = hmac.new(
                key=webhook_secret.encode("utf-8"),
                msg=body,
                digestmod=hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

razorpay_client = RazorpayTestClient()
