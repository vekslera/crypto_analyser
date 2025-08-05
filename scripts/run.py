import uvicorn
import threading
import time
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.scheduler import PriceScheduler
from server.database import create_tables
import logging
from core.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scheduler():
    scheduler = PriceScheduler(interval_seconds=DEFAULT_COLLECTION_INTERVAL)
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
    time.sleep(INITIAL_SETUP_DELAY)
    
    # Start the FastAPI server
    logger.info(MESSAGES['fastapi_starting'])
    uvicorn.run("server.api_server:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=False)

if __name__ == "__main__":
    main()