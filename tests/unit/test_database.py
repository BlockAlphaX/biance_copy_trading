from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from web.db import session


def test_init_database_creates_schema(monkeypatch, tmp_path):
    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DB_DATABASE_URL", f"sqlite:///{db_file}")

    session.reset_database_state()
    session.init_database()

    engine = session.get_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "accounts",
        "trade_records",
        "risk_alerts",
        "metric_snapshots",
        "system_events",
        "system_state",
    }
    assert expected.issubset(tables)

    session.reset_database_state()
