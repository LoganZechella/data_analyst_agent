"""
Enhanced Data Analyzer Agent - MongoDB Atlas Integration

This module implements the enhanced Data Analyzer AI agent that combines
MongoDB Atlas database connectivity via MCP with the existing OpenAI Responses API
architecture for optimal performance and capability.
"""

import os
import json
import logging
import asyncio
from typing import Iterator, Dict, Any, Optional, List
from datetime import datetime

from .main_responses_api import DataAnalyzerAgent
from .database import DatabaseQueryProcessor, QueryParser, SchemaManager, ConnectionManager
from .prompts.database_prompts import (
    DATABASE_AWARE_SYSTEM_PROMPT,
    DATABASE_EXPLORATION_PROMPT,
    DATABASE_BUSINESS_INTELLIGENCE_PROMPT,
    DATABASE_TIME_SERIES_PROMPT,
    DATABASE_CUSTOMER_ANALYTICS_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedDataAnalyzerAgent(DataAnalyzerAgent):
    """
    Enhanced Data Analyzer Agent with MongoDB Atlas integration
    
    Combines the simplified Responses API architecture with powerful database
    connectivity while maintaining real-time streaming and performance benefits.
    
    Features:
    - Native MongoDB Atlas connectivity via MCP
    - Automatic schema discovery and analysis
    - Intelligent query parsing and optimization
    - Hybrid data sources (database + inline data)
    - Advanced error handling and fallback strategies
    """
    
    def __init__(self, 
                 model: str = "gpt-4.1",
                 reasoning_effort: str = "medium",
                 mongodb_connection: Optional[str] = None,
                 database_name: Optional[str] = None,
                 enable_database: bool = True,
                 read_only: bool = True,
                 max_results: int = 10000):
        """
        Initialize the Enhanced Data Analyzer Agent
        
        Args:
            model: The OpenAI model to use
            reasoning_effort: For reasoning models - low, medium, high
            mongodb_connection: MongoDB connection string (uses env if None)
            database_name: Default database name (uses env if None)
            enable_database: Enable database connectivity
            read_only: Use read-only database access
            max_results: Maximum results per query
        """
        # Initialize base agent with enhanced system prompt
        super().__init__(model=model, reasoning_effort=reasoning_effort)
        
        # Database configuration
        self.enable_database = enable_database and bool(mongodb_connection or os.getenv("MONGODB_CONNECTION_STRING"))
        self.mongodb_connection = mongodb_connection or os.getenv("MONGODB_CONNECTION_STRING")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE_NAME")
        self.read_only = read_only
        self.max_results = max_results
        
        # Initialize database components if enabled
        self.db_processor = None
        self.query_parser = None
        self.schema_manager = None
        self.connection_manager = None
        
        if self.enable_database:
            self._initialize_database_components()
        
        # Update system prompt for database awareness
        self.system_prompt = self._get_enhanced_system_prompt()
        
        logger.info(f"Enhanced Data Analyzer Agent initialized - Database: {'Enabled' if self.enable_database else 'Disabled'}")
    
    def _initialize_database_components(self):
        """Initialize database-related components"""
        try:
            # Initialize connection manager
            from .database.connection_manager import ConnectionConfig
            
            config = ConnectionConfig(
                connection_string=self.mongodb_connection,
                database_name=self.database_name,
                read_only=self.read_only,
                max_results=self.max_results
            )
            
            self.connection_manager = ConnectionManager(config)
            
            # Initialize query parser
            self.query_parser = QueryParser()
            
            logger.info("Database components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database components: {e}")
            self.enable_database = False
            raise
    
    def _get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with database awareness"""
        if self.enable_database:
            return DATABASE_AWARE_SYSTEM_PROMPT
        else:
            # Fall back to original system prompt if database disabled
            return super()._get_system_prompt()
    
    async def analyze_with_database(self, 
                                  query: str, 
                                  data: Optional[str] = None,
                                  stream: bool = True,
                                  files: Optional[list] = None,
                                  database: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Enhanced analyze method with database support
        
        Args:
            query: The analysis request from the user
            data: Optional inline data string
            stream: Whether to stream responses in real-time
            files: Optional list of file paths to upload
            database: Optional database name override
            
        Yields:
            Dictionary containing event type and data for real-time updates
        """
        enhanced_query = query
        database_context = {}
        
        # Step 1: Parse query for database references
        if self.enable_database and self.query_parser:
            try:
                yield {
                    "type": "database_detection",
                    "message": "🔍 Analyzing query for database references...",
                    "timestamp": datetime.now().isoformat()
                }
                
                db_ref = self.query_parser.extract_database_references(query)
                
                if db_ref and db_ref.confidence > 0.5:
                    # Step 2: Execute database query
                    yield {
                        "type": "database_query_start",
                        "message": f"📊 Querying {db_ref.collection} collection...",
                        "collection": db_ref.collection,
                        "operation": db_ref.operation_type,
                        "confidence": db_ref.confidence
                    }
                    
                    database_data, schema_info = await self._execute_database_query(
                        db_ref, database, query
                    )
                    
                    yield {
                        "type": "database_query_complete",
                        "message": f"✅ Retrieved data from {db_ref.collection}",
                        "data_size": len(database_data) if database_data else 0,
                        "schema_fields": len(schema_info.get("fields", {})) if schema_info else 0
                    }
                    
                    # Step 3: Enhance query with database context
                    enhanced_query = self._enhance_query_with_database_context(
                        query, database_data, schema_info, db_ref
                    )
                    
                    database_context = {
                        "collection": db_ref.collection,
                        "operation_type": db_ref.operation_type,
                        "schema_info": schema_info,
                        "data_retrieved": bool(database_data)
                    }
                    
                else:
                    yield {
                        "type": "database_detection_complete",
                        "message": "💡 No database references detected, proceeding with standard analysis",
                        "confidence": db_ref.confidence if db_ref else 0.0
                    }
                    
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                yield {
                    "type": "database_error",
                    "message": f"⚠️ Database operation failed: {str(e)}, proceeding with inline data",
                    "error": str(e)
                }
        
        # Step 4: Execute analysis with enhanced query
        yield {
            "type": "analysis_start",
            "message": "🚀 Starting analysis with enhanced context...",
            "database_context": database_context
        }
        
        # Use parent's analyze method with enhanced query
        async for event in super().analyze(
            query=enhanced_query, 
            data=data, 
            stream=stream, 
            files=files
        ):
            # Add database context to events if available
            if database_context:
                event["database_context"] = database_context
            yield event
    
    async def _execute_database_query(self, 
                                    db_ref, 
                                    database: Optional[str],
                                    original_query: str) -> tuple:
        """Execute database query and return data with schema info"""
        try:
            # Get database client
            client = await self.connection_manager.get_client(database or db_ref.database)
            
            # Get schema manager
            if not self.schema_manager:
                self.schema_manager = SchemaManager(client)
            
            # Discover schema first for better context
            schema_info = await self.schema_manager.discover_collection_schema(
                collection=db_ref.collection,
                database=database or db_ref.database
            )
            
            # Execute the database operation
            database_data = await client.execute_database_reference(db_ref)
            
            return database_data, schema_info
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return None, None
    
    def _enhance_query_with_database_context(self, 
                                           original_query: str,
                                           database_data: Optional[str],
                                           schema_info: Optional[Dict],
                                           db_ref) -> str:
        """Enhance user query with database context and retrieved data"""
        enhancements = []
        
        # Add database context
        if db_ref:
            enhancements.append(f"Database Context: Analyzing {db_ref.collection} collection")
            if db_ref.operation_type != "query":
                enhancements.append(f"Operation Type: {db_ref.operation_type}")
        
        # Add schema information
        if schema_info and "fields" in schema_info:
            fields = list(schema_info["fields"].keys())[:10]  # Limit to first 10 fields
            enhancements.append(f"Available Fields: {', '.join(fields)}")
            
            # Add analysis recommendations if available
            if "analysis_recommendations" in schema_info:
                recommendations = schema_info["analysis_recommendations"][:3]
                if recommendations:
                    enhancements.append(f"Analysis Suggestions: {'; '.join(recommendations)}")
        
        # Add retrieved data
        if database_data:
            enhancements.append(f"Retrieved Data:\n{database_data}")
        
        # Construct enhanced query
        if enhancements:
            enhanced_query = f"{original_query}\n\n--- Database Context ---\n" + "\n".join(enhancements)
        else:
            enhanced_query = original_query
        
        return enhanced_query
    
    async def discover_collection_schema(self, 
                                       collection: str,
                                       database: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover and analyze collection schema
        
        Args:
            collection: Collection name
            database: Database name (optional)
            
        Returns:
            Schema information dictionary
        """
        if not self.enable_database:
            return {"error": "Database connectivity is disabled"}
        
        try:
            client = await self.connection_manager.get_client(database)
            
            if not self.schema_manager:
                self.schema_manager = SchemaManager(client)
            
            schema_info = await self.schema_manager.discover_collection_schema(
                collection=collection,
                database=database
            )
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {e}")
            return {"error": str(e)}
    
    async def list_collections(self, database: Optional[str] = None) -> List[str]:
        """
        List available collections in database
        
        Args:
            database: Database name (optional, uses default if None)
            
        Returns:
            List of collection names
        """
        if not self.enable_database:
            return []
        
        try:
            # Use provided database or fall back to default
            db_name = database or self.database_name
            
            if not db_name:
                logger.warning("No database name provided and no default set")
                return []
            
            client = await self.connection_manager.get_client(db_name)
            result = await client.list_collections(db_name)
            
            # Extract collection names from the result dict
            if isinstance(result, dict) and "collections" in result:
                collections = result["collections"]
                if isinstance(collections, list):
                    return collections
                else:
                    return [collections] if collections else []
            else:
                return []
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    async def test_database_connection(self) -> bool:
        """
        Test database connectivity
        
        Returns:
            True if connection successful
        """
        if not self.enable_database:
            return False
        
        try:
            client = await self.connection_manager.get_client()
            return await client.test_connection()
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_database_status(self) -> Dict[str, Any]:
        """
        Get database connection and configuration status
        
        Returns:
            Status information dictionary
        """
        status = {
            "database_enabled": self.enable_database,
            "connection_configured": bool(self.mongodb_connection),
            "database_name": self.database_name,
            "read_only": self.read_only,
            "max_results": self.max_results
        }
        
        if self.connection_manager:
            pool_status = asyncio.create_task(self.connection_manager.get_pool_status())
            # Note: This is async, would need to be called in async context
            status["connection_manager"] = "initialized"
        
        return status
    
    async def cleanup(self):
        """Cleanup database connections and resources"""
        if self.connection_manager:
            await self.connection_manager.close_all_connections()
            logger.info("Database connections cleaned up")

# Factory functions for different model configurations
def create_enhanced_standard_analyzer(mongodb_connection: Optional[str] = None) -> EnhancedDataAnalyzerAgent:
    """Create an enhanced standard data analyzer using GPT-4.1 with database support"""
    return EnhancedDataAnalyzerAgent(
        model="gpt-4.1",
        mongodb_connection=mongodb_connection
    )

def create_enhanced_reasoning_analyzer(mongodb_connection: Optional[str] = None) -> EnhancedDataAnalyzerAgent:
    """Create an enhanced reasoning analyzer using o4-mini with database support"""
    return EnhancedDataAnalyzerAgent(
        model="o4-mini", 
        reasoning_effort="high",
        mongodb_connection=mongodb_connection
    )

# Create enhanced analyzer instances
enhanced_data_analyzer_agent = create_enhanced_standard_analyzer()
enhanced_o4_analyzer_agent = create_enhanced_reasoning_analyzer()

# Maintain backward compatibility
def create_enhanced_agent_with_fallback(mongodb_connection: Optional[str] = None) -> DataAnalyzerAgent:
    """
    Create enhanced agent with fallback to standard agent if database unavailable
    
    Args:
        mongodb_connection: MongoDB connection string
        
    Returns:
        Enhanced agent if database available, standard agent otherwise
    """
    try:
        # Try to create enhanced agent
        enhanced_agent = EnhancedDataAnalyzerAgent(mongodb_connection=mongodb_connection)
        
        # Test database connectivity
        if enhanced_agent.enable_database:
            logger.info("Enhanced agent with database connectivity created successfully")
            return enhanced_agent
        else:
            raise Exception("Database connectivity not available")
            
    except Exception as e:
        logger.warning(f"Enhanced agent creation failed, falling back to standard agent: {e}")
        
        # Fall back to standard agent
        from .main_responses_api import create_standard_analyzer
        return create_standard_analyzer()

__all__ = [
    "EnhancedDataAnalyzerAgent",
    "enhanced_data_analyzer_agent", 
    "enhanced_o4_analyzer_agent",
    "create_enhanced_standard_analyzer",
    "create_enhanced_reasoning_analyzer",
    "create_enhanced_agent_with_fallback"
]

logger.info("Enhanced Data Analyzer Agent modules loaded successfully")
