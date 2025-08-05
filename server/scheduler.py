"""
Price collection scheduler (DIP compliant)
Schedules periodic price collection using dependency injection
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
from core.config import DEFAULT_COLLECTION_INTERVAL, SCHEDULER_SLEEP_INTERVAL

logger = get_logger("server.scheduler")

class PriceScheduler:
    """DIP-compliant price scheduler using dependency injection"""
    
    def __init__(self, interval_seconds: int = DEFAULT_COLLECTION_INTERVAL):
        self.interval_seconds = interval_seconds
        self.running = False
        self.crypto_service: Optional[CryptoService] = None
    
    def get_crypto_service(self) -> Optional[CryptoService]:
        """Get crypto service singleton using dependency injection"""
        if not container.is_initialized():
            logger.error("Dependency container not initialized")
            return None
        
        return container.get_crypto_service()
    
    async def collect_price_job(self):
        """Collect and store cryptocurrency price using dependency injection"""
        try:
            crypto_service = self.get_crypto_service()
            if not crypto_service:
                logger.error("Could not initialize crypto service")
                return
            
            price_data = await crypto_service.fetch_and_store_current_price("bitcoin")
            if price_data:
                logger.info(f"Successfully collected and stored Bitcoin price: ${price_data.price:,.2f}")
            else:
                logger.warning("Failed to fetch and store Bitcoin price data")
                
        except Exception as e:
            logger.error(f"Error in price collection job: {e}")
    
    def run_collection_job(self):
        asyncio.run(self.collect_price_job())
    
    def start_scheduler(self):
        """Start the price collection scheduler"""
        if not container.is_initialized():
            logger.error("Cannot start scheduler: dependency container not initialized")
            return
        
        schedule.every(self.interval_seconds).seconds.do(self.run_collection_job)
        self.running = True
        logger.info(f"Price scheduler started - collecting every {self.interval_seconds} seconds")
        
        while self.running:
            schedule.run_pending()
            time.sleep(SCHEDULER_SLEEP_INTERVAL)
    
    def stop_scheduler(self):
        self.running = False
        schedule.clear()
        logger.info("Price scheduler stopped")

if __name__ == "__main__":
    scheduler = PriceScheduler(interval_seconds=DEFAULT_COLLECTION_INTERVAL)
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
        scheduler.stop_scheduler()