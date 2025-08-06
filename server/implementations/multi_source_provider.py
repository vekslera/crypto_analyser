"""
Multi-source crypto data provider
Fetches data from multiple APIs and compares reliability
"""

import requests
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from ..interfaces.crypto_data_interface import CryptoDataProvider
from ..interfaces.database_interface import PriceData

logger = logging.getLogger(__name__)


class MultiSourceProvider(CryptoDataProvider):
    """Multi-source crypto data provider for reliability comparison"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.provider_name = "MultiSource"
        self.sources = {
            'coingecko': self._fetch_coingecko,
            'coinmarketcap': self._fetch_coinmarketcap,
            'mobula': self._fetch_mobula,
            'binance': self._fetch_binance
        }
    
    async def fetch_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price from multiple sources and compare"""
        results = {}
        
        # Fetch from all sources in parallel
        tasks = []
        for source_name, fetch_func in self.sources.items():
            task = asyncio.create_task(
                self._safe_fetch(source_name, fetch_func, symbol)
            )
            tasks.append((source_name, task))
        
        # Wait for all tasks to complete
        for source_name, task in tasks:
            try:
                result = await task
                if result:
                    results[source_name] = result
                    logger.debug(f"{source_name}: Success")
                else:
                    logger.debug(f"{source_name}: No data")
            except Exception as e:
                logger.debug(f"{source_name}: Error - {e}")
        
        # Analyze and log results
        if results:
            self._analyze_sources(results)
            # Return the most reliable result (for now, prefer CoinGecko if available)
            if 'coingecko' in results:
                return results['coingecko']
            else:
                return list(results.values())[0]
        
        return None
    
    async def _safe_fetch(self, source_name: str, fetch_func, symbol: str) -> Optional[PriceData]:
        """Safely fetch from a source with error handling"""
        try:
            return await fetch_func(symbol)
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            return None
    
    def _analyze_sources(self, results: Dict[str, PriceData]):
        """Analyze and compare data from different sources"""
        if len(results) < 2:
            return
        
        logger.info(f"Multi-source comparison ({len(results)} sources):")
        
        prices = []
        volumes = []
        
        for source_name, data in results.items():
            price_str = f"${data.price:,.2f}" if data.price else "None"
            volume_str = f"${data.volume_24h:,.0f}" if data.volume_24h else "None"
            logger.info(f"  {source_name}: Price={price_str}, Volume={volume_str}")
            
            if data.price:
                prices.append(data.price)
            if data.volume_24h:
                volumes.append(data.volume_24h)
        
        # Calculate variance
        if len(prices) > 1:
            price_variance = max(prices) - min(prices)
            price_variance_pct = (price_variance / min(prices)) * 100
            logger.info(f"  Price variance: ${price_variance:,.2f} ({price_variance_pct:.2f}%)")
        
        if len(volumes) > 1:
            volume_variance = max(volumes) - min(volumes)
            volume_variance_pct = (volume_variance / min(volumes)) * 100
            logger.info(f"  Volume variance: ${volume_variance:,.0f} ({volume_variance_pct:.2f}%)")
    
    # Source-specific implementations
    
    async def _fetch_coingecko(self, symbol: str) -> Optional[PriceData]:
        """Fetch from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
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
                return None
            
            crypto_data = data[symbol]
            
            return PriceData(
                price=crypto_data['usd'],
                market_cap=crypto_data.get('usd_market_cap'),
                volume_24h=crypto_data.get('usd_24h_vol'),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.debug(f"CoinGecko fetch failed: {e}")
            return None
    
    async def _fetch_coinmarketcap(self, symbol: str) -> Optional[PriceData]:
        """Fetch from CoinMarketCap API (free tier available)"""
        try:
            # CoinMarketCap uses different symbol mapping
            symbol_mapping = {'bitcoin': '1'}  # Bitcoin's CoinMarketCap ID
            cmc_id = symbol_mapping.get(symbol, '1')
            
            # Free tier endpoint
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            
            # NOTE: You need to get a free API key from https://coinmarketcap.com/api/
            # and set it as environment variable: CMC_API_KEY
            import os
            api_key = os.getenv('CMC_API_KEY')
            if not api_key:
                logger.debug("CoinMarketCap: CMC_API_KEY environment variable not set")
                return None
            
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': api_key,
            }
            
            params = {
                'id': cmc_id,  # Bitcoin ID
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or cmc_id not in data['data']:
                logger.debug("CoinMarketCap: Invalid response structure")
                return None
            
            crypto_data = data['data'][cmc_id]
            quote_data = crypto_data['quote']['USD']
            
            return PriceData(
                price=quote_data.get('price'),
                market_cap=quote_data.get('market_cap'),
                volume_24h=quote_data.get('volume_24h'),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.debug(f"CoinMarketCap fetch failed: {e}")
            return None
    
    async def _fetch_mobula(self, symbol: str) -> Optional[PriceData]:
        """Fetch from Mobula API"""
        try:
            # Convert bitcoin -> BTC for Mobula API
            symbol_mapping = {'bitcoin': 'bitcoin'}  # Mobula uses same naming
            mobula_symbol = symbol_mapping.get(symbol, symbol)
            
            url = f"https://api.mobula.io/api/1/market/data"
            params = {
                'asset': mobula_symbol
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data:
                return None
            
            market_data = data['data']
            
            return PriceData(
                price=market_data.get('price'),
                market_cap=market_data.get('market_cap'),
                volume_24h=market_data.get('volume'),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.debug(f"Mobula fetch failed: {e}")
            return None
    
    async def _fetch_binance(self, symbol: str) -> Optional[PriceData]:
        """Fetch from Binance API"""
        try:
            # Binance uses BTCUSDT format
            symbol_mapping = {'bitcoin': 'BTCUSDT'}
            binance_symbol = symbol_mapping.get(symbol, 'BTCUSDT')
            
            # Get current price
            price_url = "https://api.binance.com/api/v3/ticker/price"
            price_params = {'symbol': binance_symbol}
            
            # Get 24h stats  
            stats_url = "https://api.binance.com/api/v3/ticker/24hr"
            stats_params = {'symbol': binance_symbol}
            
            # Fetch both endpoints
            price_response = requests.get(price_url, params=price_params, timeout=self.timeout)
            stats_response = requests.get(stats_url, params=stats_params, timeout=self.timeout)
            
            price_response.raise_for_status()
            stats_response.raise_for_status()
            
            price_data = price_response.json()
            stats_data = stats_response.json()
            
            # Convert volume from BTC to USD (approximate)
            price = float(price_data['price'])
            volume_btc = float(stats_data['volume'])
            volume_usd = volume_btc * price
            
            return PriceData(
                price=price,
                market_cap=None,  # Binance doesn't provide market cap
                volume_24h=volume_usd,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.debug(f"Binance fetch failed: {e}")
            return None
    
    # Required interface methods
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> List[PriceData]:
        """Fetch historical data (using primary source for now)"""
        # For now, delegate to CoinGecko
        coingecko_result = await self._fetch_coingecko(symbol)
        return [coingecko_result] if coingecko_result else []
    
    async def get_supported_symbols(self) -> List[str]:
        """Get supported symbols"""
        return ['bitcoin']  # Start with Bitcoin only
    
    async def health_check(self) -> bool:
        """Check if any data source is available"""
        test_data = await self.fetch_current_price('bitcoin')
        return test_data is not None
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting info"""
        return {
            "requests_per_minute": 60,
            "provider": self.provider_name,
            "sources": list(self.sources.keys())
        }