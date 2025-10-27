"""
Episode Memory Sidecar Example

This example demonstrates how to use the EpisodeMemorySidecar to
automatically extract and store important information from conversations.

Episode memories capture:
- User preferences (likes/dislikes)
- Plans and intentions
- Personal information
- Important facts
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime


# Mock LLM for demonstration
async def mock_llm(prompt: str) -> str:
    """Mock LLM that returns sample episode extraction"""
    # Simulate LLM delay
    await asyncio.sleep(0.1)

    # Return sample JSON for episode extraction
    if "I love pizza" in prompt or "hate mushrooms" in prompt:
        return """
[
    {"content": "User loves pizza", "type": "preference", "importance": 0.8},
    {"content": "User hates mushrooms", "type": "preference", "importance": 0.8}
]
"""
    elif "planning a trip to Japan" in prompt:
        return """
[
    {"content": "User is planning a trip to Japan next month", "type": "plan", "importance": 0.9},
    {"content": "User loves sushi", "type": "preference", "importance": 0.8}
]
"""
    elif "My name is Alice" in prompt:
        return """
[
    {"content": "User's name is Alice", "type": "personal_info", "importance": 0.95},
    {"content": "User works as a software engineer in San Francisco", "type": "personal_info", "importance": 0.9}
]
"""
    else:
        return "[]"


async def example_1_simple_extraction():
    """
    Example 1: Simple rule-based extraction

    Uses pattern matching to extract common episode types without LLM.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Rule-Based Episode Extraction")
    print("="*70)

    from agent import CoreAgent
    from sidecars import EpisodeMemorySidecar

    # Create agent with memory
    agent = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )
    await agent.start()

    # Create and register episode memory sidecar (simple extraction)
    episode_sidecar = EpisodeMemorySidecar(
        memory_manager=agent.memory_manager,
        extraction_strategy="simple"  # Use rule-based extraction
    )
    agent.register_sidecar(episode_sidecar)

    print("\n📝 User Input: 'I love pizza and hate mushrooms. My favorite food!'")

    # Run agent - episode sidecar extracts memories in background
    response = await agent.run(
        user_input="I love pizza and hate mushrooms. My favorite food!",
        session_id="user-alice"
    )

    # Wait for sidecar to complete
    await asyncio.sleep(0.5)

    print(f"\n🤖 Agent Response: {response}")

    # Check stored memories
    all_memories = await agent.memory_manager.get_all_memories()
    episode_memories = [m for m in all_memories if m.metadata.get("memory_type") == "episode"]

    print(f"\n💾 Extracted Episode Memories: {len(episode_memories)}")
    for i, memory in enumerate(episode_memories, 1):
        print(f"\n{i}. Content: {memory.content}")
        print(f"   Type: {memory.metadata.get('episode_type', 'unknown')}")
        print(f"   Importance: {memory.importance}")
        print(f"   Source: {memory.metadata.get('source', 'unknown')}")

    await agent.stop()


