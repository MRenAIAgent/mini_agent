# Quickstart: Enhanced Agent Framework

> **Note**: This quickstart describes the target API after refactoring. Current implementation uses `llm_function` parameter. See `implementation-guide.md` for migration details.

## Installation & Setup

```bash
# Install the enhanced agent framework
pip install enhanced-agent-framework

# Optional: Install memory backends
pip install "enhanced-agent-framework[memgraph]"  # For graph memory
pip install "enhanced-agent-framework[redis]"     # For fast caching
```

## Basic Usage

### 1. Simple Agent with Auto Mode

```python
import asyncio
from enhanced_agent import EnhancedAgent, LLMConfig

async def main():
    # Configure LLM provider
    llm_config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key"
    )

    # Create agent with auto mode (intelligent pattern selection)
    agent = EnhancedAgent(llm_config=llm_config)
    await agent.start()

    try:
        # Simple query - uses fast mode automatically
        response = await agent.run("What is 2 + 2?")
        print(f"Simple: {response}")

        # Complex query - uses ReAct pattern automatically
        response = await agent.run(
            "Research the latest developments in quantum computing "
            "and summarize the key breakthroughs from 2024"
        )
        print(f"Complex: {response}")

    finally:
        await agent.stop()

asyncio.run(main())
```

### 2. Agent with Memory and Tools

```python
import asyncio
from enhanced_agent import EnhancedAgent, LLMConfig, MemoryConfig
from enhanced_agent.tools import WebSearchTool, CalculatorTool

async def main():
    # Configure with memory
    memory_config = MemoryConfig(
        backend_type="memgraph",
        connection_string="bolt://localhost:7687"
    )

    llm_config = LLMConfig(
        provider="anthropic",
        model="claude-3-sonnet",
        api_key="your-api-key"
    )

    agent = EnhancedAgent(
        llm_config=llm_config,
        memory_config=memory_config,
        enable_memory=True
    )

    # Add tools
    await agent.add_tool(WebSearchTool())
    await agent.add_tool(CalculatorTool())

    await agent.start()

    try:
        # Agent will remember this conversation
        response = await agent.run(
            "My name is John and I'm interested in machine learning. "
            "What are the best resources to get started?"
        )
        print(response)

        # Later in conversation - agent uses memory
        response = await agent.run(
            "Based on what I told you earlier, what specific ML project "
            "should I start with?"
        )
        print(response)

    finally:
        await agent.stop()

asyncio.run(main())
```

### 3. Streaming Responses

```python
import asyncio
from enhanced_agent import EnhancedAgent, LLMConfig

async def main():
    agent = EnhancedAgent(
        llm_config=LLMConfig(provider="openai", model="gpt-4", api_key="your-key"),
        enable_streaming=True
    )
    await agent.start()

    try:
        # Stream response for long-form content
        async for chunk in agent.run_stream(
            "Write a detailed explanation of how neural networks work"
        ):
            print(chunk, end="", flush=True)
        print()  # New line at end

    finally:
        await agent.stop()

asyncio.run(main())
```

### 4. Custom Execution Modes

```python
import asyncio
from enhanced_agent import EnhancedAgent, ExecutionMode

async def main():
    agent = EnhancedAgent(llm_config=your_llm_config)
    await agent.start()

    try:
        # Force simple mode for speed
        response = await agent.run(
            "Explain quantum computing",
            execution_mode=ExecutionMode.SIMPLE
        )

        # Force ReAct mode for complex reasoning
        response = await agent.run(
            "Plan a trip to Japan with budget analysis",
            execution_mode=ExecutionMode.REACT
        )

        # Force planning mode for multi-step tasks
        response = await agent.run(
            "Build a business plan for a sustainable energy startup",
            execution_mode=ExecutionMode.PLANNING
        )

    finally:
        await agent.stop()

asyncio.run(main())
```

### 5. MCP Server Integration

```python
import asyncio
from enhanced_agent import EnhancedAgent
from enhanced_agent.mcp import MCPServerConfig

async def main():
    agent = EnhancedAgent(llm_config=your_llm_config)

    # Connect to MCP server for file operations
    mcp_config = MCPServerConfig(
        server_path="./mcp-servers/filesystem",
        server_args=["--root-dir", "/tmp/agent-workspace"]
    )

    await agent.connect_mcp_server("filesystem", mcp_config)
    await agent.start()

    try:
        response = await agent.run(
            "Create a Python script that calculates fibonacci numbers "
            "and save it to a file"
        )
        print(response)

    finally:
        await agent.stop()

asyncio.run(main())
```

### 6. Memory Management and Insights

