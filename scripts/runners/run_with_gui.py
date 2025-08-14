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

from server.simple_scheduler import SimpleScheduler  # Changed to SimpleScheduler
from server.database import create_tables
from server.dependency_container import container
import logging
import asyncio
from core.config import *
from core.api_config import DEFAULT_COLLECTION_INTERVAL
from core.logging_config import get_logger

# Console logging is already handled by core.logging_config
# Just ensure INFO level for root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Logging is handled by core.logging_config.get_logger() - no need for explicit setup

logger = get_logger("scripts.run_with_gui")
logger.info("Console logging enabled - you will see detailed logs in terminal")

# Check environment variables
import os
cmc_key = os.getenv('CMC_API_KEY')
if not cmc_key:
    logger.warning("CMC_API_KEY not found - volume fetching may fail")

# Global variables for process management
scheduler_instance = None
fastapi_process = None
streamlit_process = None

def signal_handler(signum, frame):
    logger.info("Received interrupt signal. Shutting down...")
    cleanup_and_exit()

def cleanup_and_exit():
    global scheduler_instance, fastapi_process, streamlit_process
    
    logger.info("Starting graceful shutdown...")
    
    # Stop scheduler first
    if scheduler_instance:
        try:
            logger.info("Stopping price scheduler...")
            scheduler_instance.stop_scheduler()
            logger.info("Price scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    # Terminate processes
    processes = [
        ("Streamlit", streamlit_process),
        ("FastAPI", fastapi_process)
    ]
    
    for name, process in processes:
        if process and process.poll() is None:
            try:
                logger.info(f"Terminating {name} process...")
                process.terminate()
                process.wait(timeout=PROCESS_TERMINATION_TIMEOUT)
                logger.info(f"{name} process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} process didn't terminate gracefully, forcing kill...")
                process.kill()
                logger.info(f"{name} process killed")
            except Exception as e:
                logger.error(f"Error terminating {name} process: {e}")
    
    logger.info("Shutdown complete - all processes stopped")
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
        
        # Use SimpleScheduler with unified 5-minute interval
        scheduler_instance = SimpleScheduler(
            collection_interval_seconds=DEFAULT_COLLECTION_INTERVAL  # 300s for unified data collection
        )
        logger.info("Starting SimpleScheduler with:")
        logger.info(f"  • Unified data collection: every {DEFAULT_COLLECTION_INTERVAL}s")
        logger.info(f"  • Data: Price, Volume, Market Cap from CoinGecko")
        logger.info("  • Detailed logs will appear in this terminal")
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
    
    # Don't block on wait() - instead poll periodically to allow signal handling
    try:
        while streamlit_process.poll() is None:
            time.sleep(1)  # Check every second if process is still running
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt in streamlit process")
        cleanup_and_exit()

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
        
# CMC API key check was done at startup
        
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