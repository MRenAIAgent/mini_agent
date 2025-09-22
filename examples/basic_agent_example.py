#!/usr/bin/env python3
"""
Basic Core Agent Example

Demonstrates the essential usage of the core agent system
with minimal dependencies and setup.
"""

import asyncio
from typing import Dict, Any

# Import core agent components
from ..agent import CoreAgent
from ..tools.tool_interfaces import BaseTool, ToolDefinition, ToolParameter, ToolCall, ToolResult


class CalculatorTool(BaseTool):
    """Simple calculator tool for demonstration."""

    def __init__(self):
        definition = ToolDefinition(
            name="calculator",
            description="Perform basic arithmetic calculations",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Mathematical expression to evaluate (e.g., '2 + 3 * 4')",
                    required=True
                )
            ],
            category="math"
        )
        super().__init__(definition)

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute calculator operations."""
        import time
        start_time = time.time()

        try:
            expression = tool_call.arguments.get("expression", "")

            # Simple expression evaluation (restricted for safety)
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Expression contains invalid characters")

            # Evaluate safely
            result = eval(expression)

            return ToolResult(
                call_id=tool_call.id,
                success=True,
                result=str(result),
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Calculation error: {str(e)}",
                execution_time=time.time() - start_time
            )


class WeatherTool(BaseTool):
    """Mock weather tool for demonstration."""

    def __init__(self):
        definition = ToolDefinition(
            name="weather",
            description="Get current weather information for a location",
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="City or location name",
                    required=True
                )
            ],
            category="information"
        )
        super().__init__(definition)

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute weather lookup (mock implementation)."""
        import time
        import random
        start_time = time.time()

        try:
            location = tool_call.arguments.get("location", "Unknown")

            # Mock weather data
            temperatures = [15, 18, 22, 25, 28, 30, 33]
            conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "stormy"]

            temp = random.choice(temperatures)
            condition = random.choice(conditions)

            result = f"Weather in {location}: {temp}°C, {condition}"

            return ToolResult(
                call_id=tool_call.id,
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Weather lookup error: {str(e)}",
                execution_time=time.time() - start_time
            )


async def mock_llm_function(prompt: str) -> str:
    """
    Mock LLM function for demonstration.

    In a real implementation, this would call an actual LLM API.
    """
    # Simulate API delay
    await asyncio.sleep(0.1)

    # Simple pattern matching for demonstration
    prompt_lower = prompt.lower()

    if "calculator" in prompt_lower and "expression" in prompt_lower:
        return """Thought: I need to use the calculator tool to evaluate this mathematical expression.

Action: calculator
Action Input: {"expression": "2 + 3 * 4"}"""

    elif "weather" in prompt_lower:
        if "paris" in prompt_lower:
            location = "Paris"
        elif "london" in prompt_lower:
            location = "London"
        elif "new york" in prompt_lower:
            location = "New York"
        else:
            location = "Unknown City"

        return f"""Thought: I need to get weather information for this location.

Action: weather
Action Input: {{"location": "{location}"}}"""

    elif "hello" in prompt_lower or "hi" in prompt_lower:
        return """Thought: The user is greeting me. I should respond politely.

Final Answer: Hello! I'm a core agent with access to various tools. I can help you with calculations, weather information, and more. What would you like to know?"""

    elif "what can you do" in prompt_lower or "capabilities" in prompt_lower:
        return """Thought: The user is asking about my capabilities.

Final Answer: I'm a core agent with several capabilities:

1. **Mathematical Calculations**: I can solve arithmetic expressions using my calculator tool
2. **Weather Information**: I can provide weather updates for different locations
3. **Memory**: I can remember our conversation and relevant information
4. **Reasoning**: I use ReAct (Reasoning and Acting) to think through problems step by step

What would you like me to help you with?"""

    else:
        return """Thought: I should provide a helpful response based on what the user is asking.

Final Answer: I understand you're asking me something, but I'm not sure exactly what you need. Could you please be more specific? I can help with calculations, weather information, and various other tasks using my available tools."""


