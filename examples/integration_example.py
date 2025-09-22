#!/usr/bin/env python3
"""
Integration Example

Demonstrates how to use the core agent with different integration
interfaces for LLM providers, memory backends, and external tools.
"""

import asyncio
from typing import Dict, Any

from ..agent import CoreAgent
from ..integrations.llm_interfaces import LLMConfig, create_llm_function
from ..integrations.memory_interfaces import MemoryConnection, MemoryBackendType
from ..integrations.tool_interfaces import ToolConnection, ToolProviderType
from ..tools.tool_interfaces import BaseTool, ToolDefinition, ToolParameter, ToolCall, ToolResult


class ExampleTool(BaseTool):
    """Example tool for demonstration."""

    def __init__(self):
        definition = ToolDefinition(
            name="example_tool",
            description="An example tool for testing integration",
            parameters=[
                ToolParameter(
                    name="message",
                    type="string",
                    description="Message to process",
                    required=True
                )
            ],
            category="example"
        )
        super().__init__(definition)

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute the example tool."""
        import time
        start_time = time.time()

        try:
            message = tool_call.arguments.get("message", "")
            result = f"Processed: {message}"

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
                error=f"Tool error: {str(e)}",
                execution_time=time.time() - start_time
            )


async def demonstrate_llm_integration():
    """Demonstrate LLM provider integration."""
    print("🤖 LLM Provider Integration Demo")
    print("=" * 50)

    # Create LLM configuration
    llm_config = LLMConfig(
        provider="mock",
        model="mock-gpt-4",
        temperature=0.7,
        max_tokens=1000
    )

    # Create LLM function from config
    llm_function = await create_llm_function(llm_config)

    # Create agent with LLM integration
    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a helpful assistant that demonstrates LLM integration.",
        enable_memory=False,
        enable_optimization=False
    )

    await agent.start()

    try:
        # Test LLM integration
        response = await agent.run("Hello! Can you tell me about LLM integration?")
        print(f"Agent response: {response}")

        # Test math calculation
        response = await agent.run("What is 25 + 17?")
        print(f"Math response: {response}")

    finally:
        await agent.stop()

    print("✓ LLM integration demo completed\n")


async def demonstrate_memory_integration():
    """Demonstrate memory backend integration."""
    print("🧠 Memory Backend Integration Demo")
    print("=" * 50)

    # Create memory connection configuration
    memory_connection = MemoryConnection(
        backend_type=MemoryBackendType.IN_MEMORY
    )

    # Create agent with memory integration
    llm_config = LLMConfig(provider="mock", model="mock-model")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a helpful assistant with memory capabilities.",
        enable_memory=True,
        enable_optimization=False
    )

    await agent.start()

    try:
        # Store some memories
        await agent.remember("User prefers detailed explanations", importance=0.8)
        await agent.remember("User is interested in AI and technology", importance=0.9)
        await agent.remember("Last conversation was about machine learning", importance=0.7)

        print("✓ Stored memories")

        # Test memory recall
        memories = await agent.recall("AI technology")
        print(f"Recalled {len(memories)} memories about AI technology:")
        for memory in memories:
            print(f"  - {memory['content']} (importance: {memory['importance']})")

        # Test contextual conversation
        response = await agent.run("Tell me about artificial intelligence")
        print(f"Contextual response: {response}")

    finally:
        await agent.stop()

    print("✓ Memory integration demo completed\n")


async def demonstrate_tool_integration():
    """Demonstrate external tool integration."""
    print("🔧 External Tool Integration Demo")
    print("=" * 50)

    # Create tool connection configuration
    tool_connection = ToolConnection(
        provider_type=ToolProviderType.FUNCTION,
        name="example_provider"
    )

    # Create agent
    llm_config = LLMConfig(provider="mock", model="mock-model")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a helpful assistant with access to external tools.",
        enable_memory=False,
        enable_optimization=False
    )

    await agent.start()

    try:
        # Add local tool
        example_tool = ExampleTool()
        await agent.add_tool(example_tool)

        # List available tools
        tools = agent.list_tools()
        print(f"Available tools: {[tool['name'] for tool in tools]}")

        # Test tool usage
        response = await agent.run("Use the example tool to process the message 'Hello World'")
        print(f"Tool usage response: {response}")

    finally:
        await agent.stop()

    print("✓ Tool integration demo completed\n")


async def demonstrate_full_integration():
    """Demonstrate full agent with all integrations."""
    print("🌟 Full Integration Demo")
    print("=" * 50)

    # Create configurations
    llm_config = LLMConfig(
        provider="mock",
        model="advanced-mock",
        temperature=0.8,
        max_tokens=2000
    )

    memory_connection = MemoryConnection(
        backend_type=MemoryBackendType.IN_MEMORY
    )

    # Create fully integrated agent
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="""You are an advanced AI assistant with:
- Access to various tools for problem solving
- Long-term memory for context retention
- Adaptive capabilities through optimization

You should provide helpful, detailed responses while utilizing your capabilities effectively.""",
        enable_memory=True,
        enable_optimization=False  # Disabled for this demo
    )

    await agent.start()

    try:
        # Add tools
        await agent.add_tool(ExampleTool())

        # Store initial context
        await agent.remember("User is exploring agent integration capabilities", importance=0.9)

        # Run a complex interaction
        print("Running complex interaction...")

        conversations = [
            "Hello! I'd like to understand how integrated agents work.",
            "Can you process this message: 'Integration test successful'?",
            "What do you remember about our conversation?",
            "Calculate 15 * 8 + 12"
        ]

        for i, user_input in enumerate(conversations, 1):
            print(f"\nConversation {i}:")
            print(f"User: {user_input}")
            response = await agent.run(user_input)
            print(f"Agent: {response}")

        # Show agent statistics
        print("\n📊 Agent Statistics:")
        stats = agent.get_agent_stats()
        print(f"Session ID: {stats['session_id']}")
        print(f"Memory enabled: {stats['components']['memory_enabled']}")
        print(f"Optimization enabled: {stats['components']['optimization_enabled']}")
        print(f"Tools available: {stats['tools']['registry']['total_tools']}")
        print(f"Tool executions: {stats['tools']['execution']['total_executions']}")

    finally:
        await agent.stop()

    print("\n✓ Full integration demo completed")


async def main():
    """Main demonstration function."""
    print("🚀 Core Agent Integration Demonstrations")
    print("=" * 60)
    print("This demo shows how to integrate the core agent with different")
    print("providers for LLM, memory, and external tools.\n")

    try:
        # Run individual integration demos
        await demonstrate_llm_integration()
        await demonstrate_memory_integration()
        await demonstrate_tool_integration()

        # Run full integration demo
        await demonstrate_full_integration()

        print("\n🎉 All integration demos completed successfully!")
        print("\nNext steps:")
        print("1. Replace mock LLM with real provider (OpenAI, Anthropic, etc.)")
        print("2. Connect to real memory backend (Memgraph, Neo4j, etc.)")
        print("3. Add external tool providers (REST APIs, MCP servers, etc.)")
        print("4. Enable optimization with training data")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())