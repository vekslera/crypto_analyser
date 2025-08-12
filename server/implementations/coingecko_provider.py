"""
CoinGecko implementation of crypto data provider
Concrete implementation of CryptoDataProvider using CoinGecko API with tenacity retry logic
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log
)

from ..interfaces.crypto_data_interface import CryptoDataProvider
from ..interfaces.database_interface import PriceData
from core.api_config import CG_API_KEY

logger = logging.getLogger(__name__)


def should_retry_on_status(response):
    """Determine if we should retry based on HTTP status code"""
    if response is None:
        return True
    # Retry on rate limiting (429), server errors (5xx), but not on client errors (4xx except 429)
    return response.status_code in [429, 500, 502, 503, 504] if hasattr(response, 'status_code') else True


def is_response_valid(response):
    """Check if response is valid and shouldn't be retried"""
    return response is not None and hasattr(response, 'status_code') and 200 <= response.status_code < 300


class CoinGeckoProvider(CryptoDataProvider):
    """CoinGecko implementation of CryptoDataProvider"""
    
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.provider_name = "CoinGecko"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING, exc_info=True),
        reraise=True
    )
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> requests.Response:
        """Make API request with retry logic and Demo API key"""
        headers = {}
        
        # Add Demo API key if available
        if CG_API_KEY:
            headers['x-cg-demo-api-key'] = CG_API_KEY
            logger.debug("Using CoinGecko Demo API key")
        
        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        
        # Check for rate limiting or server errors
        if response.status_code == 429:
            logger.warning(f"Rate limited by CoinGecko API, will retry after backoff")
            raise requests.exceptions.RequestException(f"Rate limited: {response.status_code}")
        elif response.status_code >= 500:
            logger.warning(f"Server error from CoinGecko API: {response.status_code}, will retry")
            raise requests.exceptions.RequestException(f"Server error: {response.status_code}")
        
        response.raise_for_status()
        return response

    async def fetch_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price from CoinGecko API with retry logic"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': symbol,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self._make_api_request(url, params)
            
            data = response.json()
            if symbol not in data:
                logger.error(f"Symbol {symbol} not found in response")
                return None
            
            crypto_data = data[symbol]
            
            price_data = PriceData(
                price=crypto_data['usd'],
                market_cap=crypto_data.get('usd_market_cap'),
                volume_24h=crypto_data.get('usd_24h_vol'),
                timestamp=datetime.utcnow()
            )
            
            logger.debug(f"Fetched {symbol} price: ${price_data.price:,.2f}")
            return price_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API request failed after retries: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price: {e}")
            return None
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> List[PriceData]:
        """Fetch historical price data from CoinGecko with retry logic"""
        try:
            url = f"{self.base_url}/coins/{symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if days > 1 else 'hourly'
            }
            
            response = self._make_api_request(url, params)
            
            data = response.json()
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            volumes = data.get('total_volumes', [])
            
            result = []
            for i, price_point in enumerate(prices):
                timestamp_ms, price = price_point
                market_cap = market_caps[i][1] if i < len(market_caps) else None
                volume = volumes[i][1] if i < len(volumes) else None
                
                price_data = PriceData(
                    price=price,
                    timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                    market_cap=market_cap,
                    volume_24h=volume
                )
                result.append(price_data)
            
            logger.debug(f"Fetched {len(result)} historical data points for {symbol}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko historical data request failed after retries: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching historical data: {e}")
            return []

    async def fetch_interval_volume_data(self, symbol: str = "bitcoin", days: int = 1) -> List[PriceData]:
        """Fetch interval volume data from CoinGecko market chart endpoint (requires Demo API key)"""
        try:
            url = f"{self.base_url}/coins/{symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            response = self._make_api_request(url, params)
            
            data = response.json()
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            volumes = data.get('total_volumes', [])
            
            result = []
            for i in range(len(volumes)):
                if i < len(prices) and i < len(market_caps):
                    timestamp_ms, volume = volumes[i]
                    _, price = prices[i]
                    _, market_cap = market_caps[i]
                    
                    price_data = PriceData(
                        price=price,
                        timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                        market_cap=market_cap,
                        volume_24h=volume
                    )
                    result.append(price_data)
            
            logger.debug(f"Fetched {len(result)} interval volume data points for {symbol}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko interval volume request failed after retries: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching interval volume data: {e}")
            return []
    
    async def get_supported_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols from CoinGecko with retry logic"""
        try:
            url = f"{self.base_url}/coins/list"
            response = self._make_api_request(url, {})
            
            data = response.json()
            symbols = [coin['id'] for coin in data]
            
            logger.debug(f"Retrieved {len(symbols)} supported symbols")
            return symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get supported symbols after retries: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting symbols: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if CoinGecko API is accessible with retry logic"""
        try:
            url = f"{self.base_url}/ping"
            response = self._make_api_request(url, {})
            
            logger.debug("CoinGecko API health check passed")
            return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API health check failed after retries: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in health check: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of the data provider"""
        return self.provider_name
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting information for CoinGecko"""
        return {
            "requests_per_minute": 60,  # CoinGecko free tier
            "requests_per_hour": 1000,
            "provider": self.provider_name,
            "documentation": "https://www.coingecko.com/en/api/documentation"
        }