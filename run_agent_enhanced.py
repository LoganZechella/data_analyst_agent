"""
Enhanced Data Analyzer Agent Runner with MongoDB Atlas Support

Demonstrates the enhanced Data Analyzer Agent using both OpenAI Responses API
and MongoDB Atlas connectivity via MCP. Showcases real-time streaming,
database operations, and enhanced analysis capabilities.
"""

from data_analyzer_agent.main_enhanced import (
    EnhancedDataAnalyzerAgent,
    enhanced_data_analyzer_agent, 
    enhanced_o4_analyzer_agent,
    create_enhanced_agent_with_fallback
)
import asyncio
import os
import logging
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedDataAnalyzerRunner:
    """
    Enhanced runner for the Data Analyzer Agent with MongoDB Atlas integration
    """
    
    def __init__(self, model_type: str = "standard", enable_database: bool = True):
        """
        Initialize the enhanced runner
        
        Args:
            model_type: "standard" or "reasoning"
            enable_database: Enable database connectivity
        """
        self.model_type = model_type
        self.enable_database = enable_database
        
        # Initialize agent based on configuration
        if enable_database:
            self.agents = {
                "standard": enhanced_data_analyzer_agent,
                "reasoning": enhanced_o4_analyzer_agent
            }
        else:
            # Fall back to standard agents if database disabled
            from data_analyzer_agent.main_responses_api import data_analyzer_agent, o4_analyzer_agent
            self.agents = {
                "standard": data_analyzer_agent,
                "reasoning": o4_analyzer_agent
            }
        
        self.current_agent = self.agents.get(model_type, self.agents["standard"])
        
        logger.info(f"Enhanced Data Analyzer Runner initialized - Model: {model_type}, Database: {'Enabled' if enable_database else 'Disabled'}")
    
    async def run_analysis(self, query: str, data: str = None, stream: bool = True) -> None:
        """
        Run analysis with enhanced capabilities
        
        Args:
            query: The analysis request
            data: Optional inline data string
            stream: Whether to show real-time progress
        """
        print(f"\n{'='*70}")
        print(f"🚀 ENHANCED DATA ANALYZER AGENT ({self.model_type.upper()})")
        print(f"{'='*70}")
        print(f"📊 Query: {query}")
        if data:
            print(f"📁 Inline data provided: {len(data)} characters")
        if self.enable_database:
            print(f"🗄️ Database connectivity: Enabled")
        print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        try:
            # Check API key
            if not os.getenv("OPENAI_API_KEY"):
                print("❌ Error: OPENAI_API_KEY not found. Please set it in your .env file.")
                return
            
            # Check database configuration if enabled
            if self.enable_database:
                if not os.getenv("MONGODB_CONNECTION_STRING"):
                    print("⚠️ Warning: MONGODB_CONNECTION_STRING not found. Database features will be limited.")
                    self.enable_database = False
                else:
                    print(f"🔗 Database: {os.getenv('MONGODB_DATABASE_NAME', 'Default')}")
            
            final_response = None
            analysis_complete = False
            
            # Run enhanced analysis with real-time updates
            if hasattr(self.current_agent, 'analyze_with_database') and self.enable_database:
                analysis_stream = self.current_agent.analyze_with_database(
                    query=query, 
                    data=data, 
                    stream=stream
                )
            else:
                analysis_stream = self.current_agent.analyze(
                    query=query, 
                    data=data, 
                    stream=stream
                )
            
            async for event in analysis_stream:
                self._display_enhanced_event(event)
                
                if event.get("final_response"):
                    analysis_complete = True
                    final_response = event
            
            if analysis_complete:
                print(f"\n{'='*70}")
                print("🎉 ENHANCED ANALYSIS COMPLETE!")
                print(f"{'='*70}")
                print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Show database context if available
                if hasattr(final_response, 'get') and final_response.get("database_context"):
                    db_context = final_response["database_context"]
                    print(f"🗄️ Database Context: {db_context.get('collection', 'N/A')}")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Analysis interrupted by user.")
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            print(f"\n❌ Error during analysis: {str(e)}")
            print("💡 Please check your configuration and network connection.")
    
    def _display_enhanced_event(self, event: dict) -> None:
        """
        Display enhanced streaming events with database context
        
        Args:
            event: Event dictionary from the analysis stream
        """
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        # Handle database-specific events
        if event_type == "database_detection":
            print(f"🔍 {message}")
            
        elif event_type == "database_query_start":
            collection = event.get("collection", "unknown")
            operation = event.get("operation", "query")
            confidence = event.get("confidence", 0.0)
            print(f"📊 {message}")
            print(f"   Collection: {collection}, Operation: {operation}, Confidence: {confidence:.2f}")
            
        elif event_type == "database_query_complete":
            data_size = event.get("data_size", 0)
            schema_fields = event.get("schema_fields", 0)
            print(f"✅ {message}")
            print(f"   Data points: {data_size}, Schema fields: {schema_fields}")
            
        elif event_type == "database_detection_complete":
            confidence = event.get("confidence", 0.0)
            print(f"💡 {message} (confidence: {confidence:.2f})")
            
        elif event_type == "database_error":
            error = event.get("error", "Unknown error")
            print(f"⚠️ {message}")
            print(f"   Error: {error}")
            
        elif event_type == "analysis_start":
            db_context = event.get("database_context", {})
            print(f"🚀 {message}")
            if db_context.get("collection"):
                print(f"   Database context: {db_context['collection']} ({db_context.get('operation_type', 'query')})")
        
        # Handle standard Responses API events with enhanced context
        elif event_type == "response_created":
            print(f"🚀 {message}")
            
        elif event_type == "response_code_interpreter_call_in_progress":
            print(f"🔄 {message}")
            if event.get("code"):
                code_preview = event['code'][:100] + '...' if len(event['code']) > 100 else event['code']
                print(f"   Code: {code_preview}")
                
        elif event_type == "response_code_interpreter_call_code_delta":
            # Limit code streaming output for readability
            if event.get("code_chunk"):
                chunk = event['code_chunk'][:50]
                print(f"📝 Code: {chunk}", end="", flush=True)
                
        elif event_type == "response_code_interpreter_call_interpreting":
            print(f"🧠 {message}")
            
        elif event_type == "response_code_interpreter_call_completed":
            print(f"✅ {message}")
            if event.get("output"):
                output = str(event["output"])[:300]
                print(f"   Output: {output}{'...' if len(str(event['output'])) > 300 else ''}")
                
        elif event_type == "response_reasoning_delta":
            # Show reasoning process (available with o4 models)
            if event.get("reasoning_chunk"):
                reasoning = event['reasoning_chunk'][:100]
                print(f"🤔 Reasoning: {reasoning}", end="", flush=True)
                
        elif event_type == "response_reasoning_done":
            print(f"💡 {message}")
            
        elif event_type == "response_content_part_added":
            print(f"📄 {message}")
            if event.get("content"):
                content = str(event["content"])[:400]
                print(f"   Content: {content}{'...' if len(str(event['content'])) > 400 else ''}")
                
        elif event_type == "response_output_item_added":
            print(f"📤 {message}")
            
        elif event_type == "response_done":
            print(f"🎉 {message}")
            
        elif event_type == "error":
            print(f"❌ Error: {event.get('error', 'Unknown error')}")

