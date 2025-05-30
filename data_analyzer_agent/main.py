"""
Data Analyzer Agent - Main Interface

This module provides the main interface for the Data Analyzer Agent,
now powered by the OpenAI Responses API for simplified architecture
and enhanced capabilities.

For the full Responses API implementation, see main_responses_api.py
"""

# Import the new Responses API implementation
from .main_responses_api import (
    DataAnalyzerAgent,
    data_analyzer_agent,
    o4_analyzer_agent,
    create_standard_analyzer,
    create_reasoning_analyzer
)

# Import simplified prompts
from .prompts.simplified_prompts import (
    SIMPLIFIED_DATA_ANALYZER_SYSTEM_PROMPT,
    BUSINESS_INTELLIGENCE_PROMPT,
    TIME_SERIES_ANALYSIS_PROMPT,
    CUSTOMER_ANALYTICS_PROMPT
)

# Maintain backward compatibility with old interface
__all__ = [
    "DataAnalyzerAgent",
    "data_analyzer_agent",
    "o4_analyzer_agent",
    "create_standard_analyzer",
    "create_reasoning_analyzer",
    "SIMPLIFIED_DATA_ANALYZER_SYSTEM_PROMPT",
    "BUSINESS_INTELLIGENCE_PROMPT",
    "TIME_SERIES_ANALYSIS_PROMPT",
    "CUSTOMER_ANALYTICS_PROMPT"
]

# Legacy note
print("ℹ️  Data Analyzer Agent now uses OpenAI Responses API")
print("   - 75% simpler architecture")
print("   - Real-time streaming progress")  
print("   - Native code interpretation")
print("   - Enhanced models: GPT-4.1 (standard), o4-mini (reasoning)")
print("   See README_responses_api.md for details")
