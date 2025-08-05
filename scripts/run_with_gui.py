import subprocess
import threading
import time
import webbrowser
import signal
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.scheduler import PriceScheduler
from server.database import create_tables
from server.dependency_container import container
import logging
import asyncio
from core.config import *
from core.logging_config import get_logger

logger = get_logger("scripts.run_with_gui")

# Global variables for process management
scheduler_instance = None
fastapi_process = None
streamlit_process = None

def signal_handler(signum, frame):
    logger.info("Received interrupt signal. Shutting down...")
    cleanup_and_exit()

def cleanup_and_exit():
    global scheduler_instance, fastapi_process, streamlit_process
    
    # Stop scheduler
    if scheduler_instance:
        scheduler_instance.stop_scheduler()
    
    # Terminate processes
    for process in [fastapi_process, streamlit_process]:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=PROCESS_TERMINATION_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
    
    logger.info("Shutdown complete")
    sys.exit(0)

async def initialize_container():
    """Initialize the dependency container"""
    try:
        logger.info("Initializing dependency container...")
        success = await container.initialize(
            database_url=DATABASE_URL,
            crypto_provider="coingecko",
            coingecko_base_url="https://api.coingecko.com/api/v3",
            api_timeout=10
        )
        if success:
            logger.info("Dependency container initialized successfully")
            return True
        else:
            logger.error("Failed to initialize dependency container")
            return False
    except Exception as e:
        logger.error(f"Error initializing dependency container: {e}")
        return False

def run_scheduler():
    """Run the price scheduler (must be called after container initialization)"""
    global scheduler_instance
    try:
        # Wait for container to be initialized
        max_wait = 30  # seconds
        wait_time = 0
        while not container.is_initialized() and wait_time < max_wait:
            time.sleep(1)
            wait_time += 1
        
        if not container.is_initialized():
            logger.error("Container not initialized after 30 seconds, cannot start scheduler")
            return
        
        scheduler_instance = PriceScheduler(interval_seconds=DEFAULT_COLLECTION_INTERVAL)
        logger.info("Starting price scheduler...")
        scheduler_instance.start_scheduler()
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def run_fastapi():
    import uvicorn
    uvicorn.run("server.api_server:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=False)

def run_streamlit():
    global streamlit_process
    time.sleep(STREAMLIT_STARTUP_DELAY)
    streamlit_process = subprocess.Popen(["streamlit", "run", "client/gui_dashboard.py", "--server.port", str(STREAMLIT_PORT)])
    streamlit_process.wait()

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info(MESSAGES['startup_gui'])
        logger.info(MESSAGES['startup_services'])
        
        # Initialize dependency container first
        container_initialized = asyncio.run(initialize_container())
        if not container_initialized:
            logger.error("Failed to initialize dependency container, exiting")
            return
        
        # Create database tables
        create_tables()
        logger.info("Database tables created")
        
        # Start FastAPI in a separate thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        logger.info(MESSAGES['fastapi_starting'])
        
        # Wait a moment for FastAPI to start
        time.sleep(FASTAPI_STARTUP_DELAY)
        
        # Start the background scheduler (after container is initialized)
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Background scheduler started")
        
        # Open only the GUI tab (Streamlit will handle browser opening)
        # No manual browser opening needed - Streamlit opens its own tab
        
        logger.info(MESSAGES['streamlit_starting'])
        
        # Start Streamlit (this will block)
        run_streamlit()
        
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        cleanup_and_exit()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        cleanup_and_exit()

if __name__ == "__main__":
    main()