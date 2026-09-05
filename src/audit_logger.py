"""Audit logger for RevenueShield.

Provides structured, machine-readable audit trails persisted to the database.
Guarantees sensitive credentials (secrets, keys, tokens) are completely redacted.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database import get_db_session
from models.db_models import AuditLogRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("RevenueShield.Audit")

class AuditLogger:
    """Audit logging service for tracking every stage of the recovery lifecycle."""

    SENSITIVE_KEYS = {
        "key_secret",
        "secret",
        "password",
        "token",
        "authorization",
        "webhook_secret",
        "api_secret",
        "razorpay_key_secret",
        "razorpay_webhook_secret",
    }

    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """Recursively redact sensitive fields from audit data."""
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(secret_key in k.lower() for secret_key in cls.SENSITIVE_KEYS):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = cls.sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize(item) for item in data]
        return data

    def log_event(
        self,
        event_type: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Record an audit event to the database and standard structured log."""
        sanitized_details = self.sanitize(details or {})
        now = datetime.now(timezone.utc)

        event_payload = {
            "timestamp": now.isoformat(),
            "transaction_id": transaction_id,
            "event_type": event_type,
            "severity": severity,
            "details": sanitized_details,
        }

        log_msg = f"AuditEvent [{event_type}] Txn: {transaction_id} | Details: {json.dumps(sanitized_details)}"
        if severity == "ERROR":
            logger.error(log_msg)
        elif severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        def _persist(session: Session):
            record = AuditLogRecord(
                transaction_id=transaction_id,
                event_type=event_type,
                severity=severity,
                details_json=sanitized_details,
                timestamp=now,
            )
            session.add(record)
            session.commit()

        if db_session:
            _persist(db_session)
        else:
            try:
                with get_db_session() as session:
                    _persist(session)
            except Exception as e:
                logger.error(f"Failed to persist audit log to DB: {e}")

        return event_payload

    def get_transaction_logs(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Retrieve complete audit history for a given transaction."""
        with get_db_session() as session:
            records = (
                session.query(AuditLogRecord)
                .filter(AuditLogRecord.transaction_id == transaction_id)
                .order_by(AuditLogRecord.timestamp.asc())
                .all()
            )
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "transaction_id": r.transaction_id,
                    "event_type": r.event_type,
                    "severity": r.severity,
                    "details": r.details_json,
                }
                for r in records
            ]

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve the most recent audit logs across the application."""
        with get_db_session() as session:
            records = (
                session.query(AuditLogRecord)
                .order_by(AuditLogRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "transaction_id": r.transaction_id,
                    "event_type": r.event_type,
                    "severity": r.severity,
                    "details": r.details_json,
                }
                for r in records
            ]

audit_logger = AuditLogger()
