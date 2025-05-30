"""
Data Analyzer AI Agent Package

A sophisticated AI agent for data analysis using the OpenAI Responses API.
Provides native code interpretation with real-time streaming, reasoning transparency,
and dramatically simplified architecture (75% complexity reduction).

Features:
- Native code interpreter (no custom sandbox needed)
- Real-time streaming progress updates
- Reasoning transparency with o4-mini models
- Enhanced models: GPT-4.1 (standard), o4-mini (reasoning)
- Zero infrastructure maintenance
"""

__version__ = "2.0.0"  # Major version bump for Responses API migration
__author__ = "Data Analyzer Agent Development Team"

from .main import data_analyzer_agent, o4_analyzer_agent

__all__ = ["data_analyzer_agent", "o4_analyzer_agent"]
