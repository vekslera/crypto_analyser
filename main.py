from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from database import get_db, create_tables, BitcoinPrice
from bitcoin_service import BitcoinService
from shared_data import shared_data
from rate_limiter import global_rate_limiter
#import asyncio
#from typing import List, Dict, Any
from datetime import datetime #, timedelta
import pandas as pd
from pydantic import BaseModel
import os
import signal

app = FastAPI(title="Bitcoin Price Tracker", version="1.0.0")
bitcoin_service = BitcoinService()

class PriceResponse(BaseModel):
    price: float
    timestamp: datetime
    volume_24h: float = None
    market_cap: float = None

class StatsResponse(BaseModel):
    count: int
    mean: float = None
    std: float = None
    min: float = None
    max: float = None
    latest: float = None

@app.on_event("startup")
async def startup_event():
    create_tables()
    await collect_and_store_price()

async def collect_and_store_price():
    price_data = await bitcoin_service.fetch_bitcoin_price()
    if price_data:
        db = next(get_db())
        try:
            db_price = BitcoinPrice(
                price=price_data['price'],
                timestamp=price_data['timestamp'],
                volume_24h=price_data.get('volume_24h'),
                market_cap=price_data.get('market_cap')
            )
            db.add(db_price)
            db.commit()
            
            bitcoin_service.add_to_series(
                price_data['price'], 
                price_data['timestamp']
            )
        finally:
            db.close()

@app.get("/")
async def root():
    return {"message": "Bitcoin Price Tracker API", "status": "running"}

@app.get("/price/current", response_model=PriceResponse)
async def get_current_price():
    price_data = await bitcoin_service.fetch_bitcoin_price()
    if not price_data:
        raise HTTPException(status_code=503, detail="Unable to fetch current price")
    
    return PriceResponse(**price_data)

@app.post("/price/collect")
async def collect_price(background_tasks: BackgroundTasks):
    background_tasks.add_task(collect_and_store_price)
    return {"message": "Price collection initiated"}

@app.get("/price/history")
async def get_price_history(limit: int = 100, db: Session = Depends(get_db)):
    prices = db.query(BitcoinPrice).order_by(BitcoinPrice.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": price.id,
            "price": price.price,
            "timestamp": price.timestamp,
            "volume_24h": price.volume_24h,
            "market_cap": price.market_cap
        }
        for price in prices
    ]

@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    stats = bitcoin_service.get_statistics()
    if not stats:
        raise HTTPException(status_code=404, detail="No data available")
    
    return StatsResponse(**stats)

@app.get("/series/recent")
async def get_recent_series(limit: int = 50):
    series = bitcoin_service.get_recent_data(limit)
    return {
        "data": series.to_dict(),
        "count": len(series),
        "latest_timestamp": series.index[-1].isoformat() if len(series) > 0 else None
    }

@app.delete("/data/clear")
async def clear_data(db: Session = Depends(get_db)):
    try:
        db.query(BitcoinPrice).delete()
        db.commit()
        shared_data.clear_data()
        return {"message": "All data cleared successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")

@app.get("/debug/rate-limiter")
async def get_rate_limiter_status():
    """Debug endpoint to check rate limiter status"""
    stats = global_rate_limiter.get_stats()
    return {
        "rate_limiter_stats": stats,
        "can_make_call": global_rate_limiter.can_make_call(),
        "current_time": datetime.utcnow().isoformat()
    }

@app.post("/system/shutdown")
async def shutdown_server():
    """Gracefully shutdown the server"""
    import asyncio
    
    def shutdown():
        # Send SIGTERM to current process
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Schedule shutdown after sending response
    asyncio.get_event_loop().call_later(1, shutdown)
    
    return {
        "message": "Server shutdown initiated", 
        "status": "shutting_down",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)