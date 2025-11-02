"""System level helpers for engine state management."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .config_service import load_config, load_raw_config, update_config as write_config


STATE_PATH = Path("logs/system_state.json")
STATE_LOCK = Lock()
DEFAULT_VERSION = "3.0.0"


def _load_state_unlocked() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _save_state_unlocked(state: Dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def _ensure_engine_state(state: Dict[str, Any]) -> Dict[str, Any]:
    engine = state.setdefault("engine", {})
    engine.setdefault("running", False)
    engine.setdefault("start_time", None)
    engine.setdefault("version", DEFAULT_VERSION)
    return state


def get_engine_state() -> Dict[str, Any]:
    """Return current engine state."""
    with STATE_LOCK:
        state = _ensure_engine_state(_load_state_unlocked())
        _save_state_unlocked(state)
        return dict(state["engine"])


def _set_engine_state(running: bool) -> Dict[str, Any]:
    with STATE_LOCK:
        state = _ensure_engine_state(_load_state_unlocked())
        engine = state["engine"]
        
        engine["running"] = running
        engine["version"] = engine.get("version") or DEFAULT_VERSION
        engine["start_time"] = (
            datetime.now(timezone.utc).isoformat()
            if running else None
        )
        _save_state_unlocked(state)
        return dict(engine)


def start_engine() -> Dict[str, Any]:
    """Mark engine as running."""
    with STATE_LOCK:
        state = _ensure_engine_state(_load_state_unlocked())
        if state["engine"].get("running"):
            raise ValueError("Engine is already running")
    return _set_engine_state(True)


def stop_engine() -> Dict[str, Any]:
    """Mark engine as stopped."""
    with STATE_LOCK:
        state = _ensure_engine_state(_load_state_unlocked())
        if not state["engine"].get("running"):
            raise ValueError("Engine is not running")
    return _set_engine_state(False)


def restart_engine() -> Dict[str, Any]:
    """Restart engine state."""
    stop_engine()
    return _set_engine_state(True)


def get_config(redact: bool = True) -> Tuple[Dict[str, Any], Path, bool]:
    """Load configuration via config service."""
    return load_config(redact=redact)


def get_raw_config() -> Tuple[Dict[str, Any], Path, bool]:
    """Load configuration without redaction."""
    return load_raw_config()


def update_config(config: Dict[str, Any]) -> Path:
    """Update configuration file on disk."""
    return write_config(config)
