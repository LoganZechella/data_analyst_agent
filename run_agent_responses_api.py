"""
Data Analyzer Agent Runner (Responses API Implementation)

This script demonstrates the simplified Data Analyzer Agent using the OpenAI Responses API.
It showcases real-time streaming, enhanced error handling, and the dramatically reduced
complexity compared to the custom sandbox implementation.
"""

from data_analyzer_agent.main_responses_api import (
    data_analyzer_agent, 
    o4_analyzer_agent,
    DataAnalyzerAgent
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

class DataAnalyzerRunner:
    """
    Enhanced runner for the Data Analyzer Agent using Responses API
    """
    
    def __init__(self, model_type: str = "standard"):
        """
        Initialize the runner with specified model type
        
        Args:
            model_type: "standard" or "reasoning"
        """
        self.agents = {
            "standard": data_analyzer_agent,
            "reasoning": o4_analyzer_agent
        }
        
        self.current_agent = self.agents.get(model_type, data_analyzer_agent)
        self.model_type = model_type
        
        logger.info(f"Data Analyzer Runner initialized with {model_type} model")
    
    def run_analysis(self, query: str, data: str = None, stream: bool = True) -> None:
        """
        Run analysis with real-time streaming output
        
        Args:
            query: The analysis request
            data: Optional data string
            stream: Whether to show real-time progress
        """
        print(f"\n{'='*60}")
        print(f"🚀 DATA ANALYZER AGENT ({self.model_type.upper()}) - RESPONSES API")
        print(f"{'='*60}")
        print(f"📊 Query: {query}")
        if data:
            print(f"📁 Data provided: {len(data)} characters")
        print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            # Check API key
            if not os.getenv("OPENAI_API_KEY"):
                print("❌ Error: OPENAI_API_KEY not found. Please set it in your .env file.")
                return
            
            final_response = None
            analysis_complete = False
            
            # Stream the analysis with real-time updates
            for event in self.current_agent.analyze(query=query, data=data, stream=stream):
                self._display_event(event)
                
                if event.get("final_response"):
                    analysis_complete = True
                    final_response = event
            
            if analysis_complete:
                print(f"\n{'='*60}")
                print("🎉 ANALYSIS COMPLETE!")
                print(f"{'='*60}")
                print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Analysis interrupted by user.")
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            print(f"\n❌ Error during analysis: {str(e)}")
            print("💡 Please check your API key and network connection.")
    
    def _display_event(self, event: dict) -> None:
        """
        Display streaming events in a user-friendly format
        
        Args:
            event: Event dictionary from the analysis stream
        """
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        
        # Display different event types with appropriate formatting
        if event_type == "response_created":
            print(f"🚀 {message}")
            
        elif event_type == "response_code_interpreter_call_in_progress":
            print(f"🔄 {message}")
            if event.get("code"):
                print(f"   Code: {event['code'][:100]}{'...' if len(event['code']) > 100 else ''}")
                
        elif event_type == "response_code_interpreter_call_code_delta":
            # Show code streaming (could be overwhelming, so limit output)
            if event.get("code_chunk"):
                print(f"📝 Code: {event['code_chunk']}", end="", flush=True)
                
        elif event_type == "response_code_interpreter_call_interpreting":
            print(f"🧠 {message}")
            
        elif event_type == "response_code_interpreter_call_completed":
            print(f"✅ {message}")
            if event.get("output"):
                output = str(event["output"])[:200]
                print(f"   Output: {output}{'...' if len(str(event['output'])) > 200 else ''}")
                
        elif event_type == "response_reasoning_delta":
            # Show reasoning process (available with o4 models)
            if event.get("reasoning_chunk"):
                print(f"🤔 Reasoning: {event['reasoning_chunk']}", end="", flush=True)
                
        elif event_type == "response_reasoning_done":
            print(f"💡 {message}")
            
        elif event_type == "response_content_part_added":
            print(f"📄 {message}")
            if event.get("content"):
                content = str(event["content"])[:500]
                print(f"   Content: {content}{'...' if len(str(event['content'])) > 500 else ''}")
                
        elif event_type == "response_output_item_added":
            print(f"📤 {message}")
            
        elif event_type == "response_done":
            print(f"🎉 {message}")
            
        elif event_type == "error":
            print(f"❌ Error: {event.get('error', 'Unknown error')}")

def get_example_queries():
    """
    Get example queries for testing the new Responses API implementation
    """
    return [
        {
            "name": "Simple Statistics",
            "query": "Calculate basic statistics for this sales data and identify any interesting patterns.",
            "data": "product,sales,region\nLaptop,1200,North\nMouse,25,South\nKeyboard,75,North\nLaptop,1100,South\nMouse,30,North\nKeyboard,80,East",
            "description": "Basic statistical analysis with pattern identification"
        },
        {
            "name": "Time Series Analysis", 
            "query": "Analyze this monthly revenue data for trends and provide a forecast for the next 3 months.",
            "data": "month,revenue\n2024-01,50000\n2024-02,52000\n2024-03,48000\n2024-04,55000\n2024-05,57000\n2024-06,54000\n2024-07,59000\n2024-08,61000",
            "description": "Time series analysis with forecasting"
        },
        {
            "name": "Customer Segmentation",
            "query": "Segment these customers based on their purchase behavior and recommend marketing strategies for each segment.",
            "data": "customer_id,age,total_purchases,avg_order_value,frequency\n1,25,500,50,10\n2,45,2000,100,20\n3,35,150,30,5\n4,55,5000,250,20\n5,28,300,60,5\n6,42,1800,90,20\n7,38,800,80,10",
            "description": "Customer segmentation with business recommendations"
        },
        {
            "name": "Data Quality Assessment",
            "query": "Assess the quality of this dataset and recommend data cleaning steps.",
            "data": "name,age,salary,department\nJohn,25,50000,Engineering\nJane,,55000,Marketing\nBob,35,Marketing\nAlice,28,60000,Engineering\n,32,45000,Sales\nCharlie,abc,55000,Marketing",
            "description": "Data quality analysis and cleaning recommendations"
        },
        {
            "name": "Advanced Analytics",
            "query": "Build a predictive model to forecast sales based on marketing spend and provide insights on ROI optimization.",
            "data": "month,marketing_spend,sales\n1,5000,45000\n2,6000,48000\n3,4500,42000\n4,7000,52000\n5,5500,47000\n6,8000,55000\n7,6500,50000\n8,7500,53000\n9,5000,44000\n10,9000,58000",
            "description": "Predictive modeling with business optimization insights"
        }
    ]

async def run_interactive_mode():
    """
    Run the agent in interactive mode with model selection
    """
    print("\n🤖 DATA ANALYZER AGENT - RESPONSES API IMPLEMENTATION")
    print("=" * 60)
    print("Available models:")
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
    
    runner = DataAnalyzerRunner(model_type=model_type)
    
    model_details = {
        "standard": "GPT-4.1 - Enhanced performance and reliability",
        "reasoning": "o4-mini - Advanced reasoning with transparent thought process"
    }
    
    print(f"\n✅ Using {model_type} model: {model_details[model_type]}")
    print("\nCommands:")
    print("• Type your analysis request")
    print("• 'examples' - show example queries")
    print("• 'quit' - exit")
    print()

    while True:
        try:
            user_input = input("📊 Your analysis request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'examples':
                print("\n📚 Example Queries:")
                examples = get_example_queries()
                for i, example in enumerate(examples, 1):
                    print(f"\n{i}. {example['name']}")
                    print(f"   Description: {example['description']}")
                    print(f"   Query: {example['query'][:100]}...")
                    
                # Allow user to select an example
                try:
                    example_choice = input("\nSelect example (1-5) or press Enter to continue: ").strip()
                    if example_choice and example_choice.isdigit():
                        idx = int(example_choice) - 1
                        if 0 <= idx < len(examples):
                            example = examples[idx]
                            print(f"\n🚀 Running example: {example['name']}")
                            runner.run_analysis(example['query'], example['data'])
                except (ValueError, KeyboardInterrupt):
                    continue
                continue
                
            elif not user_input:
                continue
                
            # Check if user provided data
            data = None
            if "data:" in user_input.lower():
                parts = user_input.split("data:", 1)
                if len(parts) == 2:
                    user_input = parts[0].strip()
                    data = parts[1].strip()
            
            # Run the analysis
            runner.run_analysis(user_input, data)
            print("\n" + "-"*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

def main():
    """
    Main entry point for the Responses API implementation
    """
    print("🚀 DATA ANALYZER AGENT - RESPONSES API")
    print("=" * 50)
    
    # Check environment setup
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment.")
        print("Please add your OpenAI API key to the .env file.")
        return
    
    print("✅ Environment configured")
    print("📋 Available models: GPT-4.1 (standard), o4-mini (reasoning)")
    print()
    
    while True:
        print("Choose an option:")
        print("1. Interactive mode")
        print("2. Run example queries")
        print("3. Quick test")
        print("4. Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                asyncio.run(run_interactive_mode())
            elif choice == '2':
                runner = DataAnalyzerRunner("standard")
                examples = get_example_queries()
                
                for i, example in enumerate(examples, 1):
                    print(f"\n🧪 Running example {i}: {example['name']}")
                    print("-" * 40)
                    runner.run_analysis(example['query'], example['data'])
                    
                    if i < len(examples):
                        try:
                            input("\nPress Enter to continue to next example...")
                        except KeyboardInterrupt:
                            break
                            
            elif choice == '3':
                runner = DataAnalyzerRunner("standard")
                test_query = "Calculate the sum of these numbers: 10, 20, 30, 40, 50"
                print(f"\n🧪 Quick test: {test_query}")
                runner.run_analysis(test_query)
                
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
