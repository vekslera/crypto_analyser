"""
Data management API endpoints (DIP compliant)
Handles data clearing and management operations using dependency injection
"""

from fastapi import APIRouter, HTTPException

from ..dependency_container import container
from ..services.crypto_service import CryptoService
from core.config import MESSAGES, HTTP_INTERNAL_ERROR

router = APIRouter()

def get_crypto_service() -> CryptoService:
    """Dependency injection for CryptoService singleton"""
    if not container.is_initialized():
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    return container.get_crypto_service()

@router.delete("/data/clear")
async def clear_data():
    """Clear all stored cryptocurrency data"""
    try:
        crypto_service = get_crypto_service()
        success = await crypto_service.clear_all_data()
        
        if success:
            return {"message": MESSAGES['data_cleared']}
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail="Failed to clear data")
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error clearing data: {str(e)}")