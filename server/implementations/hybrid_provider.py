"""
Hybrid crypto data provider
Uses CoinMarketCap for volume data and CoinGecko for price/market cap
Optimizes for data quality and API rate limits
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..interfaces.crypto_data_interface import CryptoDataProvider
from ..interfaces.database_interface import PriceData
from .coingecko_provider import CoinGeckoProvider
from .multi_source_provider import MultiSourceProvider

logger = logging.getLogger(__name__)


class HybridProvider(CryptoDataProvider):
    """Hybrid provider using CMC for volume, CoinGecko for price/market cap"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.provider_name = "Hybrid (CoinGecko + CoinMarketCap)"
        
        # Initialize sub-providers
        self.coingecko = CoinGeckoProvider()
        self.multi_source = MultiSourceProvider(timeout=timeout)
        
        # Track last successful data for fallback
        self.last_successful_data = None
    
    async def fetch_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price combining CoinGecko + CMC volume"""
        
        try:
            # Fetch from both sources concurrently
            cg_task = asyncio.create_task(self.coingecko.fetch_current_price(symbol))
            cmc_task = asyncio.create_task(self.multi_source._fetch_coinmarketcap(symbol))
            
            # Wait for both with timeout
            cg_data, cmc_data = await asyncio.gather(cg_task, cmc_task, return_exceptions=True)
            
            # Handle exceptions
            if isinstance(cg_data, Exception):
                logger.warning(f"CoinGecko fetch failed: {cg_data}")
                cg_data = None
            
            if isinstance(cmc_data, Exception):
                logger.warning(f"CoinMarketCap fetch failed: {cmc_data}")
                cmc_data = None
            
            # Combine the data
            combined_data = self._combine_data(cg_data, cmc_data, symbol)
            
            if combined_data:
                self.last_successful_data = combined_data
                logger.info(f"Hybrid fetch successful: Price from CoinGecko, Volume from CoinMarketCap")
                return combined_data
            
            # Fallback to last successful data if recent
            if self.last_successful_data:
                time_diff = (datetime.utcnow() - self.last_successful_data.timestamp).total_seconds()
                if time_diff < 3600:  # Use if less than 1 hour old
                    logger.warning("Using cached data due to fetch failure")
                    return self.last_successful_data
            
            logger.error("All data sources failed and no recent cache available")
            return None
            
        except Exception as e:
            logger.error(f"Hybrid provider fetch failed: {e}")
            return None
    
    def _combine_data(self, cg_data: Optional[PriceData], cmc_data: Optional[PriceData], symbol: str) -> Optional[PriceData]:
        """Combine CoinGecko and CoinMarketCap data intelligently"""
        
        # Priority logic for each field:
        # Price: CoinGecko preferred (more frequent updates)
        # Volume: CoinMarketCap preferred (better quality as proven)
        # Market Cap: CoinGecko preferred (more reliable)
        
        if not cg_data and not cmc_data:
            return None
        
        # Determine best values
        price = None
        volume_24h = None
        market_cap = None
        
        # Price: Prefer CoinGecko, fallback to CMC
        if cg_data and cg_data.price:
            price = cg_data.price
        elif cmc_data and cmc_data.price:
            price = cmc_data.price
        
        # Volume: Prefer CMC, fallback to CoinGecko
        if cmc_data and cmc_data.volume_24h:
            volume_24h = cmc_data.volume_24h
        elif cg_data and cg_data.volume_24h:
            volume_24h = cg_data.volume_24h
        
        # Market Cap: Prefer CoinGecko, fallback to CMC  
        if cg_data and cg_data.market_cap:
            market_cap = cg_data.market_cap
        elif cmc_data and cmc_data.market_cap:
            market_cap = cmc_data.market_cap
        
        # Must have at least price to be useful
        if not price:
            logger.warning("No price data available from either source")
            return None
        
        # Log the data sources used
        sources_used = []
        if cg_data and cg_data.price == price:
            sources_used.append("CG:price")
        if cmc_data and cmc_data.price == price:
            sources_used.append("CMC:price")
        if cmc_data and cmc_data.volume_24h == volume_24h:
            sources_used.append("CMC:volume")
        if cg_data and cg_data.volume_24h == volume_24h:
            sources_used.append("CG:volume")
        if cg_data and cg_data.market_cap == market_cap:
            sources_used.append("CG:mcap")
        if cmc_data and cmc_data.market_cap == market_cap:
            sources_used.append("CMC:mcap")
        
        logger.debug(f"Combined data using: {', '.join(sources_used)}")
        
        return PriceData(
            price=price,
            market_cap=market_cap,
            volume_24h=volume_24h,
            timestamp=datetime.utcnow()
        )
    
    # Required interface methods
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> List[PriceData]:
        """Fetch historical data (delegate to CoinGecko for now)"""
        return await self.coingecko.fetch_historical_data(symbol, days)
    
    async def get_supported_symbols(self) -> List[str]:
        """Get supported symbols"""
        return await self.coingecko.get_supported_symbols()
    
    async def health_check(self) -> bool:
        """Check if the hybrid system is healthy"""
        try:
            test_data = await self.fetch_current_price('bitcoin')
            return test_data is not None
        except:
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting info"""
        return {
            "requests_per_minute": 30,  # Conservative for CMC free tier
            "provider": self.provider_name,
            "coingecko_limits": "60/min (no key required)",
            "coinmarketcap_limits": "333 calls/day at 5min intervals",
            "recommended_interval": "300 seconds (5 minutes)"
        }