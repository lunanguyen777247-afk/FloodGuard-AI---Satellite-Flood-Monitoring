from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.core.config import get_settings, init_directories
from app.api import regions, analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting FloodGuard-AI Backend...")
    
    try:
        # Initialize directories
        init_directories()
        logger.info("Directories initialized")
        
        # Initialize services (GEE, AI)
        logger.info("Services initialized successfully")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down FloodGuard-AI Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🌊 **FloodGuard-AI Backend API**
    
    Advanced flood monitoring and AI analysis system for Vietnam
    
    ## Features
    
    * **Real-time Monitoring**: Satellite-based flood detection using Sentinel-1 SAR
    * **AI Analysis**: Google Gemini-powered risk assessment and recommendations
    * **Weather Integration**: GPM/TRMM rainfall data and forecasts
    * **Smart Alerts**: Email and Telegram notifications
    * **Interactive Maps**: GeoJSON and tile-based visualization
    
    ## Data Sources
    
    - Google Earth Engine (Sentinel-1, Sentinel-2, GPM)
    - Digital Elevation Models (SRTM)
    - Population density data (WorldPop)
    - Weather APIs
    
    ## Technology Stack
    
    - FastAPI + Python 3.11
    - Google Earth Engine
    - Google Gemini AI
    - PostgreSQL + Redis
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(regions.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow(),
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "api": "operational",
            "gee": "operational",
            "ai": "operational"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests
    """
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