def get_enhanced_example_queries():
    """
    Get example queries showcasing enhanced database capabilities
    """
    return [
        {
            "name": "Database Collection Analysis",
            "query": "Analyze users collection and provide insights on user engagement patterns",
            "data": None,
            "description": "Demonstrates automatic database query and schema discovery",
            "requires_db": True
        },
        {
            "name": "Filtered Database Query",
            "query": "Get sales data where status = completed and analyze revenue trends",
            "data": None,
            "description": "Shows intelligent query parsing with filters",
            "requires_db": True
        },
        {
            "name": "Aggregation Analysis",
            "query": "Aggregate orders collection by customer_type and calculate average order value",
            "data": None,
            "description": "Demonstrates aggregation pipeline generation",
            "requires_db": True
        },
        {
            "name": "Time-Based Analysis",
            "query": "Analyze transactions collection for last 30 days and identify daily patterns",
            "data": None,
            "description": "Shows temporal query parsing and analysis",
            "requires_db": True
        },
        {
            "name": "Hybrid Data Analysis",
            "query": "Compare this CSV data with our products collection and identify discrepancies",
            "data": "product_id,name,price\n1,Widget A,29.99\n2,Widget B,39.99\n3,Widget C,49.99",
            "description": "Combines inline data with database queries",
            "requires_db": True
        },
        {
            "name": "Schema Discovery",
            "query": "Explore customers collection structure and recommend analysis approaches",
            "data": None,
            "description": "Demonstrates schema discovery and analysis recommendations",
            "requires_db": True
        },
        {
            "name": "Standard Inline Analysis",
            "query": "Analyze this sales data and calculate monthly growth rates",
            "data": "month,revenue\n2024-01,50000\n2024-02,52000\n2024-03,48000\n2024-04,55000\n2024-05,57000",
            "description": "Standard analysis without database (backward compatibility)",
            "requires_db": False
        }
    ]

