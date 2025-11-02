"""Rate limiter for Binance API with weight tracking."""

import time
import logging
from threading import Lock
from typing import Dict, Optional
from collections import deque


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter that tracks API weight usage according to Binance limits.
    
    Binance Futures limits:
    - 2400 weight per minute
    - Response headers contain: X-MBX-USED-WEIGHT-1M
    """
    
    def __init__(
        self,
        weight_limit: int = 2400,
        window_seconds: int = 60,
        safety_margin: float = 0.8
    ):
        """
        Initialize rate limiter.
        
        Args:
            weight_limit: Maximum weight per window (default: 2400 for Futures)
            window_seconds: Time window in seconds (default: 60)
            safety_margin: Use only this fraction of limit (default: 0.8 = 80%)
        """
        self.weight_limit = weight_limit
        self.window_seconds = window_seconds
        self.safety_margin = safety_margin
        self.effective_limit = int(weight_limit * safety_margin)
        
        # Track weight usage with timestamps
        self.weight_history: deque = deque()  # [(timestamp, weight), ...]
        self.lock = Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_weight_used = 0
        self.wait_count = 0
        self.total_wait_time = 0.0
        
        logger.info(f"Rate limiter initialized: {self.effective_limit}/{weight_limit} weight per {window_seconds}s")
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove entries older than the time window."""
        cutoff_time = current_time - self.window_seconds
        
        while self.weight_history and self.weight_history[0][0] < cutoff_time:
            self.weight_history.popleft()
    
    def _get_current_weight(self, current_time: float) -> int:
        """Calculate current weight usage in the time window."""
        self._cleanup_old_entries(current_time)
        return sum(weight for _, weight in self.weight_history)
    
    def wait_if_needed(self, weight: int = 1) -> float:
        """
        Wait if adding this weight would exceed the limit.
        
        Args:
            weight: Weight of the upcoming request
            
        Returns:
            Time waited in seconds
        """
        with self.lock:
            current_time = time.time()
            current_weight = self._get_current_weight(current_time)
            
            # Check if we need to wait
            if current_weight + weight > self.effective_limit:
                # Calculate how long to wait
                if self.weight_history:
                    oldest_time = self.weight_history[0][0]
                    wait_time = (oldest_time + self.window_seconds) - current_time
                    
                    if wait_time > 0:
                        self.wait_count += 1
                        self.total_wait_time += wait_time
                        
                        logger.warning(
                            f"Rate limit approaching: {current_weight}/{self.effective_limit} weight. "
                            f"Waiting {wait_time:.2f}s..."
                        )
                        
                        time.sleep(wait_time)
                        current_time = time.time()
                        self._cleanup_old_entries(current_time)
                        
                        return wait_time
            
            # Record this request
            self.weight_history.append((current_time, weight))
            self.total_requests += 1
            self.total_weight_used += weight
            
            return 0.0
    
    def update_from_response(self, response_headers: Dict[str, str]) -> None:
        """
        Update weight tracking from API response headers.
        
        Args:
            response_headers: HTTP response headers from Binance API
        """
        # Binance returns actual weight usage in headers
        used_weight_header = response_headers.get('X-MBX-USED-WEIGHT-1M')
        
        if used_weight_header:
            try:
                server_weight = int(used_weight_header)
                
                with self.lock:
                    current_time = time.time()
                    current_weight = self._get_current_weight(current_time)
                    
                    # If server reports higher weight, adjust our tracking
                    if server_weight > current_weight:
                        diff = server_weight - current_weight
                        logger.debug(f"Adjusting weight tracking: +{diff} (server={server_weight}, local={current_weight})")
                        self.weight_history.append((current_time, diff))
                    
                    # Warn if approaching limit
                    if server_weight > self.weight_limit * 0.9:
                        logger.warning(f"⚠️  Rate limit critical: {server_weight}/{self.weight_limit} weight used!")
                    elif server_weight > self.effective_limit:
                        logger.warning(f"Rate limit high: {server_weight}/{self.weight_limit} weight used")
                        
            except ValueError:
                logger.warning(f"Invalid weight header value: {used_weight_header}")
    
    def get_statistics(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        with self.lock:
            current_time = time.time()
            current_weight = self._get_current_weight(current_time)
            
            return {
                'total_requests': self.total_requests,
                'total_weight_used': self.total_weight_used,
                'current_weight': current_weight,
                'weight_limit': self.weight_limit,
                'effective_limit': self.effective_limit,
                'utilization': (current_weight / self.effective_limit * 100) if self.effective_limit > 0 else 0,
                'wait_count': self.wait_count,
                'total_wait_time': self.total_wait_time,
                'avg_wait_time': (self.total_wait_time / self.wait_count) if self.wait_count > 0 else 0
            }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        with self.lock:
            self.total_requests = 0
            self.total_weight_used = 0
            self.wait_count = 0
            self.total_wait_time = 0.0
