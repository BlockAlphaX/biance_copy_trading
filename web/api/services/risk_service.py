"""Risk related utilities for API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from .trade_service import get_trade_logger


ALERT_STORE_PATH = Path("logs/risk_alerts.json")
SUCCESS_STATUSES = {"FILLED", "PARTIALLY_FILLED", "SUCCESS"}
FAILURE_STATUSES = {"REJECTED", "FAILED", "CANCELLED", "EXPIRED"}


class AlertNotFound(Exception):
    """Raised when an alert is not found in storage."""


def _ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_alerts() -> List[Dict[str, Any]]:
    if not ALERT_STORE_PATH.exists():
        return []
    
    try:
        with open(ALERT_STORE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []
    
    if not isinstance(data, list):
        return []
    
    normalised: List[Dict[str, Any]] = []
    for entry in data:
        if isinstance(entry, dict):
            # Ensure required keys exist
            normalised.append({
                "id": entry.get("id") or f"alert-{len(normalised)+1}",
                "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "level": (entry.get("level") or "info").lower(),
                "type": entry.get("type") or "generic",
                "message": entry.get("message") or "",
                "acknowledged": bool(entry.get("acknowledged", False)),
                "metadata": entry.get("metadata", {})
            })
    return normalised


def _save_alerts(alerts: List[Dict[str, Any]]) -> None:
    ALERT_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(alerts, fh, ensure_ascii=False, indent=2)


def _parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _notional_from_record(record: Dict[str, Any]) -> float:
    notional = record.get("notional")
    if isinstance(notional, (int, float)):
        return float(notional)
    
    quantity = record.get("quantity")
    price = record.get("price")
    try:
        qty = float(quantity)
        px = float(price)
    except (TypeError, ValueError):
        return 0.0
    return qty * px


def _classify_follower_record(record: Dict[str, Any]) -> Tuple[bool, bool]:
    status = (record.get("status") or "").upper()
    is_error = bool(record.get("error"))
    is_success = status in SUCCESS_STATUSES and not is_error
    is_failure = is_error or status in FAILURE_STATUSES
    return is_success, is_failure


def _compute_trade_aggregates(hours: int = 24) -> Dict[str, Any]:
    logger = get_trade_logger()
    records = logger.get_all_trades()
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    totals = {
        "success_notional": 0.0,
        "failed_notional": 0.0,
        "master_notional": 0.0,
        "follower_success": 0,
        "follower_failed": 0,
        "follower_trades": 0,
        "master_trades": 0
    }
    
    for record in records:
        ts = _parse_iso8601(record.get("timestamp"))
        if ts and ts < cutoff:
            continue
        
        record_type = record.get("type")
        notional = _notional_from_record(record)
        
        if record_type == "master":
            totals["master_trades"] += 1
            totals["master_notional"] += notional
        elif record_type == "follower":
            totals["follower_trades"] += 1
            is_success, is_failure = _classify_follower_record(record)
            if is_success:
                totals["follower_success"] += 1
                totals["success_notional"] += notional
            if is_failure:
                totals["follower_failed"] += 1
                totals["failed_notional"] += notional
    
    return totals


def compute_risk_summary() -> Dict[str, Any]:
    """Compute risk summary metrics from trade history."""
    totals = _compute_trade_aggregates(hours=24)
    
    success_volume = totals["success_notional"]
    failed_volume = totals["failed_notional"]
    master_volume = totals["master_notional"]
    
    total_position_value = round(success_volume + master_volume, 2)
    total_exposure = success_volume + failed_volume + master_volume
    failure_ratio = failed_volume / total_exposure if total_exposure else 0.0
    
    # Simple heuristics for PnL estimates based on trade outcomes
    daily_pnl = round(success_volume * 0.015 - failed_volume * 0.02, 2)
    unrealized_pnl = round(success_volume * 0.008 - failed_volume * 0.015, 2)
    max_drawdown = round(-failed_volume * 0.1, 2) if failed_volume else 0.0
    
    if failure_ratio > 0.5:
        risk_level = "high"
    elif failure_ratio > 0.2:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "total_position_value": total_position_value,
        "total_unrealized_pnl": round(unrealized_pnl, 2),
        "daily_pnl": daily_pnl,
        "max_drawdown": max_drawdown,
        "risk_level": risk_level
    }


def get_trade_aggregates(hours: int = 24) -> Dict[str, Any]:
    """Expose trade aggregates for other services."""
    return _compute_trade_aggregates(hours=hours)


def _sync_dynamic_alerts() -> List[Dict[str, Any]]:
    """Synchronize dynamic alerts derived from runtime metrics."""
    alerts = _load_alerts()
    alerts_by_id = {alert["id"]: alert for alert in alerts}
    changed = False
    
    totals = _compute_trade_aggregates(hours=24)
    failure_count = totals["follower_failed"]
    follower_trades = totals["follower_trades"]
    failure_ratio = failure_count / follower_trades if follower_trades else 0.0
    
    def upsert(alert_id: str, **fields: Any) -> None:
        nonlocal changed
        fields.setdefault("metadata", {})
        existing = alerts_by_id.get(alert_id)
        if existing:
            preserved_ack = existing.get("acknowledged", False)
            for key, value in fields.items():
                if key == "acknowledged":
                    continue
                if existing.get(key) != value:
                    existing[key] = value
                    changed = True
            existing["acknowledged"] = preserved_ack
        else:
            new_alert = {
                "id": alert_id,
                "timestamp": fields.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "level": fields.get("level", "info"),
                "type": fields.get("type", "generic"),
                "message": fields.get("message", ""),
                "acknowledged": fields.get("acknowledged", False),
                "metadata": fields.get("metadata", {})
            }
            alerts.append(new_alert)
            alerts_by_id[alert_id] = new_alert
            changed = True

    def delete(alert_id: str) -> None:
        nonlocal changed
        if alert_id in alerts_by_id:
            alerts[:] = [alert for alert in alerts if alert["id"] != alert_id]
            alerts_by_id.pop(alert_id, None)
            changed = True

    now_iso = datetime.now(timezone.utc).isoformat()
    
    if failure_ratio >= 0.5 and follower_trades >= 3:
        upsert(
            "dyn-high-failure-rate",
            timestamp=now_iso,
            level="error",
            type="quality",
            message=f"Follower failure rate {failure_ratio * 100:.1f}% in last 24h",
            metadata={
                "failure_ratio": round(failure_ratio, 4),
                "follower_trades": follower_trades
            }
        )
    elif failure_ratio >= 0.3 and follower_trades >= 3:
        upsert(
            "dyn-elevated-failure-rate",
            timestamp=now_iso,
            level="warning",
            type="quality",
            message=f"Follower failure rate elevated at {failure_ratio * 100:.1f}%",
            metadata={
                "failure_ratio": round(failure_ratio, 4),
                "follower_trades": follower_trades
            }
        )
        delete("dyn-high-failure-rate")
    else:
        delete("dyn-high-failure-rate")
        delete("dyn-elevated-failure-rate")
    
    total_trades = follower_trades + totals["master_trades"]
    if total_trades == 0:
        upsert(
            "dyn-no-trades",
            timestamp=now_iso,
            level="info",
            type="activity",
            message="No trades recorded in the last 24 hours."
        )
    else:
        delete("dyn-no-trades")
    
    if changed:
        _save_alerts(alerts)
    
    return alerts


def get_alerts(acknowledged: Optional[bool], level: Optional[str]) -> List[Dict[str, Any]]:
    """Retrieve alerts optionally filtered by acknowledgement and level."""
    alerts = _sync_dynamic_alerts()
    
    filtered: List[Dict[str, Any]] = []
    for alert in alerts:
        if acknowledged is not None and alert.get("acknowledged") != acknowledged:
            continue
        if level and alert.get("level", "").lower() != level.lower():
            continue
        filtered.append(alert)
    
    filtered.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
    return filtered


def acknowledge_alert(alert_id: str) -> Dict[str, Any]:
    """Mark alert as acknowledged."""
    alerts = _sync_dynamic_alerts()
    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            _save_alerts(alerts)
            return alert
    
    raise AlertNotFound(alert_id)
