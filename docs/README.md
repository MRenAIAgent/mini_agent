# Core Agent System

A lightweight, extensible agent framework that provides essential components for building autonomous AI agents with reasoning, memory, optimization, and tool capabilities.

## Overview

The Core Agent System is designed to be minimal yet powerful, providing a clean foundation for building sophisticated AI agents. It integrates four core components:

1. **ReAct Execution Loop** - Reasoning and Acting cycle for step-by-step problem solving
2. **Memory Management** - Context retention and long-term memory storage
3. **Prompt Optimization** - Adaptive improvement through multiple optimization strategies
4. **Tool/MCP Integration** - External capabilities through tools and Model Context Protocol

## 🎯 NEW: Rich Tracing & Debugging

**Beautiful, local-only agent tracing with no external services required!**

```python
from agent import CoreAgent

# Create agent with Rich + StructLog tracing enabled
agent = CoreAgent(
    llm_function=your_llm_function,
    system_prompt="You are a helpful AI assistant",
    enable_tracing=True  # 🚀 Beautiful console tracing!
)

# Watch beautiful colored output as your agent runs
response = await agent.run("What's the weather like?")

# See clean, hierarchical tracing:
#   🚀 agent.run [self_type=CoreAgent]
#     🚀 llm.call [prompt=571chars]
#     ✅ llm.call (104ms)
#   ✅ agent.run (108ms)
```

**Run the demo:** `python test_tracing_demo.py`

## Quick Start

```python
import asyncio
from core_agent import CoreAgent
from core_agent.integrations import LLMConfig, create_llm_function

async def main():
    # Configure LLM provider
    llm_config = LLMConfig(
        provider="openai",  # or "anthropic", "mock", etc.
        model="gpt-4",
        api_key="your-api-key"
    )

    # Create LLM function
    llm_function = await create_llm_function(llm_config)

    # Create agent
    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a helpful AI assistant.",
        enable_memory=True,
        enable_optimization=False
    )

    await agent.start()

    try:
        # Basic interaction
        response = await agent.run("Hello! How can you help me?")
        print(response)

        # Remember something important
        await agent.remember("User prefers detailed explanations", importance=0.8)

        # Continue conversation with context
        response = await agent.run("Explain machine learning to me")
        print(response)

    finally:
        await agent.stop()

asyncio.run(main())
```

## 🔍 Rich Tracing Features

### What Gets Traced
- **🚀 Agent execution** - Run methods, reasoning steps, responses
- **🧠 LLM calls** - Prompts, responses, timing, context
- **🛠️ Tool calls** - Arguments, results, success/failure
- **❌ Errors** - Full stack traces with context
- **📊 Performance** - Execution time, span correlation

### Clean Tracing Output
```bash
  🚀 agent.run [self_type=CoreAgent]
    🚀 llm.call [model=gpt-4, prompt=571chars]
    ✅ llm.call (104ms)
    🚀 tool.calculator [operation=add, a=15, b=23]
    ✅ tool.calculator (23ms)
  ✅ agent.run (127ms)
```

### Custom Decorators
```python
from observability import trace_agent_execution, trace_llm_call, trace_tool_call

@trace_agent_execution("my.custom.step")
async def my_processing_step(data):
    return processed_data

@trace_llm_call("gpt-4")
async def call_llm(prompt):
    return await llm_call(prompt)
```

## Core Components

### 1. ReAct Execution Loop

The ReAct (Reasoning and Acting) executor provides structured thinking for complex problem solving:

```python
from core_agent.execution import ReactExecutor, ExecutionContext

# Create executor
executor = ReactExecutor(
    llm_call=your_llm_function,
    tool_call=your_tool_function,
    max_iterations=5
)

# Execute with reasoning
result = await executor.execute(
    user_input="What's the weather in Paris and what should I wear?",
    system_prompt="You are a helpful travel assistant."
)

print(f"Final answer: {result.final_answer}")
print(f"Iterations used: {result.iterations_used}")
```

### 2. Memory Management

Flexible memory system supporting different backends:

```python
from core_agent.memory import CoreMemoryManager
from core_agent.integrations import MemoryConnection, MemoryBackendType

# Configure memory backend
memory_connection = MemoryConnection(
    backend_type=MemoryBackendType.IN_MEMORY  # or MEMGRAPH, NEO4J, etc.
)

# Create memory manager
memory_manager = CoreMemoryManager()
await memory_manager.start()

# Store and retrieve memories
await memory_manager.store_memory(
    content="User is working on a Python project",
    importance=0.8,
    session_id="session_123"
)

memories = await memory_manager.search_memory(
    query="Python programming",
    session_id="session_123"
)
```

