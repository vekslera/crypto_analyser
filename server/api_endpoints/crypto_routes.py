"""
Cryptocurrency price API endpoints (DIP compliant)
Handles crypto price, statistics, and data collection routes using dependency injection
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any

from ..dependency_container import container
from ..services.crypto_service import CryptoService
from ..interfaces.database_interface import PriceData
from core.config import DEFAULT_API_LIMIT, DEFAULT_SERIES_LIMIT, MESSAGES, HTTP_SERVICE_UNAVAILABLE, HTTP_NOT_FOUND

router = APIRouter()

def format_price_data(prices: List[PriceData]) -> List[Dict[str, Any]]:
    """Format price data for API response"""
    return [
        {
            "id": price.id,
            "price": price.price,
            "timestamp": price.timestamp,
            "volume_24h": price.volume_24h,
            "volume_velocity": price.volume_velocity,
            "market_cap": price.market_cap
        }
        for price in prices
    ]

def get_crypto_service() -> CryptoService:
    """Dependency injection for CryptoService singleton"""
    if not container.is_initialized():
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    return container.get_crypto_service()

class PriceResponse(BaseModel):
    price: float
    timestamp: datetime
    volume_24h: float = None
    volume_velocity: float = None
    market_cap: float = None

class StatsResponse(BaseModel):
    count: int
    mean: float = None
    std: float = None
    min: float = None
    max: float = None
    latest: float = None

async def collect_and_store_price():
    """Collect and store cryptocurrency price data using dependency injection"""
    crypto_service = get_crypto_service()
    price_data = await crypto_service.fetch_and_store_current_price("bitcoin")
    return price_data

@router.get("/price/current", response_model=PriceResponse)
async def get_current_price():
    """Get current cryptocurrency price (from real-time series, updated every 60s)"""
    crypto_service = get_crypto_service()
    
    # Get the latest price from pandas series (real-time 60s updates)
    series = crypto_service.get_recent_series(limit=1)
    
    if len(series) > 0:
        # Use real-time price from series
        latest_price = series.iloc[-1]
        latest_timestamp = series.index[-1]
        
        # Get volume/market cap from most recent database record (5min updates)
        recent_prices = await crypto_service.get_recent_prices(limit=1)
        volume_24h = recent_prices[0].volume_24h if recent_prices else None
        volume_velocity = recent_prices[0].volume_velocity if recent_prices else None
        market_cap = recent_prices[0].market_cap if recent_prices else None
        
        return PriceResponse(
            price=float(latest_price),
            timestamp=latest_timestamp,
            volume_24h=volume_24h,
            volume_velocity=volume_velocity,
            market_cap=market_cap
        )
    else:
        # Fallback: if no series data, fetch once
        price_data = await crypto_service.fetch_and_store_current_price("bitcoin")
        if not price_data:
            raise HTTPException(status_code=HTTP_SERVICE_UNAVAILABLE, detail=MESSAGES['unable_to_fetch'])
        
        return PriceResponse(
            price=price_data.price,
            timestamp=price_data.timestamp,
            volume_24h=price_data.volume_24h,
            volume_velocity=price_data.volume_velocity,
            market_cap=price_data.market_cap
        )

@router.post("/price/collect")
async def collect_price(background_tasks: BackgroundTasks):
    """Manually trigger price collection"""
    background_tasks.add_task(collect_and_store_price)
    return {"message": "Price collection initiated"}

@router.get("/price/history")
async def get_price_history(limit: int = DEFAULT_API_LIMIT):
    """Get historical price data (limit-based query)"""
    crypto_service = get_crypto_service()
    prices = await crypto_service.get_price_history(limit)
    return format_price_data(prices)

@router.get("/price/history/range")
async def get_price_history_by_range(
    start_time: str,
    end_time: str
):
    """Get historical price data within a specific time range"""
    from datetime import datetime
    
    crypto_service = get_crypto_service()
    
    # Parse and validate timestamps
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {e}")
    
    # Validate time range
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    
    prices = await crypto_service.get_price_history_by_time_range(start_dt, end_dt)
    return format_price_data(prices)

@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get statistical analysis of collected price data"""
    crypto_service = get_crypto_service()
    stats = await crypto_service.get_statistics()
    
    if not stats or stats.get('count', 0) == 0:
        raise HTTPException(status_code=HTTP_NOT_FOUND, detail=MESSAGES['no_data_available'])
    
    return StatsResponse(**stats)

@router.get("/series/recent")
async def get_recent_series(limit: int = DEFAULT_SERIES_LIMIT):
    """Get recent data from pandas series"""
    crypto_service = get_crypto_service()
    series = crypto_service.get_recent_series(limit)
    
    return {
        "data": series.to_dict(),
        "count": len(series),
        "latest_timestamp": series.index[-1].isoformat() if len(series) > 0 else None
    }

@router.get("/crypto/health")
async def health_check():
    """Health check for crypto service and dependencies"""
    crypto_service = get_crypto_service()
    health = await crypto_service.health_check()
    return health

@router.get("/crypto/provider-info")
async def get_provider_info():
    """Get information about the current data provider"""
    crypto_service = get_crypto_service()
    return crypto_service.get_provider_info()

@router.get("/crypto/supported-symbols")
async def get_supported_symbols():
    """Get list of supported cryptocurrency symbols"""
    crypto_service = get_crypto_service()
    symbols = await crypto_service.get_supported_symbols()
    return {"symbols": symbols[:100]}  # Limit response size