"""
Test suite for Enhanced Data Analyzer Agent MongoDB Atlas integration

Tests database connectivity, query parsing, schema discovery, and
enhanced analysis capabilities.
"""

import pytest
import asyncio
import os
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the modules to test
from data_analyzer_agent.database.query_parser import QueryParser, DatabaseReference
from data_analyzer_agent.database.mongodb_client import DatabaseQueryProcessor
from data_analyzer_agent.database.schema_manager import SchemaManager
from data_analyzer_agent.database.connection_manager import ConnectionManager, ConnectionConfig
from data_analyzer_agent.main_enhanced import EnhancedDataAnalyzerAgent

class TestQueryParser:
    """Test suite for query parsing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = QueryParser()
    
    def test_needs_database_query_positive_cases(self):
        """Test detection of queries that need database access"""
        test_cases = [
            "analyze users collection",
            "get data from orders",
            "query products where status = active",
            "aggregate sales by month",
            "count customers by region",
            "examine inventory records"
        ]
        
        for query in test_cases:
            assert self.parser.needs_database_query(query), f"Should detect database need in: {query}"
    
    def test_needs_database_query_negative_cases(self):
        """Test detection of queries that don't need database access"""
        test_cases = [
            "calculate the sum of 1, 2, 3",
            "create a simple chart",
            "what is machine learning",
            "help me with statistics",
            "generate random numbers"
        ]
        
        for query in test_cases:
            assert not self.parser.needs_database_query(query), f"Should not detect database need in: {query}"
    
    def test_extract_collection_name(self):
        """Test collection name extraction"""
        test_cases = [
            ("analyze users collection", "users"),
            ("get data from orders", "orders"),
            ("query products where status = active", "products"),
            ("customers with age > 25", "customers"),
            ("aggregate sales by month", "sales")
        ]
        
        for query, expected_collection in test_cases:
            db_ref = self.parser.extract_database_references(query)
            assert db_ref is not None, f"Should extract reference from: {query}"
            assert db_ref.collection == expected_collection, f"Expected {expected_collection}, got {db_ref.collection}"
    
    def test_extract_filters(self):
        """Test filter extraction from queries"""
        test_cases = [
            ("users where status = active", {"status": "active"}),
            ("orders where amount > 100", {"amount": 100}),
            ("products where price = 29.99", {"price": 29.99}),
            ("customers where active = true", {"active": True})
        ]
        
        for query, expected_filters in test_cases:
            db_ref = self.parser.extract_database_references(query)
            assert db_ref is not None
            for key, value in expected_filters.items():
                assert key in db_ref.filters
                assert db_ref.filters[key] == value
    
    def test_extract_operation_types(self):
        """Test operation type detection"""
        test_cases = [
            ("count users by status", "aggregate"),
            ("aggregate sales by month", "aggregate"),
            ("group orders by customer", "aggregate"),
            ("get distinct products", "distinct"),
            ("query users collection", "query")
        ]
        
        for query, expected_operation in test_cases:
            db_ref = self.parser.extract_database_references(query)
            assert db_ref is not None
            assert db_ref.operation_type == expected_operation
    
    def test_extract_time_ranges(self):
        """Test time range extraction"""
        test_cases = [
            "orders in last 30 days",
            "sales since 2024-01-01",
            "transactions between 2024-01-01 and 2024-12-31"
        ]
        
        for query in test_cases:
            db_ref = self.parser.extract_database_references(query)
            assert db_ref is not None
            # Check that some time filter was extracted
            time_fields = [key for key in db_ref.filters.keys() if 'time' in key.lower() or 'date' in key.lower() or 'created' in key.lower()]
            assert len(time_fields) > 0 or 'created_at' in db_ref.filters
    
    def test_get_suggested_collections(self):
        """Test collection name suggestions"""
        test_cases = [
            ("analyze user data", ["users", "user_profiles", "accounts", "customers"]),
            ("examine order information", ["orders", "purchases", "transactions", "sales"]),
            ("review product catalog", ["products", "items", "inventory", "catalog"])
        ]
        
        for query, expected_collections in test_cases:
            suggestions = self.parser.get_suggested_collections(query)
            # Check that at least some expected collections are suggested
            overlap = set(suggestions) & set(expected_collections)
            assert len(overlap) > 0, f"Expected overlap between {suggestions} and {expected_collections}"

