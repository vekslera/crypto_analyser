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
    
    async def get_price_history_by_time_range(self, start_time: datetime, end_time: datetime) -> List[PriceData]:
        """Get historical price data within a specific time range"""
        try:
            prices = await self.database_repo.get_price_history_by_time_range(start_time, end_time)
            logger.debug(f"Retrieved {len(prices)} historical prices from {start_time} to {end_time}")
            return prices
        except Exception as e:
            logger.error(f"Error getting price history by time range: {e}")
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
    
    async def store_price_data(self, price_data: PriceData) -> bool:
        """Store price data directly"""
        try:
            success = await self.database_repo.save_price(price_data)
            if success:
                # Add to shared data series for real-time access
                shared_data.add_price(price_data.price, price_data.timestamp)
                logger.debug(f"Stored price data: ${price_data.price:,.2f}")
            return success
        except Exception as e:
            logger.error(f"Error storing price data: {e}")
            return False
    
    async def update_latest_volume(self, volume_24h: float) -> bool:
        """Update the most recent record with new volume data"""
        try:
            # Get the most recent record
            recent_prices = await self.database_repo.get_recent_prices(1)
            if not recent_prices:
                logger.warning("No recent records found to update volume")
                return False
            
            latest_record = recent_prices[0]
            
            # Update with new volume data
            updated_data = PriceData(
                price=latest_record.price,
                market_cap=latest_record.market_cap,
                volume_24h=volume_24h,
                timestamp=latest_record.timestamp
            )
            
            # Use database's update method if available, otherwise delete and re-insert
            success = await self._update_record_volume(latest_record.timestamp, volume_24h)
            
            if success:
                logger.debug(f"Updated latest record volume: ${volume_24h:,.0f}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating latest volume: {e}")
            return False
    
    async def _update_record_volume(self, timestamp: datetime, volume_24h: float) -> bool:
        """Update volume for a specific timestamp record"""
        try:
            # This would ideally be a database method, but for now we'll work around it
            # by checking if the database repository has an update method
            if hasattr(self.database_repo, 'update_volume_by_timestamp'):
                return await self.database_repo.update_volume_by_timestamp(timestamp, volume_24h)
            else:
                # Fallback: update using raw SQL if it's SQLite
                if hasattr(self.database_repo, 'connection'):
                    # SQLite specific update
                    cursor = self.database_repo.connection.cursor()
                    cursor.execute(
                        "UPDATE bitcoin_prices SET volume_24h = ? WHERE timestamp = ?",
                        (volume_24h, timestamp.isoformat())
                    )
                    self.database_repo.connection.commit()
                    return cursor.rowcount > 0
                else:
                    logger.error("Cannot update volume - no update method available")
                    return False
        except Exception as e:
            logger.error(f"Error in _update_record_volume: {e}")
            return False
    
    async def store_price_data_with_velocity(self, price_data: PriceData) -> bool:
        """Store price data and calculate volume velocity"""
        try:
            logger.info("  - Volume velocity calculation starting...")
            
            # Get recent records to calculate velocity, volatility, and money flow
            recent_prices = await self.database_repo.get_recent_prices(10)
            
            # Get 24 hours of data for volatility calculation using timestamp range
            from datetime import timedelta, timezone
            
            # Ensure timezone consistency - normalize all timestamps to UTC
            current_timestamp = price_data.timestamp
            if current_timestamp.tzinfo is None:
                current_timestamp = current_timestamp.replace(tzinfo=timezone.utc)
            elif current_timestamp.tzinfo != timezone.utc:
                current_timestamp = current_timestamp.astimezone(timezone.utc)
            
            twenty_four_hours_ago = current_timestamp - timedelta(hours=24)
            daily_prices = await self.database_repo.get_price_history_by_time_range(
                twenty_four_hours_ago, current_timestamp
            )
            
            # Normalize timestamps in daily_prices to UTC for consistent sorting
            for price_record in daily_prices:
                if price_record.timestamp.tzinfo is None:
                    price_record.timestamp = price_record.timestamp.replace(tzinfo=timezone.utc)
                elif price_record.timestamp.tzinfo != timezone.utc:
                    price_record.timestamp = price_record.timestamp.astimezone(timezone.utc)
            
            volume_velocity = None
            
            if recent_prices:
                prev_record = recent_prices[0]
                logger.info(f"  - Previous record found: {prev_record.timestamp}")
                logger.info(f"    Previous volume: ${prev_record.volume_24h:,.0f}" if prev_record.volume_24h else "    Previous volume: None")
                
                if prev_record.volume_24h and price_data.volume_24h:
                    # Calculate time difference in minutes
                    time_diff = (price_data.timestamp - prev_record.timestamp).total_seconds() / 60
                    
                    if time_diff > 0:
                        # Volume velocity = (volume_change) / (time_diff_in_minutes)  
                        volume_change = price_data.volume_24h - prev_record.volume_24h
                        volume_velocity = volume_change / time_diff
                        
                        logger.info(f"  - Volume velocity calculation:")
                        logger.info(f"    Current volume: ${price_data.volume_24h:,.0f}")
                        logger.info(f"    Previous volume: ${prev_record.volume_24h:,.0f}")
                        logger.info(f"    Volume change: ${volume_change:,.0f}")
                        logger.info(f"    Time difference: {time_diff:.1f} minutes")
                        logger.info(f"    Volume velocity: ${volume_velocity:,.0f}/min")
                        
                        # Check for unusual velocity
                        if abs(volume_velocity) > 1000000000:  # > 1B/min
                            logger.warning(f"    WARNING: HIGH velocity detected: ${volume_velocity:,.0f}/min")
                        elif abs(volume_velocity) < 100000:  # < 100K/min
                            logger.info(f"    SUCCESS Normal velocity: ${volume_velocity:,.0f}/min")
                        else:
                            logger.info(f"    SUCCESS Moderate velocity: ${volume_velocity:,.0f}/min")
                    else:
                        logger.warning(f"  - Invalid time difference: {time_diff} minutes")
                else:
                    if not prev_record.volume_24h:
                        logger.info("  - Previous record has no volume data")
                    if not price_data.volume_24h:
                        logger.warning("  - Current record has no volume data!")
                    logger.info("  - Cannot calculate velocity - missing volume data")
            else:
                logger.info("  - No previous records found - this is the first record")
                logger.info("  - Volume velocity will be None for first record")
            
            # Calculate volatility and money flow using 24-hour data
            volatility = None
            money_flow = None
            
            # Calculate 24-hour volatility using timestamp-based data
            if len(daily_prices) >= 2:  # Need at least 2 data points for volatility calculation
                logger.info(f"  - Calculating 24-hour volatility using {len(daily_prices)} data points...")
                
                # Create price series including new data point (ensure chronological order)
                # Use normalized timestamp for price_data
                normalized_price_data = PriceData(
                    price=price_data.price,
                    timestamp=current_timestamp,  # Use the normalized UTC timestamp
                    volume_24h=price_data.volume_24h,
                    volume_velocity=volume_velocity,
                    market_cap=price_data.market_cap,
                    volatility=None,  # Will be calculated
                    money_flow=None   # Will be calculated
                )
                all_prices = sorted(daily_prices + [normalized_price_data], key=lambda x: x.timestamp)
                prices = [data.price for data in all_prices]
                
                # Calculate returns for the entire 24-hour period
                returns = []
                for i in range(1, len(prices)):
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
                
                # Calculate 24-hour volatility using proper statistical formula
                if len(returns) >= 2:  # Need at least 2 returns
                    n = len(returns)
                    mean_return = sum(returns) / n
                    # Proper variance calculation: Σ(x - μ)² / (n-1) 
                    variance = sum([(r - mean_return)**2 for r in returns]) / (n - 1)
                    volatility = (variance ** 0.5) * 100  # Convert to percentage
                    
                    logger.info(f"    24-hour period: {twenty_four_hours_ago} to {price_data.timestamp}")
                    logger.info(f"    Data points: {len(daily_prices)} historical + 1 current = {len(all_prices)} total")
                    logger.info(f"    Returns count: {n}")
                    logger.info(f"    24-hour volatility: {volatility:.4f}%")
                    
                    # Calculate BTC volume from volatility using power law
                    k = 1.0e-2  # Adjusted for more reasonable BTC volume estimates
                    beta = 0.2
                    btc_volume = (volatility / 100 / k) ** (1 / beta)
                    
                    # Calculate money flow with direction using recent price change
                    if recent_prices:
                        price_change = price_data.price - recent_prices[0].price
                        money_flow = btc_volume * price_change
                        logger.info(f"    Estimated BTC volume: {btc_volume:,.2f} BTC")
                        logger.info(f"    Money flow: ${money_flow:+,.0f}")
                    else:
                        logger.info("    No recent price data for money flow calculation")
                else:
                    logger.info("  - Not enough returns for volatility calculation")
            else:
                logger.info(f"  - Insufficient 24-hour data for volatility calculation (only {len(daily_prices)} points)")
                logger.info("  - Need at least 2 data points within 24-hour window")
            
            # Create enhanced data with velocity, volatility, and money flow
            logger.info("  - Creating enhanced data record...")
            
            # Try to create record with all calculated metrics
            try:
                # Attempt to include all metrics in the record
                enhanced_data = type(price_data)(
                    price=price_data.price,
                    market_cap=price_data.market_cap,
                    volume_24h=price_data.volume_24h,
                    timestamp=current_timestamp,  # Use normalized UTC timestamp
                    volume_velocity=volume_velocity,
                    volatility=volatility,
                    money_flow=money_flow
                )
                logger.info("  - Enhanced record created with velocity, volatility, and money flow")
            except Exception as ve:
                # If velocity field not supported, use standard record
                logger.debug(f"  - Velocity field not supported in PriceData: {ve}")
                enhanced_data = price_data
            
            # Store the data
            logger.info("  - Attempting database insertion...")
            success = await self.database_repo.save_price(enhanced_data)
            
            if success:
                logger.info("  - SUCCESS Database insertion successful")
                
                # Add to shared data series for real-time access
                shared_data.add_price(price_data.price, price_data.timestamp)
                logger.debug("  SUCCESS: Price added to shared data series for GUI")
                
                # Summary log
                if volume_velocity is not None:
                    logger.info(f"  SUCCESS: Record stored with velocity: ${volume_velocity:,.0f}/min")
                else:
                    logger.info("  SUCCESS: Record stored without velocity (first record or missing data)")
                    
                return True
            else:
                logger.error("  - ERROR Database insertion failed")
                return False
            
        except Exception as e:
            logger.error(f"  - ERROR CRITICAL ERROR in store_price_data_with_velocity: {e}")
            import traceback
            logger.error(f"  - Full traceback:\n{traceback.format_exc()}")
            
            # Fallback to regular storage
            logger.info("  - Attempting fallback to regular storage...")
            try:
                fallback_success = await self.store_price_data(price_data)
                if fallback_success:
                    logger.info("  - SUCCESS Fallback storage successful")
                else:
                    logger.error("  - ERROR Fallback storage also failed")
                return fallback_success
            except Exception as fe:
                logger.error(f"  - ERROR Fallback storage error: {fe}")
                return False