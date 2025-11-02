def test_accounts_endpoints(api_client):
    response = api_client.get("/api/accounts")
    assert response.status_code == 200
    data = response.json()
    assert {account["name"] for account in data} == {"master", "alpha"}

    balance_response = api_client.get("/api/accounts/master/balance")
    assert balance_response.status_code == 200
    assert balance_response.json()["balance"] == 15000.0

    positions_response = api_client.get("/api/accounts/alpha/positions")
    assert positions_response.status_code == 200
    positions = positions_response.json()
    assert positions and positions[0]["symbol"] == "ETHUSDT"


def test_trade_endpoints(api_client):
    recent = api_client.get("/api/trades/recent?limit=3")
    assert recent.status_code == 200
    trades = recent.json()
    assert len(trades) == 3
    trade_ids = {trade["id"] for trade in trades}
    assert {"master-trade-1", "alpha-success-1"}.issubset(trade_ids)

    history = api_client.get("/api/trades/history?page=1&page_size=1&symbol=BTCUSDT")
    assert history.status_code == 200
    results = history.json()
    assert len(results) == 1
    assert results[0]["symbol"] == "BTCUSDT"

    stats = api_client.get("/api/trades/stats")
    assert stats.status_code == 200
    payload = stats.json()
    assert payload["total_trades"] >= 2
    assert payload["failed_trades"] >= 1


def test_logs_endpoints(api_client):
    system_logs = api_client.get("/api/logs/system?limit=1")
    assert system_logs.status_code == 200
    assert system_logs.json()[0]["message"] == "Failed to broadcast message"

    trade_logs = api_client.get("/api/logs/trades?limit=5")
    assert trade_logs.status_code == 200
    entries = trade_logs.json()
    assert any(entry["type"] == "trade" for entry in entries)

    error_logs = api_client.get("/api/logs/errors?limit=5")
    assert error_logs.status_code == 200
    errors = error_logs.json()
    assert errors[0]["type"] in {"error", "system"}


def test_risk_endpoints(api_client):
    summary = api_client.get("/api/risk/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["risk_level"] in {"low", "medium", "high"}

    alerts = api_client.get("/api/risk/alerts")
    assert alerts.status_code == 200
    alerts_data = alerts.json()
    assert alerts_data and alerts_data[0]["acknowledged"] is False

    alert_id = alerts_data[0]["id"]
    ack = api_client.post(f"/api/risk/alerts/{alert_id}/ack")
    assert ack.status_code == 200
    assert ack.json()["alert_id"] == alert_id


def test_metrics_endpoints(api_client):
    rate_limit = api_client.get("/api/metrics/rate-limit")
    assert rate_limit.status_code == 200
    payload = rate_limit.json()
    assert payload["current_weight"] == 200
    assert payload["weight_limit"] == 1200

    circuit = api_client.get("/api/metrics/circuit-breaker")
    assert circuit.status_code == 200
    data = circuit.json()
    assert data and data[0]["name"] == "alpha"


def test_system_status_and_config(api_client):
    status = api_client.get("/api/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["running"] is True
    assert payload["uptime_seconds"] is not None

    config = api_client.get("/api/config")
    assert config.status_code == 200
    config_payload = config.json()
    assert config_payload["_is_example"] is False
    master_secret = config_payload["master"]["api_secret"]
    assert master_secret.startswith("MA") and master_secret.endswith("ET")
def test_authentication_required(api_client):
    response = api_client.get("/api/accounts", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Invalid authentication credentials"
