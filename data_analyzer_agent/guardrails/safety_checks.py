"""
Safety Checks and Guardrails for Data Analyzer Agent

This module implements input guardrails to ensure safe operation
of the Python code execution sandbox.
"""

from agents import input_guardrail, GuardrailFunctionOutput, RunContextWrapper
from pydantic import BaseModel
import re
import logging

logger = logging.getLogger(__name__)

# Assume PythonCodeExecutionParams is imported from the tool definition
from ..tools.python_sandbox_tool import PythonCodeExecutionParams

DISALLOWED_MODULES = ["shutil", "subprocess", "socket", "os.system"]  # Example
DISALLOWED_FUNCTIONS = ["eval", "exec", "compile", "__import__"]
SUSPICIOUS_PATTERNS = [
    r"open\s*\(\s*['\"].*['\"],\s*['\"]w",  # File writing operations
    r"requests\.get|requests\.post|urllib",  # Network requests
    r"os\.system|subprocess\.",  # System commands
    r"socket\.",  # Socket operations
]

class CodeSafetyCheckOutput(BaseModel):
    is_safe: bool
    reasoning: str
    violations: list[str] = []

@input_guardrail  # This would be applied to the 'execute_python_code_in_sandbox' tool
async def check_python_code_safety(
    ctx: RunContextWrapper,
    agent,  # The agent calling the tool
    tool_params: str  # Tool parameters as a JSON string
) -> GuardrailFunctionOutput:
    """
    Input guardrail to check Python code for potentially unsafe operations.
    
    Args:
        ctx: Runtime context wrapper
        agent: The agent instance calling the tool
        tool_params: JSON string containing tool parameters
        
    Returns:
        GuardrailFunctionOutput with safety assessment
    """
    try:
        params = PythonCodeExecutionParams.model_validate_json(tool_params)
        code_to_check = params.code.lower()  # Case-insensitive check
        violations = []

        # Check for disallowed modules
        for module in DISALLOWED_MODULES:
            if f"import {module}" in code_to_check or f"from {module} import" in code_to_check:
                violation = f"Code attempts to import disallowed module: {module}"
                violations.append(violation)
                logger.warning(f"Safety violation detected: {violation}")

        # Check for disallowed functions
        for func in DISALLOWED_FUNCTIONS:
            if func in code_to_check:
                violation = f"Code contains potentially dangerous function: {func}"
                violations.append(violation)
                logger.warning(f"Safety violation detected: {violation}")

        # Check for suspicious patterns
        original_code = params.code  # Use original case for pattern matching
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, original_code, re.IGNORECASE):
                violation = f"Code contains suspicious pattern: {pattern}"
                violations.append(violation)
                logger.warning(f"Safety violation detected: {violation}")

        # Determine if code is safe
        is_safe = len(violations) == 0
        
        if is_safe:
            output_info = CodeSafetyCheckOutput(
                is_safe=True, 
                reasoning="Basic safety checks passed.",
                violations=[]
            )
            return GuardrailFunctionOutput(output_info=output_info, tripwire_triggered=False)
        else:
            output_info = CodeSafetyCheckOutput(
                is_safe=False,
                reasoning=f"Safety violations detected: {'; '.join(violations)}",
                violations=violations
            )
            logger.error(f"Code safety check failed: {violations}")
            return GuardrailFunctionOutput(output_info=output_info, tripwire_triggered=True)

    except Exception as e:
        # If guardrail itself fails, allow execution but log error
        logger.error(f"Error in check_python_code_safety guardrail: {str(e)}", exc_info=True)
        output_info = CodeSafetyCheckOutput(
            is_safe=True, 
            reasoning=f"Guardrail check failed: {str(e)}",
            violations=[]
        )
        return GuardrailFunctionOutput(output_info=output_info, tripwire_triggered=False)

def validate_data_analysis_relevance(query: str) -> bool:
    """
    Check if a query is relevant to data analysis tasks.
    
    Args:
        query: User query string
        
    Returns:
        bool: True if query appears to be data analysis related
    """
    data_analysis_keywords = [
        'analyze', 'analysis', 'data', 'statistics', 'plot', 'chart', 'graph',
        'mean', 'median', 'correlation', 'regression', 'model', 'predict',
        'visualize', 'csv', 'json', 'dataframe', 'pandas', 'numpy',
        'calculate', 'compute', 'aggregate', 'summarize', 'trend'
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in data_analysis_keywords)
