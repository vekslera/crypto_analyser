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
import logging
from core.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def run_scheduler():
    global scheduler_instance
    scheduler_instance = PriceScheduler(interval_seconds=DEFAULT_COLLECTION_INTERVAL)
    scheduler_instance.start_scheduler()

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
        
        # Create database tables
        create_tables()
        logger.info("Database tables created")
        
        # Start the background scheduler
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Background scheduler started")
        
        # Start FastAPI in a separate thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        logger.info(MESSAGES['fastapi_starting'])
        
        # Wait a moment for FastAPI to start
        time.sleep(FASTAPI_STARTUP_DELAY)
        
        # Open browser tabs
        try:
            webbrowser.open(STREAMLIT_URL)
            webbrowser.open(FASTAPI_DOCS_URL)
        except:
            pass
        
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