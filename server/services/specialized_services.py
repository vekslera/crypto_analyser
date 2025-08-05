"""
Specialized services demonstrating Interface Segregation Principle (ISP)
Each service depends only on the interfaces it actually needs
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

from ..interfaces.database_interface import DataReader, DataWriter, DataAdministrator, DataAnalytics, PriceData
from ..interfaces.crypto_data_interface import PriceDataFetcher, ProviderMetadata, ProviderHealth
from ..shared_data import shared_data

logger = logging.getLogger(__name__)


class PriceCollectionService:
    """Service for collecting and storing price data (only needs DataWriter and PriceDataFetcher)"""
    
    def __init__(self, 
                 data_writer: DataWriter,
                 price_fetcher: PriceDataFetcher):
        self.data_writer = data_writer
        self.price_fetcher = price_fetcher
        logger.info("PriceCollectionService initialized")
    
    async def fetch_and_store_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price and store it"""
        try:
            # Fetch from data provider
            price_data = await self.price_fetcher.fetch_current_price(symbol)
            if not price_data:
                logger.error(f"Failed to fetch current price for {symbol}")
                return None
            
            # Store in database
            success = await self.data_writer.save_price(price_data)
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


class PriceQueryService:
    """Service for querying price data (only needs DataReader)"""
    
    def __init__(self, data_reader: DataReader):
        self.data_reader = data_reader
        logger.info("PriceQueryService initialized")
    
    async def get_recent_prices(self, limit: int = 100) -> List[PriceData]:
        """Get recent price data"""
        try:
            prices = await self.data_reader.get_recent_prices(limit)
            logger.debug(f"Retrieved {len(prices)} recent prices")
            return prices
        except Exception as e:
            logger.error(f"Error getting recent prices: {e}")
            return []
    
    async def get_price_history(self, limit: int = 1000) -> List[PriceData]:
        """Get historical price data"""
        try:
            prices = await self.data_reader.get_price_history(limit)
            logger.debug(f"Retrieved {len(prices)} historical prices")
            return prices
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
    
    def get_recent_series(self, limit: int = 100) -> pd.Series:
        """Get recent data as pandas series (from shared data)"""
        try:
            series = shared_data.get_recent_data(limit)
            return series
        except Exception as e:
            logger.error(f"Error getting recent series: {e}")
            return pd.Series()


class DataAnalyticsService:
    """Service for analytics operations (only needs DataAnalytics)"""
    
    def __init__(self, 
                 data_analytics: DataAnalytics,
                 provider_metadata: ProviderMetadata):
        self.data_analytics = data_analytics
        self.provider_metadata = provider_metadata
        self.provider_name = provider_metadata.get_provider_name()
        logger.info(f"DataAnalyticsService initialized with {self.provider_name} provider")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistical analysis of price data"""
        try:
            stats = await self.data_analytics.get_statistics()
            stats['data_provider'] = self.provider_name
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'count': 0, 'data_provider': self.provider_name}


class DataMaintenanceService:
    """Service for data maintenance operations (only needs DataAdministrator)"""
    
    def __init__(self, data_administrator: DataAdministrator):
        self.data_administrator = data_administrator
        logger.info("DataMaintenanceService initialized")
    
    async def clear_all_data(self) -> bool:
        """Clear all stored data"""
        try:
            # Clear database
            db_success = await self.data_administrator.clear_all_data()
            
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
    
    async def initialize_storage(self) -> bool:
        """Initialize storage systems"""
        try:
            success = await self.data_administrator.initialize()
            if success:
                logger.info("Storage initialized successfully")
            else:
                logger.error("Failed to initialize storage")
            return success
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
            return False


class HealthMonitoringService:
    """Service for health monitoring (only needs health-related interfaces)"""
    
    def __init__(self, 
                 data_administrator: DataAdministrator,
                 provider_health: ProviderHealth,
                 provider_metadata: ProviderMetadata):
        self.data_administrator = data_administrator
        self.provider_health = provider_health
        self.provider_metadata = provider_metadata
        self.provider_name = provider_metadata.get_provider_name()
        logger.info(f"HealthMonitoringService initialized for {self.provider_name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all dependencies"""
        try:
            db_health = await self.data_administrator.health_check()
            provider_health = await self.provider_health.health_check()
            
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


class ProviderInfoService:
    """Service for provider information (only needs ProviderMetadata)"""
    
    def __init__(self, provider_metadata: ProviderMetadata):
        self.provider_metadata = provider_metadata
        self.provider_name = provider_metadata.get_provider_name()
        logger.info(f"ProviderInfoService initialized for {self.provider_name}")
    
    async def get_supported_symbols(self) -> List[str]:
        """Get supported cryptocurrency symbols"""
        try:
            symbols = await self.provider_metadata.get_supported_symbols()
            return symbols
        except Exception as e:
            logger.error(f"Error getting supported symbols: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the data provider"""
        try:
            return {
                "provider_name": self.provider_name,
                "rate_limits": self.provider_metadata.get_rate_limits()
            }
        except Exception as e:
            logger.error(f"Error getting provider info: {e}")
            return {"provider_name": self.provider_name, "error": str(e)}