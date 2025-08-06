"""
Optimal scheduler with separate GUI and DB data flows
60s: Price updates for GUI (pandas series only)
300s: Volume + smoothed price for DB storage
"""

import asyncio
import schedule
import time
import logging
import sys
import os
from typing import Optional, List
from collections import deque
from datetime import datetime
import statistics

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logging_config import get_logger

from .dependency_container import container
from .services.crypto_service import CryptoService
from core.api_config import DEFAULT_COLLECTION_INTERVAL, VOLUME_COLLECTION_INTERVAL, SCHEDULER_SLEEP_INTERVAL
from .interfaces.database_interface import PriceData

logger = get_logger("server.optimal_scheduler")


class OptimalScheduler:
    """Optimal scheduler: frequent GUI updates + quality DB data"""
    
    def __init__(self, 
                 price_interval_seconds: int = DEFAULT_COLLECTION_INTERVAL,
                 volume_interval_seconds: int = VOLUME_COLLECTION_INTERVAL):
        self.price_interval_seconds = price_interval_seconds
        self.volume_interval_seconds = volume_interval_seconds
        self.running = False
        self.crypto_service: Optional[CryptoService] = None
        
        # Price buffer for smoothing (last 5 values)
        self.price_buffer = deque(maxlen=5)
        self.last_market_cap = None
    
    def get_crypto_service(self) -> Optional[CryptoService]:
        """Get crypto service singleton"""
        if not container.is_initialized():
            logger.error("Dependency container not initialized")
            return None
        return container.get_crypto_service()
    
    async def quick_price_job(self):
        """Fetch price every 60s for GUI updates (no DB storage)"""
        try:
            logger.debug("Starting quick price fetch for GUI update...")
            
            from .implementations.coingecko_provider import CoinGeckoProvider
            cg_provider = CoinGeckoProvider()
            
            # Fetch price data
            price_data = await cg_provider.fetch_current_price("bitcoin")
            
            if price_data and price_data.price:
                # Add to price buffer for smoothing
                self.price_buffer.append(price_data.price)
                
                # Store market cap for later DB insertion
                if price_data.market_cap:
                    self.last_market_cap = price_data.market_cap
                    logger.debug(f"Updated cached market cap: ${price_data.market_cap:,.0f}")
                
                # Update GUI series (pandas) only - no DB storage
                crypto_service = self.get_crypto_service()
                if crypto_service:
                    crypto_service.add_to_series(price_data.price, price_data.timestamp)
                    logger.debug(f"Added price to GUI series: ${price_data.price:,.2f}")
                else:
                    logger.warning("Crypto service not available for GUI update")
                
                # Log current buffer state
                buffer_values = list(self.price_buffer)
                logger.info(f"GUI Update - Price: ${price_data.price:,.2f} | Buffer: {len(buffer_values)}/5 values")
                if len(buffer_values) > 1:
                    logger.debug(f"Price buffer contents: ${buffer_values[0]:,.2f} to ${buffer_values[-1]:,.2f}")
            else:
                logger.warning("CoinGecko price fetch failed - no data received")
                if price_data:
                    logger.warning(f"Price data object exists but price is: {price_data.price}")
                
        except Exception as e:
            logger.error(f"Error in quick price job: {e}")
            import traceback
            logger.error(f"Quick price job traceback: {traceback.format_exc()}")
    
    async def volume_and_db_job(self):
        """Fetch volume every 300s + store smoothed data to DB"""
        try:
            logger.info("=" * 50)
            logger.info("STARTING VOLUME & DB STORAGE JOB")
            logger.info("=" * 50)
            
            # Step 1: Fetch volume from CoinMarketCap
            logger.info("Step 1: Fetching trading volume from CoinMarketCap...")
            volume_data = None
            
            try:
                from .implementations.multi_source_provider import MultiSourceProvider
                cmc_provider = MultiSourceProvider()
                volume_data = await cmc_provider._fetch_coinmarketcap("bitcoin")
                
            except Exception as e:
                logger.error(f"Exception during CMC fetch: {e}")
                volume_data = None
            
            if volume_data and volume_data.volume_24h:
                logger.info(f"SUCCESS: CMC volume fetch successful: ${volume_data.volume_24h:,.0f}")
                if volume_data.price:
                    logger.debug(f"  CMC also provided price: ${volume_data.price:,.2f}")
                if volume_data.market_cap:
                    logger.debug(f"  CMC also provided market cap: ${volume_data.market_cap:,.0f}")
            else:
                logger.error("ERROR: CMC volume fetch failed")
                if volume_data:
                    logger.error(f"  Volume data object exists but volume_24h is: {volume_data.volume_24h}")
                    logger.error(f"  Available data: price={volume_data.price}, market_cap={volume_data.market_cap}")
                else:
                    logger.error("  No volume data object returned")
                
                # Add detailed debugging
                logger.error("  Attempting direct CMC test...")
                try:
                    test_data = await cmc_provider._fetch_coinmarketcap("bitcoin")
                    if test_data:
                        logger.error(f"  Direct test SUCCESS: volume=${test_data.volume_24h}")
                    else:
                        logger.error("  Direct test also failed")
                except Exception as e:
                    logger.error(f"  Direct test exception: {e}")
                return
            
            # Step 2: Calculate smoothed price
            logger.info("Step 2: Calculating smoothed price from buffer...")
            if len(self.price_buffer) == 0:
                logger.error("ERROR: No price data available for smoothing - price buffer is empty")
                logger.error("  This means no GUI price updates occurred before volume fetch")
                return
            
            buffer_values = list(self.price_buffer)
            smoothed_price = statistics.mean(buffer_values)
            
            logger.info(f"SUCCESS: Price smoothing successful:")
            logger.info(f"  Buffer size: {len(buffer_values)} values")
            logger.info(f"  Price range: ${min(buffer_values):,.2f} - ${max(buffer_values):,.2f}")
            logger.info(f"  Smoothed result: ${smoothed_price:.2f}")
            
            # Step 3: Prepare DB record
            logger.info("Step 3: Preparing database record...")
            market_cap_source = ""
            market_cap_value = None
            
            if self.last_market_cap:
                market_cap_value = self.last_market_cap
                market_cap_source = "CoinGecko cache"
            elif volume_data.market_cap:
                market_cap_value = volume_data.market_cap
                market_cap_source = "CoinMarketCap"
            
            db_record = PriceData(
                price=smoothed_price,
                volume_24h=volume_data.volume_24h,
                market_cap=market_cap_value,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"SUCCESS: DB record prepared:")
            logger.info(f"  Price: ${db_record.price:,.2f} (smoothed from CoinGecko)")
            logger.info(f"  Volume: ${db_record.volume_24h:,.0f} (from CoinMarketCap)")
            logger.info(f"  Market Cap: ${market_cap_value:,.0f} (from {market_cap_source})" if market_cap_value else "  Market Cap: None")
            logger.info(f"  Timestamp: {db_record.timestamp}")
            
            # Step 4: Store to database with velocity calculation
            logger.info("Step 4: Storing to database with velocity calculation...")
            crypto_service = self.get_crypto_service()
            if not crypto_service:
                logger.error("ERROR: Crypto service not available for DB storage")
                return
            
            success = await crypto_service.store_price_data_with_velocity(db_record)
            
            if success:
                logger.info("SUCCESS: DATABASE STORAGE SUCCESSFUL")
                logger.info(f"  Record stored in: data/crypto_analyser.db")
                logger.info(f"  Volume velocity: Auto-calculated and stored")
                logger.info(f"  Price buffer cleared: {len(self.price_buffer)} -> 0 values")
                
                # Clear price buffer after successful DB storage
                old_buffer_size = len(self.price_buffer)
                self.price_buffer.clear()
                logger.debug(f"Price buffer cleared: {old_buffer_size} values removed")
                
                # Summary
                logger.info("VOLUME & DB JOB COMPLETED SUCCESSFULLY")
            else:
                logger.error("ERROR: DATABASE STORAGE FAILED")
                logger.error("  DB record was not stored")
                logger.error("  Price buffer NOT cleared (keeping for retry)")
                
        except Exception as e:
            logger.error("ERROR: CRITICAL ERROR IN VOLUME & DB JOB")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    def run_quick_price_job(self):
        """Wrapper for quick price job"""
        asyncio.run(self.quick_price_job())
    
    def run_volume_and_db_job(self):
        """Wrapper for volume and DB job"""
        asyncio.run(self.volume_and_db_job())
    
    def start_scheduler(self):
        """Start the optimal scheduler"""
        if not container.is_initialized():
            logger.error("Cannot start scheduler: dependency container not initialized")
            return
        
        # Schedule quick price updates for GUI
        schedule.every(self.price_interval_seconds).seconds.do(self.run_quick_price_job)
        
        # Schedule volume + DB storage
        schedule.every(self.volume_interval_seconds).seconds.do(self.run_volume_and_db_job)
        
        self.running = True
        
        # Calculate API usage
        cg_calls_per_day = (24 * 60 * 60) / self.price_interval_seconds
        cmc_calls_per_day = (24 * 60 * 60) / self.volume_interval_seconds
        cmc_calls_per_month = cmc_calls_per_day * 30
        
        logger.info(f"Optimal scheduler started:")
        logger.info(f"  - GUI price updates: every {self.price_interval_seconds}s ({cg_calls_per_day:.0f}/day)")
        logger.info(f"  - DB + volume updates: every {self.volume_interval_seconds}s ({cmc_calls_per_day:.0f}/day)")
        logger.info(f"  - CMC monthly usage: {cmc_calls_per_month:.0f}/10,000 ({cmc_calls_per_month/10000*100:.1f}%)")
        logger.info(f"  - Price smoothing: 5-point average")
        logger.info(f"  - Database: data/crypto_analyser.db")
        logger.info(f"  - Volume velocity: Calculated and stored automatically")
        logger.info(f"")
        logger.info(f"Data flows:")
        logger.info(f"  - GUI: Real-time price updates (60s)")
        logger.info(f"  - DB: Smoothed price + CMC volume + velocity (300s)")
        
        while self.running:
            schedule.run_pending()
            time.sleep(SCHEDULER_SLEEP_INTERVAL)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Optimal scheduler stopped")


if __name__ == "__main__":
    scheduler = OptimalScheduler(
        price_interval_seconds=DEFAULT_COLLECTION_INTERVAL,
        volume_interval_seconds=VOLUME_COLLECTION_INTERVAL
    )
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Optimal scheduler interrupted by user")
        scheduler.stop_scheduler()