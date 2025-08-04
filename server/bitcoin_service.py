import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from .shared_data import shared_data
from .rate_limiter import global_rate_limiter
from core.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinService:
    def __init__(self):
        self.base_url = COINGECKO_BASE_URL
        # Use global rate limiter instead of instance-specific rate limiting
        # Use shared data store instead of instance-specific series
    
    async def fetch_bitcoin_price(self) -> Optional[Dict[str, Any]]:
        # Check global cache first
        cached_data = global_rate_limiter.get_cached_data()
        if cached_data:
            return cached_data
        
        # Wait if needed to respect rate limits
        global_rate_limiter.wait_if_needed()
        
        try:
            url = f"{self.base_url}/simple/price"
            params = COINGECKO_PARAMS
            
            response = requests.get(url, params=params, timeout=API_REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            bitcoin_data = data['bitcoin']
            
            price_data = {
                'price': bitcoin_data['usd'],
                'market_cap': bitcoin_data.get('usd_market_cap'),
                'volume_24h': bitcoin_data.get('usd_24h_vol'),
                'timestamp': datetime.utcnow()
            }
            
            # Record successful call and cache data globally
            global_rate_limiter.record_successful_call(price_data)
            
            logger.info(f"Fetched Bitcoin price: ${price_data['price']:,.2f}")
            return price_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Bitcoin price: {e}")
            
            # Handle rate limit errors specially
            is_rate_limit = hasattr(e, 'response') and e.response and e.response.status_code == HTTP_RATE_LIMIT
            global_rate_limiter.record_failed_call(is_rate_limit_error=is_rate_limit)
            
            # Return cached data if available, even if expired
            cached_data = global_rate_limiter.get_cached_data()
            if cached_data:
                logger.info("Returning cached data due to API error")
                return cached_data
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def add_to_series(self, price: float, timestamp: datetime = None) -> None:
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        shared_data.add_price(price, timestamp)
        logger.info(f"Added price ${price:,.2f} to shared data series at {timestamp}")
    
    def get_recent_data(self, limit: int = DEFAULT_API_LIMIT) -> pd.Series:
        return shared_data.get_recent_data(limit)
    
    def get_statistics(self) -> Dict[str, float]:
        return shared_data.get_statistics()