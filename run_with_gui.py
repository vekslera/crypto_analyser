import subprocess
import threading
import time
import webbrowser
import signal
import sys
#import os
from scheduler import PriceScheduler
from database import create_tables
import logging

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
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    logger.info("Shutdown complete")
    sys.exit(0)

def run_scheduler():
    global scheduler_instance
    scheduler_instance = PriceScheduler(interval_seconds=60)  # Increased for rate limiting
    scheduler_instance.start_scheduler()

def run_fastapi():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

def run_streamlit():
    global streamlit_process
    time.sleep(5)  # Wait for FastAPI to start
    streamlit_process = subprocess.Popen(["streamlit", "run", "gui_dashboard.py", "--server.port", "8501"])
    streamlit_process.wait()

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting Bitcoin Price Tracker with GUI...")
        logger.info("Press Ctrl+C to stop all services")
        
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
        logger.info("FastAPI server starting on http://localhost:8000")
        
        # Wait a moment for FastAPI to start
        time.sleep(3)
        
        # Open browser tabs
        try:
            webbrowser.open("http://localhost:8501")  # Streamlit GUI
            webbrowser.open("http://localhost:8000/docs")  # FastAPI docs
        except:
            pass
        
        logger.info("Starting Streamlit GUI on http://localhost:8501")
        
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