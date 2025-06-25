from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import database
from app.routers import contacts, deals, activities, dashboard


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Tiny CRM API",
        description="A simple CRM API built with FastAPI and MongoDB",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # Include routers
    app.include_router(contacts.router, prefix=settings.API_PREFIX)
    app.include_router(deals.router, prefix=settings.API_PREFIX)
    app.include_router(activities.router, prefix=settings.API_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_PREFIX)

    # Event handlers
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up...")
        await database.connect_to_mongo()
        logger.info("Connected to MongoDB")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down...")
        await database.close_mongo_connection()
        logger.info("Disconnected from MongoDB")

    @app.get("/")
    async def root():
        return {"message": "Welcome to Tiny CRM API"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


# Create app instance
app = create_application() 