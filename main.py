from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.services.realtime_service import start_realtime_service, stop_realtime_service
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import get_logger
from app.core.middleware import (
    RequestValidationMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    MaintenanceMiddleware,
    RequestLoggingMiddleware
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting QR Code Ordering System")
    
    # Start error monitoring background tasks
    from app.core.error_monitoring import error_monitor
    error_monitor.start_background_tasks()
    
    await start_realtime_service()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Shutting down QR Code Ordering System")
    await stop_realtime_service()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan
)

# Register global exception handlers
register_exception_handlers(app)

# Add middleware (order matters - first added is outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MaintenanceMiddleware, maintenance_mode=False)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(RequestValidationMiddleware)
if settings.debug:
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True, log_response_body=False)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )