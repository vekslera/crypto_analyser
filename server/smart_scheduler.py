"""
Smart scheduler - fetches both sources simultaneously
Uses CoinGecko for price/market cap, CoinMarketCap for volume
All data points have complete information
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
from .services.backup_service import get_backup_service
from core.api_config import VOLUME_COLLECTION_INTERVAL, SCHEDULER_SLEEP_INTERVAL
from .interfaces.database_interface import PriceData
from datetime import datetime

logger = get_logger("server.smart_scheduler")


class SmartScheduler:
    """Single scheduler that combines both data sources intelligently"""
    
    def __init__(self, collection_interval_seconds: int = VOLUME_COLLECTION_INTERVAL):
        # Use 5-minute intervals to respect CMC limits
        self.collection_interval_seconds = collection_interval_seconds
        self.running = False
        self.crypto_service: Optional[CryptoService] = None
        
        # Track last successful volume to fill gaps
        self.last_known_volume = None
        
        # Backup service
        self.backup_service = get_backup_service()
    
    def get_crypto_service(self) -> Optional[CryptoService]:
        """Get crypto service singleton using dependency injection"""
        if not container.is_initialized():
            logger.error("Dependency container not initialized")
            return None
        
        return container.get_crypto_service()
    
    async def collect_combined_data_job(self):
        """Collect data from both sources and combine intelligently"""
        try:
            crypto_service = self.get_crypto_service()
            if not crypto_service:
                logger.error("Could not initialize crypto service")
                return
            
            # Import providers
            from .implementations.coingecko_provider import CoinGeckoProvider
            from .implementations.multi_source_provider import MultiSourceProvider
            
            # Fetch from both sources concurrently
            cg_provider = CoinGeckoProvider()
            cmc_provider = MultiSourceProvider()
            
            logger.debug("Fetching data from both CoinGecko and CoinMarketCap...")
            
            # Run both requests in parallel
            cg_task = asyncio.create_task(cg_provider.fetch_current_price("bitcoin"))
            cmc_task = asyncio.create_task(cmc_provider._fetch_coinmarketcap("bitcoin"))
            
            cg_data, cmc_data = await asyncio.gather(cg_task, cmc_task, return_exceptions=True)
            
            # Handle exceptions
            if isinstance(cg_data, Exception):
                logger.warning(f"CoinGecko fetch failed: {cg_data}")
                cg_data = None
            
            if isinstance(cmc_data, Exception):
                logger.warning(f"CoinMarketCap fetch failed: {cmc_data}")
                cmc_data = None
            
            # Combine data intelligently
            combined_data = self._create_combined_data(cg_data, cmc_data)
            
            if combined_data:
                # Store the complete record
                success = await crypto_service.store_price_data(combined_data)
                if success:
                    vol_str = f"${combined_data.volume_24h:,.0f}" if combined_data.volume_24h else "None"
                    mcap_str = f"${combined_data.market_cap:,.0f}" if combined_data.market_cap else "None"
                    
                    logger.info(f"Smart collection successful:")
                    logger.info(f"  Price: ${combined_data.price:,.2f} (CoinGecko)")
                    logger.info(f"  Volume: {vol_str} (CoinMarketCap)")  
                    logger.info(f"  Market Cap: {mcap_str} (CoinGecko)")
                else:
                    logger.error("Failed to store combined data")
            else:
                logger.error("Failed to create combined data from both sources")
                
        except Exception as e:
            logger.error(f"Error in combined collection job: {e}")
            import traceback
            traceback.print_exc()
    
    async def create_daily_backup(self):
        """Create a daily backup of the database"""
        try:
            logger.info("Creating daily database backup...")
            result = self.backup_service.create_backup()
            
            if result['success']:
                logger.info(f"Daily backup created successfully: {result['backup_file']} ({result['record_count']} records)")
                
                # Also clean up old backups (keep 30 days)
                cleanup_result = self.backup_service.cleanup_old_backups(keep_days=30)
                if cleanup_result['success'] and cleanup_result['deleted_count'] > 0:
                    logger.info(f"Cleaned up {cleanup_result['deleted_count']} old backup files")
                    
            else:
                logger.error(f"Daily backup failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in daily backup: {e}")
    
    def _create_combined_data(self, cg_data: Optional[PriceData], cmc_data: Optional[PriceData]) -> Optional[PriceData]:
        """Create a complete data record from both sources"""
        
        # Priority for each field:
        # Price: CoinGecko (more frequent, reliable)
        # Volume: CoinMarketCap (higher quality, less spikes)  
        # Market Cap: CoinGecko (more reliable)
        
        price = None
        volume_24h = None
        market_cap = None
        
        # Get price from CoinGecko (preferred) or CMC (fallback)
        if cg_data and cg_data.price:
            price = cg_data.price
            logger.debug("Using CoinGecko price")
        elif cmc_data and cmc_data.price:
            price = cmc_data.price
            logger.debug("Using CoinMarketCap price (fallback)")
        
        # Get volume from CMC (preferred) or CG (fallback) or last known
        if cmc_data and cmc_data.volume_24h:
            volume_24h = cmc_data.volume_24h
            self.last_known_volume = volume_24h  # Store for future use
            logger.debug("Using CoinMarketCap volume")
        elif cg_data and cg_data.volume_24h:
            volume_24h = cg_data.volume_24h
            logger.debug("Using CoinGecko volume (CMC unavailable)")
        elif self.last_known_volume:
            volume_24h = self.last_known_volume
            logger.debug("Using last known volume (both sources unavailable)")
        
        # Get market cap from CoinGecko (preferred) or CMC (fallback)
        if cg_data and cg_data.market_cap:
            market_cap = cg_data.market_cap
            logger.debug("Using CoinGecko market cap")
        elif cmc_data and cmc_data.market_cap:
            market_cap = cmc_data.market_cap
            logger.debug("Using CoinMarketCap market cap (fallback)")
        
        # Must have at least price to create a record
        if not price:
            logger.error("No price data available from either source")
            return None
        
        # Log what we're using
        sources_used = []
        if cg_data and price == cg_data.price:
            sources_used.append("CG:price")
        if cmc_data and price == cmc_data.price:
            sources_used.append("CMC:price")
        if cmc_data and volume_24h == cmc_data.volume_24h:
            sources_used.append("CMC:volume")
        elif cg_data and volume_24h == cg_data.volume_24h:
            sources_used.append("CG:volume")
        elif volume_24h == self.last_known_volume:
            sources_used.append("cached:volume")
        if cg_data and market_cap == cg_data.market_cap:
            sources_used.append("CG:mcap")
        elif cmc_data and market_cap == cmc_data.market_cap:
            sources_used.append("CMC:mcap")
        
        logger.debug(f"Combined data sources: {', '.join(sources_used)}")
        
        return PriceData(
            price=price,
            market_cap=market_cap,
            volume_24h=volume_24h,
            timestamp=datetime.utcnow()
        )
    
    def run_collection_job(self):
        """Wrapper for combined collection"""
        asyncio.run(self.collect_combined_data_job())
    
    def run_backup_job(self):
        """Wrapper for daily backup"""
        asyncio.run(self.create_daily_backup())
    
    def start_scheduler(self):
        """Start the smart collection scheduler"""
        if not container.is_initialized():
            logger.error("Cannot start scheduler: dependency container not initialized")
            return
        
        schedule.every(self.collection_interval_seconds).seconds.do(self.run_collection_job)
        
        # Schedule daily backup at midnight
        schedule.every().day.at("00:00").do(self.run_backup_job)
        
        self.running = True
        
        # Calculate API usage
        calls_per_day = (24 * 60 * 60) / self.collection_interval_seconds
        calls_per_month = calls_per_day * 30
        
        logger.info(f"Smart scheduler started:")
        logger.info(f"  - Combined collection every {self.collection_interval_seconds}s")
        logger.info(f"  - Daily backup scheduled at midnight")
        logger.info(f"  - CMC monthly usage: ~{calls_per_month:.0f}/10,000 calls ({calls_per_month/10000*100:.1f}%)")
        logger.info(f"  - All records have complete price, volume, and market cap data")
        logger.info(f"  - Volume velocity calculation will work properly")
        
        while self.running:
            schedule.run_pending()
            time.sleep(SCHEDULER_SLEEP_INTERVAL)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Smart scheduler stopped")


if __name__ == "__main__":
    scheduler = SmartScheduler(collection_interval_seconds=VOLUME_COLLECTION_INTERVAL)
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Smart scheduler interrupted by user")
        scheduler.stop_scheduler()