"""
Cryptocurrency data source interfaces for dependency inversion (ISP compliant)
Segregated interfaces for focused crypto data operations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from .database_interface import PriceData


class PriceDataFetcher(ABC):
    """Interface for fetching cryptocurrency price data"""
    
    @abstractmethod
    async def fetch_current_price(self, symbol: str = "bitcoin") -> Optional[PriceData]:
        """Fetch current price for a cryptocurrency"""
        pass
    
    @abstractmethod
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> List[PriceData]:
        """Fetch historical price data"""
        pass


class ProviderMetadata(ABC):
    """Interface for provider metadata and capabilities"""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the data provider"""
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting information"""
        pass
    
    @abstractmethod
    async def get_supported_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols"""
        pass


class ProviderHealth(ABC):
    """Interface for provider health monitoring"""
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data provider is accessible"""
        pass


class CryptoDataProvider(PriceDataFetcher, ProviderMetadata, ProviderHealth):
    """Composite interface for full crypto data provider access (backward compatibility)"""
    pass


class RateLimiter(ABC):
    """Abstract interface for rate limiting"""
    
    @abstractmethod
    def can_make_request(self) -> bool:
        """Check if a request can be made"""
        pass
    
    @abstractmethod
    def wait_if_needed(self) -> None:
        """Wait if rate limit requires it"""
        pass
    
    @abstractmethod
    def record_request(self) -> None:
        """Record that a request was made"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        pass


class CacheInterface(ABC):
    """Abstract interface for caching"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cached value with optional TTL"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cached values"""
        pass