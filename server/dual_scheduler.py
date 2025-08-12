"""
Dual price collection scheduler
Separate intervals for price data (60s) and volume data (300s)
"""

import asyncio
import schedule
import time
import logging
import sys
import os
from typing import Optional

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logging_config import get_logger

from .dependency_container import container
from .services.crypto_service import CryptoService
from core.api_config import DEFAULT_COLLECTION_INTERVAL, VOLUME_COLLECTION_INTERVAL, SCHEDULER_SLEEP_INTERVAL

logger = get_logger("server.dual_scheduler")


class DualPriceScheduler:
    """Scheduler with separate intervals for price and volume data"""
    
    def __init__(self, 
                 price_interval_seconds: int = DEFAULT_COLLECTION_INTERVAL,
                 volume_interval_seconds: int = VOLUME_COLLECTION_INTERVAL):
        self.price_interval_seconds = price_interval_seconds
        self.volume_interval_seconds = volume_interval_seconds
        self.running = False
        self.crypto_service: Optional[CryptoService] = None
    
    def get_crypto_service(self) -> Optional[CryptoService]:
        """Get crypto service singleton using dependency injection"""
        if not container.is_initialized():
            logger.error("Dependency container not initialized")
            return None
        
        return container.get_crypto_service()
    
    async def collect_price_job(self):
        """Collect price and market cap data (frequent - 60s)"""
        try:
            crypto_service = self.get_crypto_service()
            if not crypto_service:
                logger.error("Could not initialize crypto service for price collection")
                return
            
            # Get CoinGecko data for price and market cap
            from .implementations.coingecko_provider import CoinGeckoProvider
            cg_provider = CoinGeckoProvider()
            
            price_data = await cg_provider.fetch_current_price("bitcoin")
            if price_data:
                # Store only price and market cap (without volume to avoid conflicts)
                limited_data = type(price_data)(
                    price=price_data.price,
                    market_cap=price_data.market_cap,
                    volume_24h=None,  # Don't store volume from CoinGecko
                    timestamp=price_data.timestamp
                )
                
                stored = await crypto_service.store_price_data(limited_data)
                if stored:
                    logger.debug(f"Price scheduler: Stored price ${price_data.price:,.2f}, market cap ${price_data.market_cap:,.0f}")
                else:
                    logger.warning("Price scheduler: Failed to store price data")
            else:
                logger.warning("Price scheduler: Failed to fetch CoinGecko price data")
                
        except Exception as e:
            logger.error(f"Error in price collection job: {e}")
    
    async def collect_volume_job(self):
        """Collect volume data and update existing records (less frequent - 300s)"""
        try:
            crypto_service = self.get_crypto_service()
            if not crypto_service:
                logger.error("Could not initialize crypto service for volume collection")
                return
            
            # Get CoinMarketCap volume data
            from .implementations.multi_source_provider import MultiSourceProvider
            cmc_provider = MultiSourceProvider()
            
            volume_data = await cmc_provider._fetch_coinmarketcap("bitcoin")
            if volume_data and volume_data.volume_24h:
                # Update the most recent record with CMC volume data
                success = await crypto_service.update_latest_volume(volume_data.volume_24h)
                if success:
                    logger.info(f"Volume scheduler: Updated latest record with CMC volume ${volume_data.volume_24h:,.0f}")
                else:
                    logger.warning("Volume scheduler: Failed to update volume data")
            else:
                logger.warning("Volume scheduler: Failed to fetch CMC volume data")
                
        except Exception as e:
            logger.error(f"Error in volume collection job: {e}")
    
    def run_price_collection_job(self):
        """Wrapper for price collection"""
        asyncio.run(self.collect_price_job())
    
    def run_volume_collection_job(self):
        """Wrapper for volume collection"""  
        asyncio.run(self.collect_volume_job())
    
    def start_scheduler(self):
        """Start both price and volume collection schedulers"""
        if not container.is_initialized():
            logger.error("Cannot start scheduler: dependency container not initialized")
            return
        
        # Schedule price collection (frequent)
        schedule.every(self.price_interval_seconds).seconds.do(self.run_price_collection_job)
        
        # Schedule volume collection (less frequent)  
        schedule.every(self.volume_interval_seconds).seconds.do(self.run_volume_collection_job)
        
        self.running = True
        logger.info(f"Dual scheduler started:")
        logger.info(f"  - Price collection every {self.price_interval_seconds}s (CoinGecko)")
        logger.info(f"  - Volume collection every {self.volume_interval_seconds}s (CoinMarketCap)")
        logger.info(f"  - CMC monthly usage: ~{(30*24*60*60)/self.volume_interval_seconds:.0f} calls/month")
        
        while self.running:
            schedule.run_pending()
            time.sleep(SCHEDULER_SLEEP_INTERVAL)
    
    def stop_scheduler(self):
        """Stop both schedulers"""
        self.running = False
        schedule.clear()
        logger.info("Dual scheduler stopped")


if __name__ == "__main__":
    scheduler = DualPriceScheduler(
        price_interval_seconds=DEFAULT_COLLECTION_INTERVAL,
        volume_interval_seconds=VOLUME_COLLECTION_INTERVAL
    )
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Dual scheduler interrupted by user")
        scheduler.stop_scheduler()