class TestDatabaseQueryProcessor:
    """Test suite for database query processing"""
    
    def setup_method(self):
        """Setup test fixtures with mocked components"""
        self.mock_connection_string = "mongodb://localhost:27017/test"
        self.mock_database_name = "test_db"
    
    @patch('data_analyzer_agent.database.mongodb_client.MCPServerStdio')
    def test_initialization(self, mock_mcp_server):
        """Test DatabaseQueryProcessor initialization"""
        processor = DatabaseQueryProcessor(
            connection_string=self.mock_connection_string,
            database_name=self.mock_database_name
        )
        
        assert processor.connection_string == self.mock_connection_string
        assert processor.database_name == self.mock_database_name
        assert processor.read_only is True
        assert processor.max_results == 10000
        mock_mcp_server.assert_called_once()
    
    @patch('data_analyzer_agent.database.mongodb_client.MCPServerStdio')
    async def test_query_collection(self, mock_mcp_server):
        """Test collection querying"""
        # Setup mock
        mock_server_instance = Mock()
        mock_server_instance.call_tool = AsyncMock()
        mock_server_instance.call_tool.return_value = Mock(output='{"documents": [{"_id": "1", "name": "test"}]}')
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_server.return_value = mock_server_instance
        
        processor = DatabaseQueryProcessor(
            connection_string=self.mock_connection_string,
            database_name=self.mock_database_name
        )
        
        result = await processor.query_collection("test_collection")
        
        assert isinstance(result, str)
        assert "test" in result
        mock_server_instance.call_tool.assert_called_once()
    
    @patch('data_analyzer_agent.database.mongodb_client.MCPServerStdio')
    async def test_execute_database_reference(self, mock_mcp_server):
        """Test database reference execution"""
        # Setup mock
        mock_server_instance = Mock()
        mock_server_instance.call_tool = AsyncMock()
        mock_server_instance.call_tool.return_value = Mock(output='{"documents": [{"_id": "1"}]}')
        mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
        mock_server_instance.__aexit__ = AsyncMock(return_value=None)
        mock_mcp_server.return_value = mock_server_instance
        
        processor = DatabaseQueryProcessor(
            connection_string=self.mock_connection_string,
            database_name=self.mock_database_name
        )
        
        db_ref = DatabaseReference(
            collection="test_collection",
            operation_type="query",
            filters={"status": "active"}
        )
        
        result = await processor.execute_database_reference(db_ref)
        assert isinstance(result, str)
        mock_server_instance.call_tool.assert_called_once()

