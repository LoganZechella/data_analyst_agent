"""
Data Analyzer Agent - Responses API Implementation

This module implements the Data Analyzer AI agent using the OpenAI Responses API
instead of the custom sandbox infrastructure. This provides native code interpretation
with real-time streaming, better error handling, and simplified architecture.
"""

from openai import OpenAI
from openai.types.responses import ResponseCreateParams
from dotenv import load_dotenv
import os
import logging
from typing import Iterator, Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DataAnalyzerAgent:
    """
    Enhanced Data Analyzer Agent using OpenAI Responses API
    
    Features:
    - Native code interpretation (no custom sandbox needed)
    - Real-time progress streaming
    - Built-in error handling and artifact management
    - Reasoning transparency with o4 models
    """
    
    def __init__(self, model: str = "gpt-4.1", reasoning_effort: str = "medium"):
        """
        Initialize the Data Analyzer Agent
        
        Args:
            model: The OpenAI model to use (gpt-4.1, o4-mini, etc.)
            reasoning_effort: For reasoning models - low, medium, high
        """
        self.client = OpenAI()  # Uses OPENAI_API_KEY from environment
        self.model = model
        self.reasoning_effort = reasoning_effort
        
        # Simplified system prompt focused on analysis strategy
        self.system_prompt = self._get_system_prompt()
        
        logger.info(f"Data Analyzer Agent initialized with model: {model}")
    
    def _get_system_prompt(self) -> str:
        """
        Get the simplified system prompt for the Responses API implementation
        """
        return """
# Role and Objective
You are DataAnalyzer, an expert AI data analyst. Your objective is to analyze data and provide clear, accurate insights using the built-in code interpreter. Focus on analytical strategy and insight generation.

# Core Capabilities
- Load and process various data formats (CSV, JSON, Excel, etc.)
- Perform statistical analysis and data exploration
- Create visualizations and charts
- Generate actionable insights and recommendations
- Handle complex multi-step analytical workflows

# Analysis Approach
1. **Understand the Request**: Clarify what analysis is needed
2. **Plan the Analysis**: Outline your analytical approach
3. **Execute with Code**: Use the code interpreter for all computations
4. **Interpret Results**: Explain findings clearly and provide insights
5. **Recommend Actions**: Suggest next steps based on analysis

# Best Practices
- Always validate data before analysis
- Use appropriate visualizations for the data type
- Provide clear explanations of statistical findings
- Handle missing or invalid data gracefully
- Focus on actionable insights rather than just statistics

# Output Format
- Lead with key insights and recommendations
- Support findings with data and visualizations
- Explain methodology when relevant
- Use clear, non-technical language unless technical detail is requested

# Available Libraries
The code interpreter has access to common data science libraries:
pandas, numpy, matplotlib, seaborn, scikit-learn, scipy, plotly, and more.

Now analyze the user's request and provide comprehensive insights.
"""
    
    def analyze(self, 
                query: str, 
                data: Optional[str] = None,
                stream: bool = True,
                files: Optional[list] = None) -> Iterator[Dict[str, Any]]:
        """
        Analyze data based on user query using Responses API
        
        Args:
            query: The analysis request from the user
            data: Optional data string (CSV, JSON, etc.)
            stream: Whether to stream responses in real-time
            files: Optional list of file paths to upload
            
        Yields:
            Dictionary containing event type and data for real-time updates
        """
        try:
            # Prepare input messages
            input_messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self.system_prompt
                        }
                    ]
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "input_text",
                            "text": query
                        }
                    ]
                }
            ]
            
            # Add data if provided
            if data:
                input_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text", 
                            "text": f"Data:\n{data}"
                        }
                    ]
                })
            
            # Prepare tools - using native code interpreter
            tools = [{"type": "code_interpreter"}]
            
            # Add file search if files provided
            if files:
                tools.append({"type": "file_search"})
            
            # Create response with Responses API
            response_params = {
                "input": input_messages,
                "model": self.model,
                "tools": tools,
                "stream": stream
            }
            
            # Add reasoning effort for reasoning models (o4, o1, etc.)
            if self.model.startswith(("o4", "o1")):
                response_params["reasoning"] = {
                    "effort": "high"
                }
            
            logger.info(f"Starting analysis with model {self.model}")
            
            if stream:
                # Stream the response for real-time updates
                response_stream = self.client.responses.create(**response_params)
                
                for event in response_stream:
                    yield self._process_stream_event(event)
            else:
                # Non-streaming response
                response = self.client.responses.create(**response_params)
                yield self._process_final_response(response)
                
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "message": f"Analysis failed: {str(e)}"
            }
    
    def _process_stream_event(self, event) -> Dict[str, Any]:
        """
        Process streaming events from the Responses API
        
        Args:
            event: Stream event from the API
            
        Returns:
            Processed event data
        """
        event_data = {
            "type": event.type,
            "timestamp": getattr(event, 'timestamp', None)
        }
        
        # Handle different event types
        if event.type == "response_created":
            event_data.update({
                "message": "🚀 Analysis started",
                "response_id": event.response.id,
                "status": event.response.status
            })
            
        elif event.type == "response_code_interpreter_call_in_progress":
            event_data.update({
                "message": "🔄 Executing code...",
                "code": getattr(event, 'code', 'Code execution in progress')
            })
            
        elif event.type == "response_code_interpreter_call_code_delta":
            event_data.update({
                "message": "📝 Code streaming",
                "delta": event.delta,
                "code_chunk": event.delta
            })
            
        elif event.type == "response_code_interpreter_call_interpreting":
            event_data.update({
                "message": "🧠 Interpreting results...",
                "status": "interpreting"
            })
            
        elif event.type == "response_code_interpreter_call_completed":
            event_data.update({
                "message": "✅ Code execution completed",
                "output": getattr(event, 'output', None),
                "status": "completed"
            })
            
        elif event.type == "response_reasoning_delta":
            # Available with reasoning models - shows reasoning process
            event_data.update({
                "message": "🤔 Reasoning...",
                "reasoning": event.delta,
                "reasoning_chunk": event.delta
            })
            
        elif event.type == "response_reasoning_done":
            event_data.update({
                "message": "💡 Reasoning complete",
                "reasoning": event.reasoning
            })
            
        elif event.type == "response_content_part_added":
            event_data.update({
                "message": "📄 Content generated",
                "content_type": event.part.type,
                "content": getattr(event.part, 'text', None)
            })
            
        elif event.type == "response_output_item_added":
            event_data.update({
                "message": "📤 Output generated",
                "item_type": event.item.type,
                "item": event.item
            })
            
        elif event.type == "response_done":
            event_data.update({
                "message": "🎉 Analysis complete!",
                "status": "completed",
                "final_response": True
            })
            
        return event_data
    
    def _process_final_response(self, response) -> Dict[str, Any]:
        """
        Process non-streaming response from the Responses API
        
        Args:
            response: Final response from the API
            
        Returns:
            Processed response data
        """
        return {
            "type": "response_complete",
            "response_id": response.id,
            "status": response.status,
            "message": "Analysis complete",
            "output": response.output,
            "usage": getattr(response, 'usage', None)
        }

# Factory functions for different model configurations
def create_standard_analyzer() -> DataAnalyzerAgent:
    """Create a standard data analyzer using GPT-4.1"""
    return DataAnalyzerAgent(model="gpt-4.1")

def create_reasoning_analyzer() -> DataAnalyzerAgent:
    """Create an advanced reasoning analyzer using o4-mini"""
    return DataAnalyzerAgent(model="o4-mini", reasoning_effort="high")

# Export the main analyzer instances
data_analyzer_agent = create_standard_analyzer()
o4_analyzer_agent = create_reasoning_analyzer()

__all__ = [
    "DataAnalyzerAgent",
    "data_analyzer_agent", 
    "o4_analyzer_agent",
    "create_standard_analyzer",
    "create_reasoning_analyzer"
]

logger.info("Data Analyzer Agent (Responses API) modules loaded successfully")
