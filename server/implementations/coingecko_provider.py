"""
CoinGecko implementation of crypto data provider
Concrete implementation of CryptoDataProvider using CoinGecko API
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from ..interfaces.crypto_data_interface import CryptoDataProvider
from ..interfaces.database_interface import PriceData

logger = logging.getLogger(__name__)


class CoinGeckoProvider(CryptoDataProvider):
    """CoinGecko implementation of CryptoDataProvider"""
    
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.provider_name = "CoinGecko"
    
    async def fetch_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price from CoinGecko API"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': symbol,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
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
            logger.error(f"CoinGecko API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price: {e}")
            return None
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> List[PriceData]:
        """Fetch historical price data from CoinGecko"""
        try:
            url = f"{self.base_url}/coins/{symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if days > 1 else 'hourly'
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
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
            logger.error(f"CoinGecko historical data request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching historical data: {e}")
            return []
    
    async def get_supported_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols from CoinGecko"""
        try:
            url = f"{self.base_url}/coins/list"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            symbols = [coin['id'] for coin in data]
            
            logger.debug(f"Retrieved {len(symbols)} supported symbols")
            return symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get supported symbols: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting symbols: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if CoinGecko API is accessible"""
        try:
            url = f"{self.base_url}/ping"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                logger.debug("CoinGecko API health check passed")
                return True
            else:
                logger.warning(f"CoinGecko API health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API health check failed: {e}")
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