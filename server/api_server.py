"""
FastAPI server for Crypto Analyser (DIP compliant)
Orchestrates all API endpoints and handles application startup with dependency injection
"""

from fastapi import FastAPI
import logging

# Set up comprehensive logging first
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logging_config import get_logger

from .dependency_container import container
from .api_endpoints.crypto_routes import router as crypto_router, collect_and_store_price
from .api_endpoints.data_routes import router as data_router
from .api_endpoints.config_routes import router as config_router
from .api_endpoints.system_routes import router as system_router
from .api_endpoints.debug_routes import router as debug_router
from core.config import APP_TITLE, APP_VERSION, FASTAPI_HOST, FASTAPI_PORT, DATABASE_URL

logger = get_logger("server.api_server")

# Create FastAPI application
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Include all routers
app.include_router(crypto_router)
app.include_router(data_router)
app.include_router(config_router)
app.include_router(system_router)
app.include_router(debug_router)

@app.on_event("startup")
async def startup_event():
    """FastAPI startup event - container is already initialized by startup script"""
    try:
        if not container.is_initialized():
            logger.warning("Container not initialized - this should have been done by startup script")
            return
        
        logger.info("FastAPI startup complete - container already initialized")
        
    except Exception as e:
        logger.error(f"FastAPI startup failed: {e}")
        raise

@app.get("/health")
async def application_health():
    """Overall application health check"""
    if not container.is_initialized():
        return {"status": "unhealthy", "message": "Dependencies not initialized"}
    
    health = await container.health_check()
    overall_status = "healthy" if all(health.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "dependencies": health,
        "app_title": APP_TITLE,
        "version": APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)