async def run_enhanced_interactive_mode():
    """
    Run the enhanced agent in interactive mode with database capabilities
    """
    print("\n🤖 ENHANCED DATA ANALYZER AGENT - MONGODB ATLAS INTEGRATION")
    print("=" * 70)
    
    # Check database configuration
    db_available = bool(os.getenv("MONGODB_CONNECTION_STRING"))
    if db_available:
        db_name = os.getenv("MONGODB_DATABASE_NAME", "Default")
        print(f"🗄️ Database: Connected to {db_name}")
    else:
        print("⚠️ Database: Not configured (set MONGODB_CONNECTION_STRING)")
    
    print("\nAvailable models:")
    print("1. Standard (GPT-4.1) - Enhanced balanced performance")
    print("2. Reasoning (o4-mini) - Advanced reasoning with transparency")
    print()
    
    # Model selection
    while True:
        try:
            choice = input("Select model (1-2): ").strip()
            model_map = {"1": "standard", "2": "reasoning"}
            if choice in model_map:
                model_type = model_map[choice]
                break
            else:
                print("Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return
    
    runner = EnhancedDataAnalyzerRunner(model_type=model_type, enable_database=db_available)
    
    model_details = {
        "standard": "GPT-4.1 - Enhanced performance with database connectivity",
        "reasoning": "o4-mini - Advanced reasoning with database awareness"
    }
    
    print(f"\n✅ Using {model_type} model: {model_details[model_type]}")
    print("\nCommands:")
    print("• Type your analysis request")
    print("• 'examples' - show example queries")
    print("• 'collections' - list available database collections (if DB enabled)")
    print("• 'schema [collection]' - discover collection schema")
    print("• 'status' - show database status")
    print("• 'quit' - exit")
    print()

    while True:
        try:
            user_input = input("📊 Your analysis request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'examples':
                print("\n📚 Enhanced Example Queries:")
                examples = get_enhanced_example_queries()
                for i, example in enumerate(examples, 1):
                    db_req = "🗄️ " if example['requires_db'] else "📄 "
                    print(f"\n{i}. {db_req}{example['name']}")
                    print(f"   Description: {example['description']}")
                    print(f"   Query: {example['query'][:80]}...")
                    
                # Allow user to select an example
                try:
                    example_choice = input("\nSelect example (1-7) or press Enter to continue: ").strip()
                    if example_choice and example_choice.isdigit():
                        idx = int(example_choice) - 1
                        if 0 <= idx < len(examples):
                            example = examples[idx]
                            if example['requires_db'] and not db_available:
                                print("⚠️ This example requires database connectivity")
                                continue
                            print(f"\n🚀 Running example: {example['name']}")
                            await runner.run_analysis(example['query'], example['data'])
                except (ValueError, KeyboardInterrupt):
                    continue
                continue
            
            elif user_input.lower() == 'collections':
                if not db_available:
                    print("⚠️ Database connectivity not available")
                    continue
                    
                print("🗄️ Listing database collections...")
                try:
                    collections = await runner.current_agent.list_collections()
                    if collections:
                        print(f"Found {len(collections)} collections:")
                        for i, collection in enumerate(collections, 1):
                            print(f"  {i}. {collection}")
                    else:
                        print("No collections found or unable to access database")
                except Exception as e:
                    print(f"❌ Error listing collections: {e}")
                continue
            
            elif user_input.lower().startswith('schema '):
                if not db_available:
                    print("⚠️ Database connectivity not available")
                    continue
                    
                collection_name = user_input[7:].strip()
                if not collection_name:
                    print("Usage: schema [collection_name]")
                    continue
                    
                print(f"🔍 Discovering schema for {collection_name}...")
                try:
                    schema_info = await runner.current_agent.discover_collection_schema(collection_name)
                    if "error" in schema_info:
                        print(f"❌ Error: {schema_info['error']}")
                    else:
                        print(f"✅ Schema discovered for {collection_name}:")
                        fields = schema_info.get("fields", {})
                        print(f"   Fields: {len(fields)}")
                        for field_name, field_info in list(fields.items())[:5]:
                            types = ", ".join(field_info.get("types", []))
                            presence = field_info.get("presence_ratio", 0) * 100
                            print(f"   • {field_name}: {types} ({presence:.1f}% present)")
                        if len(fields) > 5:
                            print(f"   ... and {len(fields) - 5} more fields")
                except Exception as e:
                    print(f"❌ Error discovering schema: {e}")
                continue
            
            elif user_input.lower() == 'status':
                print("📊 System Status:")
                print(f"   Model: {model_type}")
                print(f"   Database: {'Enabled' if db_available else 'Disabled'}")
                if db_available:
                    try:
                        is_connected = await runner.current_agent.test_database_connection()
                        print(f"   Connection: {'✅ Active' if is_connected else '❌ Failed'}")
                        status = runner.current_agent.get_database_status()
                        print(f"   Database Name: {status.get('database_name', 'N/A')}")
                        print(f"   Read-Only: {status.get('read_only', 'N/A')}")
                    except Exception as e:
                        print(f"   Connection: ❌ Error - {e}")
                continue
                
            elif not user_input:
                continue
                
            # Check if user provided inline data
            data = None
            if "data:" in user_input.lower():
                parts = user_input.split("data:", 1)
                if len(parts) == 2:
                    user_input = parts[0].strip()
                    data = parts[1].strip()
            
            # Run the analysis
            await runner.run_analysis(user_input, data)
            print("\n" + "-"*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

async def run_enhanced_example_queries():
    """
    Run enhanced example queries to demonstrate capabilities
    """
    examples = get_enhanced_example_queries()
    db_available = bool(os.getenv("MONGODB_CONNECTION_STRING"))
    
    print("🧪 Running Enhanced Example Queries")
    print("=" * 50)
    
    # Filter examples based on database availability
    available_examples = [ex for ex in examples if not ex['requires_db'] or db_available]
    
    if not db_available:
        print("⚠️ Database examples will be skipped (no MONGODB_CONNECTION_STRING)")
    
    runner = EnhancedDataAnalyzerRunner("standard", enable_database=db_available)
    
    for i, example in enumerate(available_examples, 1):
        db_indicator = "🗄️ " if example['requires_db'] else "📄 "
        print(f"\n{db_indicator}Example {i}: {example['name']}")
        print(f"Description: {example['description']}")
        print("Query:", example['query'][:100] + "..." if len(example['query']) > 100 else example['query'])
        print("-" * 50)
        
        await runner.run_analysis(example['query'], example['data'])
        
        print("✅ Example completed")
        print("\n" + "="*50)
        
        # Ask user if they want to continue
        if i < len(available_examples):
            try:
                continue_choice = input("\nContinue to next example? (y/n): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    break
            except KeyboardInterrupt:
                print("\n👋 Stopping examples.")
                break

def main():
    """
    Main entry point for the enhanced runner
    """
    print("🚀 ENHANCED DATA ANALYZER AGENT")
    print("=" * 40)
    
    # Check environment setup
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment.")
        print("Please add your OpenAI API key to the .env file.")
        return
    
    # Check database configuration
    db_configured = bool(os.getenv("MONGODB_CONNECTION_STRING"))
    if db_configured:
        db_name = os.getenv("MONGODB_DATABASE_NAME", "Default")
        print(f"✅ Database: Connected to {db_name}")
    else:
        print("⚠️ Database: Not configured (optional)")
        print("Set MONGODB_CONNECTION_STRING for database features")
    
    print("📋 Available models: GPT-4.1 (standard), o4-mini (reasoning)")
    print()
    
    while True:
        print("Choose an option:")
        print("1. Interactive mode (enter custom queries)")
        print("2. Run enhanced example queries")
        print("3. Database connection test")
        print("4. Quick test query")
        print("5. Exit")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                asyncio.run(run_enhanced_interactive_mode())
            elif choice == '2':
                asyncio.run(run_enhanced_example_queries())
            elif choice == '3':
                if not db_configured:
                    print("❌ Database not configured. Please set MONGODB_CONNECTION_STRING.")
                    continue
                    
                print("🔗 Testing database connection...")
                try:
                    # Create agent and test connection
                    agent = create_enhanced_agent_with_fallback()
                    if hasattr(agent, 'test_database_connection'):
                        is_connected = asyncio.run(agent.test_database_connection())
                        if is_connected:
                            print("✅ Database connection successful!")
                            
                            # Try to list collections
                            collections = asyncio.run(agent.list_collections())
                            if collections:
                                print(f"📊 Found {len(collections)} collections: {', '.join(collections[:5])}")
                                if len(collections) > 5:
                                    print(f"   ... and {len(collections) - 5} more")
                            else:
                                print("📊 No collections found or limited permissions")
                        else:
                            print("❌ Database connection failed")
                    else:
                        print("⚠️ Database features not available")
                except Exception as e:
                    print(f"❌ Connection test error: {e}")
                    
            elif choice == '4':
                runner = EnhancedDataAnalyzerRunner("standard", enable_database=db_configured)
                test_query = "Calculate the sum and average of these numbers: 10, 20, 30, 40, 50"
                print(f"\n🧪 Quick test: {test_query}")
                asyncio.run(runner.run_analysis(test_query))
                
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
