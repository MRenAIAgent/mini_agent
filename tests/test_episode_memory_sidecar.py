"""
Tests for Episode Memory Sidecar

Verifies that episode memories are correctly extracted and stored
from user conversations.
"""

import pytest
import asyncio
from datetime import datetime


# Mock LLM for testing
async def mock_llm(prompt: str) -> str:
    """Mock LLM that returns sample episode extraction"""
    await asyncio.sleep(0.01)

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
    {"content": "User is planning a trip to Japan", "type": "plan", "importance": 0.9},
    {"content": "User loves sushi", "type": "preference", "importance": 0.8}
]
"""
    else:
        return "[]"


class TestEpisodeMemorySidecar:
    """Test episode memory extraction and storage"""

    @pytest.mark.asyncio
    async def test_simple_extraction_preferences(self):
        """Test simple rule-based extraction of user preferences"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        # Create agent
        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        # Register episode sidecar with simple extraction
        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Run agent with preference statement
        await agent.run(
            user_input="I love pizza and hate mushrooms.",
            session_id="test-session-1"
        )

        # Wait for sidecar
        await asyncio.sleep(0.2)

        # Check episode memories were stored
        all_memories = await agent.memory_manager.get_all_memories()
        episode_memories = [
            m for m in all_memories
            if m.metadata.get("memory_type") == "episode"
        ]

        assert len(episode_memories) > 0, "Should extract at least one episode memory"

        # Verify memory types
        preference_memories = [
            m for m in episode_memories
            if m.metadata.get("episode_type") == "preference"
        ]
        assert len(preference_memories) > 0, "Should extract preference memories"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_simple_extraction_plans(self):
        """Test simple rule-based extraction of user plans"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Run with plan statement
        await agent.run(
            user_input="I'm planning to visit Paris next month.",
            session_id="test-session-2"
        )

        await asyncio.sleep(0.2)

        # Check for plan memories
        all_memories = await agent.memory_manager.get_all_memories()
        plan_memories = [
            m for m in all_memories
            if m.metadata.get("episode_type") == "plan"
        ]

        assert len(plan_memories) > 0, "Should extract plan memories"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_simple_extraction_personal_info(self):
        """Test simple rule-based extraction of personal information"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Run with personal info
        await agent.run(
            user_input="My name is Alice. I work as a software engineer.",
            session_id="test-session-3"
        )

        await asyncio.sleep(0.2)

        # Check for personal info memories
        all_memories = await agent.memory_manager.get_all_memories()
        personal_info_memories = [
            m for m in all_memories
            if m.metadata.get("episode_type") == "personal_info"
        ]

        assert len(personal_info_memories) > 0, "Should extract personal info memories"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_llm_extraction(self):
        """Test LLM-powered episode extraction"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        # Register with LLM extraction
        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            llm_function=mock_llm,
            extraction_strategy="llm"
        )
        agent.register_sidecar(episode_sidecar)

        # Run agent
        await agent.run(
            user_input="I love pizza and hate mushrooms.",
            session_id="test-session-4"
        )

        await asyncio.sleep(0.2)

        # Check memories
        all_memories = await agent.memory_manager.get_all_memories()
        episode_memories = [
            m for m in all_memories
            if m.metadata.get("memory_type") == "episode"
        ]

        assert len(episode_memories) >= 2, "LLM should extract multiple memories"

        # Verify content matches expected extractions
        contents = [m.content for m in episode_memories]
        assert any("pizza" in c.lower() for c in contents), "Should extract pizza preference"
        assert any("mushroom" in c.lower() for c in contents), "Should extract mushroom preference"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_no_extraction_for_generic_input(self):
        """Test that generic questions don't generate episode memories"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Run with generic question
        await agent.run(
            user_input="What's the weather today?",
            session_id="test-session-5"
        )

        await asyncio.sleep(0.2)

        # Check that no episode memories were created
        all_memories = await agent.memory_manager.get_all_memories()
        episode_memories = [
            m for m in all_memories
            if m.metadata.get("memory_type") == "episode"
        ]

        assert len(episode_memories) == 0, "Generic questions shouldn't create episode memories"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_episode_memory_metadata(self):
        """Test that episode memories have correct metadata"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        await agent.run(
            user_input="I love coffee.",
            session_id="test-session-6"
        )

        await asyncio.sleep(0.2)

        # Check metadata
        all_memories = await agent.memory_manager.get_all_memories()
        episode_memories = [
            m for m in all_memories
            if m.metadata.get("memory_type") == "episode"
        ]

        assert len(episode_memories) > 0

        memory = episode_memories[0]

        # Verify metadata fields
        assert memory.metadata.get("memory_type") == "episode"
        assert memory.metadata.get("episode_type") in ["preference", "plan", "personal_info", "general"]
        assert memory.metadata.get("source") == "conversation_analysis"
        assert "extracted_from" in memory.metadata
        assert memory.importance > 0.0

        await agent.stop()

    @pytest.mark.asyncio
    async def test_multiple_episode_types_in_one_message(self):
        """Test extracting multiple episode types from a single message"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Message with multiple types
        await agent.run(
            user_input="My name is Bob. I love hiking and I'm planning to climb Mt. Everest next year.",
            session_id="test-session-7"
        )

        await asyncio.sleep(0.2)

        # Check for multiple types
        all_memories = await agent.memory_manager.get_all_memories()
        episode_memories = [
            m for m in all_memories
            if m.metadata.get("memory_type") == "episode"
        ]

        assert len(episode_memories) >= 2, "Should extract multiple episodes from one message"

        # Check we got different types
        types = set(m.metadata.get("episode_type") for m in episode_memories)
        assert len(types) > 1, "Should extract different episode types"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_episode_retrieval_by_type(self):
        """Test retrieving episode memories by type"""
        from agent import CoreAgent
        from sidecars import EpisodeMemorySidecar

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        episode_sidecar = EpisodeMemorySidecar(
            memory_manager=agent.memory_manager,
            extraction_strategy="simple"
        )
        agent.register_sidecar(episode_sidecar)

        # Add multiple types of memories
        await agent.run("I love pizza.", session_id="test-session-8")
        await asyncio.sleep(0.1)

        await agent.run("I'm planning a vacation.", session_id="test-session-8")
        await asyncio.sleep(0.1)

        await agent.run("My name is Carol.", session_id="test-session-8")
        await asyncio.sleep(0.1)

        # Retrieve and filter
        all_memories = await agent.memory_manager.get_all_memories()

        preferences = [
            m for m in all_memories
            if m.metadata.get("episode_type") == "preference"
        ]
        plans = [
            m for m in all_memories
            if m.metadata.get("episode_type") == "plan"
        ]
        personal_info = [
            m for m in all_memories
            if m.metadata.get("episode_type") == "personal_info"
        ]

        assert len(preferences) > 0, "Should have preference memories"
        assert len(plans) > 0, "Should have plan memories"
        assert len(personal_info) > 0, "Should have personal info memories"

        await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
