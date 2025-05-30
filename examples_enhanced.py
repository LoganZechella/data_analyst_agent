"""
Enhanced Data Analyzer Agent Examples

Demonstrates the full capabilities of the Enhanced Data Analyzer Agent
with MongoDB Atlas integration via MCP.
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import enhanced agent
from data_analyzer_agent.main_enhanced import (
    EnhancedDataAnalyzerAgent,
    create_enhanced_agent_with_fallback
)

async def example_1_database_collection_analysis():
    """Example 1: Analyze a complete database collection"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 1: Database Collection Analysis")
    print("="*60)
    
    # Create enhanced agent with fallback
    agent = create_enhanced_agent_with_fallback()
    
    query = "Analyze users collection and provide comprehensive insights on user engagement patterns, demographics, and activity levels"
    
    print(f"Query: {query}\n")
    
    # Stream the analysis
    async for event in agent.analyze_with_database(query=query, stream=True):
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        if event_type in ["database_detection", "database_query_start", "database_query_complete"]:
            print(f"🗄️ {message}")
            if event.get("collection"):
                print(f"   Collection: {event.get('collection')}")
        elif event_type == "response_done":
            print(f"✅ {message}")
            break
        elif event_type == "error":
            print(f"❌ {message}")
            break

async def example_2_filtered_database_query():
    """Example 2: Query database with filters"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 2: Filtered Database Query")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    query = "Get sales data where status = completed and amount > 1000, then analyze revenue trends and identify top customers"
    
    print(f"Query: {query}\n")
    
    async for event in agent.analyze_with_database(query=query, stream=True):
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        if event_type in ["database_query_start", "database_query_complete"]:
            print(f"📊 {message}")
            if event.get("data_size"):
                print(f"   Retrieved: {event.get('data_size')} records")
        elif event_type == "response_done":
            print(f"✅ {message}")
            break

async def example_3_aggregation_analysis():
    """Example 3: Aggregation operations"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 3: Aggregation Analysis")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    query = "Aggregate orders collection by customer_type and calculate average order value, total revenue, and customer count for each segment"
    
    print(f"Query: {query}\n")
    
    async for event in agent.analyze_with_database(query=query, stream=True):
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        if event_type == "database_query_start":
            print(f"🔄 {message}")
            operation = event.get("operation", "unknown")
            print(f"   Operation: {operation}")
        elif event_type == "response_code_interpreter_call_completed":
            print(f"💻 Code execution completed")
        elif event_type == "response_done":
            print(f"✅ {message}")
            break

async def example_4_time_based_analysis():
    """Example 4: Time-based data analysis"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 4: Time-Based Analysis")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    query = "Analyze transactions collection for the last 30 days and identify daily patterns, peak hours, and weekly trends"
    
    print(f"Query: {query}\n")
    
    async for event in agent.analyze_with_database(query=query, stream=True):
        if event.get("type") == "database_query_start":
            print(f"⏰ Querying transactions for last 30 days...")
        elif event.get("type") == "response_code_interpreter_call_in_progress":
            print(f"📈 Analyzing temporal patterns...")
        elif event.get("type") == "response_done":
            print(f"✅ Time-based analysis complete!")
            break

async def example_5_hybrid_data_analysis():
    """Example 5: Hybrid analysis with database and inline data"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 5: Hybrid Data Analysis")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    # Sample inline data
    inline_data = """product_id,external_price,external_rating
1,29.99,4.5
2,39.99,4.2
3,49.99,4.8
4,59.99,4.0
5,69.99,4.6"""
    
    query = "Compare this external pricing data with our products collection and identify pricing discrepancies and rating correlations"
    
    print(f"Query: {query}")
    print(f"Inline Data: {len(inline_data)} characters\n")
    
    async for event in agent.analyze_with_database(query=query, data=inline_data, stream=True):
        if event.get("type") == "database_query_start":
            print(f"🔄 Querying products collection...")
        elif event.get("type") == "analysis_start":
            print(f"🔗 Starting hybrid analysis...")
        elif event.get("type") == "response_done":
            print(f"✅ Hybrid analysis complete!")
            break

