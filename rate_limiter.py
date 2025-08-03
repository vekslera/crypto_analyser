"""
Global rate limiter for CoinGecko API calls
Ensures all parts of the application respect rate limits
"""

from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

class GlobalRateLimiter:
    """
    Global rate limiter to ensure we don't exceed CoinGecko API limits
    CoinGecko free tier: ~5-15 calls per minute
    We'll be conservative with 4 calls per minute (15 second intervals)
    """
    
    def __init__(self, min_interval_seconds=15):
        self.min_interval = min_interval_seconds
        self.last_successful_call = None
        self.cached_data = None
        self.cache_expiry = None
        self.call_count = 0
    
    def can_make_call(self):
        """Check if we can make an API call without hitting rate limits"""
        if not self.last_successful_call:
            return True
        
        time_since_last = (datetime.utcnow() - self.last_successful_call).total_seconds()
        return time_since_last >= self.min_interval
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        if not self.last_successful_call:
            return 0
        
        time_since_last = (datetime.utcnow() - self.last_successful_call).total_seconds()
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.info(f"Global rate limiter: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
            return wait_time
        return 0
    
    def record_successful_call(self, data=None):
        """Record a successful API call"""
        self.last_successful_call = datetime.utcnow()
        self.call_count += 1
        
        if data:
            self.cached_data = data
            self.cache_expiry = datetime.utcnow() + timedelta(seconds=30)  # 30 second cache
        
        logger.info(f"API call #{self.call_count} completed successfully")
    
    def record_failed_call(self, is_rate_limit_error=False):
        """Record a failed API call"""
        if is_rate_limit_error:
            # For 429 errors, still update the timer to enforce waiting
            self.last_successful_call = datetime.utcnow()
            logger.warning("429 rate limit error - enforcing delay")
        else:
            # For other errors, don't update timer (allows faster retry)
            logger.info("API call failed (non-rate-limit) - no delay enforced")
    
    def get_cached_data(self):
        """Get cached data if still valid"""
        if self.cached_data and self.cache_expiry:
            if datetime.utcnow() < self.cache_expiry:
                logger.info("Returning cached data")
                return self.cached_data
        return None
    
    def get_stats(self):
        """Get rate limiter statistics"""
        return {
            'total_calls': self.call_count,
            'last_call': self.last_successful_call,
            'has_cache': bool(self.cached_data),
            'cache_valid': bool(self.cached_data and self.cache_expiry and datetime.utcnow() < self.cache_expiry)
        }

# Global instance - all parts of the app will use this
global_rate_limiter = GlobalRateLimiter()