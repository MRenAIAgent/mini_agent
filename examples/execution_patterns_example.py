#!/usr/bin/env python3
"""
Execution Patterns Example

Demonstrates different execution patterns available in the core agent
and how they handle various types of tasks differently.
"""

import asyncio
from typing import Dict, Any

from ..agent import CoreAgent
from ..execution.execution_patterns import ExecutionPatternType
from ..integrations.llm_interfaces import LLMConfig, create_llm_function
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


async def demonstrate_react_pattern():
    """Demonstrate ReAct execution pattern."""
    print("🔄 ReAct Pattern Demo")
    print("=" * 40)

    # Create agent with ReAct pattern
    llm_config = LLMConfig(provider="mock", model="mock-react")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a helpful assistant that can use tools to solve problems.",
        execution_pattern=ExecutionPatternType.REACT,
        enable_pattern_selection=False,
        enable_memory=False
    )

    await agent.start()

    try:
        # Add calculator tool
        await agent.add_tool(CalculatorTool())

        # Test with a calculation task
        response = await agent.run_with_pattern(
            "What's 15 * 8 + 12?",
            ExecutionPatternType.REACT
        )
        print(f"Question: What's 15 * 8 + 12?")
        print(f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ ReAct pattern demo completed\n")


async def demonstrate_chain_of_thought():
    """Demonstrate Chain of Thought execution pattern."""
    print("🧠 Chain of Thought Pattern Demo")
    print("=" * 40)

    # Create agent with Chain of Thought pattern
    llm_config = LLMConfig(provider="mock", model="mock-cot")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a thoughtful assistant that explains your reasoning.",
        execution_pattern=ExecutionPatternType.CHAIN_OF_THOUGHT,
        enable_pattern_selection=False,
        enable_memory=False
    )

    await agent.start()

    try:
        # Test with a reasoning task
        response = await agent.run_with_pattern(
            "Explain why the sky appears blue during the day",
            ExecutionPatternType.CHAIN_OF_THOUGHT
        )
        print(f"Question: Explain why the sky appears blue during the day")
        print(f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ Chain of Thought pattern demo completed\n")


async def demonstrate_plan_and_execute():
    """Demonstrate Plan and Execute execution pattern."""
    print("📋 Plan and Execute Pattern Demo")
    print("=" * 40)

    # Create agent with Plan and Execute pattern
    llm_config = LLMConfig(provider="mock", model="mock-plan")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a strategic assistant that creates detailed plans.",
        execution_pattern=ExecutionPatternType.PLAN_AND_EXECUTE,
        enable_pattern_selection=False,
        enable_memory=False
    )

    await agent.start()

    try:
        # Test with a planning task
        response = await agent.run_with_pattern(
            "How would you organize a successful team meeting?",
            ExecutionPatternType.PLAN_AND_EXECUTE
        )
        print(f"Question: How would you organize a successful team meeting?")
        print(f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ Plan and Execute pattern demo completed\n")


async def demonstrate_reflection_pattern():
    """Demonstrate Reflection execution pattern."""
    print("🪞 Reflection Pattern Demo")
    print("=" * 40)

    # Create agent with Reflection pattern
    llm_config = LLMConfig(provider="mock", model="mock-reflection")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a thoughtful assistant that reflects on your answers.",
        execution_pattern=ExecutionPatternType.REFLECTION,
        enable_pattern_selection=False,
        enable_memory=False
    )

    await agent.start()

    try:
        # Test with an evaluation task
        response = await agent.run_with_pattern(
            "What are the pros and cons of remote work?",
            ExecutionPatternType.REFLECTION
        )
        print(f"Question: What are the pros and cons of remote work?")
        print(f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ Reflection pattern demo completed\n")


async def demonstrate_socratic_pattern():
    """Demonstrate Socratic questioning pattern."""
    print("❓ Socratic Pattern Demo")
    print("=" * 40)

    # Create agent with Socratic pattern
    llm_config = LLMConfig(provider="mock", model="mock-socratic")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a philosophical assistant that explores questions deeply.",
        execution_pattern=ExecutionPatternType.SOCRATIC,
        enable_pattern_selection=False,
        enable_memory=False
    )

    await agent.start()

    try:
        # Test with a philosophical question
        response = await agent.run_with_pattern(
            "What does it mean to be successful?",
            ExecutionPatternType.SOCRATIC
        )
        print(f"Question: What does it mean to be successful?")
        print(f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ Socratic pattern demo completed\n")


async def demonstrate_automatic_pattern_selection():
    """Demonstrate automatic pattern selection."""
    print("🤖 Automatic Pattern Selection Demo")
    print("=" * 50)

    # Create agent with automatic pattern selection
    llm_config = LLMConfig(provider="mock", model="mock-auto")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are an intelligent assistant that adapts to different types of questions.",
        enable_pattern_selection=True,  # Enable automatic selection
        enable_memory=False
    )

    await agent.start()

    try:
        # Add tools for action-based tasks
        await agent.add_tool(CalculatorTool())

        # Test different types of inputs
        test_inputs = [
            "Calculate 25 * 16 + 7",  # Should use ReAct
            "Explain step by step how photosynthesis works",  # Should use Chain of Thought
            "Create a plan for learning a new programming language",  # Should use Plan and Execute
            "Evaluate the benefits and drawbacks of electric vehicles",  # Should use Reflection
            "What is the meaning of justice?",  # Should use Socratic
        ]

        for user_input in test_inputs:
            print(f"\nInput: {user_input}")

            # Get pattern suggestion
            suggestion = agent.suggest_execution_pattern(user_input)
            print(f"Suggested pattern: {suggestion['suggested_pattern']}")
            print(f"Reasoning: {suggestion['selection_reasoning']}")

            # Run with automatic selection
            response = await agent.run(user_input)
            print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")

    finally:
        await agent.stop()

    print("\n✓ Automatic pattern selection demo completed\n")


