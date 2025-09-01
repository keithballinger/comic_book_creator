"""Rate limiting for API calls."""

import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls with exponential backoff."""
    
    def __init__(
        self,
        calls_per_minute: int = 60,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        """Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum API calls per minute
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff multiplier
        """
        self.calls_per_minute = calls_per_minute
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Calculate minimum time between calls
        self.min_interval = 60.0 / calls_per_minute
        
        # Track call times
        self.call_times = []
        self._lock = asyncio.Lock()
        
    async def acquire(self):
        """Acquire permission to make an API call."""
        async with self._lock:
            now = time.time()
            
            # Remove old call times (older than 1 minute)
            self.call_times = [t for t in self.call_times if now - t < 60]
            
            # Check if we've hit the rate limit
            if len(self.call_times) >= self.calls_per_minute:
                # Calculate wait time
                oldest_call = self.call_times[0]
                wait_time = 60 - (now - oldest_call) + 0.1  # Add small buffer
                
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    
                    # Recalculate after wait
                    now = time.time()
                    self.call_times = [t for t in self.call_times if now - t < 60]
            
            # Check minimum interval between calls
            if self.call_times:
                last_call = self.call_times[-1]
                elapsed = now - last_call
                
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    await asyncio.sleep(wait_time)
                    now = time.time()
            
            # Record this call
            self.call_times.append(now)
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with rate limiting and retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Acquire rate limit permission
                await self.acquire()
                
                # Execute the function
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a rate limit error from the API
                if 'rate' in str(e).lower() or '429' in str(e):
                    wait_time = (self.backoff_factor ** attempt) * 2
                    logger.warning(
                        f"API rate limit error on attempt {attempt + 1}, "
                        f"waiting {wait_time}s before retry"
                    )
                    await asyncio.sleep(wait_time)
                    
                # Check if this is a temporary error
                elif any(err in str(e).lower() for err in ['timeout', 'connection', '500', '502', '503']):
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Temporary error on attempt {attempt + 1}, "
                        f"waiting {wait_time}s before retry: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    
                else:
                    # Non-retryable error
                    logger.error(f"Non-retryable error: {e}")
                    raise
        
        # All retries exhausted
        logger.error(f"All {self.max_retries} retries failed")
        raise last_exception
    
    def reset(self):
        """Reset the rate limiter."""
        self.call_times.clear()
    
    def get_current_rate(self) -> float:
        """Get current API call rate (calls per minute).
        
        Returns:
            Current rate of API calls
        """
        now = time.time()
        recent_calls = [t for t in self.call_times if now - t < 60]
        return len(recent_calls)
    
    def get_remaining_calls(self) -> int:
        """Get remaining API calls available in current minute.
        
        Returns:
            Number of remaining calls
        """
        return max(0, self.calls_per_minute - int(self.get_current_rate()))


class TokenBucketRateLimiter:
    """Token bucket algorithm for smoother rate limiting."""
    
    def __init__(
        self,
        tokens_per_second: float,
        bucket_size: int,
        initial_tokens: Optional[int] = None
    ):
        """Initialize token bucket rate limiter.
        
        Args:
            tokens_per_second: Rate of token replenishment
            bucket_size: Maximum tokens in bucket
            initial_tokens: Initial token count (defaults to bucket_size)
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = initial_tokens if initial_tokens is not None else bucket_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        async with self._lock:
            # Update token count based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.bucket_size,
                self.tokens + elapsed * self.tokens_per_second
            )
            self.last_update = now
            
            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_and_acquire(self, tokens: int = 1):
        """Wait until tokens are available and acquire them.
        
        Args:
            tokens: Number of tokens to acquire
        """
        while not await self.acquire(tokens):
            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.tokens_per_second
            await asyncio.sleep(wait_time)