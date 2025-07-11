"""
Redis client configuration and connection pool management.

This module provides a centralized Redis connection pool that is efficient
and robust for production environments. It uses connection pooling to reuse
existing connections and avoid the overhead of creating new connections
for each request.
"""

import logging
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool instance
redis_pool: Optional[redis.ConnectionPool] = None


def create_redis_pool() -> redis.ConnectionPool:
    """
    Create and configure a Redis connection pool.
    
    SSL Security Notes:
    - REDIS_SSL_CERT_REQS='required' (default): Full certificate verification (most secure)
    - REDIS_SSL_CERT_REQS='optional': Certificate verification if present
    - REDIS_SSL_CERT_REQS='none': No certificate verification (insecure, not recommended)
    
    For production environments, always use 'required' with proper certificates.
    
    Returns:
        redis.ConnectionPool: Configured Redis connection pool
    """
    try:
        # Build connection parameters
        connection_params = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB,
            "decode_responses": True,
            "max_connections": settings.REDIS_MAX_CONNECTIONS,
            "retry_on_timeout": settings.REDIS_RETRY_ON_TIMEOUT,
            "socket_connect_timeout": settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            "socket_keepalive": settings.REDIS_SOCKET_KEEPALIVE,
        }
        
        # Add authentication if provided
        if settings.REDIS_USERNAME:
            connection_params["username"] = settings.REDIS_USERNAME
        if settings.REDIS_PASSWORD:
            connection_params["password"] = settings.REDIS_PASSWORD
            
        # Add SSL configuration if enabled
        if settings.REDIS_SSL:
            import ssl
            connection_params["ssl"] = True
            
            # SSL certificate verification (secure by default)
            if settings.REDIS_SSL_CERT_REQS.lower() == 'none':
                connection_params["ssl_cert_reqs"] = ssl.CERT_NONE
                logger.warning(
                    "Redis SSL certificate verification is DISABLED. "
                    "This is insecure and not recommended for production environments."
                )
            elif settings.REDIS_SSL_CERT_REQS.lower() == 'optional':
                connection_params["ssl_cert_reqs"] = ssl.CERT_OPTIONAL
                logger.info("Redis SSL certificate verification set to OPTIONAL")
            else:  # 'required' (default and most secure)
                connection_params["ssl_cert_reqs"] = ssl.CERT_REQUIRED
                logger.info("Redis SSL certificate verification set to REQUIRED (secure)")
            
            # SSL certificate files
            if settings.REDIS_SSL_CA_CERTS:
                connection_params["ssl_ca_certs"] = settings.REDIS_SSL_CA_CERTS
            if settings.REDIS_SSL_CERTFILE:
                connection_params["ssl_certfile"] = settings.REDIS_SSL_CERTFILE
            if settings.REDIS_SSL_KEYFILE:
                connection_params["ssl_keyfile"] = settings.REDIS_SSL_KEYFILE
            
            # Hostname verification
            connection_params["ssl_check_hostname"] = settings.REDIS_SSL_CHECK_HOSTNAME
        
        # Create connection pool
        pool = redis.ConnectionPool(**connection_params)
        
        logger.info(f"Redis connection pool created successfully: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return pool
        
    except Exception as e:
        logger.error(f"Failed to create Redis connection pool: {e}")
        raise


async def init_redis_pool() -> None:
    """
    Initialize the global Redis connection pool.
    Should be called during application startup.
    """
    global redis_pool
    
    if redis_pool is None:
        redis_pool = create_redis_pool()
        
        # Test the connection
        test_client = Redis(connection_pool=redis_pool)
        try:
            await test_client.ping()
            logger.info("Redis connection pool initialized and tested successfully")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        finally:
            await test_client.aclose()


async def close_redis_pool() -> None:
    """
    Close the global Redis connection pool.
    Should be called during application shutdown.
    """
    global redis_pool
    
    if redis_pool:
        try:
            await redis_pool.disconnect()
            redis_pool = None
            logger.info("Redis connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")


def get_redis_client() -> Redis:
    """
    Get a Redis client from the connection pool.
    
    This function is designed to be used with FastAPI's dependency injection.
    
    Returns:
        Redis: Redis client instance from the connection pool
        
    Raises:
        RuntimeError: If the connection pool is not initialized
    """
    if redis_pool is None:
        raise RuntimeError(
            "Redis connection pool is not initialized. "
            "Make sure to call init_redis_pool() during application startup."
        )
    
    return Redis(connection_pool=redis_pool)


async def get_redis_client_async() -> Redis:
    """
    Compatibility wrapper for get_redis_client in async contexts.
    
    Note: This doesn't perform any async operations, it just wraps
    the synchronous client retrieval for use in async functions.   
     
    Returns:
        Redis: Redis client instance from the connection pool
        
    Raises:
        RuntimeError: If the connection pool is not initialized
    """
    return get_redis_client()


class RedisHealthCheck:
    """
    Redis health check utilities.
    """
    
    @staticmethod
    async def check_connection() -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            client = get_redis_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @staticmethod
    async def get_info() -> dict:
        """
        Get Redis server information.
        
        Returns:
            dict: Redis server information
        """
        try:
            client = get_redis_client()
            info = await client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {} 