"""
Cryptocurrency service layer
Business logic for cryptocurrency operations using dependency injection
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

from ..interfaces.database_interface import DatabaseRepository, PriceData
from ..interfaces.crypto_data_interface import CryptoDataProvider
from ..shared_data import shared_data

logger = logging.getLogger(__name__)


class CryptoService:
    """Service layer for cryptocurrency operations (DIP compliant)"""
    
    def __init__(self, 
                 database_repo: DatabaseRepository,
                 data_provider: CryptoDataProvider):
        self.database_repo = database_repo
        self.data_provider = data_provider
        self.provider_name = data_provider.get_provider_name()
        logger.info(f"CryptoService initialized with {self.provider_name} provider")
    
    async def fetch_and_store_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price and store it"""
        try:
            # Fetch from data provider
            price_data = await self.data_provider.fetch_current_price(symbol)
            if not price_data:
                logger.error(f"Failed to fetch current price for {symbol}")
                return None
            
            # Store in database
            success = await self.database_repo.save_price(price_data)
            if not success:
                logger.error(f"Failed to store price data for {symbol}")
                return None
            
            # Add to shared data series for real-time access
            shared_data.add_price(price_data.price, price_data.timestamp)
            
            logger.info(f"Successfully fetched and stored {symbol} price: ${price_data.price:,.2f}")
            return price_data
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_current_price: {e}")
            return None
    
    async def get_recent_prices(self, limit: int = 100) -> List[PriceData]:
        """Get recent price data"""
        try:
            prices = await self.database_repo.get_recent_prices(limit)
            logger.debug(f"Retrieved {len(prices)} recent prices")
            return prices
        except Exception as e:
            logger.error(f"Error getting recent prices: {e}")
            return []
    
    async def get_price_history(self, limit: int = 1000) -> List[PriceData]:
        """Get historical price data"""
        try:
            prices = await self.database_repo.get_price_history(limit)
            logger.debug(f"Retrieved {len(prices)} historical prices")
            return prices
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistical analysis of price data"""
        try:
            stats = await self.database_repo.get_statistics()
            stats['data_provider'] = self.provider_name
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'count': 0, 'data_provider': self.provider_name}
    
    async def clear_all_data(self) -> bool:
        """Clear all stored data"""
        try:
            # Clear database
            db_success = await self.database_repo.clear_all_data()
            
            # Clear shared data
            shared_data.clear_data()
            
            if db_success:
                logger.info("Successfully cleared all data")
                return True
            else:
                logger.error("Failed to clear database data")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
    
    def get_recent_series(self, limit: int = 100) -> pd.Series:
        """Get recent data as pandas series (from shared data)"""
        try:
            series = shared_data.get_recent_data(limit)
            return series
        except Exception as e:
            logger.error(f"Error getting recent series: {e}")
            return pd.Series()
    
    def add_to_series(self, price: float, timestamp: datetime = None):
        """Add price to shared data series"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        shared_data.add_price(price, timestamp)
        logger.debug(f"Added price ${price:,.2f} to series at {timestamp}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all dependencies"""
        try:
            db_health = await self.database_repo.health_check()
            provider_health = await self.data_provider.health_check()
            
            return {
                "service_healthy": True,
                "database_healthy": db_health,
                "data_provider_healthy": provider_health,
                "data_provider_name": self.provider_name
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service_healthy": False,
                "error": str(e),
                "data_provider_name": self.provider_name
            }
    
    async def get_supported_symbols(self) -> List[str]:
        """Get supported cryptocurrency symbols"""
        try:
            symbols = await self.data_provider.get_supported_symbols()
            return symbols
        except Exception as e:
            logger.error(f"Error getting supported symbols: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the data provider"""
        try:
            return {
                "provider_name": self.provider_name,
                "rate_limits": self.data_provider.get_rate_limits()
            }
        except Exception as e:
            logger.error(f"Error getting provider info: {e}")
            return {"provider_name": self.provider_name, "error": str(e)}