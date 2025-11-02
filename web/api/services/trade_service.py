"""Helpers for working with trade log data."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from datetime import datetime

from src.trade_logger import TradeLogger

from .config_service import load_raw_config


DEFAULT_TRADE_LOG_PATH = Path("logs/futures_trades.jsonl")


def _resolve_trade_log_path() -> str:
    """Determine the path to the trade log file from configuration."""
    config, _, _ = load_raw_config()
    
    advanced = config.get("advanced")
    if isinstance(advanced, dict):
        trade_logging = advanced.get("trade_logging")
        if isinstance(trade_logging, dict):
            log_path = trade_logging.get("log_file")
            if isinstance(log_path, str) and log_path.strip():
                return log_path
    
    logging_cfg = config.get("logging")
    if isinstance(logging_cfg, dict):
        log_path = logging_cfg.get("file")
        if isinstance(log_path, str) and log_path.strip():
            return log_path
    
    return str(DEFAULT_TRADE_LOG_PATH)


@lru_cache(maxsize=1)
def _get_cached_trade_logger(log_path: str) -> TradeLogger:
    """Return cached TradeLogger instance for the given path."""
    return TradeLogger(log_file=log_path)


def get_trade_logger() -> TradeLogger:
    """Get TradeLogger instance configured for the application."""
    return _get_cached_trade_logger(_resolve_trade_log_path())


def _parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO8601 timestamp to datetime."""
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _to_float(value: Any) -> float:
    """Safely convert values to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _record_account(record: Dict[str, Any]) -> str:
    """Resolve account name for a trade record."""
    if record.get("type") == "master":
        return "master"
    return record.get("follower_name") or "unknown"


def _normalise_status(record: Dict[str, Any]) -> str:
    """Determine trade status from record."""
    if record.get("type") == "master":
        return "FILLED"
    status = record.get("status")
    if isinstance(status, str) and status:
        return status.upper()
    return "UNKNOWN"


def _normalise_order_type(record: Dict[str, Any]) -> str:
    """Determine order type from record."""
    value = record.get("order_type")
    if isinstance(value, str) and value:
        return value.upper()
    if record.get("type") == "master":
        return "MARKET"
    return "UNKNOWN"


def record_to_trade(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert raw trade log record to API response shape."""
    return {
        "id": record.get("id"),
        "timestamp": record.get("timestamp"),
        "account": _record_account(record),
        "symbol": record.get("symbol"),
        "side": record.get("side"),
        "quantity": _to_float(record.get("quantity")),
        "price": _to_float(record.get("price")),
        "status": _normalise_status(record),
        "order_type": _normalise_order_type(record),
        "position_side": record.get("position_side") or "BOTH",
    }


def list_recent_trades(limit: int, account: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return recent trades limited by count with optional account filter."""
    logger = get_trade_logger()
    records = logger.get_recent_trades(count=limit * 4 if account else limit)
    account_filter = account.lower() if account else None
    
    formatted: List[Dict[str, Any]] = []
    for record in records:
        if account_filter and _record_account(record).lower() != account_filter:
            continue
        formatted.append(record_to_trade(record))
        if len(formatted) >= limit:
            break
    
    return formatted


def _filter_records(
    records: Iterable[Dict[str, Any]],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    symbol: Optional[str],
    account: Optional[str]
) -> List[Dict[str, Any]]:
    """Apply filters to trade records."""
    filtered: List[Tuple[Optional[datetime], Dict[str, Any]]] = []
    account_filter = account.lower() if account else None
    for record in records:
        ts = _parse_iso8601(record.get("timestamp"))
        if start_time and (not ts or ts < start_time):
            continue
        if end_time and (not ts or ts > end_time):
            continue
        if symbol and record.get("symbol") != symbol:
            continue
        if account_filter and _record_account(record).lower() != account_filter:
            continue
        filtered.append((ts, record))
    
    # Sort by timestamp descending (latest first)
    filtered.sort(key=lambda item: item[0] or datetime.min, reverse=True)
    return [record for _, record in filtered]


def query_trade_history(
    start_time: Optional[str],
    end_time: Optional[str],
    symbol: Optional[str],
    account: Optional[str],
    page: int,
    page_size: int
) -> List[Dict[str, Any]]:
    """Query trade history using filters and pagination."""
    logger = get_trade_logger()
    records = logger.get_all_trades()
    
    start_dt = _parse_iso8601(start_time)
    end_dt = _parse_iso8601(end_time)
    
    filtered = _filter_records(records, start_dt, end_dt, symbol, account)
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    page_records = filtered[start_index:end_index]
    
    return [record_to_trade(record) for record in page_records]


def get_trade_statistics(hours: int = 24) -> Dict[str, Any]:
    """Return aggregate trade statistics for the requested window."""
    logger = get_trade_logger()
    stats = logger.get_statistics(hours=hours)
    
    total_trades = stats.get("master_trades", 0) + stats.get("follower_trades", 0)
    successful = stats.get("follower_success", 0)
    failed = stats.get("follower_failed", 0) + stats.get("errors", 0)
    attempt_count = successful + failed
    
    success_rate = 0.0
    if attempt_count > 0:
        success_rate = round(successful / attempt_count * 100, 2)
    
    return {
        "total_trades": total_trades,
        "successful_trades": successful,
        "failed_trades": failed,
        "success_rate": success_rate,
        "total_volume": round(stats.get("total_volume", 0.0), 4),
    }


def get_trade_detail(trade_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve detailed trade information by identifier."""
    logger = get_trade_logger()
    record = logger.get_trade_by_id(trade_id)
    if not record:
        return None
    
    trade = record_to_trade(record)
    # Attach additional metadata for detail view
    trade.update({
        "order_id": record.get("order_id"),
        "trade_id": record.get("trade_id"),
        "notional": record.get("notional"),
        "follower_name": record.get("follower_name"),
    })
    if record.get("error"):
        trade["error"] = record.get("error")
    if record.get("context"):
        trade["context"] = record.get("context")
    return trade
