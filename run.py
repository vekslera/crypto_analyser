import uvicorn
import threading
import time
from scheduler import PriceScheduler
from database import create_tables
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scheduler():
    scheduler = PriceScheduler(interval_seconds=60)  # Collect every 60 seconds
    scheduler.start_scheduler()

def main():
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Start the background scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Background scheduler started")
    
    # Give scheduler a moment to start
    time.sleep(2)
    
    # Start the FastAPI server
    logger.info("Starting FastAPI server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()