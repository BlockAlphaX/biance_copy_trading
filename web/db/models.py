"""SQLAlchemy ORM models for the application."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from .session import Base


class TimestampMixin:
    """Shared timestamp columns."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AccountType(enum.Enum):
    """Account classification."""

    MASTER = "master"
    FOLLOWER = "follower"


class Account(Base, TimestampMixin):
    """Persisted account metadata and current state."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    type = Column(Enum(AccountType, name="account_type"), nullable=False)
    balance = Column(Float, server_default="0", nullable=False)
    available_balance = Column(Float, server_default="0", nullable=False)
    leverage = Column(Integer, server_default="1", nullable=False)
    margin_type = Column(String(32), nullable=True)
    position_mode = Column(String(32), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    details = Column(JSON, nullable=True)


class TradeRecord(Base):
    """Historical trade executions recorded from the engine."""

    __tablename__ = "trade_records"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
    )
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    account_name = Column(String(128), nullable=False, index=True)
    account_type = Column(Enum(AccountType, name="trade_account_type"), nullable=False)
    symbol = Column(String(32), nullable=False, index=True)
    side = Column(String(8), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    notional = Column(Float, nullable=True)
    order_type = Column(String(16), nullable=True)
    position_side = Column(String(16), nullable=True)
    status = Column(String(32), nullable=True)
    error = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RiskAlert(Base, TimestampMixin):
    """Stored risk alerts and acknowledgement state."""

    __tablename__ = "risk_alerts"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
    )
    level = Column(String(32), nullable=False)
    alert_type = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    context = Column(JSON, nullable=True)


class MetricSnapshot(Base):
    """Time-series metrics captured from the trading engine."""

    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(64), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SystemEvent(Base):
    """Application-level events and log entries."""

    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    level = Column(String(16), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SystemState(Base):
    """Key-value store for persisting engine state."""

    __tablename__ = "system_state"

    key = Column(String(64), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
