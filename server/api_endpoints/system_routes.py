"""
System management API endpoints
Handles application lifecycle and system operations
"""

from fastapi import APIRouter
from datetime import datetime
import asyncio
import os
import signal

from core.config import MESSAGES

router = APIRouter()

@router.get("/")
async def root():
    """API root endpoint with status information"""
    return {"message": MESSAGES['api_root'], "status": MESSAGES['status_running']}

@router.post("/system/shutdown")
async def shutdown_server():
    """Gracefully shutdown the server"""
    def shutdown():
        # Send SIGTERM to current process
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Schedule shutdown after sending response
    asyncio.get_event_loop().call_later(1, shutdown)
    
    return {
        "message": MESSAGES['server_shutdown'], 
        "status": MESSAGES['status_shutting_down'],
        "timestamp": datetime.utcnow().isoformat()
    }