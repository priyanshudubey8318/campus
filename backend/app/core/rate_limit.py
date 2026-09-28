"""Sliding-window in-memory rate limiter for authentication endpoints.

Provides protection against credential stuffing and brute-force attacks by
tracking failed attempts per IP address and normalized username/email.
"""

import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Tuple

from app.core.config import get_settings

settings = get_settings()


class BaseRateLimiter(ABC):
    """Abstract interface for rate limiters.
    
    Provides a standardized contract for throttling authentication endpoints.
    Allows seamlessly swapping the local single-process memory implementation
    with a distributed multi-instance backend (e.g., Redis / Memcached)
    in production environments without modifying dependent service code.
    """

    @abstractmethod
    def check(self, key: str) -> Tuple[bool, int]:
        """Check if a key is rate-limited. Returns (is_rate_limited, retry_after_seconds)."""
        pass

    @abstractmethod
    def record_failure(self, key: str) -> Tuple[bool, int]:
        """Record a failure for key. Returns (is_rate_limited, retry_after_seconds)."""
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset attempts for key upon successful authentication."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all rate limit state."""
        pass


class SlidingWindowRateLimiter(BaseRateLimiter):
    """Thread-safe sliding window rate limiter implemented in process memory.
    
    LIMITATION NOTE:
    This limiter operates strictly within the single Python process memory space.
    It protects single-node deployments and local development against brute-force
    attacks. In a multi-worker or horizontally scaled cluster behind a load balancer,
    rate limit counters are not shared across processes. A distributed store (e.g. Redis)
    implementing BaseRateLimiter must be used for multi-node production topologies.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()


    def _cleanup_window(self, key: str, now: float) -> List[float]:
        cutoff = now - self.window_seconds
        valid_attempts = [t for t in self._attempts[key] if t > cutoff]
        self._attempts[key] = valid_attempts
        return valid_attempts

    def check(self, key: str) -> Tuple[bool, int]:
        """Check if a key is currently rate-limited.
        
        Returns:
            Tuple of (is_rate_limited: bool, retry_after_seconds: int)
        """
        now = time.time()
        with self._lock:
            attempts = self._cleanup_window(key, now)
            if len(attempts) >= self.max_attempts:
                oldest_in_window = min(attempts)
                retry_after = int(self.window_seconds - (now - oldest_in_window)) + 1
                return True, max(1, retry_after)
            return False, 0

    def record_failure(self, key: str) -> Tuple[bool, int]:
        """Record a failed attempt and return whether key is now rate-limited."""
        now = time.time()
        with self._lock:
            attempts = self._cleanup_window(key, now)
            attempts.append(now)
            self._attempts[key] = attempts
            if len(attempts) >= self.max_attempts:
                oldest_in_window = min(attempts)
                retry_after = int(self.window_seconds - (now - oldest_in_window)) + 1
                return True, max(1, retry_after)
            return False, 0

    def reset(self, key: str) -> None:
        """Reset attempts for a key upon successful authentication."""
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]

    def clear(self) -> None:
        """Clear all tracked rate limit attempts."""
        with self._lock:
            self._attempts.clear()


# Global rate limiter initialized from settings
login_rate_limiter = SlidingWindowRateLimiter(
    max_attempts=settings.LOGIN_RATE_LIMIT_ATTEMPTS,
    window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
)