### 3. Prompt Optimization

Multiple optimization strategies for adaptive improvement:

```python
from core_agent.optimization import CoreOptimizer, TrainingExample

# Create optimizer
optimizer = CoreOptimizer()

# Prepare training examples
examples = [
    TrainingExample(
        input="What is 2 + 2?",
        expected_output="The answer is 4."
    ),
    # ... more examples
]

# Optimize prompt
result = await optimizer.optimize(
    initial_prompt="You are a helpful math assistant.",
    training_examples=examples,
    agent_evaluator=your_agent_evaluator
)

if result.success:
    print(f"Optimized prompt: {result.optimized_prompt}")
    print(f"Improvement: {result.improvement:.2%}")
```

### 4. Tool Integration

Unified interface for tools and external services:

```python
from core_agent.tools import ToolManager
from core_agent.integrations import ToolConnection, ToolProviderType

# Create tool manager
tool_manager = ToolManager()

# Add local tools
await tool_manager.register_tool(your_custom_tool)

# Connect to external providers
connection = ToolConnection(
    provider_type=ToolProviderType.REST_API,
    name="weather_service",
    endpoint="https://api.weather.com"
)

# Execute tools
result = await tool_manager.execute_tool_by_name(
    name="weather",
    arguments={"city": "Paris"}
)
```

## Integration Interfaces

The core agent supports multiple integration points for maximum flexibility:

### LLM Providers

```python
from core_agent.integrations import LLMConfig, LLMProviderFactory

# OpenAI
openai_config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-key",
    temperature=0.7
)

# Anthropic
anthropic_config = LLMConfig(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key="your-key"
)

# Local model
local_config = LLMConfig(
    provider="local",
    model="llama-2-7b",
    base_url="http://localhost:8080"
)
```

### Memory Backends

```python
from core_agent.integrations import MemoryConnection, MemoryBackendType

# In-memory (for development)
memory_config = MemoryConnection(
    backend_type=MemoryBackendType.IN_MEMORY
)

# Memgraph
memgraph_config = MemoryConnection(
    backend_type=MemoryBackendType.MEMGRAPH,
    host="localhost",
    port=7687,
    username="memgraph",
    password="password"
)

# Neo4j
neo4j_config = MemoryConnection(
    backend_type=MemoryBackendType.NEO4J,
    connection_string="bolt://localhost:7687",
    username="neo4j",
    password="password"
)
```

### External Tool Providers

```python
from core_agent.integrations import ToolConnection, ToolProviderType

# REST API
rest_config = ToolConnection(
    provider_type=ToolProviderType.REST_API,
    name="api_service",
    endpoint="https://api.example.com",
    authentication={"type": "bearer", "token": "your-token"}
)

# MCP Server
mcp_config = ToolConnection(
    provider_type=ToolProviderType.MCP_SERVER,
    name="file_server",
    endpoint="stdio:///path/to/mcp/server"
)
```

## Examples

The `examples/` directory contains comprehensive demonstrations:

- **`basic_agent_example.py`** - Simple agent setup with mock LLM
- **`integration_example.py`** - Integration with different providers
- **`advanced_features.py`** - Memory, optimization, and tool usage

Run examples:

```bash
cd core_agent/examples
python basic_agent_example.py
python integration_example.py
```

## Architecture

```
Core Agent System
├── execution/          # ReAct execution loop
│   ├── react_executor.py
│   ├── context.py
│   └── result.py
├── memory/             # Memory management
│   ├── memory_manager.py
│   ├── context.py
│   └── storage.py
├── optimization/       # Prompt optimization
│   ├── core_optimizer.py
│   ├── strategies/
│   └── metrics.py
├── tools/              # Tool management
│   ├── tool_manager.py
│   ├── registry.py
│   └── mcp_adapter.py
├── integrations/       # Provider interfaces
│   ├── llm_interfaces.py
│   ├── memory_interfaces.py
│   └── tool_interfaces.py
└── agent.py           # Main CoreAgent class
```

## Configuration

### Agent Configuration

