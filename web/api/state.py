"""Shared application state singletons."""

from .websocket import WebSocketManager

# Global WebSocket manager instance shared across modules.
ws_manager = WebSocketManager()
