"""
Connection Manager for MongoDB Database Operations

Handles connection pooling, configuration management, and connection health
monitoring for efficient and reliable database access.
"""

import os
import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ConnectionConfig:
    """Configuration for MongoDB connection"""
    connection_string: str
    database_name: str
    read_only: bool = True
    max_results: int = 10000
    connection_timeout: int = 30
    pool_size: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0

class ConnectionManager:
    """
    Manages MongoDB connections with pooling, health monitoring, and failover
    
    Provides efficient connection management for high-performance database
    operations while maintaining security and reliability.
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        """
        Initialize connection manager
        
        Args:
            config: Connection configuration (uses environment if None)
        """
        self.config = config or self._load_config_from_env()
        self._connection_pool = {}
        self._health_status = {}
        self._last_health_check = {}
        self._health_check_interval = 300  # 5 minutes
        
        logger.info(f"Connection manager initialized for database: {self.config.database_name}")
    
    def _load_config_from_env(self) -> ConnectionConfig:
        """Load configuration from environment variables"""
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("MONGODB_CONNECTION_STRING environment variable is required")
        
        return ConnectionConfig(
            connection_string=connection_string,
            database_name=os.getenv("MONGODB_DATABASE_NAME", ""),
            read_only=os.getenv("MONGODB_READ_ONLY", "true").lower() == "true",
            max_results=int(os.getenv("MONGODB_MAX_RESULTS", "10000")),
            connection_timeout=int(os.getenv("MONGODB_CONNECTION_TIMEOUT", "30")),
            pool_size=int(os.getenv("MONGODB_POOL_SIZE", "5")),
            retry_attempts=int(os.getenv("MONGODB_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("MONGODB_RETRY_DELAY", "1.0"))
        )
    
    async def get_client(self, database: Optional[str] = None) -> 'DatabaseQueryProcessor':
        """
        Get a database client from the pool
        
        Args:
            database: Database name (uses default if None)
            
        Returns:
            DatabaseQueryProcessor instance
        """
        from .mongodb_client import DatabaseQueryProcessor
        
        database = database or self.config.database_name
        pool_key = database
        
        # Check if we have a healthy connection in the pool
        if pool_key in self._connection_pool:
            client = self._connection_pool[pool_key]
            if await self._is_connection_healthy(client, pool_key):
                return client
            else:
                # Remove unhealthy connection
                await self._cleanup_connection(pool_key)
        
        # Create new connection
        client = await self._create_connection(database)
        self._connection_pool[pool_key] = client
        
        return client
    
    async def _create_connection(self, database: str) -> 'DatabaseQueryProcessor':
        """Create a new database connection"""
        from .mongodb_client import DatabaseQueryProcessor
        
        try:
            client = DatabaseQueryProcessor(
                connection_string=self.config.connection_string,
                database_name=database,
                read_only=self.config.read_only,
                max_results=self.config.max_results,
                connection_timeout=self.config.connection_timeout
            )
            
            # Test the connection
            if await client.test_connection():
                self._health_status[database] = True
                self._last_health_check[database] = datetime.now()
                logger.info(f"Created healthy connection to database: {database}")
                return client
            else:
                raise Exception("Connection test failed")
                
        except Exception as e:
            logger.error(f"Failed to create connection to {database}: {e}")
            raise
    
    async def _is_connection_healthy(self, client: 'DatabaseQueryProcessor', database: str) -> bool:
        """Check if connection is healthy"""
        # Check cache first
        last_check = self._last_health_check.get(database)
        if last_check and (datetime.now() - last_check).seconds < self._health_check_interval:
            return self._health_status.get(database, False)
        
        # Perform health check
        try:
            is_healthy = await client.test_connection()
            self._health_status[database] = is_healthy
            self._last_health_check[database] = datetime.now()
            
            if not is_healthy:
                logger.warning(f"Health check failed for database: {database}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check error for {database}: {e}")
            self._health_status[database] = False
            return False
    
    async def _cleanup_connection(self, database: str):
        """Clean up unhealthy connection"""
        if database in self._connection_pool:
            try:
                client = self._connection_pool[database]
                if hasattr(client, '__aexit__'):
                    await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error cleaning up connection for {database}: {e}")
            finally:
                del self._connection_pool[database]
                self._health_status[database] = False
    
    async def execute_with_retry(self, operation_func, *args, **kwargs):
        """
        Execute database operation with retry logic
        
        Args:
            operation_func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Operation result
        """
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await operation_func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Operation failed (attempt {attempt + 1}/{self.config.retry_attempts}): {e}")
                
                if attempt < self.config.retry_attempts - 1:
                    # Wait before retry with exponential backoff
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    
                    # Clear connection pool to force reconnection
                    await self._clear_pool()
        
        # All retries failed
        logger.error(f"Operation failed after {self.config.retry_attempts} attempts: {last_exception}")
        raise last_exception
    
    async def _clear_pool(self):
        """Clear all connections in the pool"""
        for database in list(self._connection_pool.keys()):
            await self._cleanup_connection(database)
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Get connection pool status
        
        Returns:
            Dictionary with pool information
        """
        status = {
            "pool_size": len(self._connection_pool),
            "active_connections": list(self._connection_pool.keys()),
            "health_status": dict(self._health_status),
            "last_health_checks": {
                db: check_time.isoformat() 
                for db, check_time in self._last_health_check.items()
            },
            "configuration": {
                "database_name": self.config.database_name,
                "read_only": self.config.read_only,
                "max_results": self.config.max_results,
                "pool_size": self.config.pool_size,
                "retry_attempts": self.config.retry_attempts
            }
        }
        
        return status
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all connections
        
        Returns:
            Dictionary mapping database names to health status
        """
        results = {}
        
        for database, client in self._connection_pool.items():
            try:
                is_healthy = await client.test_connection()
                results[database] = is_healthy
                self._health_status[database] = is_healthy
                self._last_health_check[database] = datetime.now()
                
            except Exception as e:
                logger.error(f"Health check failed for {database}: {e}")
                results[database] = False
                self._health_status[database] = False
        
        return results
    
    async def close_all_connections(self):
        """Close all connections in the pool"""
        logger.info("Closing all database connections")
        
        for database in list(self._connection_pool.keys()):
            await self._cleanup_connection(database)
        
        self._connection_pool.clear()
        self._health_status.clear()
        self._last_health_check.clear()
        
        logger.info("All connections closed")
    
    def get_config(self) -> ConnectionConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, **kwargs):
        """
        Update configuration parameters
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")

# Global connection manager instance
_connection_manager = None

def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager instance"""
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    
    return _connection_manager

async def initialize_connection_manager(config: Optional[ConnectionConfig] = None):
    """Initialize global connection manager"""
    global _connection_manager
    
    _connection_manager = ConnectionManager(config)
    logger.info("Global connection manager initialized")

async def cleanup_connections():
    """Cleanup global connection manager"""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close_all_connections()
        _connection_manager = None
        logger.info("Global connection manager cleaned up")