async def demonstrate_basic_usage():
    """Demonstrate basic core agent usage."""
    print("🤖 Core Agent Basic Usage Demo")
    print("=" * 50)

    # Create a core agent
    agent = CoreAgent(
        llm_function=mock_llm_function,
        system_prompt="You are a helpful assistant with access to tools.",
        max_iterations=3,
        enable_memory=True,
        enable_optimization=False
    )

    # Start the agent
    await agent.start()

    try:
        # Add tools
        calculator = CalculatorTool()
        weather = WeatherTool()

        await agent.add_tool(calculator)
        await agent.add_tool(weather)

        print(f"✓ Agent started with session ID: {agent.session_id}")
        print(f"✓ Added tools: {[tool.name for tool in [calculator, weather]]}")
        print()

        # Test basic interactions
        test_inputs = [
            "Hello! What can you do?",
            "What's 15 + 27?",
            "How's the weather in Paris?",
            "Calculate 100 / 4 + 6"
        ]

        for i, user_input in enumerate(test_inputs, 1):
            print(f"Test {i}: {user_input}")
            response = await agent.run(user_input)
            print(f"Response: {response}")
            print("-" * 30)

        # Show agent statistics
        print("\n📊 Agent Statistics:")
        stats = agent.get_agent_stats()
        print(f"Session ID: {stats['session_id']}")
        print(f"Tools available: {stats['tools']['registry']['total_tools']}")
        print(f"Tool executions: {stats['tools']['execution']['total_executions']}")
        print(f"Memory enabled: {stats['components']['memory_enabled']}")

    finally:
        # Clean up
        await agent.stop()
        print("\n✓ Agent stopped and cleaned up")


async def demonstrate_memory_features():
    """Demonstrate memory capabilities."""
    print("\n🧠 Memory Features Demo")
    print("=" * 30)

    agent = CoreAgent(
        llm_function=mock_llm_function,
        system_prompt="You are a helpful assistant that remembers important information.",
        enable_memory=True
    )

    await agent.start()

    try:
        # Store some memories
        print("Storing memories...")
        await agent.remember("User prefers metric units for temperature", importance=0.8)
        await agent.remember("User is working on a math project", importance=0.6)
        await agent.remember("User lives in Paris, France", importance=0.9)

        # Test recall
        print("\nRecalling memories about 'temperature':")
        memories = await agent.recall("temperature")
        for memory in memories:
            print(f"- {memory['content']} (importance: {memory['importance']})")

        print("\nRecalling memories about 'Paris':")
        memories = await agent.recall("Paris")
        for memory in memories:
            print(f"- {memory['content']} (importance: {memory['importance']})")

        # Get context summary
        summary = await agent.get_context_summary()
        print(f"\nContext summary: {summary}")

    finally:
        await agent.stop()


async def demonstrate_tool_integration():
    """Demonstrate tool integration features."""
    print("\n🔧 Tool Integration Demo")
    print("=" * 35)

    agent = CoreAgent(
        llm_function=mock_llm_function,
        system_prompt="You are a helpful assistant with calculator and weather tools."
    )

    await agent.start()

    try:
        # Add tools
        await agent.add_tool(CalculatorTool())
        await agent.add_tool(WeatherTool(), aliases=["weather_check", "forecast"])

        # List available tools
        tools = agent.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

        print("\nTesting tool execution...")

        # Test calculator
        response = await agent.run("What's 25 * 4 + 10?")
        print(f"Math question response: {response}")

        # Test weather
        response = await agent.run("What's the weather like in London?")
        print(f"Weather question response: {response}")

    finally:
        await agent.stop()


async def main():
    """Main demonstration function."""
    print("🌟 Core Agent System Demo")
    print("=" * 60)
    print("This demo shows the core agent capabilities:")
    print("- ReAct execution loop")
    print("- Tool integration")
    print("- Memory management")
    print("- Basic conversation handling")
    print()

    try:
        # Run demonstrations
        await demonstrate_basic_usage()
        await demonstrate_memory_features()
        await demonstrate_tool_integration()

        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Replace mock_llm_function with real LLM API calls")
        print("2. Add more sophisticated tools")
        print("3. Enable prompt optimization with training data")
        print("4. Connect to MCP servers for additional capabilities")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())