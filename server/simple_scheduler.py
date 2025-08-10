"""
Simple scheduler with unified 5-minute intervals
Fetches all data (price, volume, market cap) from CoinGecko every 5 minutes
Eliminates the smoothing mechanism and dual data flow complexity
"""

import asyncio
import schedule
import time
import logging
import sys
import os
from typing import Optional
from datetime import datetime

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logging_config import get_logger

from .dependency_container import container
from .services.crypto_service import CryptoService
from core.api_config import DEFAULT_COLLECTION_INTERVAL, SCHEDULER_SLEEP_INTERVAL
from .interfaces.database_interface import PriceData

logger = get_logger("server.simple_scheduler")


class SimpleScheduler:
    """Simple unified scheduler: single 5-minute interval for all data"""
    
    def __init__(self, collection_interval_seconds: int = DEFAULT_COLLECTION_INTERVAL):
        self.collection_interval_seconds = collection_interval_seconds
        self.running = False
        self.crypto_service: Optional[CryptoService] = None
    
    def get_crypto_service(self) -> Optional[CryptoService]:
        """Get crypto service singleton"""
        if not container.is_initialized():
            logger.error("Dependency container not initialized")
            return None
        return container.get_crypto_service()
    
    async def unified_data_job(self):
        """Fetch all data from CoinGecko every 5 minutes"""
        try:
            logger.info("=" * 50)
            logger.info("STARTING UNIFIED DATA COLLECTION (5-MINUTE)")
            logger.info("=" * 50)
            
            # Fetch all data from CoinGecko
            logger.info("Fetching price, volume, and market cap from CoinGecko...")
            
            from .implementations.coingecko_provider import CoinGeckoProvider
            cg_provider = CoinGeckoProvider()
            
            # Get current data
            price_data = await cg_provider.fetch_current_price("bitcoin")
            
            if not price_data or not price_data.price:
                logger.error("ERROR: CoinGecko fetch failed - no price data received")
                return
            
            logger.info("SUCCESS: CoinGecko data fetched:")
            logger.info(f"  Price: ${price_data.price:,.2f}")
            logger.info(f"  Volume 24h: ${price_data.volume_24h:,.0f}" if price_data.volume_24h else "  Volume 24h: None")
            logger.info(f"  Market Cap: ${price_data.market_cap:,.0f}" if price_data.market_cap else "  Market Cap: None")
            logger.info(f"  Timestamp: {price_data.timestamp}")
            
            # Update GUI series (pandas) for real-time display
            crypto_service = self.get_crypto_service()
            if crypto_service:
                crypto_service.add_to_series(price_data.price, price_data.timestamp)
                logger.debug(f"Updated GUI series with current price")
            else:
                logger.warning("Crypto service not available for GUI update")
            
            # Store to database with velocity calculation
            logger.info("Storing to database with velocity calculation...")
            
            if crypto_service:
                success = await crypto_service.store_price_data_with_velocity(price_data)
                
                if success:
                    logger.info("SUCCESS: DATABASE STORAGE SUCCESSFUL")
                    logger.info(f"  Record stored in: data/crypto_analyser.db")
                    logger.info(f"  Volume velocity: Auto-calculated and stored")
                    logger.info("UNIFIED DATA COLLECTION COMPLETED SUCCESSFULLY")
                else:
                    logger.error("ERROR: DATABASE STORAGE FAILED")
            else:
                logger.error("ERROR: Crypto service not available for DB storage")
                
        except Exception as e:
            logger.error("ERROR: CRITICAL ERROR IN UNIFIED DATA JOB")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    def run_unified_data_job(self):
        """Wrapper for unified data job"""
        asyncio.run(self.unified_data_job())
    
    def start_scheduler(self):
        """Start the simple scheduler"""
        if not container.is_initialized():
            logger.error("Cannot start scheduler: dependency container not initialized")
            return
        
        # Schedule unified data collection
        schedule.every(self.collection_interval_seconds).seconds.do(self.run_unified_data_job)
        
        self.running = True
        
        # Calculate API usage
        cg_calls_per_day = (24 * 60 * 60) / self.collection_interval_seconds
        cg_calls_per_month = cg_calls_per_day * 30
        
        logger.info(f"Simple scheduler started:")
        logger.info(f"  - Unified data collection: every {self.collection_interval_seconds}s")
        logger.info(f"  - CoinGecko calls: {cg_calls_per_day:.0f}/day ({cg_calls_per_month:.0f}/month)")
        logger.info(f"  - Database: data/crypto_analyser.db")
        logger.info(f"  - Volume velocity: Calculated from 24h volume differences")
        logger.info(f"  - Data: Price, Volume 24h, Market Cap from CoinGecko")
        logger.info(f"")
        logger.info(f"Simplified architecture:")
        logger.info(f"  - Single 5-minute interval for all data")
        logger.info(f"  - No price smoothing (direct values)")
        logger.info(f"  - GUI and DB updated simultaneously")
        
        while self.running:
            schedule.run_pending()
            time.sleep(SCHEDULER_SLEEP_INTERVAL)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Simple scheduler stopped")


if __name__ == "__main__":
    scheduler = SimpleScheduler(collection_interval_seconds=DEFAULT_COLLECTION_INTERVAL)
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Simple scheduler interrupted by user")
        scheduler.stop_scheduler()