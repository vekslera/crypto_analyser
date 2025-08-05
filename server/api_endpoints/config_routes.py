"""
Configuration management API endpoints
Handles user parameters and application configuration
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from core.config import get_all_user_parameters, update_user_parameters, reset_user_parameters, MESSAGES, HTTP_INTERNAL_ERROR

router = APIRouter()

@router.get("/config/user-parameters")
async def get_user_parameters():
    """Get current user parameters configuration"""
    return {
        "user_parameters": get_all_user_parameters(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/config/user-parameters")
async def update_user_parameters_endpoint(updates: dict):
    """Update user parameters configuration"""
    try:
        update_user_parameters(updates)
        return {
            "message": "User parameters updated successfully",
            "updated_parameters": updates,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error updating parameters: {str(e)}")

@router.post("/config/reset-parameters")
async def reset_user_parameters_endpoint():
    """Reset all user parameters to default values"""
    try:
        reset_user_parameters()
        return {
            "message": "User parameters reset to defaults",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error resetting parameters: {str(e)}")