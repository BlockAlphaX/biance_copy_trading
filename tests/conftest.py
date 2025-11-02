from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from threading import Lock
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import yaml
from fastapi.testclient import TestClient

from web.api import auth


from web.api.main import app  # noqa: E402
from web.api.state import ws_manager  # noqa: E402
from web.api.services import (  # noqa: E402
    config_service,
    account_service,
    system_service,
    risk_service,
    metrics_service,
    log_service,
    trade_service,
)


@pytest.fixture(autouse=True)
def reset_ws_manager():
    ws_manager.active_connections.clear()
    ws_manager.subscriptions.clear()
    yield
    ws_manager.active_connections.clear()
    ws_manager.subscriptions.clear()


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    monkeypatch.setenv("API_JWT_SECRET", "test-secret")
    auth.reset_auth_settings_cache()

    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    trade_log_path = tmp_path / "logs" / "futures_trades.jsonl"
    trade_log_path.parent.mkdir(parents=True, exist_ok=True)

    system_state_path = tmp_path / "state" / "system_state.json"
    account_state_path = tmp_path / "state" / "account_state.json"
    metrics_state_path = tmp_path / "state" / "metrics_state.json"
    alert_store_path = tmp_path / "state" / "risk_alerts.json"
    for path in [system_state_path, account_state_path, metrics_state_path, alert_store_path]:
        path.parent.mkdir(parents=True, exist_ok=True)

    system_log_path = tmp_path / "logs" / "api.log"

    config_path = config_dir / "config.yaml"
    config_data = {
        "base_url": "https://testnet.binancefuture.com",
        "master": {
            "api_key": "MASTERKEY",
            "api_secret": "MASTERSECRET",
        },
        "followers": [
            {
                "name": "alpha",
                "api_key": "ALPHAKEY",
                "api_secret": "ALPHASECRET",
                "scale": 1.2,
                "enabled": True,
            }
        ],
        "trading": {
            "leverage": 20,
            "margin_type": "ISOLATED",
            "position_mode": "hedge",
        },
        "advanced": {
            "trade_logging": {
                "log_file": str(trade_log_path),
            },
            "rate_limit": {
                "weight_limit": 1200,
                "safety_margin": 0.9,
            },
        },
    }
    config_path.write_text(
        yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_service, "CONFIG_FILENAME", config_path)
    monkeypatch.setattr(config_service, "CONFIG_EXAMPLE_FILENAME", config_path)

    monkeypatch.setattr(account_service, "STATE_PATH", account_state_path)
    monkeypatch.setattr(account_service, "STATE_LOCK", Lock())

    monkeypatch.setattr(system_service, "STATE_PATH", system_state_path)
    monkeypatch.setattr(system_service, "STATE_LOCK", Lock())

    monkeypatch.setattr(metrics_service, "STATE_PATH", metrics_state_path)
    monkeypatch.setattr(risk_service, "ALERT_STORE_PATH", alert_store_path)
    monkeypatch.setattr(log_service, "SYSTEM_LOG_PATH", system_log_path)

    monkeypatch.setattr(trade_service, "_resolve_trade_log_path", lambda: str(trade_log_path))
    trade_service._get_cached_trade_logger.cache_clear()

    now = datetime.now(timezone.utc)
    system_state_path.write_text(
        json.dumps(
            {
                "engine": {
                    "running": True,
                    "start_time": (now - timedelta(minutes=5)).isoformat(),
                    "version": "3.0.0",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    account_state_path.write_text(
        json.dumps(
            {
                "accounts": {
                    "master": {
                        "name": "master",
                        "type": "master",
                        "balance": 15000.0,
                        "available_balance": 12000.0,
                        "leverage": 20,
                        "margin_type": "ISOLATED",
                        "position_mode": "hedge",
                        "enabled": True,
                    },
                    "alpha": {
                        "name": "alpha",
                        "type": "follower",
                        "balance": 4500.0,
                        "available_balance": 3900.0,
                        "leverage": 15,
                        "margin_type": "CROSSED",
                        "position_mode": "one_way",
                        "enabled": True,
                    },
                },
                "positions": {
                    "master": [
                        {
                            "symbol": "BTCUSDT",
                            "side": "LONG",
                            "size": 0.1,
                            "entry_price": 27000.0,
                            "mark_price": 27100.0,
                            "unrealized_pnl": 10.0,
                            "leverage": 20,
                        }
                    ],
                    "alpha": [
                        {
                            "symbol": "ETHUSDT",
                            "side": "SHORT",
                            "size": 1.5,
                            "entry_price": 1900.0,
                            "mark_price": 1885.0,
                            "unrealized_pnl": 22.5,
                            "leverage": 15,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    trade_records = [
        {
            "id": "master-trade-1",
            "timestamp": now.isoformat(),
            "type": "master",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.1,
            "price": 27000.0,
            "position_side": "BOTH",
            "notional": 2700.0,
        },
        {
            "id": "alpha-success-1",
            "timestamp": (now - timedelta(seconds=5)).isoformat(),
            "type": "follower",
            "follower_name": "alpha",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.05,
            "price": 27010.0,
            "position_side": "BOTH",
            "order_type": "MARKET",
            "status": "FILLED",
            "notional": 1350.5,
        },
        {
            "id": "alpha-failure-1",
            "timestamp": (now - timedelta(seconds=10)).isoformat(),
            "type": "follower",
            "follower_name": "alpha",
            "symbol": "ETHUSDT",
            "side": "SELL",
            "quantity": 0.5,
            "price": 1880.0,
            "position_side": "BOTH",
            "order_type": "LIMIT",
            "status": "REJECTED",
            "error": "INSUFFICIENT_BALANCE",
            "notional": 940.0,
        },
        {
            "id": "error-1",
            "timestamp": (now - timedelta(seconds=15)).isoformat(),
            "type": "error",
            "follower_name": "alpha",
            "symbol": "ETHUSDT",
            "error_type": "balance",
            "error_message": "Insufficient margin",
            "context": {"order_id": 12345},
        },
    ]
    trade_log_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in trade_records),
        encoding="utf-8",
    )

    metrics_state_path.write_text(
        json.dumps(
            {
                "rate_limit": {
                    "total_requests": 320,
                    "current_weight": 200,
                    "wait_count": 4,
                    "total_wait_time": 1.6,
                    "utilization": 55.5,
                },
                "circuit_breakers": [
                    {
                        "name": "alpha",
                        "state": "HALF_OPEN",
                        "success_rate": 70.0,
                        "failure_count": 3,
                        "total_calls": 10,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    alert_store_path.write_text(
        json.dumps(
            [
                {
                    "id": "alert-1",
                    "timestamp": now.isoformat(),
                    "level": "warning",
                    "type": "drawdown",
                    "message": "Follower alpha experienced elevated failure rate",
                    "acknowledged": False,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    system_log_path.write_text(
        "\n".join(
            [
                "2024-01-01 00:00:00,000 - api - INFO - API server started",
                "2024-01-01 00:01:00,000 - api - ERROR - Failed to broadcast message",
            ]
        ),
        encoding="utf-8",
    )

    token = auth.create_access_token("test-user")
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    client.token = token  # type: ignore[attr-defined]
    return client
