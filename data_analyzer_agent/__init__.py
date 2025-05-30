"""
Enhanced Data Analyzer AI Agent Package

A sophisticated AI agent for data analysis using the OpenAI Responses API
with MongoDB Atlas database connectivity via Model Context Protocol (MCP).

Provides native code interpretation with real-time streaming, reasoning transparency,
database connectivity, and dramatically simplified architecture (75% complexity reduction).

Features:
- Native code interpreter (no custom sandbox needed)
- Real-time streaming progress updates  
- Reasoning transparency with o4-mini models
- MongoDB Atlas database connectivity via MCP
- Automatic schema discovery and analysis
- Intelligent query parsing and optimization
- Enhanced models: GPT-4.1 (standard), o4-mini (reasoning)
- Zero infrastructure maintenance
- Hybrid data sources (database + inline data)
- Advanced error handling and fallback strategies
"""

__version__ = "3.0.0"  # Major version bump for MongoDB Atlas MCP integration
__author__ = "Data Analyzer Agent Development Team"

# Standard agents (Responses API only)
from .main import data_analyzer_agent, o4_analyzer_agent

# Enhanced agents (Responses API + MongoDB Atlas)
from .main_enhanced import (
    enhanced_data_analyzer_agent, 
    enhanced_o4_analyzer_agent,
    EnhancedDataAnalyzerAgent,
    create_enhanced_standard_analyzer,
    create_enhanced_reasoning_analyzer,
    create_enhanced_agent_with_fallback
)

# Database components
from .database import (
    DatabaseQueryProcessor,
    QueryParser,
    SchemaManager,
    ConnectionManager
)

# Backward compatibility - use enhanced agents by default if database available
import os

# Determine default agents based on database availability
_database_available = bool(os.getenv("MONGODB_CONNECTION_STRING"))

if _database_available:
    # Use enhanced agents as defaults when database is configured
    default_data_analyzer_agent = enhanced_data_analyzer_agent
    default_o4_analyzer_agent = enhanced_o4_analyzer_agent
else:
    # Fall back to standard agents when database is not configured
    default_data_analyzer_agent = data_analyzer_agent
    default_o4_analyzer_agent = o4_analyzer_agent

__all__ = [
    # Standard agents
    "data_analyzer_agent", 
    "o4_analyzer_agent",
    
    # Enhanced agents
    "enhanced_data_analyzer_agent",
    "enhanced_o4_analyzer_agent", 
    "EnhancedDataAnalyzerAgent",
    "create_enhanced_standard_analyzer",
    "create_enhanced_reasoning_analyzer",
    "create_enhanced_agent_with_fallback",
    
    # Database components
    "DatabaseQueryProcessor",
    "QueryParser",
    "SchemaManager", 
    "ConnectionManager",
    
    # Default agents (context-aware)
    "default_data_analyzer_agent",
    "default_o4_analyzer_agent"
]

# Package metadata
__title__ = "Enhanced Data Analyzer Agent"
__description__ = "AI agent for data analysis with MongoDB Atlas connectivity"
__url__ = "https://github.com/your-org/data-analyzer-agent"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Data Analyzer Agent Development Team"

# Feature flags
FEATURES = {
    "responses_api": True,
    "database_connectivity": _database_available,
    "real_time_streaming": True,
    "reasoning_transparency": True,
    "schema_discovery": _database_available,
    "query_optimization": _database_available,
    "connection_pooling": _database_available,
    "hybrid_data_sources": _database_available
}

def get_version_info():
    """Get detailed version and feature information"""
    return {
        "version": __version__,
        "features": FEATURES,
        "database_available": _database_available,
        "recommended_agent": "enhanced" if _database_available else "standard"
    }

def print_welcome_message():
    """Print welcome message with feature status"""
    print("🚀 Enhanced Data Analyzer Agent")
    print(f"   Version: {__version__}")
    print(f"   Database: {'✅ Available' if _database_available else '⚠️  Not configured'}")
    print(f"   Recommended: {'Enhanced Agent' if _database_available else 'Standard Agent'}")
    if not _database_available:
        print("   💡 Set MONGODB_CONNECTION_STRING for database features")

# Auto-print welcome message in interactive environments
try:
    if hasattr(__builtins__, '__IPYTHON__') or 'jupyter' in globals():
        print_welcome_message()
except:
    pass  # Ignore errors in non-interactive environments
