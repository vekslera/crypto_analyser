"""
SQLite implementation of database repository
Concrete implementation of DatabaseRepository using SQLite
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..interfaces.database_interface import DatabaseRepository, PriceData

logger = logging.getLogger(__name__)

Base = declarative_base()


class BitcoinPriceModel(Base):
    """SQLite model for Bitcoin price data"""
    __tablename__ = "bitcoin_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    volume_24h = Column(Float, nullable=True)
    volume_velocity = Column(Float, nullable=True)  # USD per minute
    market_cap = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    money_flow = Column(Float, nullable=True)

    def to_price_data(self) -> PriceData:
        """Convert SQLAlchemy model to PriceData"""
        return PriceData(
            price=self.price,
            timestamp=self.timestamp,
            volume_24h=self.volume_24h,
            volume_velocity=self.volume_velocity,
            market_cap=self.market_cap,
            volatility=self.volatility,
            money_flow=self.money_flow
        )


class SQLiteRepository(DatabaseRepository):
    """SQLite implementation of DatabaseRepository"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
    
    async def initialize(self) -> bool:
        """Initialize SQLite database"""
        try:
            self.engine = create_engine(
                self.database_url, 
                connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("SQLite database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            return False
    
    def _get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    async def _calculate_volume_velocity(self, new_volume: float, new_timestamp: datetime) -> Optional[float]:
        """Volume velocity calculation disabled - no longer needed"""
        # Volume velocity calculation removed as it's no longer used in the application
        return None

    async def save_price(self, price_data: PriceData) -> bool:
        """Save price data to SQLite"""
        try:
            # Calculate volume velocity if not provided
            if price_data.volume_velocity is None and price_data.volume_24h is not None:
                price_data.volume_velocity = await self._calculate_volume_velocity(
                    price_data.volume_24h, 
                    price_data.timestamp
                )
            
            with self._get_session() as session:
                db_price = BitcoinPriceModel(
                    price=price_data.price,
                    timestamp=price_data.timestamp,
                    volume_24h=price_data.volume_24h,
                    volume_velocity=price_data.volume_velocity,
                    market_cap=price_data.market_cap,
                    volatility=price_data.volatility,
                    money_flow=price_data.money_flow
                )
                session.add(db_price)
                session.commit()
                logger.debug(f"Saved price data: ${price_data.price:,.2f}")
                return True
        except Exception as e:
            logger.error(f"Failed to save price data: {e}")
            return False
    
    async def get_recent_prices(self, limit: int = 100) -> List[PriceData]:
        """Get recent price data from SQLite"""
        try:
            with self._get_session() as session:
                prices = session.query(BitcoinPriceModel)\
                    .order_by(BitcoinPriceModel.timestamp.desc())\
                    .limit(limit)\
                    .all()
                
                # Convert to PriceData and reverse for chronological order
                result = [price.to_price_data() for price in reversed(prices)]
                logger.debug(f"Retrieved {len(result)} recent prices")
                return result
        except Exception as e:
            logger.error(f"Failed to get recent prices: {e}")
            return []
    
    async def get_price_history(self, limit: int = 1000) -> List[PriceData]:
        """Get historical price data from SQLite"""
        try:
            with self._get_session() as session:
                prices = session.query(BitcoinPriceModel)\
                    .order_by(BitcoinPriceModel.timestamp.desc())\
                    .limit(limit)\
                    .all()
                
                result = [price.to_price_data() for price in reversed(prices)]
                logger.debug(f"Retrieved {len(result)} historical prices")
                return result
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []
    
    async def get_price_history_by_time_range(self, start_time: datetime, end_time: datetime) -> List[PriceData]:
        """Get historical price data within a specific time range from SQLite"""
        try:
            with self._get_session() as session:
                prices = session.query(BitcoinPriceModel)\
                    .filter(BitcoinPriceModel.timestamp >= start_time)\
                    .filter(BitcoinPriceModel.timestamp <= end_time)\
                    .order_by(BitcoinPriceModel.timestamp.asc())\
                    .all()
                
                result = [price.to_price_data() for price in prices]
                logger.debug(f"Retrieved {len(result)} historical prices from {start_time} to {end_time}")
                return result
        except Exception as e:
            logger.error(f"Failed to get price history by time range: {e}")
            return []
    
    async def clear_all_data(self) -> bool:
        """Clear all data from SQLite"""
        try:
            with self._get_session() as session:
                session.query(BitcoinPriceModel).delete()
                session.commit()
                logger.info("Cleared all price data from database")
                return True
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistical data from SQLite"""
        try:
            with self._get_session() as session:
                stats = session.query(
                    func.count(BitcoinPriceModel.id).label('count'),
                    func.avg(BitcoinPriceModel.price).label('mean'),
                    func.min(BitcoinPriceModel.price).label('min'),
                    func.max(BitcoinPriceModel.price).label('max')
                ).first()
                
                if stats and stats.count > 0:
                    # Get latest price
                    latest = session.query(BitcoinPriceModel)\
                        .order_by(BitcoinPriceModel.timestamp.desc())\
                        .first()
                    
                    result = {
                        'count': stats.count,
                        'mean': float(stats.mean) if stats.mean else 0,
                        'min': float(stats.min) if stats.min else 0,
                        'max': float(stats.max) if stats.max else 0,
                        'latest': float(latest.price) if latest else 0
                    }
                    logger.debug(f"Retrieved statistics: {result}")
                    return result
                else:
                    return {'count': 0}
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'count': 0}
    
    async def health_check(self) -> bool:
        """Check SQLite database health"""
        try:
            with self._get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False