```python
import asyncio
from enhanced_agent import EnhancedAgent

async def main():
    agent = EnhancedAgent(
        llm_config=your_llm_config,
        enable_memory=True
    )
    await agent.start()

    try:
        # Have some conversations
        await agent.run("I'm working on a Python project about data analysis")
        await agent.run("I'm using pandas and matplotlib")
        await agent.run("I need help with performance optimization")

        # Get memory insights
        summary = await agent.get_memory_summary()
        print(f"Conversation summary: {summary}")

        # Search memory explicitly
        memories = await agent.search_memory("Python data analysis")
        print(f"Found {len(memories)} relevant memories")

        # Get knowledge graph
        knowledge_graph = await agent.get_knowledge_graph()
        print(f"Knowledge graph has {len(knowledge_graph.nodes)} concepts")

    finally:
        await agent.stop()

asyncio.run(main())
```

### 7. Performance Benchmarking

```python
import asyncio
from enhanced_agent import EnhancedAgent, BenchmarkSuite

async def main():
    agent = EnhancedAgent(llm_config=your_llm_config)
    await agent.start()

    try:
        # Run benchmark against other frameworks
        benchmark = BenchmarkSuite()
        results = await benchmark.compare_frameworks(
            agent=agent,
            frameworks=["langchain", "langgraph"],
            test_suite="agent_reasoning"
        )

        print(f"Performance vs LangChain: {results.score_vs_langchain}")
        print(f"Performance vs LangGraph: {results.score_vs_langgraph}")
        print(f"Average response time: {results.avg_response_time_ms}ms")

    finally:
        await agent.stop()

asyncio.run(main())
```

## Configuration Examples

### Memory Configuration

```python
from enhanced_agent import MemoryConfig

# Memgraph for production
memory_config = MemoryConfig(
    backend_type="memgraph",
    connection_string="bolt://localhost:7687",
    cache_size=5000,
    decay_rate=0.01
)

# Redis for fast development
memory_config = MemoryConfig(
    backend_type="redis",
    connection_string="redis://localhost:6379",
    cache_size=10000
)

# In-memory for testing
memory_config = MemoryConfig(
    backend_type="in_memory",
    cache_size=1000
)
```

### LLM Configuration

```python
from enhanced_agent import LLMConfig

# OpenAI
llm_config = LLMConfig(
    provider="openai",
    model="gpt-4-turbo",
    api_key="sk-...",
    temperature=0.7,
    max_tokens=4000
)

# Anthropic
llm_config = LLMConfig(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key="sk-ant-...",
    temperature=0.3
)

# Local model via Ollama
llm_config = LLMConfig(
    provider="ollama",
    model="llama3:70b",
    base_url="http://localhost:11434"
)
```

## Quick Validation

Run this script to validate your setup:

```python
import asyncio
from enhanced_agent import EnhancedAgent, LLMConfig, validate_setup

async def validate():
    # Test basic functionality
    print("Testing basic agent setup...")

    llm_config = LLMConfig(
        provider="openai",  # Replace with your provider
        model="gpt-4",      # Replace with your model
        api_key="your-key"  # Replace with your API key
    )

    agent = EnhancedAgent(llm_config=llm_config)

    # Run validation suite
    results = await validate_setup(agent)

    if results.all_passed:
        print("✅ All tests passed! Your agent is ready to use.")
    else:
        print("❌ Some tests failed:")
        for test, result in results.test_results.items():
            status = "✅" if result.passed else "❌"
            print(f"  {status} {test}: {result.message}")

asyncio.run(validate())
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more advanced use cases
2. **Add Custom Tools**: Learn how to create and register your own tools
3. **Optimize Memory**: Configure memory backends for your specific use case
4. **Benchmark Performance**: Run comparisons against other agent frameworks
5. **Deploy**: See deployment guides for production environments

## Common Issues

### Memory Backend Connection

```python
# If Memgraph connection fails, try:
memory_config = MemoryConfig(
    backend_type="in_memory"  # Fallback to in-memory
)
```

### Tool Registration Errors

```python
# Validate tool before registration
tool = WebSearchTool()
validation_result = await agent.validate_tool(tool)
if validation_result.valid:
    await agent.add_tool(tool)
else:
    print(f"Tool validation failed: {validation_result.error}")
```

### LLM Provider Issues

```python
# Test LLM connection
try:
    agent = EnhancedAgent(llm_config=llm_config)
    await agent.start()
    response = await agent.run("Hello")
    print("LLM connection successful")
except Exception as e:
    print(f"LLM connection failed: {e}")
```

This quickstart gets you up and running with the Enhanced Agent Framework. For detailed documentation, visit the full API reference.