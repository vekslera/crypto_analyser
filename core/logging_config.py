"""
Logging configuration for the application
Sets up comprehensive file and console logging
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
SERVER_LOG_FILE = LOGS_DIR / "server.log"
CLIENT_LOG_FILE = LOGS_DIR / "client.log"
API_LOG_FILE = LOGS_DIR / "api.log"
SCHEDULER_LOG_FILE = LOGS_DIR / "scheduler.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_file_logger(name: str, log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger that writes to a specific file"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_api_logging():
    """Set up logging specifically for FastAPI/Uvicorn"""
    # Configure uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    fastapi_logger = logging.getLogger("fastapi")
    
    # File handler for API logs
    api_file_handler = logging.handlers.RotatingFileHandler(
        API_LOG_FILE,
        maxBytes=10*1024*1024,
        backupCount=5
    )
    api_file_handler.setLevel(logging.INFO)
    api_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    api_file_handler.setFormatter(api_formatter)
    
    # Add file handlers to API loggers
    for logger in [uvicorn_logger, uvicorn_access_logger, fastapi_logger]:
        logger.addHandler(api_file_handler)


def setup_application_logging():
    """Set up comprehensive logging for the entire application"""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Create application-specific loggers
    server_logger = setup_file_logger("server", SERVER_LOG_FILE)
    client_logger = setup_file_logger("client", CLIENT_LOG_FILE)
    scheduler_logger = setup_file_logger("scheduler", SCHEDULER_LOG_FILE)
    debug_logger = setup_file_logger("debug", DEBUG_LOG_FILE, logging.DEBUG)
    
    # Set up API logging
    setup_api_logging()
    
    # Log startup message
    server_logger.info("="*60)
    server_logger.info(f"APPLICATION STARTUP - {datetime.now()}")
    server_logger.info("="*60)
    
    return {
        "server": server_logger,
        "client": client_logger,
        "scheduler": scheduler_logger,
        "debug": debug_logger
    }


def get_logger(name: str) -> logging.Logger:
    """Get a logger by name, ensuring it's configured for file output"""
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up with default file logging
    if not logger.handlers:
        log_file = LOGS_DIR / f"{name}.log"
        return setup_file_logger(name, log_file)
    
    return logger


# Initialize logging when this module is imported
loggers = setup_application_logging()