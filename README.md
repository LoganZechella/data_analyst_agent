# 📊 Data Analyzer AI Agent

A sophisticated AI agent for data analysis using the OpenAI Agents SDK. This agent can execute arbitrary Python code in a secure sandbox environment to perform complex data analysis, visualization, and reporting tasks.

## 🎯 Key Features

- **Dynamic Python Code Generation**: Generates and executes custom Python code for any analysis task
- **Secure Sandbox Execution**: Runs code in an isolated Jupyter kernel environment  
- **Multi-Format Data Support**: Handles CSV, JSON, databases, and various data formats
- **Advanced Error Handling**: Automatically debugs and retries failed code execution
- **Comprehensive Prompting**: Uses advanced prompt engineering for reliable performance
- **Safety Guardrails**: Input validation and safety checks for secure operation
- **Multiple Model Support**: Compatible with GPT-4, GPT-4-Turbo, and o1 models

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   User Query    │───▶│  Data Analyzer  │───▶│ Python Sandbox  │
│                 │    │     Agent       │    │     Server      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              │                         │
                       ┌──────▼──────┐         ┌────────▼────────┐
                       │             │         │                 │
                       │ OpenAI API  │         │ Jupyter Kernel  │
                       │             │         │   + Libraries   │
                       └─────────────┘         └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Docker (optional, for containerized sandbox)

### Installation

1. **Clone and setup the project:**
   ```bash
   cd /users/logan/git/agents/OpenAIAgents/data_analyst_agent
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r sandbox_server/requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Start the sandbox server:**
   ```bash
   # In a separate terminal
   uvicorn sandbox_server.main:app --reload --port 8000
   ```

5. **Run the agent:**
   ```bash
   python run_agent.py
   ```

## 📋 Usage Examples

### Basic Data Analysis

```python
# Example query:
"I have data as CSV: 'name,age,salary\\nAlice,25,50000\\nBob,30,60000'. Calculate average salary and age distribution."
```

### Statistical Analysis

```python
# Example query:
"Generate 1000 random samples from a normal distribution. Perform statistical tests and create visualizations."
```

### Data Visualization

```python
# Example query:
"Create a scatter plot showing the relationship between two variables with correlation analysis."
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file from `.env.template`:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
PYTHON_SANDBOX_API_URL=http://localhost:8000
AGENT_MODEL=gpt-4
AGENT_TEMPERATURE=0.2
LOG_LEVEL=INFO
```

### Model Selection

Choose different models based on your needs:

```python
from data_analyzer_agent.main import (
    data_analyzer_agent,      # GPT-4 (balanced)
    gpt4_turbo_analyzer_agent, # GPT-4-Turbo (more capable)
    o1_analyzer_agent         # o1-preview (advanced reasoning)
)
```

## 🛡️ Security Features

- **Sandbox Isolation**: Code execution in isolated Jupyter kernels
- **Input Guardrails**: Validates code for potentially dangerous operations  
- **Resource Limits**: Timeouts and memory constraints
- **Network Restrictions**: Controlled external access
- **Error Containment**: Graceful handling of execution failures

## 📁 Project Structure

```
data_analyst_agent/
├── data_analyzer_agent/          # Main agent package
│   ├── __init__.py
│   ├── main.py                   # Agent definitions
│   ├── tools/                    # Agent tools
│   │   ├── __init__.py
│   │   └── python_sandbox_tool.py
│   ├── prompts/                  # System prompts
│   │   ├── __init__.py
│   │   └── system_prompts.py
│   └── guardrails/               # Safety checks
│       ├── __init__.py
│       └── safety_checks.py
├── sandbox_server/               # Python execution server
│   ├── main.py                   # FastAPI server
│   ├── requirements.txt          # Sandbox dependencies
│   └── Dockerfile               # Container definition
├── requirements.txt              # Main dependencies
├── .env.template                # Environment template
├── run_agent.py                 # Main execution script
└── README.md                    # This file
```

## 🔍 Advanced Usage

### Custom Analysis Workflows

The agent follows a structured Plan-Code-Execute-Reflect cycle:

1. **Plan**: Analyzes the request and creates an execution strategy
2. **Code**: Generates appropriate Python code for the analysis
3. **Execute**: Runs code in the secure sandbox environment
4. **Reflect**: Interprets results and handles any errors

### Error Handling and Debugging

The agent automatically:
- Detects and analyzes Python execution errors
- Attempts to debug and fix code issues
- Retries execution with corrected code
- Provides detailed error reporting if fixes fail

### Database Integration

Connect to databases by setting connection strings in environment:

```env
TARGET_DB_CONNECTION_URI=postgresql://user:password@host:port/database
```

The agent generates SQL queries and handles database connections securely.

## 🐳 Docker Deployment

### Sandbox Server

```bash
cd sandbox_server
docker build -t data-analyzer-sandbox .
docker run -p 8000:8000 data-analyzer-sandbox
```

### Full Stack Deployment

See the development guide for production deployment with gVisor security.

## 🧪 Testing

Run example queries to test functionality:

```bash
python run_agent.py
# Choose option 2: "Run example queries"
```

Available test scenarios:
- Simple CSV Analysis
- JSON Data Processing  
- Statistical Analysis
- Data Visualization
- Complex Multi-variable Analysis

## 📚 Documentation

- **Development Guide**: See `Data Analyzer Agent Development.md` for detailed implementation guide
- **API Reference**: Sandbox server API at `http://localhost:8000/docs` when running
- **Prompt Engineering**: Advanced prompting techniques in the development guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the OpenAI Agents ecosystem. See individual license files for details.

## 🆘 Troubleshooting

### Common Issues

1. **Sandbox server not running**:
   ```bash
   uvicorn sandbox_server.main:app --reload --port 8000
   ```

2. **OpenAI API key not configured**:
   - Check `.env` file has `OPENAI_API_KEY` set
   - Verify API key is valid and has sufficient credits

3. **Module import errors**:
   ```bash
   pip install -r requirements.txt
   pip install -r sandbox_server/requirements.txt
   ```

4. **Permission errors**:
   - Ensure proper file permissions
   - Check virtual environment activation

### Debug Mode

Enable detailed logging:

```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Support

For issues and questions:
- Check the development guide for detailed explanations
- Review error logs for specific issues
- Ensure all dependencies are properly installed

---

## 🚀 Next Steps

Once you have the basic setup running:

1. **Explore Examples**: Run the provided example queries to understand capabilities
2. **Custom Analyses**: Try your own data analysis tasks
3. **Advanced Features**: Explore multi-model strategies and custom guardrails
4. **Production Deployment**: Follow security guidelines for production use

Happy analyzing! 📊✨
