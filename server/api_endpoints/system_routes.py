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
    """Gracefully shutdown the entire application"""
    def shutdown():
        try:
            # On Windows, kill the entire process tree including parent
            import subprocess
            current_pid = os.getpid()
            
            # Get parent process ID
            result = subprocess.run(['wmic', 'process', 'where', f'ProcessId={current_pid}', 'get', 'ParentProcessId', '/value'], 
                                  capture_output=True, text=True)
            
            parent_pid = None
            for line in result.stdout.split('\n'):
                if 'ParentProcessId=' in line:
                    parent_pid = int(line.split('=')[1].strip())
                    break
            
            if parent_pid:
                # Kill the parent process (which should kill all children)
                os.kill(parent_pid, signal.SIGTERM)
            else:
                # Fallback: kill current process
                os.kill(current_pid, signal.SIGTERM)
                
        except Exception as e:
            # Fallback: kill current process
            os.kill(os.getpid(), signal.SIGTERM)
    
    # Schedule shutdown after sending response
    asyncio.get_event_loop().call_later(1, shutdown)
    
    return {
        "message": MESSAGES['server_shutdown'], 
        "status": MESSAGES['status_shutting_down'],
        "timestamp": datetime.utcnow().isoformat()
    }