"""Circuit breaker pattern for fault tolerance."""

import time
import logging
from enum import Enum
from threading import Lock
from typing import Callable, Any, Optional
from collections import deque


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        window_size: int = 10
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name for logging
            failure_threshold: Number of failures to open circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before trying half-open
            window_size: Size of sliding window for failure tracking
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window_size = window_size
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        
        # Track recent results in sliding window
        self.recent_results: deque = deque(maxlen=window_size)
        
        self.lock = Lock()
        
        # Statistics
        self.total_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_rejections = 0
        
        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, timeout={timeout}s"
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is OPEN or function fails
        """
        with self.lock:
            self.total_calls += 1
            
            # Check if circuit is OPEN
            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if time.time() - self.last_failure_time >= self.timeout:
                    logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN (timeout expired)")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.last_state_change = time.time()
                else:
                    self.total_rejections += 1
                    raise Exception(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Retry after {self.timeout}s."
                    )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        with self.lock:
            self.total_successes += 1
            self.recent_results.append(True)
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.success_threshold:
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                        f"({self.success_count} consecutive successes)"
                    )
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.last_state_change = time.time()
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        with self.lock:
            self.total_failures += 1
            self.recent_results.append(False)
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                    f"(failure during recovery test)"
                )
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.last_state_change = time.time()
                
            elif self.state == CircuitState.CLOSED:
                # Calculate failure rate in recent window
                if len(self.recent_results) >= self.window_size:
                    failure_rate = sum(1 for r in self.recent_results if not r) / len(self.recent_results)
                    
                    if self.failure_count >= self.failure_threshold:
                        logger.error(
                            f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                            f"({self.failure_count} failures, {failure_rate*100:.1f}% failure rate)"
                        )
                        self.state = CircuitState.OPEN
                        self.last_state_change = time.time()
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        with self.lock:
            logger.info(f"Circuit breaker '{self.name}': Manual reset to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.recent_results.clear()
            self.last_state_change = time.time()
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self.lock:
            return self.state
    
    def get_statistics(self) -> dict:
        """Get circuit breaker statistics."""
        with self.lock:
            uptime = time.time() - self.last_state_change
            
            return {
                'name': self.name,
                'state': self.state.value,
                'total_calls': self.total_calls,
                'total_successes': self.total_successes,
                'total_failures': self.total_failures,
                'total_rejections': self.total_rejections,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'success_rate': (self.total_successes / self.total_calls * 100) if self.total_calls > 0 else 0,
                'current_state_duration': uptime,
                'last_failure_time': self.last_failure_time
            }


class CircuitBreakerManager:
    """Manage multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}
        self.lock = Lock()
    
    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    timeout=timeout
                )
            return self.breakers[name]
    
    def get_all_statistics(self) -> dict:
        """Get statistics for all circuit breakers."""
        with self.lock:
            return {
                name: breaker.get_statistics()
                for name, breaker in self.breakers.items()
            }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
