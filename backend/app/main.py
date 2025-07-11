from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import database
from app.core.redis_client import init_redis_pool, close_redis_pool, RedisHealthCheck
from app.routers import contacts, deals, activities, dashboard, auth, organizations, invites, memberships


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    This context manager handles the startup and shutdown of the application,
    including database and Redis connections.
    """
    # Startup
    logger.info("TinyCRM API is starting up...")
    
    try:
        # Initialize MongoDB connection
        await database.connect_to_mongo()
        logger.info("Connected to MongoDB")
        
        # Initialize Redis connection pool
        await init_redis_pool()
        logger.info("Redis connection pool initialized")
        
        # Verify Redis connection
        redis_healthy = await RedisHealthCheck.check_connection()
        if not redis_healthy:
            logger.warning("Redis connection check failed, but continuing startup")
        
        logger.info("TinyCRM API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start TinyCRM API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("TinyCRM API is shutting down...")
    
    try:
        # Close Redis connection pool
        await close_redis_pool()
        logger.info("Redis connection pool closed")
        
        # Close MongoDB connection
        await database.close_mongo_connection()
        logger.info("MongoDB connection closed")
        
        logger.info("TinyCRM API shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during TinyCRM API shutdown: {e}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="TinyCRM API",
        description="A simple CRM API with multi-tenant architecture and OAuth2 authentication",
        version="2.0.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # Include routers
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(organizations.router, prefix=settings.API_PREFIX)
    app.include_router(invites.router, prefix=settings.API_PREFIX)
    app.include_router(memberships.router, prefix=settings.API_PREFIX)
    app.include_router(contacts.router, prefix=settings.API_PREFIX)
    app.include_router(deals.router, prefix=settings.API_PREFIX)
    app.include_router(activities.router, prefix=settings.API_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_PREFIX)

    # Note: Event handlers are now managed by the lifespan context manager

    @app.get("/")
    async def root():
        return {"message": "TinyCRM API", "version": "2.0.0", "status": "running"}
    
    @app.get("/redis-info")
    async def redis_info():
        """
        Get Redis server information for debugging purposes.
        """
        try:
            info = await RedisHealthCheck.get_info()
            return {"redis_info": info}
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"error": "Failed to get Redis information", "details": str(e)}

    @app.get("/health")
    async def health_check():
        """
        Health check endpoint that verifies the status of all services.
        """
        health_status = {
            "status": "healthy",
            "services": {
                "api": "healthy",
                "mongodb": "unknown",
                "redis": "unknown"
            }
        }
        
        # Check MongoDB connection
        try:
            # Simple check if database is connected
            if database.client:
                health_status["services"]["mongodb"] = "healthy"
            else:
                health_status["services"]["mongodb"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception:
            health_status["services"]["mongodb"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check Redis connection
        try:
            redis_healthy = await RedisHealthCheck.check_connection()
            if redis_healthy:
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception:
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
        
        return health_status

    return app


# Create app instance
app = create_application() 