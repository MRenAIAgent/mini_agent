"""
Example: Automatic Prompt Optimization with CoreOptimizer

This example demonstrates how to use the built-in DSPy-inspired
automatic prompt optimization system in mini_agent.

The system supports three optimization strategies:
1. Bootstrap - Few-shot example generation
2. Coordinate Ascent (COPRO-inspired) - Iterative prompt refinement
3. Bayesian - Exploration/exploitation optimization
"""

import asyncio
from agent import CoreAgent
from optimization import CoreOptimizer, TrainingExample
from integrations.llm_factory import LLMConfig


async def mock_llm_function(prompt: str) -> str:
    """Mock LLM for demonstration purposes."""
    # Simple mock that can answer basic math questions
    if "2 + 2" in prompt or "2+2" in prompt:
        return "The answer is 4."
    elif "5 * 3" in prompt or "5*3" in prompt:
        return "The answer is 15."
    elif "10 - 7" in prompt or "10-7" in prompt:
        return "The answer is 3."
    elif "What is" in prompt and "?" in prompt:
        return "I'll solve this step by step. The answer is 42."
    else:
        return "I can help you with that calculation."


async def main():
    print("=" * 70)
    print("🚀 Automatic Prompt Optimization Example")
    print("=" * 70)

    # Step 1: Create agent with optimization enabled
    print("\n[1] Creating agent with optimization enabled...\n")

    agent = CoreAgent(
        llm_function=mock_llm_function,
        system_prompt="You are a helpful math assistant.",
        enable_memory=False,
        enable_optimization=True  # ✅ Enable automatic optimization
    )

    await agent.start()

    # Step 2: Test baseline performance
    print("[2] Testing baseline performance...\n")

    baseline_response = await agent.run("What is 2 + 2?")
    print(f"Baseline Response: {baseline_response}\n")

    # Step 3: Prepare training examples
    print("[3] Preparing training examples...\n")

    training_examples = [
        {
            "input": "What is 2 + 2?",
            "output": "The answer is 4."
        },
        {
            "input": "Calculate 5 * 3",
            "output": "The answer is 15."
        },
        {
            "input": "What is 10 - 7?",
            "output": "The answer is 3."
        },
        {
            "input": "Solve 8 / 2",
            "output": "The answer is 4."
        }
    ]

    print(f"Training examples: {len(training_examples)} examples")

    # Step 4: Run automatic optimization with different strategies
    strategies = ["bootstrap", "coordinate_ascent", "bayesian"]

    for strategy in strategies:
        print(f"\n{'=' * 70}")
        print(f"[4.{strategies.index(strategy) + 1}] Running optimization with '{strategy}' strategy...")
        print("=" * 70)

        # Run optimization
        improved = await agent.optimize_prompt(
            training_examples=training_examples,
            strategy=strategy
        )

        if improved:
            print(f"\n✅ Optimization successful with {strategy}!")

            # Show optimization history
            if agent.optimization_history:
                last_result = agent.optimization_history[-1]
                print(f"\nOptimization Results:")
                print(f"  - Strategy: {last_result.get('strategy_used', 'N/A')}")
                print(f"  - Initial Score: {last_result.get('initial_score', 0):.2%}")
                print(f"  - Final Score: {last_result.get('final_score', 0):.2%}")
                print(f"  - Improvement: {last_result.get('improvement', 0):.2%}")
                print(f"  - Iterations: {last_result.get('iterations_taken', 0)}")
                print(f"  - API Calls: {last_result.get('api_calls', 0)}")
                print(f"  - Time: {last_result.get('execution_time', 0):.2f}s")

                # Show optimized prompt (truncated)
                optimized = last_result.get('optimized_prompt', '')
                if len(optimized) > 200:
                    print(f"\nOptimized Prompt (first 200 chars):")
                    print(f"  {optimized[:200]}...")
                else:
                    print(f"\nOptimized Prompt:")
                    print(f"  {optimized}")
        else:
            print(f"\n⚠️ Optimization with {strategy} did not improve performance")

    # Step 5: Test optimized agent
    print(f"\n{'=' * 70}")
    print("[5] Testing optimized agent performance...")
    print("=" * 70 + "\n")

    test_inputs = [
        "What is 2 + 2?",
        "Calculate 5 * 3",
        "What is 10 - 7?"
    ]

    for test_input in test_inputs:
        response = await agent.run(test_input)
        print(f"Q: {test_input}")
        print(f"A: {response}\n")

    await agent.stop()

    print("=" * 70)
    print("✅ Optimization example complete!")
    print("=" * 70)


