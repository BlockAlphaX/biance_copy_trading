import pytest
from starlette.websockets import WebSocketDisconnect

from web.api.main import app

from web.api.websocket import WebSocketManager
from web.api.state import ws_manager


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        self.messages.append(message)


@pytest.mark.asyncio
async def test_websocket_manager_broadcast_and_subscriptions():
    manager = WebSocketManager()

    ws_primary = DummyWebSocket()
    ws_secondary = DummyWebSocket()

    await manager.connect(ws_primary)
    await manager.connect(ws_secondary)

    assert ws_primary.accepted is True
    assert manager.get_connection_count() == 2

    manager.subscribe(ws_primary, "trades")
    manager.subscribe(ws_secondary, "trades")

    await manager.broadcast({"event": "heartbeat"})
    assert ws_primary.messages[-1]["event"] == "heartbeat"
    assert ws_secondary.messages[-1]["event"] == "heartbeat"

    await manager.broadcast_to_channel("trades", {"event": "trade_update"})
    assert ws_primary.messages[-1]["event"] == "trade_update"
    assert ws_secondary.messages[-1]["event"] == "trade_update"

    manager.unsubscribe(ws_secondary, "trades")
    await manager.broadcast_to_channel("trades", {"event": "channel_only"})
    assert ws_primary.messages[-1]["event"] == "channel_only"
    assert ws_secondary.messages[-1]["event"] == "trade_update"

    manager.disconnect(ws_primary)
    manager.disconnect(ws_secondary)
    assert manager.get_connection_count() == 0


def test_websocket_endpoint_tracks_connections(api_client):
    assert ws_manager.get_connection_count() == 0
    token = api_client.token  # type: ignore[attr-defined]
    with api_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("ping")
        assert ws_manager.get_connection_count() == 1
    assert ws_manager.get_connection_count() == 0


def test_websocket_connection_rejects_missing_token(api_client):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with unauthenticated_client.websocket_connect("/ws"):
            pass


def test_trade_websocket_provides_snapshot_and_refresh(api_client):
    token = api_client.token  # type: ignore[attr-defined]
    with api_client.websocket_connect(f"/ws/trades?token={token}") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "trade_snapshot"
        assert len(initial["data"]) > 0

        websocket.send_json({"action": "refresh", "limit": 2})
        refreshed = websocket.receive_json()
        assert refreshed["type"] == "trade_snapshot"
        assert len(refreshed["data"]) == 2


def test_metrics_websocket_streams_snapshots(api_client):
    token = api_client.token  # type: ignore[attr-defined]
    with api_client.websocket_connect(f"/ws/metrics?token={token}") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "metrics_snapshot"
        assert "rate_limit" in snapshot
        assert "circuit_breakers" in snapshot

        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
