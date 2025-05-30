"""
Data Analyzer Agent Runner

This script demonstrates how to run the Data Analyzer Agent with various
analysis tasks. It provides examples and testing capabilities for the agent.
"""

from data_analyzer_agent.main import data_analyzer_agent, gpt4_turbo_analyzer_agent, o1_analyzer_agent
from agents import Runner, set_tracing_disabled
import asyncio
import os
import logging
from dotenv import load_dotenv
import json

# Load environment variables from .env file (e.g., OPENAI_API_KEY, PYTHON_SANDBOX_API_URL)
load_dotenv()

# Configure logging for the run script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optionally disable OpenAI's default tracing if not configured or desired for local runs
# set_tracing_disabled(True)
# Or configure Langfuse/other OTel exporter for tracing

async def run_analysis_task(user_query: str, agent=None):
    """
    Runs the Data Analyzer agent with a given user query.
    
    Args:
        user_query: The analysis request from the user
        agent: Optional specific agent instance to use (defaults to data_analyzer_agent)
    
    Returns:
        The result from the agent execution
    """
    if agent is None:
        agent = data_analyzer_agent
        
    logger.info(f"Initiating Data Analyzer agent run with query: '{user_query[:100]}...'")

    # Ensure OPENAI_API_KEY is available (usually handled by SDK if set in env)
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set. Please set it in your .env file or environment.")
        print("❌ Error: OPENAI_API_KEY is not configured. Please:")
        print("1. Copy .env.template to .env")
        print("2. Add your OpenAI API key to the .env file")
        print("3. Ensure the sandbox server is running: uvicorn sandbox_server.main:app --reload --port 8000")
        return None

    # Check if sandbox server is configured
    sandbox_url = os.getenv("PYTHON_SANDBOX_API_URL", "http://localhost:8000")
    logger.info(f"Using sandbox server at: {sandbox_url}")

    try:
        # The Runner.run() method orchestrates the agent's execution.
        # It handles the interaction loop with the LLM, tool calls, etc.
        result = await Runner.run(starting_agent=agent, input=user_query)

        logger.info("Agent run completed.")
        print("\\n" + "="*60)
        print("🎯 ANALYSIS COMPLETE")
        print("="*60)
        
        if result.final_output:
            print(result.final_output)
        else:
            logger.warning("Agent did not produce a final output. Check logs/trace for details.")
            print("⚠️  Agent did not produce a final output. Check logs for details.")

        # For debugging, you can inspect the full history:
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            print("\\n" + "-"*60)
            print("🔍 DEBUG: Execution Trace")
            print("-"*60)
            for i, message in enumerate(result.history[-5:]):  # Show last 5 messages
                role = getattr(message, 'role', 'system_internal')
                content_summary = str(getattr(message, 'content', ''))[:200] if hasattr(message, 'content') else ""
                print(f"Step {i+1} - {role}: {content_summary}...")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tc in message.tool_calls:
                        print(f"  🔧 Tool: {tc.function.name}")
                if hasattr(message, 'tool_outputs') and message.tool_outputs:
                    for to in message.tool_outputs:
                        output_summary = str(to.output)[:200] if to.output else ""
                        print(f"  📤 Output: {output_summary}...")

        return result
    except Exception as e:
        logger.error(f"An error occurred during the agent run: {str(e)}", exc_info=True)
        print(f"❌ An error occurred: {str(e)}")
        print("\\n💡 Troubleshooting tips:")
        print("1. Ensure the sandbox server is running: uvicorn sandbox_server.main:app --reload --port 8000")
        print("2. Check your .env file has OPENAI_API_KEY set")
        print("3. Verify network connectivity to OpenAI API and sandbox server")
        return None

