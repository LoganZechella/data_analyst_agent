"""
Main Data Analyzer Agent Definition

This module defines the Data Analyzer AI agent using the OpenAI Agents SDK.
It combines system prompts, tools, and configuration to create a capable
data analysis agent.
"""

from agents import Agent, ModelSettings
# Potentially import LiteLLmModel if using non-OpenAI models [3]
# from agents.extensions.models.litellm_model import LitellmModel

# Import prompts from prompts.py
from .prompts.system_prompts import DATA_ANALYZER_SYSTEM_PROMPT
from .tools.python_sandbox_tool import python_execution_tool  # Will be created
from .guardrails.safety_checks import check_python_code_safety

# Load API keys from .env file (create this file with your OPENAI_API_KEY)
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in .env file or environment variables. Please set it before running the agent.")
    # Note: The OpenAI SDK typically picks up the API key from the environment variable automatically.
    # Explicitly setting it might be needed for some specific client configurations.

# Create the Data Analyzer Agent
data_analyzer_agent = Agent(
    name="DataAnalyzer",
    instructions=DATA_ANALYZER_SYSTEM_PROMPT,  # Defined in prompts.py
    model="gpt-4", # Using GPT-4 for robust reasoning and code generation
                   # Consider gpt-4-1106-preview or newer models for latest features
                   # For more advanced reasoning, could use o1-preview or o1-mini
    model_settings=ModelSettings(
        temperature=0.2,  # Low temperature for more controlled, deterministic responses
        max_tokens=4000,  # Sufficient for detailed analysis and code generation
    ),
    tools=[python_execution_tool],  # Added the sandbox execution tool
    # Note: Guardrails would be added here if using OpenAI Agents SDK guardrail system
    # guardrails=[check_python_code_safety]  # Uncomment if guardrails are supported
)

# Example of using LiteLLM for a different model provider (conceptual)
# from agents.extensions.models.litellm_model import LitellmModel
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# claude_analyzer_agent = Agent(
#     name="ClaudeDataAnalyzer",
#     instructions=DATA_ANALYZER_SYSTEM_PROMPT,
#     model=LitellmModel(model="anthropic/claude-3-opus-20240229", api_key=ANTHROPIC_API_KEY),
#     tools=[python_execution_tool]
# )

# Alternative configuration for more advanced models
gpt4_turbo_analyzer_agent = Agent(
    name="DataAnalyzerTurbo",
    instructions=DATA_ANALYZER_SYSTEM_PROMPT,
    model="gpt-4-turbo-preview",  # More capable version for complex analyses
    model_settings=ModelSettings(
        temperature=0.1,  # Even lower temperature for maximum precision
        max_tokens=4000,
    ),
    tools=[python_execution_tool]
)

# For very complex reasoning tasks, consider o1-preview
# Note: o1 models may have different parameter requirements
o1_analyzer_agent = Agent(
    name="DataAnalyzerO1",
    instructions=DATA_ANALYZER_SYSTEM_PROMPT,
    model="o1-preview",  # Advanced reasoning model for complex analyses
    model_settings=ModelSettings(
        # Note: o1 models may not support temperature parameter
        max_tokens=4000,
    ),
    tools=[python_execution_tool]
)

# Export the default agent
__all__ = [
    "data_analyzer_agent", 
    "gpt4_turbo_analyzer_agent", 
    "o1_analyzer_agent"
]

logger.info("Data Analyzer Agent initialized successfully")