async def advanced_optimization_example():
    """Advanced example using CoreOptimizer directly with custom settings."""

    print("\n" + "=" * 70)
    print("🔬 Advanced Optimization Example (CoreOptimizer Direct Usage)")
    print("=" * 70 + "\n")

    # Create optimizer with custom settings
    optimizer = CoreOptimizer(
        strategy="bootstrap",  # or "coordinate_ascent", "bayesian"
        max_iterations=5,
        convergence_threshold=0.90,
        timeout_seconds=120
    )

    # Prepare training examples
    training_examples = [
        TrainingExample(
            input="What is 2 + 2?",
            expected_output="The answer is 4."
        ),
        TrainingExample(
            input="Calculate 5 * 3",
            expected_output="The answer is 15."
        ),
        TrainingExample(
            input="What is 10 - 7?",
            expected_output="The answer is 3."
        )
    ]

    # Create agent evaluator function
    async def agent_evaluator(prompt: str, example: TrainingExample) -> str:
        """Evaluate agent with a specific prompt on a training example."""
        # Simulate agent execution with the candidate prompt
        full_prompt = f"{prompt}\n\nUser: {example.input}\nAssistant:"
        response = await mock_llm_function(full_prompt)
        return response

    print("[1] Starting optimization with custom settings...")
    print(f"    Strategy: {optimizer.get_strategy_name()}")
    print(f"    Metric: {optimizer.get_metric_name()}")
    print(f"    Max Iterations: {optimizer.max_iterations}")
    print(f"    Convergence Threshold: {optimizer.convergence_threshold}\n")

    # Run optimization
    result = await optimizer.optimize(
        initial_prompt="You are a helpful math assistant.",
        training_examples=training_examples,
        agent_evaluator=agent_evaluator,
        optimization_target="accuracy"
    )

    # Display results
    print("\n" + "=" * 70)
    print("📊 Optimization Results")
    print("=" * 70)
    print(f"\nSuccess: {result.success}")
    print(f"Initial Score: {result.initial_score:.2%}")
    print(f"Final Score: {result.final_score:.2%}")
    print(f"Improvement: {result.improvement:.2%}")
    print(f"Iterations: {result.iterations_taken}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"API Calls: {result.api_calls}")
    print(f"Strategy Used: {result.strategy_used}")

    if result.optimization_history:
        print(f"\n📈 Optimization History ({len(result.optimization_history)} steps):")
        for i, step in enumerate(result.optimization_history[:3], 1):  # Show first 3 steps
            print(f"\n  Step {i}:")
            print(f"    Strategy: {step.get('strategy', 'N/A')}")
            print(f"    Score: {step.get('evaluation_score', 0):.2%}")
            print(f"    Improvement: {'+' if step.get('is_best') else ''}")

        if len(result.optimization_history) > 3:
            print(f"\n  ... and {len(result.optimization_history) - 3} more steps")

    print("\n" + "=" * 70)
    print("✅ Advanced optimization complete!")
    print("=" * 70)

    return result


async def comparison_example():
    """Compare all three optimization strategies."""

    print("\n" + "=" * 70)
    print("🔬 Strategy Comparison")
    print("=" * 70 + "\n")

    training_examples = [
        TrainingExample(
            input="What is 2 + 2?",
            expected_output="The answer is 4.",
            metadata={"difficulty": "easy"}
        ),
        TrainingExample(
            input="Calculate 5 * 3",
            expected_output="The answer is 15.",
            metadata={"difficulty": "easy"}
        ),
        TrainingExample(
            input="What is 10 - 7?",
            expected_output="The answer is 3.",
            metadata={"difficulty": "easy"}
        )
    ]

    async def agent_evaluator(prompt: str, example: TrainingExample) -> str:
        full_prompt = f"{prompt}\n\nUser: {example.input}\nAssistant:"
        return await mock_llm_function(full_prompt)

    strategies = {
        "bootstrap": "Bootstrap Few-Shot",
        "coordinate_ascent": "Coordinate Ascent (COPRO)",
        "bayesian": "Bayesian Optimization"
    }

    results = {}

    for strategy_key, strategy_name in strategies.items():
        print(f"\n{'─' * 70}")
        print(f"Testing: {strategy_name}")
        print("─" * 70)

        optimizer = CoreOptimizer(
            strategy=strategy_key,
            max_iterations=3,  # Keep it quick for demo
            convergence_threshold=0.90
        )

        result = await optimizer.optimize(
            initial_prompt="You are a helpful math assistant.",
            training_examples=training_examples,
            agent_evaluator=agent_evaluator
        )

        results[strategy_key] = result

        print(f"\n✅ {strategy_name} Complete:")
        print(f"   Improvement: {result.improvement:.2%}")
        print(f"   Final Score: {result.final_score:.2%}")
        print(f"   Time: {result.execution_time:.2f}s")
        print(f"   API Calls: {result.api_calls}")

    # Summary comparison
    print("\n" + "=" * 70)
    print("📊 Strategy Comparison Summary")
    print("=" * 70)
    print(f"\n{'Strategy':<25} {'Improvement':<15} {'Final Score':<15} {'Time':<10}")
    print("─" * 70)

    for strategy_key, strategy_name in strategies.items():
        result = results[strategy_key]
        print(f"{strategy_name:<25} {result.improvement:>12.1%}   "
              f"{result.final_score:>12.1%}   {result.execution_time:>7.2f}s")

    # Find best strategy
    best_strategy = max(results.items(), key=lambda x: x[1].improvement)
    print("\n" + "─" * 70)
    print(f"🏆 Best Strategy: {strategies[best_strategy[0]]} "
          f"(+{best_strategy[1].improvement:.1%} improvement)")
    print("=" * 70)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║           Mini Agent - Automatic Prompt Optimization                ║
║                  DSPy-Inspired Optimization System                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Run basic example
    asyncio.run(main())

    # Uncomment to run advanced examples:
    # asyncio.run(advanced_optimization_example())
    # asyncio.run(comparison_example())

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Next Steps:                                                         ║
║  1. Try different optimization strategies                            ║
║  2. Add more training examples                                       ║
║  3. Use real LLM instead of mock                                     ║
║  4. Customize optimization metrics                                   ║
║  5. Integrate with your production agent                             ║
║                                                                      ║
║  Documentation: docs/PROMPT_OPTIMIZATION_PROPOSAL.md                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
