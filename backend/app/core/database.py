from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class DatabaseManager:
    """MongoDB database connection manager."""
    
    def __init__(self):
        self.client = None
        self.database = None
    
    async def connect_to_mongo(self):
        """Create database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.database = self.client[settings.DB_NAME]
    
    async def close_mongo_connection(self):
        """Close database connection."""
        if self.client:
            self.client.close()


# Global database instance
database = DatabaseManager()


# Dependency to get database
async def get_database():
    """Get database dependency for FastAPI dependency injection."""
    return database.database 