async def example_6_schema_discovery():
    """Example 6: Schema discovery and analysis recommendations"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 6: Schema Discovery")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    if hasattr(agent, 'discover_collection_schema'):
        print("🔍 Discovering schema for 'users' collection...")
        
        try:
            schema_info = await agent.discover_collection_schema("users")
            
            if "error" not in schema_info:
                print(f"✅ Schema discovered successfully!")
                print(f"   Collection: {schema_info.get('collection')}")
                print(f"   Fields: {len(schema_info.get('fields', {}))}")
                print(f"   Sample Size: {schema_info.get('sample_size', 0)}")
                
                # Show first few fields
                fields = schema_info.get('fields', {})
                print(f"   Top Fields:")
                for i, (field_name, field_info) in enumerate(list(fields.items())[:5]):
                    types = ", ".join(field_info.get('types', []))
                    presence = field_info.get('presence_ratio', 0) * 100
                    print(f"     • {field_name}: {types} ({presence:.1f}% present)")
                
                # Show recommendations
                recommendations = schema_info.get('analysis_recommendations', [])
                if recommendations:
                    print(f"   Analysis Recommendations:")
                    for rec in recommendations[:3]:
                        print(f"     • {rec}")
            else:
                print(f"❌ Schema discovery failed: {schema_info['error']}")
                
        except Exception as e:
            print(f"❌ Schema discovery error: {e}")
    else:
        print("⚠️ Schema discovery not available (database not enabled)")

async def example_7_performance_monitoring():
    """Example 7: Performance monitoring and optimization"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 7: Performance Monitoring")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    if hasattr(agent, 'get_database_status'):
        print("📊 Checking database status...")
        
        try:
            status = agent.get_database_status()
            print(f"✅ Database Status:")
            print(f"   Enabled: {status.get('database_enabled')}")
            print(f"   Connected: {status.get('connection_configured')}")
            print(f"   Database: {status.get('database_name')}")
            print(f"   Read-Only: {status.get('read_only')}")
            print(f"   Max Results: {status.get('max_results')}")
            
            # Test connection
            if hasattr(agent, 'test_database_connection'):
                print("\n🔗 Testing database connection...")
                is_connected = await agent.test_database_connection()
                print(f"   Connection Test: {'✅ Success' if is_connected else '❌ Failed'}")
                
                if is_connected and hasattr(agent, 'list_collections'):
                    print("\n📋 Listing collections...")
                    collections = await agent.list_collections()
                    if collections:
                        print(f"   Found {len(collections)} collections:")
                        for col in collections[:10]:  # Show first 10
                            print(f"     • {col}")
                        if len(collections) > 10:
                            print(f"     ... and {len(collections) - 10} more")
                    else:
                        print("   No collections found or access limited")
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
    else:
        print("⚠️ Database status not available")

async def example_8_error_handling():
    """Example 8: Error handling and fallback scenarios"""
    print("\n" + "="*60)
    print("📊 EXAMPLE 8: Error Handling and Fallback")
    print("="*60)
    
    agent = create_enhanced_agent_with_fallback()
    
    # Test with non-existent collection
    query = "Analyze nonexistent_collection and provide insights"
    
    print(f"Query: {query} (testing error handling)\n")
    
    async for event in agent.analyze_with_database(query=query, stream=True):
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        if event_type == "database_error":
            print(f"⚠️ Database Error (Expected): {message}")
            print("   Agent should gracefully handle this error")
        elif event_type == "response_done":
            print(f"✅ Error handling test complete")
            break

async def main():
    """Run all examples"""
    print("🚀 Enhanced Data Analyzer Agent - Comprehensive Examples")
    print("=" * 70)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found. Please set it in your .env file.")
        return
    
    db_configured = bool(os.getenv("MONGODB_CONNECTION_STRING"))
    print(f"🗄️ Database: {'Configured' if db_configured else 'Not configured'}")
    
    if not db_configured:
        print("⚠️ Some examples require database connectivity")
        print("   Set MONGODB_CONNECTION_STRING for full functionality")
    
    print("\n🎯 Running examples...")
    
    try:
        # Run examples
        await example_1_database_collection_analysis()
        await example_2_filtered_database_query()
        await example_3_aggregation_analysis()
        await example_4_time_based_analysis()
        await example_5_hybrid_data_analysis()
        await example_6_schema_discovery()
        await example_7_performance_monitoring()
        await example_8_error_handling()
        
        print("\n" + "="*70)
        print("🎉 All examples completed successfully!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