async def example_2_llm_extraction():
    """
    Example 2: LLM-powered extraction

    Uses LLM to intelligently extract episode memories with better accuracy.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: LLM-Powered Episode Extraction")
    print("="*70)

    from agent import CoreAgent
    from sidecars import EpisodeMemorySidecar

    # Create agent with memory
    agent = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )
    await agent.start()

    # Create and register episode memory sidecar (LLM extraction)
    episode_sidecar = EpisodeMemorySidecar(
        memory_manager=agent.memory_manager,
        llm_function=mock_llm,  # Provide LLM for extraction
        extraction_strategy="llm"  # Use LLM-based extraction
    )
    agent.register_sidecar(episode_sidecar)

    print("\n📝 User Input: 'I'm planning a trip to Japan next month. I love sushi!'")

    # Run agent
    response = await agent.run(
        user_input="I'm planning a trip to Japan next month. I love sushi!",
        session_id="user-bob"
    )

    # Wait for sidecar
    await asyncio.sleep(0.5)

    print(f"\n🤖 Agent Response: {response}")

    # Check stored memories
    all_memories = await agent.memory_manager.get_all_memories()
    episode_memories = [m for m in all_memories if m.metadata.get("memory_type") == "episode"]

    print(f"\n💾 Extracted Episode Memories: {len(episode_memories)}")
    for i, memory in enumerate(episode_memories, 1):
        print(f"\n{i}. Content: {memory.content}")
        print(f"   Type: {memory.metadata.get('episode_type', 'unknown')}")
        print(f"   Importance: {memory.importance}")

    await agent.stop()


async def example_3_personal_info_extraction():
    """
    Example 3: Personal information extraction

    Extracts and stores personal information with high importance.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Personal Information Extraction")
    print("="*70)

    from agent import CoreAgent
    from sidecars import EpisodeMemorySidecar

    # Create agent
    agent = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )
    await agent.start()

    # Register episode sidecar
    episode_sidecar = EpisodeMemorySidecar(
        memory_manager=agent.memory_manager,
        llm_function=mock_llm,
        extraction_strategy="llm"
    )
    agent.register_sidecar(episode_sidecar)

    print("\n📝 User Input: 'My name is Alice. I work as a software engineer in San Francisco.'")

    # Run agent
    response = await agent.run(
        user_input="My name is Alice. I work as a software engineer in San Francisco.",
        session_id="user-alice-2"
    )

    # Wait for sidecar
    await asyncio.sleep(0.5)

    print(f"\n🤖 Agent Response: {response}")

    # Check stored memories
    all_memories = await agent.memory_manager.get_all_memories()
    episode_memories = [m for m in all_memories if m.metadata.get("memory_type") == "episode"]

    print(f"\n💾 Extracted Episode Memories: {len(episode_memories)}")
    for i, memory in enumerate(episode_memories, 1):
        print(f"\n{i}. Content: {memory.content}")
        print(f"   Type: {memory.metadata.get('episode_type', 'unknown')}")
        print(f"   Importance: {memory.importance}")

    await agent.stop()


async def example_4_memory_retrieval():
    """
    Example 4: Retrieving episode memories

    Shows how to search and retrieve stored episode memories.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Retrieving Episode Memories")
    print("="*70)

    from agent import CoreAgent
    from sidecars import EpisodeMemorySidecar

    # Create agent
    agent = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )
    await agent.start()

    # Register episode sidecar
    episode_sidecar = EpisodeMemorySidecar(
        memory_manager=agent.memory_manager,
        extraction_strategy="simple"
    )
    agent.register_sidecar(episode_sidecar)

    # Store some conversations
    conversations = [
        "I love coffee but hate tea.",
        "I'm planning to learn Python next month.",
        "My name is Charlie. I live in New York."
    ]

    print("\n📝 Storing conversations:")
    for conv in conversations:
        print(f"   - {conv}")
        await agent.run(user_input=conv, session_id="user-charlie")
        await asyncio.sleep(0.3)  # Wait for sidecar

    # Search for specific types of memories
    print("\n🔍 Searching for preferences:")
    all_memories = await agent.memory_manager.get_all_memories()
    preferences = [
        m for m in all_memories
        if m.metadata.get("episode_type") == "preference"
    ]

    for memory in preferences:
        print(f"   - {memory.content}")

    print("\n🔍 Searching for plans:")
    plans = [
        m for m in all_memories
        if m.metadata.get("episode_type") == "plan"
    ]

    for memory in plans:
        print(f"   - {memory.content}")

    print("\n🔍 Searching for personal info:")
    personal_info = [
        m for m in all_memories
        if m.metadata.get("episode_type") == "personal_info"
    ]

    for memory in personal_info:
        print(f"   - {memory.content}")

    # Get memory stats
    stats = await agent.memory_manager.get_memory_stats()
    print(f"\n📊 Total memories stored: {stats.get('total_memories', 0)}")

    await agent.stop()


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("EPISODE MEMORY SIDECAR EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate automatic episode memory extraction")
    print("from conversations using the EpisodeMemorySidecar.")

    # Run examples
    await example_1_simple_extraction()
    await example_2_llm_extraction()
    await example_3_personal_info_extraction()
    await example_4_memory_retrieval()

    print("\n" + "="*70)
    print("✅ All examples completed!")
    print("="*70)
    print("\nKey Takeaways:")
    print("1. Episode memories are automatically extracted from conversations")
    print("2. Two extraction strategies: 'simple' (rule-based) and 'llm' (intelligent)")
    print("3. Memories are tagged with type, importance, and source")
    print("4. Episode memories can be retrieved and filtered by type")
    print("5. Everything happens in background - no blocking!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
