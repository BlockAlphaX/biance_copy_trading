"""Trade logger for persisting trading records."""

import json
import logging
import hashlib
from collections import deque
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Iterable, List
from threading import Lock
from uuid import uuid4


logger = logging.getLogger(__name__)


class TradeLogger:
    """
    Logger for persisting trade records to JSON file.
    
    Each trade is recorded with timestamp, symbol, side, quantity, price, etc.
    """
    
    def __init__(self, log_file: str = "logs/trades.jsonl"):
        """
        Initialize trade logger.
        
        Args:
            log_file: Path to trade log file (JSONL format)
        """
        self.log_file = Path(log_file)
        self.lock = Lock()
        
        # Create log directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Trade logger initialized: {self.log_file}")
    
    def log_master_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        position_side: str = "BOTH",
        order_id: Optional[int] = None,
        trade_id: Optional[int] = None
    ) -> None:
        """
        Log a master account trade.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Execution price
            position_side: Position side (BOTH/LONG/SHORT)
            order_id: Order ID
            trade_id: Trade ID
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'type': 'master',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'position_side': position_side,
            'order_id': order_id,
            'trade_id': trade_id,
            'notional': quantity * price
        }
        
        self._write_record(record)
    
    def log_follower_trade(
        self,
        follower_name: str,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float],
        position_side: str = "BOTH",
        order_type: str = "MARKET",
        status: str = "UNKNOWN",
        order_id: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log a follower account trade.
        
        Args:
            follower_name: Name of the follower account
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Execution price (None for MARKET orders)
            position_side: Position side (BOTH/LONG/SHORT)
            order_type: Order type (MARKET/LIMIT)
            status: Order status (FILLED/REJECTED/etc)
            order_id: Order ID
            error: Error message if failed
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'type': 'follower',
            'follower_name': follower_name,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'position_side': position_side,
            'order_type': order_type,
            'status': status,
            'order_id': order_id,
            'error': error
        }
        
        if price:
            record['notional'] = quantity * price
        
        self._write_record(record)
    
    def log_error(
        self,
        follower_name: str,
        symbol: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error event.
        
        Args:
            follower_name: Name of the follower account
            symbol: Trading pair symbol
            error_type: Type of error (balance/min_notional/api/etc)
            error_message: Error message
            context: Additional context
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'follower_name': follower_name,
            'symbol': symbol,
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        }
        
        self._write_record(record)
    
    def _ensure_record_id(self, record: Dict[str, Any]) -> str:
        """Ensure each record has a stable identifier."""
        record_id = record.get('id')
        if record_id:
            return record_id
        
        # Use uuid for new entries while keeping deterministic fallback for legacy rows
        deterministic_source = json.dumps(
            {k: record[k] for k in sorted(record.keys()) if k != 'id'},
            ensure_ascii=False,
            sort_keys=True,
            default=str
        )
        record_id = hashlib.sha1(deterministic_source.encode('utf-8')).hexdigest()[:12]
        record['id'] = record_id
        return record_id
    
    def _write_record(self, record: Dict[str, Any]) -> None:
        """
        Write a record to the log file.
        
        Args:
            record: Record dictionary to write
        """
        with self.lock:
            try:
                if 'id' not in record:
                    record = dict(record)
                    record['id'] = uuid4().hex[:12]
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to write trade log: {e}")
    
    def _load_records(
        self,
        limit: Optional[int] = None,
        record_types: Optional[Iterable[str]] = None
    ) -> List[Dict[str, Any]]:
        """Load records from the log file with optional filtering."""
        if not self.log_file.exists():
            return []
        
        records: Iterable[Dict[str, Any]]
        buffer: Iterable
        if limit is not None:
            buffer = deque(maxlen=limit)
        else:
            buffer = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    self._ensure_record_id(record)
                    
                    if record_types and record.get('type') not in record_types:
                        continue
                    
                    if isinstance(buffer, deque):
                        buffer.append(record)
                    else:
                        buffer.append(record)
        except Exception as e:
            logger.error(f"Failed to load trade records: {e}")
            return []
        
        if isinstance(buffer, deque):
            records = list(buffer)
        else:
            records = list(buffer)
        return records
    
    def get_recent_trades(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades from log file.
        
        Args:
            count: Number of recent trades to retrieve
            
        Returns:
            List of trade records
        """
        records = self._load_records(limit=count, record_types={'master', 'follower'})
        # Return newest first
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return records
    
    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Return all trade records (master and follower) sorted by timestamp."""
        records = self._load_records(record_types={'master', 'follower'})
        records.sort(key=lambda x: x.get('timestamp', ''))
        return records
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a trade record by its identifier."""
        if not self.log_file.exists():
            return None
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    if record.get('id') == trade_id:
                        return record
                    
                    # Legacy rows might not have ID persisted
                    if not record.get('id'):
                        self._ensure_record_id(record)
                        if record['id'] == trade_id:
                            return record
        except Exception as e:
            logger.error(f"Failed to read trade by id: {e}")
        
        return None
    
    def get_records_by_type(self, record_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return records filtered by type."""
        records = self._load_records(limit=limit, record_types={record_type})
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return records
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get trading statistics from log file.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Statistics dictionary
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stats = {
            'master_trades': 0,
            'follower_trades': 0,
            'follower_success': 0,
            'follower_failed': 0,
            'errors': 0,
            'total_volume': 0.0,
            'symbols': set(),
            'followers': set()
        }
        
        try:
            if not self.log_file.exists():
                return stats
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    try:
                        record_time = datetime.fromisoformat(record['timestamp'])
                    except (KeyError, ValueError, TypeError):
                        continue
                    
                    if record_time.tzinfo is None:
                        record_time = record_time.replace(tzinfo=timezone.utc)
                    else:
                        record_time = record_time.astimezone(timezone.utc)
                    
                    if record_time < cutoff_time:
                        continue
                    
                    record_type = record.get('type')
                    
                    if record_type == 'master':
                        stats['master_trades'] += 1
                        stats['total_volume'] += record.get('notional', 0.0)
                        symbol = record.get('symbol')
                        if symbol:
                            stats['symbols'].add(symbol)
                    
                    elif record_type == 'follower':
                        stats['follower_trades'] += 1
                        status = (record.get('status') or '').upper()
                        if status in {'FILLED', 'PARTIALLY_FILLED', 'SUCCESS'}:
                            stats['follower_success'] += 1
                        elif status in {'CANCELLED', 'REJECTED', 'FAILED'} or record.get('error'):
                            stats['follower_failed'] += 1
                        
                        follower_name = record.get('follower_name')
                        if follower_name:
                            stats['followers'].add(follower_name)
                        
                        if 'notional' in record:
                            stats['total_volume'] += record['notional']
                    
                    elif record_type == 'error':
                        stats['errors'] += 1
                        follower_name = record.get('follower_name')
                        if follower_name:
                            stats['followers'].add(follower_name)
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
        
        # Convert sets to lists for JSON serialization
        stats['symbols'] = list(stats['symbols'])
        stats['followers'] = list(stats['followers'])
        
        return stats
