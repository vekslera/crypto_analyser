"""
Data management API endpoints (DIP compliant)
Handles data clearing and management operations using dependency injection
"""

from fastapi import APIRouter, HTTPException

from ..dependency_container import container
from ..services.crypto_service import CryptoService
from ..services.gap_filling_service import GapFillingService
from ..services.backup_service import get_backup_service
from core.config import MESSAGES, HTTP_INTERNAL_ERROR

router = APIRouter()

def get_crypto_service() -> CryptoService:
    """Dependency injection for CryptoService singleton"""
    if not container.is_initialized():
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    return container.get_crypto_service()

def get_gap_filling_service() -> GapFillingService:
    """Dependency injection for GapFillingService"""
    if not container.is_initialized():
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    # Create GapFillingService with database repository
    database_repo = container.get_database_repository()
    return GapFillingService(database_repo)

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


@router.post("/data/fill-gaps")
async def fill_data_gaps(check_recent_days: int = 30, max_gaps: int = 10):
    """Fill data gaps using CoinGecko API"""
    try:
        gap_service = get_gap_filling_service()
        result = await gap_service.fill_all_gaps(min_gap_hours=1.0, max_gaps=max_gaps, check_recent_days=check_recent_days)
        
        if result['success']:
            return {
                "message": result['message'],
                "gaps_detected": result.get('gaps_detected', 0),
                "gaps_filled": result['gaps_filled'],
                "records_inserted": result['records_inserted'],
                "remaining_gaps": result.get('remaining_gaps', 0)
            }
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=result['message'])
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error filling gaps: {str(e)}")


@router.get("/data/gaps")
async def detect_data_gaps(check_recent_days: int = 30):
    """Detect data gaps without filling them"""
    try:
        gap_service = get_gap_filling_service()
        gaps = await gap_service.detect_gaps(min_gap_hours=1.0, check_recent_days=check_recent_days)
        
        gap_summary = []
        total_gap_hours = 0
        
        for gap in gaps:
            gap_info = {
                "start": gap['start'].isoformat(),
                "end": gap['end'].isoformat(), 
                "duration_hours": round(gap['duration_hours'], 2)
            }
            gap_summary.append(gap_info)
            total_gap_hours += gap['duration_hours']
        
        return {
            "gaps_found": len(gaps),
            "total_gap_hours": round(total_gap_hours, 2),
            "total_gap_days": round(total_gap_hours / 24, 2),
            "gaps": gap_summary[:10]  # Return first 10 gaps for preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error detecting gaps: {str(e)}")


@router.post("/data/backup")
async def create_database_backup():
    """Create a backup of the database"""
    try:
        backup_service = get_backup_service()
        result = backup_service.create_backup()
        
        if result['success']:
            return {
                "message": result['message'],
                "backup_file": result['backup_file'],
                "record_count": result['record_count'],
                "timestamp": result['timestamp']
            }
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=result['message'])
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error creating backup: {str(e)}")


@router.get("/data/backups")
async def list_database_backups():
    """List all available database backups"""
    try:
        backup_service = get_backup_service()
        backups = backup_service.list_backups()
        
        return {
            "backups": backups,
            "total_backups": len(backups)
        }
        
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error listing backups: {str(e)}")


@router.post("/data/backup/cleanup")
async def cleanup_old_backups(keep_days: int = 30):
    """Remove old database backups"""
    try:
        backup_service = get_backup_service()
        result = backup_service.cleanup_old_backups(keep_days)
        
        if result['success']:
            return {
                "message": result['message'],
                "deleted_count": result['deleted_count'],
                "deleted_files": result['deleted_files']
            }
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=result['message'])
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error cleaning up backups: {str(e)}")


@router.post("/data/backup/restore/{backup_filename}")
async def restore_from_backup(backup_filename: str):
    """Restore database from a specific backup"""
    try:
        backup_service = get_backup_service()
        result = backup_service.restore_from_backup(backup_filename)
        
        if result['success']:
            return {
                "message": result['message'],
                "backup_used": result['backup_used'],
                "record_count": result['record_count'],
                "current_backup": result['current_backup']
            }
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=result['message'])
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error restoring from backup: {str(e)}")


@router.post("/data/recalculate-volatility")
async def recalculate_volatility(days_back: int = 35):
    """Recalculate volatility for recent data"""
    try:
        gap_service = get_gap_filling_service()
        result = await gap_service.recalculate_volatility_for_recent_data(days_back=days_back)
        
        if result['success']:
            return {
                "message": result['message'],
                "records_updated": result['records_updated'],
                "total_recent_records": result.get('total_recent_records', 0)
            }
        else:
            raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=result['message'])
            
    except Exception as e:
        raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail=f"Error recalculating volatility: {str(e)}")