"""Metrics helpers for API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .config_service import load_raw_config
from .risk_service import get_trade_aggregates


STATE_PATH = Path("logs/metrics_state.json")


def _load_state() -> Dict[str, Any]:
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


def _get_rate_limit_config() -> Dict[str, Any]:
    config, _, _ = load_raw_config()
    advanced = config.get("advanced", {}) if isinstance(config, dict) else {}
    if isinstance(advanced, dict):
        rate_limit_cfg = advanced.get("rate_limit", {})
        if isinstance(rate_limit_cfg, dict):
            return rate_limit_cfg
    return {}


def get_rate_limit_metrics() -> Dict[str, Any]:
    """Return rate limit metrics using config, state overrides, and trade activity."""
    state = _load_state().get("rate_limit", {})
    rate_cfg = _get_rate_limit_config()
    
    weight_limit = int(rate_cfg.get("weight_limit", 2400))
    safety_margin = float(rate_cfg.get("safety_margin", 0.8))
    effective_limit = max(int(weight_limit * safety_margin), 1)
    
    aggregates = get_trade_aggregates(hours=1)
    fallback_requests = aggregates["master_trades"] + aggregates["follower_trades"]
    
    total_requests = state.get("total_requests", fallback_requests)
    current_weight = state.get("current_weight", min(total_requests * 5, effective_limit))
    wait_count = state.get("wait_count", 0)
    total_wait_time = state.get("total_wait_time", 0.0)
    
    utilization = state.get(
        "utilization",
        round(current_weight / effective_limit * 100, 2) if effective_limit else 0.0
    )
    
    return {
        "total_requests": int(total_requests),
        "current_weight": int(current_weight),
        "weight_limit": weight_limit,
        "utilization": float(utilization),
        "wait_count": int(wait_count),
        "total_wait_time": float(total_wait_time)
    }


def get_circuit_breaker_status() -> List[Dict[str, Any]]:
    """Return circuit breaker-like health for followers."""
    state = _load_state()
    overrides = {entry.get("name"): entry for entry in state.get("circuit_breakers", []) if isinstance(entry, dict)}
    
    config, _, _ = load_raw_config()
    followers = config.get("followers", []) if isinstance(config, dict) else []
    aggregates = get_trade_aggregates(hours=6)
    
    failure_count = max(aggregates["follower_failed"], 0)
    follower_trades = max(aggregates["follower_trades"], 0)
    success_rate = 100.0
    if follower_trades > 0:
        success_rate = round((1 - failure_count / follower_trades) * 100, 2)
    
    failure_ratio = (failure_count / follower_trades) if follower_trades else 0.0
    if failure_ratio >= 0.5:
        default_state = "OPEN"
    elif failure_ratio >= 0.3:
        default_state = "HALF_OPEN"
    else:
        default_state = "CLOSED"
    
    statuses: List[Dict[str, Any]] = []
    if isinstance(followers, list) and followers:
        for follower in followers:
            if not isinstance(follower, dict):
                continue
            name = follower.get("name")
            if not name:
                continue
            
            override = overrides.get(name, {})
            statuses.append({
                "name": name,
                "state": override.get("state", default_state),
                "success_rate": override.get("success_rate", success_rate),
                "failure_count": override.get("failure_count", failure_count),
                "total_calls": override.get("total_calls", follower_trades)
            })
    else:
        statuses.append({
            "name": "followers",
            "state": overrides.get("followers", {}).get("state", default_state),
            "success_rate": overrides.get("followers", {}).get("success_rate", success_rate),
            "failure_count": overrides.get("followers", {}).get("failure_count", failure_count),
            "total_calls": overrides.get("followers", {}).get("total_calls", follower_trades)
        })
    
    return statuses


def get_system_performance() -> Dict[str, Any]:
    """Collect basic system performance metrics."""
    try:
        import psutil
    except ImportError as exc:  # pragma: no cover - psutil is part of optional deps
        raise RuntimeError("psutil module not available") from exc

    return {
        "cpu_percent": float(psutil.cpu_percent(interval=0.1)),
        "memory_percent": float(psutil.virtual_memory().percent),
        "disk_percent": float(psutil.disk_usage("/").percent),
    }
