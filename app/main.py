"""
Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.api.chat import router as chat_router
from app.observability.logging import setup_logging
from app.db.mongodb import mongodb_manager
from fastapi.staticfiles import StaticFiles
import os

# Setup logging first
setup_logging()
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix=settings.API_PREFIX)

# Mount exports directory for Excel file downloads
exports_dir = "exports"
if not os.path.exists(exports_dir):
    os.makedirs(exports_dir)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")

# Mount charts directory for generated visualizations
from pathlib import Path
charts_dir = Path("charts/generated")
charts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/charts/generated", StaticFiles(directory=str(charts_dir)), name="charts")


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Application starting up")
    logger.info(f"API Title: {settings.API_TITLE}")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Connect to MongoDB
    try:
        await mongodb_manager.connect()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        # Continue without MongoDB (graceful degradation)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Application shutting down")
    
    # Disconnect from MongoDB
    try:
        await mongodb_manager.disconnect()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"MongoDB disconnection error: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PostgreSQL Chat API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3300,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