def get_example_queries():
    """
    Returns a list of example queries for testing the agent.
    """
    return [
        {
            "name": "Simple CSV Analysis",
            "query": "I have data as a CSV string: 'name,age,city\\nAlice,25,New York\\nBob,30,Los Angeles\\nCharlie,35,Chicago'. Load this data and calculate the average age. Also tell me how many unique cities are in the dataset.",
            "description": "Basic data loading and simple statistics"
        },
        {
            "name": "JSON Data Processing",
            "query": "I have sales data as JSON: '[{\"product\":\"Apple\",\"sales\":100,\"region\":\"North\"},{\"product\":\"Banana\",\"sales\":150,\"region\":\"South\"},{\"product\":\"Apple\",\"sales\":120,\"region\":\"South\"}]'. Calculate total sales by product and create a summary report.",
            "description": "JSON processing and aggregation"
        },
        {
            "name": "Statistical Analysis",
            "query": "Generate 100 random numbers from a normal distribution with mean=50 and std=10. Calculate descriptive statistics and create a histogram. Explain what the distribution looks like.",
            "description": "Statistical analysis and visualization"
        },
        {
            "name": "Data Visualization",
            "query": "Create sample data for monthly sales over 12 months with some seasonal patterns. Generate a line plot showing the trend and calculate the month-over-month growth rate.",
            "description": "Data generation and advanced visualization"
        },
        {
            "name": "Complex Analysis",
            "query": "Create a dataset of 200 customers with features: age (20-80), income (30k-200k), and purchase_amount. Analyze the correlation between age, income, and purchase behavior. Create appropriate visualizations and provide insights.",
            "description": "Multi-variable analysis and correlation study"
        }
    ]

async def run_interactive_mode():
    """
    Run the agent in interactive mode, allowing users to input custom queries.
    """
    print("🤖 Data Analyzer Agent - Interactive Mode")
    print("=" * 50)
    print("Enter your data analysis requests. Type 'quit' to exit.")
    print("Type 'examples' to see sample queries.")
    print("Type 'help' for usage tips.")
    print()

    while True:
        try:
            user_input = input("📊 Your analysis request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'examples':
                print("\\n📚 Example Queries:")
                for i, example in enumerate(get_example_queries(), 1):
                    print(f"\\n{i}. {example['name']}:")
                    print(f"   {example['description']}")
                    print(f"   Query: {example['query'][:100]}...")
                print()
                continue
            elif user_input.lower() == 'help':
                print("\\n💡 Usage Tips:")
                print("• Provide data as CSV or JSON strings in your query")
                print("• Be specific about the analysis you want")
                print("• Ask for visualizations if needed")
                print("• The agent can handle statistical analysis, data cleaning, and reporting")
                print("• Check that the sandbox server is running before making requests")
                print()
                continue
            elif not user_input:
                continue
                
            await run_analysis_task(user_input)
            print("\\n" + "-"*50 + "\\n")
            
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

async def run_example_queries():
    """
    Run all example queries to demonstrate the agent's capabilities.
    """
    examples = get_example_queries()
    
    print("🧪 Running Example Queries")
    print("=" * 50)
    
    for i, example in enumerate(examples, 1):
        print(f"\\n📊 Example {i}: {example['name']}")
        print(f"Description: {example['description']}")
        print("Query:", example['query'][:100] + "..." if len(example['query']) > 100 else example['query'])
        print("-" * 40)
        
        result = await run_analysis_task(example['query'])
        
        if result:
            print("✅ Example completed successfully")
        else:
            print("❌ Example failed")
            
        print("\\n" + "="*50)
        
        # Ask user if they want to continue
        if i < len(examples):
            try:
                continue_choice = input("\\nContinue to next example? (y/n): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    break
            except KeyboardInterrupt:
                print("\\n👋 Stopping examples.")
                break

def main():
    """
    Main entry point for the script.
    """
    print("🚀 Data Analyzer Agent")
    print("=" * 30)
    
    # Check environment setup
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment.")
        print("Please copy .env.template to .env and configure your API key.")
    
    # Check if sandbox server is likely running
    sandbox_url = os.getenv("PYTHON_SANDBOX_API_URL", "http://localhost:8000")
    print(f"📡 Sandbox server configured at: {sandbox_url}")
    print("Make sure to start it with: uvicorn sandbox_server.main:app --reload --port 8000")
    print()
    
    while True:
        print("Choose an option:")
        print("1. Interactive mode (enter custom queries)")
        print("2. Run example queries")
        print("3. Single test query")
        print("4. Exit")
        
        try:
            choice = input("\\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                asyncio.run(run_interactive_mode())
            elif choice == '2':
                asyncio.run(run_example_queries())
            elif choice == '3':
                test_query = "Generate 10 random numbers between 1 and 100, calculate their mean and standard deviation, and tell me the results."
                print(f"\\n🧪 Running test query: {test_query}")
                asyncio.run(run_analysis_task(test_query))
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
