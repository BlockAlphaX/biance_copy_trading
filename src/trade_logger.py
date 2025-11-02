"""Trade logger for persisting trading records."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock


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
    
    def _write_record(self, record: Dict[str, Any]) -> None:
        """
        Write a record to the log file.
        
        Args:
            record: Record dictionary to write
        """
        with self.lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to write trade log: {e}")
    
    def get_recent_trades(self, count: int = 100) -> list:
        """
        Get recent trades from log file.
        
        Args:
            count: Number of recent trades to retrieve
            
        Returns:
            List of trade records
        """
        trades = []
        
        try:
            if not self.log_file.exists():
                return trades
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-count:]:
                try:
                    trades.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to read trade log: {e}")
        
        return trades
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get trading statistics from log file.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Statistics dictionary
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {
            'master_trades': 0,
            'follower_trades': 0,
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
                        record_time = datetime.fromisoformat(record['timestamp'])
                        
                        if record_time < cutoff_time:
                            continue
                        
                        if record['type'] == 'master':
                            stats['master_trades'] += 1
                            stats['total_volume'] += record.get('notional', 0)
                            stats['symbols'].add(record['symbol'])
                            
                        elif record['type'] == 'follower':
                            stats['follower_trades'] += 1
                            stats['followers'].add(record['follower_name'])
                            if 'notional' in record:
                                stats['total_volume'] += record['notional']
                                
                        elif record['type'] == 'error':
                            stats['errors'] += 1
                            
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
        
        # Convert sets to lists for JSON serialization
        stats['symbols'] = list(stats['symbols'])
        stats['followers'] = list(stats['followers'])
        
        return stats
