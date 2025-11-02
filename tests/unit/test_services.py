from threading import Lock
from pathlib import Path
import sys

import pytest

TEST_ROOT = Path(__file__).resolve().parents[2]
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from web.api.services import trade_service, system_service, risk_service


@pytest.fixture
def temp_trade_log(monkeypatch, tmp_path):
    log_path = tmp_path / "trades.jsonl"
    monkeypatch.setattr(trade_service, "_resolve_trade_log_path", lambda: str(log_path))
    trade_service._get_cached_trade_logger.cache_clear()
    yield log_path
    trade_service._get_cached_trade_logger.cache_clear()


@pytest.fixture
def isolated_system_state(monkeypatch, tmp_path):
    state_file = tmp_path / "system_state.json"
    monkeypatch.setattr(system_service, "STATE_PATH", state_file)
    monkeypatch.setattr(system_service, "STATE_LOCK", Lock())
    return state_file


@pytest.fixture
def isolated_alert_store(monkeypatch, tmp_path, temp_trade_log):
    alert_file = tmp_path / "risk_alerts.json"
    monkeypatch.setattr(risk_service, "ALERT_STORE_PATH", alert_file)
    return alert_file


def test_trade_service_returns_empty_when_no_logs(temp_trade_log):
    trades = trade_service.list_recent_trades(limit=10)
    assert trades == []
    
    stats = trade_service.get_trade_statistics()
    assert stats["total_trades"] == 0


def test_system_service_start_stop(isolated_system_state):
    state = system_service.start_engine()
    assert state["running"] is True
    assert state["start_time"]
    
    with pytest.raises(ValueError):
        system_service.start_engine()
    
    state = system_service.stop_engine()
    assert state["running"] is False
    assert state["start_time"] is None
    
    with pytest.raises(ValueError):
        system_service.stop_engine()


def test_risk_service_alerts_generation(isolated_alert_store):
    alerts = risk_service.get_alerts(acknowledged=None, level=None)
    assert isinstance(alerts, list)
    assert alerts, "Expected at least one dynamic alert with no trades"
    
    alert_id = alerts[0]["id"]
    acknowledged = risk_service.acknowledge_alert(alert_id)
    assert acknowledged["acknowledged"] is True
    
    acknowledged_alerts = risk_service.get_alerts(acknowledged=True, level=None)
    ids = [alert["id"] for alert in acknowledged_alerts]
    assert alert_id in ids
