"""
Main FastAPI application.

Entry point for the Stock Tracker Backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from app.core.database import db
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for database connections
    and other resources.
    """
    # Startup
    logger.info("Starting Stock Tracker Backend...")

    try:
        # Connect to MongoDB
        await db.connect_mongodb()
        logger.info("MongoDB connected successfully")

        # Connect to Redis
        await db.connect_redis()
        logger.info("Redis connected successfully")

    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Stock Tracker Backend...")

    try:
        # Close database connections
        await db.close_mongodb()
        await db.close_redis()
        logger.info("Database connections closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Comprehensive stock tracking and analysis backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the health status of the API and its dependencies.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
