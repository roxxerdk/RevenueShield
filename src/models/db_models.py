"""Database models for RevenueShield persistence."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class RecoveryState(str, Enum):
    AT_RISK = "AT_RISK"
    DIAGNOSED = "DIAGNOSED"
    DECISION_MADE = "DECISION_MADE"
    POLICY_APPROVED = "POLICY_APPROVED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_CAPTURED = "PAYMENT_CAPTURED"
    RECOVERED = "RECOVERED"
    RECOVERY_FAILED = "RECOVERY_FAILED"
    REMINDER_SENT = "REMINDER_SENT"
    ESCALATED = "ESCALATED"

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    transaction_id = Column(String(100), primary_key=True, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    order_id = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default=RecoveryState.AT_RISK.value, index=True)
    
    # Diagnosis details
    failure_reason = Column(String(100), nullable=True)
    failure_source = Column(String(100), nullable=True)
    failure_step = Column(String(100), nullable=True)
    risk_level = Column(String(20), default="medium")
    
    # Verification & Recovery
    recovered = Column(Boolean, default=False)
    amount_recovered = Column(Float, default=0.0)
    net_recovered = Column(Float, default=0.0)
    
    # Razorpay Test Mode reference
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    decisions = relationship("RecoveryDecisionRecord", back_populates="case", cascade="all, delete-orphan")
    actions = relationship("RecoveryActionRecord", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogRecord", back_populates="case", cascade="all, delete-orphan")

class RecoveryDecisionRecord(Base):
    __tablename__ = "recovery_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), ForeignKey("recovery_cases.transaction_id"), nullable=False, index=True)
    
    p_retry = Column(Float, nullable=False)
    p_reminder = Column(Float, nullable=False)
    p_escalation = Column(Float, nullable=False)
    
    selected_action = Column(String(50), nullable=False)
    expected_value = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    
    allowed = Column(Boolean, nullable=False)
    policy_reason = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=utc_now)

    case = relationship("RecoveryCase", back_populates="decisions")

class RecoveryActionRecord(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), ForeignKey("recovery_cases.transaction_id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    case = relationship("RecoveryCase", back_populates="actions")

class WebhookEventRecord(Base):
    __tablename__ = "webhook_events"

    event_id = Column(String(100), primary_key=True)
    event_type = Column(String(100), nullable=False, index=True)
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True, index=True)
    signature_verified = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)

class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), ForeignKey("recovery_cases.transaction_id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), default="INFO")
    details_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True)

    case = relationship("RecoveryCase", back_populates="audit_logs")