```python
agent = CoreAgent(
    llm_function=llm_function,           # Required: LLM function
    system_prompt="Your prompt here",    # Agent's base prompt
    max_iterations=5,                    # Max ReAct iterations
    enable_memory=True,                  # Enable memory system
    enable_optimization=False,           # Enable prompt optimization
    session_id="unique_session"          # Optional session ID
)
```

### Advanced Configuration

```python
# Custom memory backend
from core_agent.integrations import MemoryBackendFactory

custom_backend = MemoryBackendFactory.create_backend(memory_connection)
agent.memory_manager.set_backend(custom_backend)

# Custom optimization strategy
agent.optimizer.set_strategy("coordinate_ascent")

# Tool execution callback
async def on_tool_executed(tool_call, result):
    print(f"Tool {tool_call.name} executed: {result.success}")

agent.tool_manager.set_execution_callback(on_tool_executed)
```

## Performance

The core agent is designed for efficiency:

- **Lightweight**: Minimal dependencies and overhead
- **Async**: Full async/await support for concurrent operations
- **Modular**: Only load components you need
- **Scalable**: Supports connection pooling and caching

Typical performance metrics:
- Agent initialization: < 100ms
- Simple query: 200-500ms (depending on LLM)
- Memory operations: < 50ms (in-memory), < 200ms (graph DB)
- Tool execution: Varies by tool complexity

## Testing

The system includes comprehensive testing utilities:

```python
from core_agent.integrations import MockLLMProvider, InMemoryBackend

# Create test agent
mock_llm = MockLLMProvider()
mock_llm.set_default_response("Test response")

test_agent = CoreAgent(
    llm_function=mock_llm.generate,
    enable_memory=False
)

# Test interactions
response = await test_agent.run("Test input")
assert "Test response" in response
```

## Extending the System

### Custom LLM Provider

```python
from core_agent.integrations import LLMProvider, LLMResponse

class CustomLLMProvider(LLMProvider):
    async def generate(self, prompt, system_prompt=None, **kwargs):
        # Your custom LLM implementation
        response = await your_llm_api(prompt)

        return LLMResponse(
            content=response.text,
            model=self.config.model,
            tokens_used=response.tokens,
            latency_ms=response.latency
        )

# Register provider
LLMProviderFactory.register_provider("custom", CustomLLMProvider)
```

### Custom Memory Backend

```python
from core_agent.integrations import MemoryBackend

class CustomMemoryBackend(MemoryBackend):
    async def store_entry(self, entry):
        # Your storage implementation
        pass

    async def retrieve_entries(self, query):
        # Your retrieval implementation
        pass

# Register backend
MemoryBackendFactory.register_backend(
    MemoryBackendType.CUSTOM,
    CustomMemoryBackend
)
```

### Custom Tool

```python
from core_agent.tools import BaseTool, ToolDefinition

class CustomTool(BaseTool):
    def __init__(self):
        definition = ToolDefinition(
            name="custom_tool",
            description="My custom tool",
            parameters=[...],
            category="custom"
        )
        super().__init__(definition)

    async def execute(self, tool_call):
        # Your tool implementation
        pass

# Add to agent
await agent.add_tool(CustomTool())
```

## Best Practices

1. **Start Simple**: Begin with mock providers, then integrate real services
2. **Monitor Performance**: Use built-in statistics and health checks
3. **Handle Errors**: Implement proper error handling and fallbacks
4. **Optimize Prompts**: Use the optimization framework with training data
5. **Manage Memory**: Regular cleanup and importance-based filtering
6. **Test Thoroughly**: Use mock providers for unit testing

## Troubleshooting

### Common Issues

**Agent not responding**
```python
# Check LLM configuration
health = await agent.llm_provider.validate_connection()
print(f"LLM connected: {health}")
```

**Memory issues**
```python
# Check memory statistics
stats = await agent.memory_manager.get_memory_stats()
print(f"Memory entries: {stats.total_entries}")
```

**Tool failures**
```python
# Check tool status
tool_stats = agent.tool_manager.get_execution_stats()
print(f"Success rate: {tool_stats['success_rate']}%")
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
agent = CoreAgent(
    llm_function=llm_function,
    debug=True  # Enables detailed execution logging
)
```

## Contributing

The core agent system is designed to be extensible. To contribute:

1. Follow the existing patterns for new providers
2. Add comprehensive tests for new components
3. Update documentation for new features
4. Ensure backward compatibility

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Check the examples directory
- Review integration interfaces
- Use mock providers for testing
- Monitor agent statistics for debugging