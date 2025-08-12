"""
Database interfaces for dependency inversion (ISP compliant)
Segregated interfaces for focused database operations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PriceData:
    """Data class for cryptocurrency price information"""
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    volume_velocity: Optional[float] = None  # USD per minute
    market_cap: Optional[float] = None
    volatility: Optional[float] = None
    money_flow: Optional[float] = None
    id: Optional[int] = None


class DataReader(ABC):
    """Interface for read-only data operations"""
    
    @abstractmethod
    async def get_recent_prices(self, limit: int = 100) -> List[PriceData]:
        """Get recent price data from storage"""
        pass
    
    @abstractmethod
    async def get_price_history(self, limit: int = 1000) -> List[PriceData]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    async def get_price_history_by_time_range(self, start_time: datetime, end_time: datetime) -> List[PriceData]:
        """Get historical price data within a specific time range"""
        pass


class DataWriter(ABC):
    """Interface for write operations"""
    
    @abstractmethod
    async def save_price(self, price_data: PriceData) -> bool:
        """Save price data to storage"""
        pass


class DataAdministrator(ABC):
    """Interface for administrative operations"""
    
    @abstractmethod
    async def clear_all_data(self) -> bool:
        """Clear all stored data"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize database/storage"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        pass


class DataAnalytics(ABC):
    """Interface for analytics and statistical operations"""
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistical data"""
        pass


class DatabaseRepository(DataReader, DataWriter, DataAdministrator, DataAnalytics):
    """Composite interface for full database access (backward compatibility)"""
    pass


class DatabaseSession(ABC):
    """Abstract interface for database session management"""
    
    @abstractmethod
    def __enter__(self):
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @abstractmethod
    def commit(self):
        pass
    
    @abstractmethod
    def rollback(self):
        pass