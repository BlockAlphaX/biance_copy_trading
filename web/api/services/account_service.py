"""Account state helpers for API routes."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from .config_service import load_raw_config


STATE_PATH = Path("logs/account_state.json")
STATE_LOCK = Lock()


def _load_state_unlocked() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {"accounts": {}, "positions": {}}
    
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"accounts": {}, "positions": {}}
    
    if not isinstance(data, dict):
        return {"accounts": {}, "positions": {}}
    
    data.setdefault("accounts", {})
    data.setdefault("positions", {})
    return data


def _save_state_unlocked(state: Dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def _default_account_values(account_type: str, follower_config: Dict[str, Any] | None, trading_cfg: Dict[str, Any]) -> Dict[str, Any]:
    if account_type == "master":
        leverage = trading_cfg.get("leverage", 10)
        margin_type = trading_cfg.get("margin_type", "CROSSED")
        position_mode = trading_cfg.get("position_mode", "one_way")
        return {
            "balance": 10000.0,
            "available_balance": 8500.0,
            "leverage": leverage,
            "margin_type": margin_type,
            "position_mode": position_mode,
            "enabled": True
        }
    
    scale = 1.0
    enabled = True
    if follower_config:
        scale = follower_config.get("scale", 1.0)
        enabled = follower_config.get("enabled", True)
    
    balance = round(5000.0 * scale, 2)
    available = round(balance * 0.85, 2)
    
    return {
        "balance": balance,
        "available_balance": available,
        "leverage": trading_cfg.get("leverage", 10),
        "margin_type": trading_cfg.get("margin_type", "CROSSED"),
        "position_mode": trading_cfg.get("position_mode", "one_way"),
        "enabled": enabled
    }


def _ensure_accounts(state: Dict[str, Any]) -> bool:
    config, _, _ = load_raw_config()
    trading_cfg = config.get("trading", {}) if isinstance(config, dict) else {}
    
    accounts_section: Dict[str, Dict[str, Any]] = state.setdefault("accounts", {})
    positions_section: Dict[str, List[Dict[str, Any]]] = state.setdefault("positions", {})
    
    updated = False
    
    # Master account
    master_entry = accounts_section.get("master")
    if not isinstance(master_entry, dict):
        master_entry = {"name": "master", "type": "master"}
        master_entry.update(_default_account_values("master", None, trading_cfg))
        accounts_section["master"] = master_entry
        updated = True
    else:
        master_entry.setdefault("name", "master")
        master_entry.setdefault("type", "master")
        defaults = _default_account_values("master", None, trading_cfg)
        for key, value in defaults.items():
            master_entry.setdefault(key, value)
    
    positions_section.setdefault("master", [])
    
    # Followers
    followers = config.get("followers", []) if isinstance(config, dict) else []
    if isinstance(followers, list):
        for follower in followers:
            if not isinstance(follower, dict):
                continue
            name = follower.get("name")
            if not name:
                continue
            
            entry = accounts_section.get(name)
            if not isinstance(entry, dict):
                entry = {"name": name, "type": "follower"}
                entry.update(_default_account_values("follower", follower, trading_cfg))
                accounts_section[name] = entry
                updated = True
            else:
                entry.setdefault("name", name)
                entry.setdefault("type", "follower")
                defaults = _default_account_values("follower", follower, trading_cfg)
                for key, value in defaults.items():
                    entry.setdefault(key, value)
            positions_section.setdefault(name, [])
    
    return updated


def _load_state_with_defaults_locked() -> Dict[str, Any]:
    state = _load_state_unlocked()
    if _ensure_accounts(state):
        _save_state_unlocked(state)
    return state


def list_accounts() -> List[Dict[str, Any]]:
    with STATE_LOCK:
        state = _load_state_with_defaults_locked()
        return list(state["accounts"].values())


def get_account(name: str) -> Dict[str, Any]:
    with STATE_LOCK:
        state = _load_state_with_defaults_locked()
        account = state["accounts"].get(name)
        if not account:
            raise KeyError(f"Account '{name}' not found")
        return dict(account)


def get_account_balance(name: str) -> Dict[str, Any]:
    account = get_account(name)
    return {
        "name": account["name"],
        "balance": account["balance"],
        "available_balance": account["available_balance"],
        "currency": "USDT"
    }


def list_positions(name: str) -> List[Dict[str, Any]]:
    with STATE_LOCK:
        state = _load_state_with_defaults_locked()
        if name not in state["accounts"]:
            raise KeyError(f"Account '{name}' not found")
        return list(state["positions"].get(name, []))


def update_leverage(name: str, leverage: int) -> Dict[str, Any]:
    if leverage <= 0:
        raise ValueError("Leverage must be positive")
    
    with STATE_LOCK:
        state = _load_state_with_defaults_locked()
        if name not in state["accounts"]:
            raise KeyError(f"Account '{name}' not found")
        state["accounts"][name]["leverage"] = leverage
        _save_state_unlocked(state)
        return dict(state["accounts"][name])


def set_account_enabled(name: str, enabled: bool) -> Dict[str, Any]:
    with STATE_LOCK:
        state = _load_state_with_defaults_locked()
        if name not in state["accounts"]:
            raise KeyError(f"Account '{name}' not found")
        state["accounts"][name]["enabled"] = enabled
        _save_state_unlocked(state)
        return dict(state["accounts"][name])
