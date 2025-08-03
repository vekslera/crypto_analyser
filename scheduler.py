import asyncio
import schedule
import time
from bitcoin_service import BitcoinService
from database import SessionLocal, BitcoinPrice
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceScheduler:
    def __init__(self, interval_seconds: int = 60):  # Increased to 60 seconds for rate limiting
        self.bitcoin_service = BitcoinService()
        self.interval_seconds = interval_seconds
        self.running = False
    
    async def collect_price_job(self):
        try:
            price_data = await self.bitcoin_service.fetch_bitcoin_price()
            if price_data:
                db = SessionLocal()
                try:
                    db_price = BitcoinPrice(
                        price=price_data['price'],
                        timestamp=price_data['timestamp'],
                        volume_24h=price_data.get('volume_24h'),
                        market_cap=price_data.get('market_cap')
                    )
                    db.add(db_price)
                    db.commit()
                    
                    self.bitcoin_service.add_to_series(
                        price_data['price'], 
                        price_data['timestamp']
                    )
                    logger.info(f"Successfully collected and stored Bitcoin price: ${price_data['price']:,.2f}")
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Database error: {e}")
                finally:
                    db.close()
            else:
                logger.warning("Failed to fetch Bitcoin price data")
                
        except Exception as e:
            logger.error(f"Error in price collection job: {e}")
    
    def run_collection_job(self):
        asyncio.run(self.collect_price_job())
    
    def start_scheduler(self):
        schedule.every(self.interval_seconds).seconds.do(self.run_collection_job)
        self.running = True
        logger.info(f"Price scheduler started - collecting every {self.interval_seconds} seconds")
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop_scheduler(self):
        self.running = False
        schedule.clear()
        logger.info("Price scheduler stopped")

if __name__ == "__main__":
    scheduler = PriceScheduler(interval_seconds=60)  # Collect every 60 seconds
    try:
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
        scheduler.stop_scheduler()