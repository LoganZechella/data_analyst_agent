"""
MongoDB Client for MCP Integration

Handles MongoDB Atlas operations via Model Context Protocol (MCP).
Provides secure database access while maintaining connection efficiency.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from agents.mcp.server import MCPServerStdio
from .query_parser import DatabaseReference
from .connection_manager import ConnectionManager
from .exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

class DatabaseQueryProcessor:
    """
    Handles MongoDB operations via MCP server
    
    Provides secure, efficient database access with built-in safety features
    including read-only mode, query limits, and connection management.
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 database_name: Optional[str] = None,
                 read_only: bool = True,
                 max_results: int = 10000,
                 connection_timeout: int = 30,
                 connection_manager: ConnectionManager = None):
        """
        Initialize MongoDB MCP client
        
        Args:
            connection_string: MongoDB connection string
            database_name: Default database name
            read_only: Enable read-only mode for safety
            max_results: Maximum number of results per query
            connection_timeout: Connection timeout in seconds
            connection_manager: Connection manager for MCP session
        """
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE_NAME")
        self.read_only = read_only
        self.max_results = max_results
        self.connection_timeout = connection_timeout
        self.connection_manager = connection_manager
        
        if not self.connection_string:
            raise ValueError("MongoDB connection string is required. Set MONGODB_CONNECTION_STRING environment variable.")
        
        self.mcp_server = None
        self._initialize_mcp_server()
    
    def _initialize_mcp_server(self):
        """Initialize MCP server connection"""
        try:
            env_vars = {
                "MDB_MCP_CONNECTION_STRING": self.connection_string,
                "MDB_MCP_READ_ONLY": str(self.read_only).lower(),
            }
            
            if self.database_name:
                env_vars["MDB_MCP_DATABASE_NAME"] = self.database_name
            
            self.mcp_server = MCPServerStdio(
                params={
                    "command": "npx",
                    "args": ["-y", "mongodb-mcp-server"],
                    "env": env_vars
                },
                name="mongodb_client",
                cache_tools_list=True  # Cache for performance
            )
            
            logger.info("MongoDB MCP server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB MCP server: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.mcp_server:
            await self.mcp_server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.mcp_server:
            await self.mcp_server.__aexit__(exc_type, exc_val, exc_tb)
    
    async def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            async with self:
                db_result = await self.list_databases()
                db_count = db_result.get("count", 0)
                logger.info(f"Connection test successful. Found {db_count} databases.")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _extract_text_content(self, content) -> str:
        """
        Helper method to extract text from MCP response content.
        Handles both TextContent objects and plain strings for backward compatibility.
        
        Args:
            content: The content from MCP response, can be string, list of strings, 
                    or list of TextContent objects
                    
        Returns:
            str: Extracted text content
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if hasattr(item, 'text'):
                    # This is a TextContent object
                    text_parts.append(item.text)
                elif isinstance(item, str):
                    # This is a plain string
                    text_parts.append(item)
                else:
                    # Convert to string as fallback
                    text_parts.append(str(item))
            return "\n".join(text_parts)
        else:
            return str(content)
    
    async def list_databases(self) -> Dict[str, Any]:
        """List available databases using MCP."""
        try:
            logger.info("Listing databases using MCP")
            
            async with self:
                result = await self.mcp_server.call_tool(
                    "list-databases",
                    {}
                )
                
                # Extract text content from the MCP response
                content_text = self._extract_text_content(result.content)
                
                # Parse the content based on format
                if isinstance(content_text, str):
                    try:
                        databases = json.loads(content_text)
                    except json.JSONDecodeError:
                        # If not JSON, split by lines and clean
                        databases = [db.strip() for db in content_text.split('\n') if db.strip()]
                else:
                    databases = content_text
                
                return {
                    "databases": databases,
                    "count": len(databases) if isinstance(databases, list) else 0
                }
            
        except Exception as e:
            logger.error(f"Error listing databases: {str(e)}")
            raise DatabaseConnectionError(f"Failed to list databases: {str(e)}")
    
    async def list_collections(self, database_name: Optional[str] = None) -> Dict[str, Any]:
        """List collections in a specific database using MCP."""
        # Use provided database name or fall back to instance default
        db_name = database_name or self.database_name
        
        if not db_name:
            raise ValueError("Database name is required. Either provide database_name parameter or set database_name in constructor.")
        
        try:
            logger.info(f"Listing collections in database: {db_name}")
            
            async with self:
                result = await self.mcp_server.call_tool(
                    "list-collections",
                    {"database": db_name}
                )
                
                # Extract text content from the MCP response
                content_text = self._extract_text_content(result.content)
                
                # Parse the content
                if isinstance(content_text, str):
                    try:
                        collections = json.loads(content_text)
                    except json.JSONDecodeError:
                        collections = [col.strip() for col in content_text.split('\n') if col.strip()]
                else:
                    collections = content_text
                
                return {
                    "collections": collections,
                    "database": db_name,
                    "count": len(collections) if isinstance(collections, list) else 0
                }
            
        except Exception as e:
            logger.error(f"Error listing collections in {db_name}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to list collections in database '{db_name}': {str(e)}")
    
    async def query_collection(self, database_name: str, collection_name: str, 
                             query: Dict[str, Any] = None, limit: int = 10) -> Dict[str, Any]:
        """Query a specific collection using MCP."""
        try:
            logger.info(f"Querying collection {collection_name} in {database_name}")
            
            # Prepare query parameters
            params = {
                "database": database_name,
                "collection": collection_name,
                "limit": limit
            }
            
            if query:
                params["query"] = json.dumps(query)
            
            async with self:
                result = await self.mcp_server.call_tool(
                    "find",
                    params
                )
                
                # Extract text content from the MCP response  
                content_text = self._extract_text_content(result.content)
                
                # Parse the result
                if isinstance(content_text, str):
                    try:
                        documents = json.loads(content_text)
                    except json.JSONDecodeError:
                        # If not JSON, return as text
                        documents = {"result": content_text}
                else:
                    documents = content_text
                
                return {
                    "documents": documents,
                    "database": database_name,
                    "collection": collection_name,
                    "query": query,
                    "limit": limit
                }
            
        except Exception as e:
            logger.error(f"Error querying collection {collection_name}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to query collection: {str(e)}")
    
    async def aggregate_collection(self,
                                 collection: str,
                                 pipeline: List[Dict],
                                 database: Optional[str] = None,
                                 limit: Optional[int] = None) -> str:
        """
        Perform aggregation on collection
        
        Args:
            collection: Collection name
            pipeline: MongoDB aggregation pipeline
            database: Database name (uses default if None)
            limit: Maximum number of results
            
        Returns:
            JSON string containing aggregation results
        """
        # Use provided database name or fall back to instance default
        db_name = database or self.database_name
        
        if not db_name:
            raise ValueError("Database name is required. Either provide database parameter or set database_name in constructor.")
        
        # Apply safety limits
        limit = min(limit or self.max_results, self.max_results)
        
        # Add limit stage to pipeline if not present
        if limit and not any('$limit' in stage for stage in pipeline):
            pipeline.append({"$limit": limit})
        
        try:
            async with self:
                result = await self.mcp_server.call_tool(
                    "aggregate",
                    {
                        "database": db_name,
                        "collection": collection,
                        "pipeline": pipeline
                    }
                )
                
                # Extract text content from the MCP response
                content_text = self._extract_text_content(result.content)
                
                # Parse the result
                if isinstance(content_text, str):
                    try:
                        # Try to parse as JSON first
                        data = json.loads(content_text)
                        json_result = json.dumps(data, default=str)
                        logger.info(f"Aggregation returned results from {db_name}.{collection}")
                        return json_result
                    except json.JSONDecodeError:
                        # If not JSON, return as string
                        logger.info(f"Aggregation returned text results from {db_name}.{collection}")
                        return content_text
                else:
                    json_result = json.dumps(content_text, default=str)
                    logger.info(f"Aggregation completed for {db_name}.{collection}")
                    return json_result
                
        except Exception as e:
            logger.error(f"Failed to aggregate collection {db_name}.{collection}: {e}")
            return json.dumps({"documents": [], "error": str(e)})
    
    async def count_documents(self,
                            collection: str,
                            filter_query: Optional[Dict] = None,
                            database: Optional[str] = None) -> int:
        """
        Count documents in collection
        
        Args:
            collection: Collection name
            filter_query: MongoDB filter query
            database: Database name (uses default if None)
            
        Returns:
            Document count
        """
        # Use provided database name or fall back to instance default
        db_name = database or self.database_name
        
        if not db_name:
            raise ValueError("Database name is required. Either provide database parameter or set database_name in constructor.")
        
        filter_query = filter_query or {}
        
        try:
            async with self:
                result = await self.mcp_server.call_tool(
                    "count",
                    {
                        "database": db_name,
                        "collection": collection,
                        "query": filter_query
                    }
                )
                
                # Extract text content from the MCP response
                content_text = self._extract_text_content(result.content)
                
                # Parse the result
                if isinstance(content_text, str):
                    try:
                        data = json.loads(content_text)
                        count = data.get("count", 0)
                    except json.JSONDecodeError:
                        # If not JSON, try to parse as integer
                        try:
                            count = int(content_text.strip())
                        except ValueError:
                            count = 0
                else:
                    count = content_text.get("count", 0) if isinstance(content_text, dict) else 0
                
                logger.debug(f"Count: {count} documents in {db_name}.{collection}")
                return count
                
        except Exception as e:
            logger.error(f"Failed to count documents in {db_name}.{collection}: {e}")
            return 0
    
    async def get_distinct_values(self,
                                collection: str,
                                field: str,
                                filter_query: Optional[Dict] = None,
                                database: Optional[str] = None) -> List:
        """
        Get distinct values for a field
        
        Args:
            collection: Collection name
            field: Field name
            filter_query: MongoDB filter query
            database: Database name (uses default if None)
            
        Returns:
            List of distinct values
        """
        # Use provided database name or fall back to instance default
        db_name = database or self.database_name
        
        if not db_name:
            raise ValueError("Database name is required. Either provide database parameter or set database_name in constructor.")
        
        filter_query = filter_query or {}
        
        try:
            async with self:
                result = await self.mcp_server.call_tool(
                    "find",
                    {
                        "database": db_name,
                        "collection": collection,
                        "query": filter_query,
                        "projection": {field: 1},
                        "distinct": field
                    }
                )
                
                # Extract text content from the MCP response
                content_text = self._extract_text_content(result.content)
                
                # Parse the result
                if isinstance(content_text, str):
                    try:
                        data = json.loads(content_text)
                        values = data.get("values", [])
                    except json.JSONDecodeError:
                        # If not JSON, try to parse as list
                        values = [content_text.strip()] if content_text.strip() else []
                else:
                    values = content_text.get("values", []) if isinstance(content_text, dict) else []
                
                logger.debug(f"Found {len(values)} distinct values for {field} in {db_name}.{collection}")
                return values
                
        except Exception as e:
            logger.error(f"Failed to get distinct values for {field} in {db_name}.{collection}: {e}")
            return []
    
    async def execute_database_reference(self, db_ref: DatabaseReference) -> str:
        """
        Execute a database operation based on DatabaseReference
        
        Args:
            db_ref: DatabaseReference object with operation details
            
        Returns:
            JSON string containing results
        """
        try:
            if db_ref.operation_type == "count":
                count = await self.count_documents(
                    collection=db_ref.collection,
                    filter_query=db_ref.filters,
                    database=db_ref.database
                )
                return json.dumps({"count": count, "collection": db_ref.collection})
            
            elif db_ref.operation_type == "distinct":
                # Extract field from filters if present
                field = db_ref.filters.pop("field", "_id")
                values = await self.get_distinct_values(
                    collection=db_ref.collection,
                    field=field,
                    filter_query=db_ref.filters,
                    database=db_ref.database
                )
                return json.dumps({"distinct_values": values, "field": field, "collection": db_ref.collection})
            
            elif db_ref.operation_type == "aggregate":
                # Build aggregation pipeline
                pipeline = []
                
                # Add match stage if filters present
                if db_ref.filters and any(k != "group_by" for k in db_ref.filters.keys()):
                    match_stage = {k: v for k, v in db_ref.filters.items() if k != "group_by"}
                    pipeline.append({"$match": match_stage})
                
                # Add group stage if group_by field specified
                if "group_by" in db_ref.filters:
                    group_field = db_ref.filters["group_by"]
                    pipeline.append({
                        "$group": {
                            "_id": f"${group_field}",
                            "count": {"$sum": 1}
                        }
                    })
                    pipeline.append({"$sort": {"count": -1}})
                
                return await self.aggregate_collection(
                    collection=db_ref.collection,
                    pipeline=pipeline,
                    database=db_ref.database,
                    limit=db_ref.limit
                )
            
            else:  # default to query
                result = await self.query_collection(
                    database_name=db_ref.database,
                    collection_name=db_ref.collection,
                    query=db_ref.filters,
                    limit=db_ref.limit or 10
                )
                # Return as JSON string to maintain compatibility
                return json.dumps(result, default=str)
                
        except Exception as e:
            logger.error(f"Failed to execute database reference: {e}")
            return json.dumps({"error": str(e), "operation": db_ref.operation_type, "collection": db_ref.collection})
    
    async def get_collection_sample(self, 
                                  collection: str, 
                                  sample_size: int = 5,
                                  database: Optional[str] = None) -> str:
        """
        Get a sample of documents from collection for schema inference
        
        Args:
            collection: Collection name
            sample_size: Number of sample documents
            database: Database name (uses default if None)
            
        Returns:
            JSON string containing sample documents
        """
        # Use provided database name or fall back to instance default
        db_name = database or self.database_name
        
        if not db_name:
            raise ValueError("Database name is required. Either provide database parameter or set database_name in constructor.")
        
        result = await self.query_collection(
            database_name=db_name,
            collection_name=collection,
            limit=sample_size
        )
        # Return as JSON string to maintain compatibility
        return json.dumps(result, default=str)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information for debugging
        
        Returns:
            Dictionary with connection details
        """
        return {
            "database_name": self.database_name,
            "read_only": self.read_only,
            "max_results": self.max_results,
            "connection_timeout": self.connection_timeout,
            "has_connection_string": bool(self.connection_string)
        }
