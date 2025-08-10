"""
Dependency injection container (ISP compliant)
Manages creation and configuration of dependencies following DIP and ISP
"""

import logging
import sys
import os
from typing import Optional

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logging_config import get_logger

from .interfaces.database_interface import (
    DatabaseRepository, DataReader, DataWriter, DataAdministrator, DataAnalytics
)
from .interfaces.crypto_data_interface import (
    CryptoDataProvider, PriceDataFetcher, ProviderMetadata, ProviderHealth
)
from .implementations.sqlite_repository import SQLiteRepository
from .implementations.coingecko_provider import CoinGeckoProvider
from .implementations.hybrid_provider import HybridProvider
from .services.crypto_service import CryptoService

logger = get_logger("server.dependency_container")


class DependencyContainer:
    """Container for managing dependencies"""
    
    def __init__(self):
        self._database_repository: Optional[DatabaseRepository] = None
        self._crypto_data_provider: Optional[CryptoDataProvider] = None
        self._crypto_service: Optional[CryptoService] = None
        self._initialized = False
    
    async def initialize(self, 
                        database_url: str = None,
                        crypto_provider: str = "coingecko",
                        **kwargs) -> bool:
        """Initialize all dependencies"""
        try:
            # Initialize database repository
            if database_url:
                if database_url.startswith("sqlite"):
                    self._database_repository = SQLiteRepository(database_url)
                # Easy to add other databases here:
                # elif database_url.startswith("postgresql"):
                #     self._database_repository = PostgreSQLRepository(database_url)
                # elif database_url.startswith("mongodb"):
                #     self._database_repository = MongoRepository(database_url)
                else:
                    raise ValueError(f"Unsupported database URL: {database_url}")
                
                await self._database_repository.initialize()
                logger.info(f"Database repository initialized: {type(self._database_repository).__name__}")
            
            # Initialize crypto data provider
            if crypto_provider.lower() == "coingecko":
                base_url = kwargs.get("coingecko_base_url", "https://api.coingecko.com/api/v3")
                timeout = kwargs.get("api_timeout", 10)
                self._crypto_data_provider = CoinGeckoProvider(base_url, timeout)
            elif crypto_provider.lower() == "hybrid":
                timeout = kwargs.get("api_timeout", 10)
                self._crypto_data_provider = HybridProvider(timeout)
            # Easy to add other providers here:
            # elif crypto_provider.lower() == "binance":
            #     self._crypto_data_provider = BinanceProvider(**kwargs)
            # elif crypto_provider.lower() == "coinbase":
            #     self._crypto_data_provider = CoinbaseProvider(**kwargs)
            else:
                raise ValueError(f"Unsupported crypto provider: {crypto_provider}")
            
            logger.info(f"Crypto data provider initialized: {self._crypto_data_provider.get_provider_name()}")
            
            # Initialize the crypto service (singleton)
            self._crypto_service = CryptoService(
                database_repo=self._database_repository,
                data_provider=self._crypto_data_provider
            )
            logger.info("CryptoService singleton initialized")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            return False
    
    # Composite interfaces (backward compatibility)
    def get_database_repository(self) -> DatabaseRepository:
        """Get database repository instance"""
        if not self._initialized or not self._database_repository:
            raise RuntimeError("Container not initialized or database repository not available")
        return self._database_repository
    
    def get_crypto_data_provider(self) -> CryptoDataProvider:
        """Get crypto data provider instance"""
        if not self._initialized or not self._crypto_data_provider:
            raise RuntimeError("Container not initialized or crypto data provider not available")
        return self._crypto_data_provider
    
    # Segregated interfaces (ISP compliant)
    def get_data_reader(self) -> DataReader:
        """Get data reader interface"""
        if not self._initialized or not self._database_repository:
            raise RuntimeError("Container not initialized or database repository not available")
        return self._database_repository
    
    def get_data_writer(self) -> DataWriter:
        """Get data writer interface"""
        if not self._initialized or not self._database_repository:
            raise RuntimeError("Container not initialized or database repository not available")
        return self._database_repository
    
    def get_data_administrator(self) -> DataAdministrator:
        """Get data administrator interface"""
        if not self._initialized or not self._database_repository:
            raise RuntimeError("Container not initialized or database repository not available")
        return self._database_repository
    
    def get_data_analytics(self) -> DataAnalytics:
        """Get data analytics interface"""
        if not self._initialized or not self._database_repository:
            raise RuntimeError("Container not initialized or database repository not available")
        return self._database_repository
    
    def get_price_data_fetcher(self) -> PriceDataFetcher:
        """Get price data fetcher interface"""
        if not self._initialized or not self._crypto_data_provider:
            raise RuntimeError("Container not initialized or crypto data provider not available")
        return self._crypto_data_provider
    
    def get_provider_metadata(self) -> ProviderMetadata:
        """Get provider metadata interface"""
        if not self._initialized or not self._crypto_data_provider:
            raise RuntimeError("Container not initialized or crypto data provider not available")
        return self._crypto_data_provider
    
    def get_provider_health(self) -> ProviderHealth:
        """Get provider health interface"""
        if not self._initialized or not self._crypto_data_provider:
            raise RuntimeError("Container not initialized or crypto data provider not available")
        return self._crypto_data_provider
    
    def get_crypto_service(self) -> CryptoService:
        """Get crypto service singleton"""
        if not self._initialized or not self._crypto_service:
            raise RuntimeError("Container not initialized or crypto service not available")
        return self._crypto_service
    
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized
    
    async def health_check(self) -> dict:
        """Check health of all dependencies"""
        health_status = {
            "container_initialized": self._initialized,
            "database_healthy": False,
            "crypto_provider_healthy": False
        }
        
        if self._database_repository:
            health_status["database_healthy"] = await self._database_repository.health_check()
        
        if self._crypto_data_provider:
            health_status["crypto_provider_healthy"] = await self._crypto_data_provider.health_check()
        
        return health_status


# Global container instance
container = DependencyContainer()