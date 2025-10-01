#!/usr/bin/env python3
"""
Test script to demonstrate Rich + StructLog tracing functionality.

This script shows how the agent tracing works with beautiful console output
and structured logging for debugging AI agent execution.
"""

import asyncio
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent import CoreAgent
    from observability import configure_tracing, get_console, get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install dependencies: pip install rich structlog")
    sys.exit(1)


# Mock LLM function for testing
async def mock_llm_call(prompt: str) -> str:
    """Mock LLM function that simulates thinking and provides ReAct-formatted responses."""
    # Simulate processing time
    await asyncio.sleep(0.1)

    if "hello" in prompt.lower():
        return """Thought: The user is greeting me. I should respond in a friendly and helpful manner.
Final Answer: Hello! I'm a test agent. How can I help you today?"""

    elif "weather" in prompt.lower():
        return """Thought: The user is asking about the weather. I would need to use a weather tool to get current weather information, but I don't have access to one in this demo.
Final Answer: I would need to use a weather tool to get current weather information. Unfortunately, I don't have access to a weather service in this demo, but in a real scenario I would check the current weather conditions for you."""

    elif "math" in prompt.lower() or "calculate" in prompt.lower():
        if "15 * 23" in prompt:
            return """Thought: The user wants me to calculate 15 × 23. I can do this calculation directly.
Final Answer: I can help with that calculation! 15 × 23 = 345."""
        else:
            return """Thought: The user is asking about math or calculations. I should offer to help with their specific calculation.
Final Answer: I can help with math! For example, 2 + 2 = 4. What specific calculation would you like me to do?"""

    else:
        return """Thought: The user has made a request. I should provide a helpful response while being honest about my capabilities in this demo.
Final Answer: I understand your request. Let me think about this step by step and provide a helpful response based on what I can do in this demo environment."""


class TestTool:
    """Simple test tool for demonstration."""

    def __init__(self, name: str):
        self.name = name

    async def execute(self, **kwargs) -> dict:
        """Execute the test tool."""
        await asyncio.sleep(0.05)  # Simulate tool execution time
        return {
            "success": True,
            "result": f"Tool '{self.name}' executed successfully with args: {kwargs}"
        }


async def test_agent_tracing():
    """Test agent tracing with various operations."""
    console = get_console()
    logger = get_logger()

    if console:
        console.print("\n[bold blue]🚀 Starting Agent Tracing Demo[/bold blue]")
        console.print("=" * 60)

    # Initialize agent with tracing enabled
    agent = CoreAgent(
        llm_function=mock_llm_call,
        system_prompt="You are a helpful AI assistant that can answer questions and use tools.",
        enable_memory=False,  # Disable memory for simpler demo
        enable_optimization=False,
        enable_tracing=True,  # Enable our Rich + StructLog tracing
        session_id="demo_session"
    )

    await agent.start()

    if console:
        console.print("\n[bold green]Agent initialized successfully![/bold green]\n")

    # Test cases to demonstrate tracing
    test_cases = [
        "Hello, how are you?",
        "What's the weather like today?",
        "Can you help me calculate 15 * 23?",
    ]

    try:
        for i, test_input in enumerate(test_cases, 1):
            if console:
                console.print(f"\n[bold yellow]📝 Test Case {i}:[/bold yellow] {test_input}")
                console.print("-" * 50)

            # This will trigger our tracing decorators
            response = await agent.run(test_input)

            if console:
                console.print(f"[bold green]🤖 Response:[/bold green] {response}")
                console.print()

    except Exception as e:
        if console:
            console.print(f"[red]❌ Error during testing: {e}[/red]")
        logger.error("Test failed", error=str(e))
        raise

    finally:
        await agent.stop()
        if console:
            console.print("\n[bold blue]🏁 Agent Tracing Demo Completed![/bold blue]")


async def test_individual_decorators():
    """Test individual decorator functions."""
    console = get_console()

    if console:
        console.print("\n[bold blue]🔧 Testing Individual Decorators[/bold blue]")
        console.print("=" * 60)

    # Import decorators
    from observability import trace_agent_execution, trace_llm_call, trace_tool_call

    @trace_agent_execution("demo.processing")
    async def demo_processing(data: str):
        """Demo function with agent execution tracing."""
        await asyncio.sleep(0.1)
        return f"Processed: {data}"

    @trace_llm_call("mock-gpt-4")
    async def demo_llm_call(prompt: str):
        """Demo function with LLM call tracing."""
        await asyncio.sleep(0.2)
        return f"LLM Response to: {prompt[:50]}..."

    @trace_tool_call("calculator")
    async def demo_tool_call(operation: str, a: int, b: int):
        """Demo function with tool call tracing."""
        await asyncio.sleep(0.05)
        if operation == "add":
            return {"success": True, "result": a + b}
        return {"success": False, "error": "Unknown operation"}

    # Test the decorated functions
    try:
        result1 = await demo_processing("test data")
        if console:
            console.print(f"Processing result: {result1}")

        result2 = await demo_llm_call("What is the meaning of life?")
        if console:
            console.print(f"LLM result: {result2}")

        result3 = await demo_tool_call("add", 42, 13)
        if console:
            console.print(f"Tool result: {result3}")

    except Exception as e:
        if console:
            console.print(f"[red]❌ Error in decorator testing: {e}[/red]")


def print_setup_info():
    """Print setup information and requirements."""
    console = get_console()

    if console:
        console.print("""
[bold blue]📋 Detailed Clean Tracing - Best of Both Worlds[/bold blue]

[green]✅ Features:[/green]
• [bold]All detailed information from original format[/bold]
• Clean, hierarchical structure - easy to follow
• Span IDs for correlation and debugging
• Prompt previews and response content
• Proper indentation showing execution nesting
• Color-coded status: 🚀 starting, ✅ success, ❌ error

[yellow]📊 What you'll see:[/yellow]
• [blue]🚀 agent.run[/blue] (span: abc123def)
  └─ input: "What's the weather?"
  └─ type: CoreAgent
• [blue]🚀 llm.call[/blue] (span: def456ghi)
  └─ parent_span: abc123def
  └─ model: gpt-4
  └─ prompt_length: 571 chars
  └─ prompt_preview: "You are following the ReAct..."
• [green]✅ llm.call[/green] (104ms)
  └─ response_length: 87 chars
  └─ response_preview: "I would need to use a weather tool..."

[cyan]🎯 Detailed clean format shows:[/cyan]
• All trace information in organized structure
• Span correlation IDs for debugging
• Full prompt and response previews
• Execution hierarchy and timing
• No messy ANSI color codes

[dim]💡 Perfect for debugging with all the details you need![/dim]
""")


async def main():
    """Main demo function."""
    try:
        # Configure tracing with detailed format for rich information
        configure_tracing(clean_format=True, detailed=True)

        print_setup_info()

        # Test individual decorators
        await test_individual_decorators()

        # Test full agent with tracing
        await test_agent_tracing()

        console = get_console()
        if console:
            console.print("\n[bold green]🎉 All tests completed successfully![/bold green]")
            console.print("\n[dim]Now you can see all the detailed trace information in a clean, readable format![/dim]")

    except Exception as e:
        console = get_console()
        if console:
            console.print(f"\n[red]❌ Demo failed with error: {e}[/red]")
        raise


if __name__ == "__main__":
    # Run the demo
    print("🔍 Rich + StructLog Agent Tracing Demo")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)