"""
Database module for Data Analyzer Agent

Provides MongoDB Atlas integration via Model Context Protocol (MCP).
Enables direct database connectivity while maintaining the simplified
Responses API architecture.
"""

from .mongodb_client import DatabaseQueryProcessor
from .query_parser import QueryParser
from .schema_manager import SchemaManager
from .connection_manager import ConnectionManager

__all__ = [
    "DatabaseQueryProcessor",
    "QueryParser", 
    "SchemaManager",
    "ConnectionManager"
]

__version__ = "1.0.0"
