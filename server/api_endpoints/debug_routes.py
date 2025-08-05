"""
Debug and monitoring API endpoints
Handles debugging, monitoring, and diagnostic endpoints
"""

from fastapi import APIRouter
from datetime import datetime

from ..rate_limiter import global_rate_limiter

router = APIRouter()

@router.get("/debug/rate-limiter")
async def get_rate_limiter_status():
    """Debug endpoint to check rate limiter status"""
    stats = global_rate_limiter.get_stats()
    return {
        "rate_limiter_stats": stats,
        "can_make_call": global_rate_limiter.can_make_call(),
        "current_time": datetime.utcnow().isoformat()
    }