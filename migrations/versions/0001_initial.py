"""Initial schema for Binance Copy Trading service"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    account_type_enum = sa.Enum("master", "follower", name="account_type")
    trade_account_type_enum = sa.Enum("master", "follower", name="trade_account_type")

    bind = op.get_bind()
    account_type_enum.create(bind, checkfirst=True)
    trade_account_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", account_type_enum, nullable=False),
        sa.Column("balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("available_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("leverage", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("margin_type", sa.String(length=32), nullable=True),
        sa.Column("position_mode", sa.String(length=32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("name", name="uq_accounts_name"),
    )
    op.create_index("ix_accounts_name", "accounts", ["name"], unique=False)

    op.create_table(
        "system_state",
        sa.Column("key", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_metric_snapshots_category", "metric_snapshots", ["category"], unique=False)
    op.create_index("ix_metric_snapshots_recorded_at", "metric_snapshots", ["recorded_at"], unique=False)

    op.create_table(
        "risk_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_risk_alerts_level", "risk_alerts", ["level"], unique=False)

    op.create_table(
        "system_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="INFO"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_system_events_event_type", "system_events", ["event_type"], unique=False)
    op.create_index("ix_system_events_created_at", "system_events", ["created_at"], unique=False)

    op.create_table(
        "trade_records",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL")),
        sa.Column("account_name", sa.String(length=128), nullable=False),
        sa.Column("account_type", trade_account_type_enum, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("notional", sa.Float(), nullable=True),
        sa.Column("order_type", sa.String(length=16), nullable=True),
        sa.Column("position_side", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_trade_records_account_name", "trade_records", ["account_name"], unique=False)
    op.create_index("ix_trade_records_symbol", "trade_records", ["symbol"], unique=False)
    op.create_index("ix_trade_records_occurred_at", "trade_records", ["occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trade_records_occurred_at", table_name="trade_records")
    op.drop_index("ix_trade_records_symbol", table_name="trade_records")
    op.drop_index("ix_trade_records_account_name", table_name="trade_records")
    op.drop_table("trade_records")

    op.drop_index("ix_system_events_created_at", table_name="system_events")
    op.drop_index("ix_system_events_event_type", table_name="system_events")
    op.drop_table("system_events")

    op.drop_index("ix_risk_alerts_level", table_name="risk_alerts")
    op.drop_table("risk_alerts")

    op.drop_index("ix_metric_snapshots_recorded_at", table_name="metric_snapshots")
    op.drop_index("ix_metric_snapshots_category", table_name="metric_snapshots")
    op.drop_table("metric_snapshots")

    op.drop_table("system_state")

    op.drop_index("ix_accounts_name", table_name="accounts")
    op.drop_table("accounts")

    sa.Enum(name="trade_account_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="account_type").drop(op.get_bind(), checkfirst=True)
