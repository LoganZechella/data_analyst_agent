"""
Python Execution Sandbox Server

A FastAPI server that provides secure Python code execution using Jupyter kernels.
This server receives Python code via HTTP POST requests and executes it in an
isolated environment, returning structured results including stdout, stderr,
and any generated artifacts.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from jupyter_client.asynchronous import AsyncKernelManager
import asyncio
import json
import logging
import traceback  # For detailed exception logging
import base64
import io

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow re-entrant asyncio loops, common in Jupyter/FastAPI contexts
import nest_asyncio
nest_asyncio.apply()

app = FastAPI(
    title="Data Analyzer Python Sandbox",
    description="Secure Python code execution environment for the Data Analyzer Agent",
    version="1.0.0"
)

# In a production system, you'd have a pool of kernel managers or a more robust setup.
# For this local dev example, we create one per request, which is inefficient but simple.
# A better approach for local dev might be a single, long-lived kernel if concurrency is not an issue.

class CodeExecutionRequest(BaseModel):
    code: str
    data: str | None = None  # Optional data string (e.g., JSON or CSV)

class CodeExecutionResponse(BaseModel):
    stdout: str
    stderr: str
    results: list
    error_info: dict | None
    artifacts: list

async def execute_code_in_jupyter_kernel(code: str, data_input: str | None) -> dict:
    """
    Execute Python code in a Jupyter kernel and return structured results.
    
    Args:
        code: Python code string to execute
        data_input: Optional data to make available as input_data_str variable
        
    Returns:
        Dictionary with execution results including stdout, stderr, errors, and artifacts
    """
    kernel_manager = AsyncKernelManager()
    await kernel_manager.start_kernel()
    client = kernel_manager.client()
    client.start_channels()
    logger.info(f"Jupyter kernel {kernel_manager.kernel_id} started for code execution.")

    full_code = code
    if data_input:
        # Make data_input available as a Python string variable named 'input_data_str'
        # Ensure data_input is properly escaped to be a valid Python string literal
        escaped_data_input = json.dumps(data_input)   
        full_code = f"input_data_str = {escaped_data_input}\\n{code}"
        logger.info("input_data_str prepended to user code.")

    logger.debug(f"Executing full code in kernel:\\n{full_code}")
    msg_id = client.execute(full_code)

    stdout_list = []
    stderr_list = []
    results_list = []  # To store 'execute_result' or 'display_data'
    error_info = None

    execution_timeout = 60  # seconds

    try:
        while True:
            try:
                # Wait for a message on iopub channel with a timeout
                msg = await asyncio.wait_for(client.get_iopub_msg(), timeout=execution_timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Execution timed out waiting for iopub message from kernel {kernel_manager.kernel_id}.")
                error_info = {"ename": "TimeoutError", "evalue": "Code execution timed out", "traceback": ["Execution exceeded timeout limit."]}
                break  # Exit loop on timeout

            if msg['parent_header'].get('msg_id') == msg_id:
                msg_type = msg['header']['msg_type']
                content = msg['content']
                logger.debug(f"Kernel message received: type={msg_type}, content snippet={str(content)[:200]}")

                if msg_type == 'stream':
                    if content['name'] == 'stdout':
                        stdout_list.append(content['text'])
                    elif content['name'] == 'stderr':
                        stderr_list.append(content['text'])
                elif msg_type == 'execute_result':
                    # Capture plain text representation if available
                    results_list.append(content['data'].get('text/plain', ''))
                elif msg_type == 'display_data':
                    # Handle potential image data (e.g., from matplotlib)
                    if 'image/png' in content['data']:
                        results_list.append({"type": "image_png_base64", "data": content['data']['image/png']})
                    elif 'text/plain' in content['data']:
                         results_list.append({"type": "text_plain", "data": content['data']['text/plain']})
                    else:  # Fallback for other display data
                        results_list.append({"type": "unknown_display_data", "data": content['data']})
                elif msg_type == 'error':
                    logger.error(f"Python execution error in kernel: {content['ename']}: {content['evalue']}")
                    error_info = {
                        "ename": content['ename'],
                        "evalue": content['evalue'],
                        "traceback": content['traceback']  # This is a list of strings
                    }
                    # Error messages might also appear on stderr
                    stderr_list.append(f"ERROR: {content['ename']}: {content['evalue']}\\n" + "\\n".join(content['traceback']))
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    # Execution is idle, this usually means completion or an error that halted execution.
                    # We rely on the shell message for definitive status.
                    logger.info(f"Kernel status idle for {kernel_manager.kernel_id}. Checking shell reply.")
                    break  # Exit iopub loop and check shell reply

    except Exception as e:
        logger.error(f"Exception while processing kernel messages for {kernel_manager.kernel_id}: {str(e)}\\n{traceback.format_exc()}", exc_info=True)
        if not error_info:  # Ensure some error is reported
             error_info = {"ename": "SandboxError", "evalue": "Error processing kernel messages", "traceback": [str(e)]}

    # Check shell reply for final status (important for catching some errors or confirming success)
    try:
        shell_reply = await asyncio.wait_for(client.get_shell_msg(), timeout=5.0)
        if shell_reply['parent_header'].get('msg_id') == msg_id:
            if shell_reply['content']['status'] == 'error' and not error_info:
                content = shell_reply['content']
                logger.error(f"Python execution error confirmed by shell reply: {content['ename']}: {content['evalue']}")
                error_info = {
                    "ename": content['ename'],
                    "evalue": content['evalue'],
                    "traceback": content['traceback']
                }
                stderr_list.append(f"SHELL_ERROR: {content['ename']}: {content['evalue']}\\n" + "\\n".join(content['traceback']))
            elif shell_reply['content']['status'] == 'ok':
                 logger.info(f"Execution completed successfully for kernel {kernel_manager.kernel_id}.")

    except asyncio.TimeoutError:
        logger.warning(f"Timeout waiting for shell reply from kernel {kernel_manager.kernel_id}.")
        if not error_info and not stdout_list and not results_list:  # If no output and no error yet
            error_info = {"ename": "TimeoutError", "evalue": "Timeout waiting for shell reply, execution status unknown.", "traceback": []}
    except Exception as e:
        logger.error(f"Exception while getting shell reply for {kernel_manager.kernel_id}: {str(e)}\\n{traceback.format_exc()}", exc_info=True)
        if not error_info:
            error_info = {"ename": "SandboxShellError", "evalue": "Error getting shell reply", "traceback": [str(e)]}
    finally:
        logger.info(f"Shutting down kernel {kernel_manager.kernel_id}.")
        await kernel_manager.shutdown_kernel(now=True)  # Ensure kernel is always shut down
        client.stop_channels()

    return {
        "stdout": "".join(stdout_list),
        "stderr": "".join(stderr_list),
        "results": results_list,   
        "error_info": error_info,  # Will be null if no Python error
        "artifacts": []  # Placeholder; artifact handling from display_data needs more robust implementation
                         # For example, 'results_list' might contain base64 image data that the LLM's prompt
                         # needs to be aware of to instruct the code to save or to interpret.
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Data Analyzer Python Sandbox Server", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "python-sandbox",
        "version": "1.0.0",
        "features": ["jupyter-kernel", "python-execution", "artifact-support"]
    }

@app.post("/execute")
async def execute_code_endpoint(request_data: CodeExecutionRequest, request: Request):
    """
    Execute Python code in a secure Jupyter kernel environment.
    
    Args:
        request_data: Request containing code and optional data input
        request: FastAPI request object for logging
        
    Returns:
        Structured execution results including stdout, stderr, errors, and artifacts
    """
    # Log client IP for auditing/debugging (if behind a proxy, need to check X-Forwarded-For)
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Received /execute request from {client_host}. Code (first 100 chars): {request_data.code[:100]}...")
    
    try:
        result = await execute_code_in_jupyter_kernel(request_data.code, request_data.data)
        logger.info(f"Execution result for request from {client_host}: stdout_len={len(result['stdout'])}, stderr_len={len(result['stderr'])}, has_error={result['error_info'] is not None}")
        return result
    except Exception as e:
        logger.error(f"Unhandled error in /execute endpoint from {client_host}: {str(e)}\\n{traceback.format_exc()}", exc_info=True)
        # Return a structured error in the expected format if possible
        return {
            "error": f"Server error during execution: {str(e)}", 
            "stdout": "", 
            "stderr": str(e), 
            "results": [], 
            "error_info": {
                "ename": "FastAPIError", 
                "evalue": str(e), 
                "traceback": [traceback.format_exc()]
            },
            "artifacts": []
        }

# Optional: Add middleware for CORS if needed
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Data Analyzer Python Sandbox Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# To run this server:
# Save as sandbox_server/main.py
# Ensure dependencies from sandbox_server/requirements.txt are installed in the environment
# Then, from the 'data_analyst_agent' directory:
# uvicorn sandbox_server.main:app --reload --port 8000 --host 0.0.0.0