async def demonstrate_pattern_comparison():
    """Demonstrate comparing different patterns on the same input."""
    print("⚖️ Pattern Comparison Demo")
    print("=" * 40)

    # Create agent for comparison
    llm_config = LLMConfig(provider="mock", model="mock-compare")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a versatile assistant.",
        enable_memory=False
    )

    await agent.start()

    try:
        # Compare patterns on the same question
        question = "How can artificial intelligence impact education?"

        patterns_to_compare = [
            ExecutionPatternType.CHAIN_OF_THOUGHT,
            ExecutionPatternType.PLAN_AND_EXECUTE,
            ExecutionPatternType.REFLECTION
        ]

        print(f"Question: {question}")
        print(f"Comparing patterns: {[p.value for p in patterns_to_compare]}")

        comparison_results = await agent.compare_patterns(question, patterns_to_compare)

        print("\nComparison Results:")
        for pattern_name, result in comparison_results["results"].items():
            print(f"\n{pattern_name.upper()}:")
            print(f"  Success: {result['success']}")
            if result['success']:
                answer = result['answer']
                print(f"  Answer: {answer[:150]}..." if len(answer) > 150 else f"  Answer: {answer}")
                print(f"  Steps: {result['steps_count']}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")

    finally:
        await agent.stop()

    print("\n✓ Pattern comparison demo completed\n")


async def demonstrate_fallback_patterns():
    """Demonstrate fallback pattern execution."""
    print("🔄 Fallback Patterns Demo")
    print("=" * 40)

    # Create agent
    llm_config = LLMConfig(provider="mock", model="mock-fallback")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a resilient assistant.",
        enable_memory=False
    )

    await agent.start()

    try:
        # Try with fallback patterns
        fallback_patterns = [
            ExecutionPatternType.REACT,
            ExecutionPatternType.CHAIN_OF_THOUGHT,
            ExecutionPatternType.REFLECTION
        ]

        response = await agent.run_with_fallback(
            "Solve this complex problem: How to balance work and life?",
            fallback_patterns
        )

        print(f"Question: Solve this complex problem: How to balance work and life?")
        print(f"Fallback patterns: {[p.value for p in fallback_patterns]}")
        print(f"Response: {response}")

        # Show pattern stats
        stats = agent.get_pattern_stats()
        print(f"\nPattern Usage Stats: {stats['pattern_usage']}")

    finally:
        await agent.stop()

    print("✓ Fallback patterns demo completed\n")


async def demonstrate_custom_pattern_rules():
    """Demonstrate adding custom pattern selection rules."""
    print("⚙️ Custom Pattern Rules Demo")
    print("=" * 40)

    # Create agent
    llm_config = LLMConfig(provider="mock", model="mock-custom")
    llm_function = await create_llm_function(llm_config)

    agent = CoreAgent(
        llm_function=llm_function,
        system_prompt="You are a customizable assistant.",
        enable_pattern_selection=True,
        enable_memory=False
    )

    await agent.start()

    try:
        # Add custom rule for technical questions
        def is_technical_question(user_input: str, params=None) -> bool:
            technical_keywords = ["algorithm", "programming", "code", "technical", "implementation"]
            return any(keyword in user_input.lower() for keyword in technical_keywords)

        agent.add_pattern_rule(
            "technical_questions",
            is_technical_question,
            ExecutionPatternType.PLAN_AND_EXECUTE,
            priority=15  # High priority
        )

        # Test the custom rule
        technical_input = "How would you implement a sorting algorithm?"
        print(f"Input: {technical_input}")

        suggestion = agent.suggest_execution_pattern(technical_input)
        print(f"Suggested pattern: {suggestion['suggested_pattern']}")
        print(f"Reasoning: {suggestion['selection_reasoning']}")

        response = await agent.run(technical_input)
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")

    finally:
        await agent.stop()

    print("✓ Custom pattern rules demo completed\n")


async def main():
    """Main demonstration function."""
    print("🌟 Core Agent Execution Patterns Demo")
    print("=" * 60)
    print("This demo shows different execution patterns and how they")
    print("handle various types of tasks with different reasoning approaches.\n")

    try:
        # Run individual pattern demonstrations
        await demonstrate_react_pattern()
        await demonstrate_chain_of_thought()
        await demonstrate_plan_and_execute()
        await demonstrate_reflection_pattern()
        await demonstrate_socratic_pattern()

        # Run advanced features
        await demonstrate_automatic_pattern_selection()
        await demonstrate_pattern_comparison()
        await demonstrate_fallback_patterns()
        await demonstrate_custom_pattern_rules()

        print("🎉 All execution pattern demos completed successfully!")
        print("\nKey Takeaways:")
        print("1. Different patterns suit different types of tasks")
        print("2. Automatic selection can choose the best pattern")
        print("3. Fallback patterns provide resilience")
        print("4. Custom rules allow fine-tuned control")
        print("5. Pattern comparison helps optimize performance")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())