class TestSchemaManager:
    """Test suite for schema management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db_client = Mock()
        self.schema_manager = SchemaManager(self.mock_db_client)
    
    async def test_discover_collection_schema(self):
        """Test schema discovery"""
        # Mock sample data
        sample_documents = [
            {"_id": "1", "name": "John", "age": 30, "email": "john@example.com"},
            {"_id": "2", "name": "Jane", "age": 25, "email": "jane@example.com"},
            {"_id": "3", "name": "Bob", "age": 35, "active": True}
        ]
        
        self.mock_db_client.get_collection_sample = AsyncMock()
        self.mock_db_client.get_collection_sample.return_value = json.dumps({"documents": sample_documents})
        self.mock_db_client.database_name = "test_db"
        
        schema_info = await self.schema_manager.discover_collection_schema("test_collection")
        
        assert "fields" in schema_info
        assert "name" in schema_info["fields"]
        assert "age" in schema_info["fields"]
        assert "email" in schema_info["fields"]
        assert schema_info["sample_size"] == 3
        
        # Check field analysis
        name_field = schema_info["fields"]["name"]
        assert name_field["presence_ratio"] == 1.0  # Present in all documents
        assert "str" in name_field["types"]
        
        age_field = schema_info["fields"]["age"]
        assert age_field["presence_ratio"] == 1.0
        assert "int" in age_field["types"]
    
    def test_analyze_fields(self):
        """Test field analysis functionality"""
        documents = [
            {"name": "John", "age": 30, "tags": ["dev", "python"]},
            {"name": "Jane", "age": 25, "active": True},
            {"name": "Bob", "location": {"city": "NYC", "state": "NY"}}
        ]
        
        fields = self.schema_manager._analyze_fields(documents)
        
        assert "name" in fields
        assert fields["name"]["presence_ratio"] == 1.0
        assert "str" in fields["name"]["types"]
        
        assert "age" in fields
        assert fields["age"]["presence_ratio"] == 2/3  # Present in 2 out of 3 docs
        
        assert "tags" in fields
        assert fields["tags"]["is_array"] is True
        
        assert "location.city" in fields  # Nested field
        assert fields["location.city"]["is_nested"] is False  # It's a leaf node
        assert "location" in fields
        assert fields["location"]["is_nested"] is True

class TestConnectionManager:
    """Test suite for connection management"""
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        config = ConnectionConfig(
            connection_string="mongodb://localhost:27017",
            database_name="test_db",
            read_only=True
        )
        
        manager = ConnectionManager(config)
        
        assert manager.config.connection_string == "mongodb://localhost:27017"
        assert manager.config.database_name == "test_db"
        assert manager.config.read_only is True
    
    @patch.dict(os.environ, {
        'MONGODB_CONNECTION_STRING': 'mongodb://localhost:27017',
        'MONGODB_DATABASE_NAME': 'test_db',
        'MONGODB_READ_ONLY': 'true'
    })
    def test_config_from_environment(self):
        """Test configuration loading from environment"""
        manager = ConnectionManager()
        
        assert manager.config.connection_string == "mongodb://localhost:27017"
        assert manager.config.database_name == "test_db"
        assert manager.config.read_only is True

class TestEnhancedDataAnalyzerAgent:
    """Test suite for enhanced agent functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_connection_string = "mongodb://localhost:27017/test"
    
    @patch('data_analyzer_agent.main_enhanced.ConnectionManager')
    @patch('data_analyzer_agent.main_enhanced.QueryParser')
    def test_initialization_with_database(self, mock_query_parser, mock_connection_manager):
        """Test enhanced agent initialization with database enabled"""
        agent = EnhancedDataAnalyzerAgent(
            mongodb_connection=self.mock_connection_string,
            enable_database=True
        )
        
        assert agent.enable_database is True
        assert agent.mongodb_connection == self.mock_connection_string
        mock_connection_manager.assert_called_once()
        mock_query_parser.assert_called_once()
    
    def test_initialization_without_database(self):
        """Test enhanced agent initialization with database disabled"""
        agent = EnhancedDataAnalyzerAgent(enable_database=False)
        
        assert agent.enable_database is False
        assert agent.db_processor is None
        assert agent.query_parser is None
    
    @patch('data_analyzer_agent.main_enhanced.ConnectionManager')
    @patch('data_analyzer_agent.main_enhanced.QueryParser') 
    async def test_analyze_with_database_detection(self, mock_query_parser, mock_connection_manager):
        """Test analysis with database query detection"""
        # Setup mocks
        mock_parser_instance = Mock()
        mock_parser_instance.extract_database_references.return_value = DatabaseReference(
            collection="users",
            operation_type="query",
            confidence=0.8
        )
        mock_query_parser.return_value = mock_parser_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.get_client = AsyncMock()
        mock_connection_manager.return_value = mock_manager_instance
        
        agent = EnhancedDataAnalyzerAgent(
            mongodb_connection=self.mock_connection_string,
            enable_database=True
        )
        
        # Mock the parent analyze method
        with patch.object(agent.__class__.__bases__[0], 'analyze') as mock_parent_analyze:
            mock_parent_analyze.return_value = iter([
                {"type": "response_created", "message": "Analysis started"}
            ])
            
            # Mock database operations
            agent._execute_database_query = AsyncMock(return_value=(
                '{"documents": [{"_id": "1", "name": "test"}]}',
                {"fields": {"name": {"types": ["str"]}}}
            ))
            
            events = []
            async for event in agent.analyze_with_database("analyze users collection"):
                events.append(event)
                # Break after a few events to avoid infinite loop in test
                if len(events) > 5:
                    break
            
            # Verify that database detection events were generated
            event_types = [event.get("type") for event in events]
            assert "database_detection" in event_types
    
    def test_get_database_status(self):
        """Test database status reporting"""
        agent = EnhancedDataAnalyzerAgent(
            mongodb_connection=self.mock_connection_string,
            enable_database=True
        )
        
        status = agent.get_database_status()
        
        assert "database_enabled" in status
        assert "connection_configured" in status
        assert status["database_enabled"] is True
        assert status["connection_configured"] is True

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_mock(self):
        """Test complete workflow with mocked components"""
        # This test would require extensive mocking but demonstrates the concept
        with patch('data_analyzer_agent.database.mongodb_client.MCPServerStdio') as mock_mcp:
            mock_server_instance = Mock()
            mock_server_instance.__aenter__ = AsyncMock(return_value=mock_server_instance)
            mock_server_instance.__aexit__ = AsyncMock(return_value=None)
            mock_server_instance.call_tool = AsyncMock()
            mock_server_instance.call_tool.return_value = Mock(
                output='{"documents": [{"_id": "1", "name": "test", "age": 25}]}'
            )
            mock_mcp.return_value = mock_server_instance
            
            # Create enhanced agent
            agent = EnhancedDataAnalyzerAgent(
                mongodb_connection="mongodb://localhost:27017",
                enable_database=True
            )
            
            # Mock the parent analyze method
            with patch.object(agent.__class__.__bases__[0], 'analyze') as mock_parent_analyze:
                mock_parent_analyze.return_value = iter([
                    {"type": "response_done", "message": "Analysis complete", "final_response": True}
                ])
                
                # Test the workflow
                events = []
                async for event in agent.analyze_with_database("analyze users collection"):
                    events.append(event)
                    if event.get("final_response"):
                        break
                
                # Verify workflow progression
                assert len(events) > 0
                assert any(event.get("type") == "database_detection" for event in events)

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
