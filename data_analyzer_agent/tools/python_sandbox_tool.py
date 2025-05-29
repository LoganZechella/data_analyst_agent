"""
Python Sandbox Tool for Data Analyzer Agent

This module implements the execute_python_code tool that interfaces with
the Python sandbox server to execute arbitrary Python code securely.
"""

from agents import function_tool, RunContextWrapper
from pydantic import BaseModel, Field
import httpx  # For making async HTTP calls to the sandbox API
import json
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration for the sandbox API endpoint
# For local custom sandbox:
PYTHON_SANDBOX_API_URL = os.getenv("PYTHON_SANDBOX_API_URL", "http://localhost:8000")
# For E2B (if chosen as primary or alternative):
# E2B_API_KEY = os.getenv("E2B_API_KEY")

class PythonCodeExecutionParams(BaseModel):
    code: str = Field(..., description="The Python code to execute in the sandbox. Ensure the code prints results to stdout or handles return values appropriately for capture.")
    data_input: str | None = Field(None, description="Optional input data for the code, as a JSON string or CSV string. This will be made available in the Python script as a variable named 'input_data_str'.")
    # Potentially add:
    # timeout: int = Field(default=60, description="Maximum execution time in seconds.")
    # required_libraries: list[str] | None = Field(None, description="List of libraries to ensure are available.")

@function_tool(
    name="execute_python_code",
    description="Executes arbitrary Python code in a secure sandbox to perform data analysis, computations, or manipulations. Input data can be provided. Returns a JSON string containing the execution result (stdout, stderr, returned values/plots, and any errors).",
)
async def execute_python_code_in_sandbox(ctx: RunContextWrapper, params: PythonCodeExecutionParams) -> str:
    """
    Executes Python code in a sandboxed environment via an external API.
    :param code: The Python code string to execute.
    :param data_input: Optional. Data to be made available to the Python code, typically as a JSON string or CSV string.
    :return: A JSON string representing the sandbox execution output.
    """
    logger.info(f"Tool 'execute_python_code_in_sandbox' called. Code (first 100 chars): {params.code[:100]}...")

    # This implementation calls a custom FastAPI sandbox.
    # An alternative E2B implementation is commented out below.
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for potentially long analyses
            payload = {"code": params.code, "data": params.data_input}
            logger.debug(f"Sending payload to sandbox: {payload}")
            response = await client.post(f"{PYTHON_SANDBOX_API_URL}/execute", json=payload)

            logger.info(f"Sandbox response status: {response.status_code}")
            response.raise_for_status()  # Raise an exception for HTTP errors 4xx/5xx

            # The sandbox is expected to return a JSON string.
            # This string itself is what the LLM will receive and must parse.
            # No further parsing here, the LLM handles the content of response.text.
            logger.debug(f"Sandbox response text: {response.text[:500]}...")  # Log snippet of response
            return response.text
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        logger.error(f"HTTP error calling sandbox: {e.response.status_code if e.response else 'N/A'} - {error_detail}", exc_info=True)
        return json.dumps({"error": f"HTTP error calling sandbox: {e.response.status_code if e.response else 'N/A'}", "details": error_detail, "stdout": "", "stderr": error_detail, "results": [], "error_info": {"ename": "HTTPStatusError", "evalue": str(e.response.status_code if e.response else 'N/A'), "traceback": [error_detail]}})
    except httpx.RequestError as e:
        logger.error(f"Request error calling sandbox: {str(e)}", exc_info=True)
        return json.dumps({"error": f"Request error calling sandbox: {str(e)}", "stdout": "", "stderr": str(e), "results": [], "error_info": {"ename": "RequestError", "evalue": str(e), "traceback": [str(e)]}})
    except Exception as e:
        logger.error(f"An unexpected error occurred in tool: {str(e)}", exc_info=True)
        return json.dumps({"error": f"An unexpected error occurred in the tool: {str(e)}", "stdout": "", "stderr": str(e), "results": [], "error_info": {"ename": "ToolException", "evalue": str(e), "traceback": [str(e)]}})

# # E2B Alternative Implementation (conceptual):
# from e2b_code_interpreter import Sandbox, Result  # Requires E2B_API_KEY
# import base64
# 
# @function_tool(name="execute_python_code_e2b", description="Executes Python code in an E2B sandbox.")
# async def execute_python_with_e2b(ctx: RunContextWrapper, params: PythonCodeExecutionParams) -> str:
#     if not E2B_API_KEY:
#         return json.dumps({"error": "E2B_API_KEY not configured."})
#     logger.info(f"Executing code with E2B: {params.code[:100]}...")
#     try:
#         async with Sandbox(api_key=E2B_API_KEY) as sandbox:
#             if params.data_input:
#                 # Example: Make data_input available as a file or environment variable
#                 await sandbox.filesystem.write("input_data.txt", params.data_input)
#                 # Or modify code to load from this file, or inject as variable
#                 # For simplicity, assume code knows to look for 'input_data.txt' or input_data_str is prepended
#                 # More robust: prepend to code: injected_code = f"input_data_str = '''{params.data_input}'''\\n{params.code}"
# 
#             exec_result: Result = await sandbox.notebook.exec_cell(
#                 params.code,
#                 # timeout_secs=params.timeout  # If timeout param is added
#             )
# 
#             artifacts_data = []
#             for artifact in exec_result.artifacts:
#                 # E2B returns artifact objects that can be downloaded
#                 # For LLM consumption, might convert to base64 or provide URLs if sandbox hosts them
#                 # This is a simplified representation
#                 content_bytes = await artifact.download()
#                 artifacts_data.append({
#                     "name": artifact.name,  # E2B might not provide name directly, depends on how it's saved
#                     "content_base64": base64.b64encode(content_bytes).decode('utf-8'),
#                     "size": artifact.size
#                 })
# 
#             output = {
#                 "stdout": "".join(log.line for log in exec_result.logs if log.source == "stdout"),
#                 "stderr": "".join(log.line for log in exec_result.logs if log.source == "stderr"),
#                 "results": [res.text for res in exec_result.results if hasattr(res, 'text')],  # Simplified: E2B results can be complex (img, html etc)
#                 "error_info": {
#                     "ename": exec_result.error.name,
#                     "evalue": exec_result.error.value,
#                     "traceback": exec_result.error.traceback_raw
#                 } if exec_result.error else None,
#                 "artifacts": artifacts_data
#             }
#             return json.dumps(output)
#     except Exception as e:
#         logger.error(f"Error during E2B execution: {str(e)}", exc_info=True)
#         return json.dumps({"error": f"E2B execution failed: {str(e)}", "stdout": "", "stderr": str(e), "results": [], "error_info": {"ename": "E2BException", "evalue": str(e), "traceback": [str(e)]}})

# Select which tool implementation to export
python_execution_tool = execute_python_code_in_sandbox
# python_execution_tool = execute_python_with_e2b  # Uncomment to use E2B
