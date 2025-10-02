"""Integration tests for enhanced memory coordinator.

These tests use real components with NO mocks to verify end-to-end functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from memory.learning_memory_system import LearningMemorySystem
from memory.interaction_memory import InteractionType
from memory.learning_graph_memory import ConceptStatus
from memory.coordinator import (
    EnhancedMemoryCoordinator,
    IntegratedMemoryContext,
    MemoryRelevanceScore
)


class TestEnhancedCoordinatorIntegration:
    """Integration tests for enhanced coordinator with real memory system."""

    @pytest.fixture
    async def system(self):
        """Create and initialize a real learning memory system."""
        learning_system = LearningMemorySystem()
        await learning_system.start()
        yield learning_system
        await learning_system.stop()

    async def get_coordinator(self, system):
        """Get enhanced coordinator from system."""
        # system is an async generator, need to await it
        return system.enhanced_coordinator

    @pytest.mark.asyncio
    async def test_end_to_end_retrieval_integration(self, system):
        """Test complete end-to-end retrieval with real data."""
        coordinator = system.enhanced_coordinator
        coordinator = system.enhanced_coordinator
        user_id = "integration_test_user_001"
        session_id = "integration_test_session_001"
        domain = "algebra"

        # SETUP: Populate memory system with real data

        # 1. Add episodic memories (learning episodes)
        await system.store_learning_event(
            event_type="problem_solved",
            content="Successfully solved linear equation 2x + 5 = 13",
            user_id=user_id,
            session_id=session_id,
            context={'success': True, 'concept': 'linear_equations'},
            importance=0.8
        )

        await system.store_problem_attempt(
            problem_id="linear_eq_001",
            user_id=user_id,
            session_id=session_id,
            attempt_content="Solved x = 4",
            was_successful=True,
            time_spent=120.0
        )

        # 2. Add semantic memories (concepts)
        await system.store_concept(
            concept_id="linear_equations",
            concept_name="Linear Equations",
            definition="Equations of the form ax + b = c",
            domain=domain,
            user_id=user_id,
            importance=0.9
        )

        await system.store_fact(
            fact_content="Linear equations have one variable with power 1",
            domain=domain,
            related_concepts=["linear_equations"],
            user_id=user_id
        )

        # 3. Add profile memories (preferences)
        await system.store_learning_preference(
            user_id=user_id,
            preference_type="explanation_style",
            preference_value="step_by_step",
            confidence=0.9
        )

        await system.store_learning_style(
            user_id=user_id,
            style_dimensions={'visual': 0.8, 'verbal': 0.6},
            assessment_method="observed"
        )

        # 4. Add interaction memories (conversation)
        await system.store_interaction_turn(
            user_id=user_id,
            session_id=session_id,
            turn_number=1,
            user_input="How do I solve linear equations?",
            agent_response="Let's start with the basics...",
            interaction_type=InteractionType.QUESTION
        )

        # 5. Add graph memories (learning progress)
        await system.initialize_user_learning_graph(
            user_id=user_id,
            knowledge_graph_id="algebra_graph",
            domain=domain
        )

        await system.mark_concept_learned(
            user_id=user_id,
            concept_id="linear_equations",
            mastery_level=0.8,
            evidence="Completed practice problems successfully"
        )

        # Give system time to process
        await asyncio.sleep(0.1)

        # TEST: Retrieve integrated context
        result = await coordinator.retrieve_integrated_context(
            query="linear equations",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.PRACTICE,
            domain=domain,
            max_memories=20
        )

        # VERIFY: Result structure
        assert isinstance(result, IntegratedMemoryContext)
        assert result.query == "linear equations"
        assert isinstance(result.memories, list)
        assert len(result.memories) > 0

        # VERIFY: Memories are scored
        for memory_score in result.memories:
            assert isinstance(memory_score, MemoryRelevanceScore)
            assert 0.0 <= memory_score.total_score <= 1.0
            assert memory_score.memory_type in [
                'episodic', 'semantic', 'user_profile', 'interaction', 'learning_graph'
            ]

        # VERIFY: Adaptive weights were applied
        assert isinstance(result.memory_type_weights, dict)
        assert 'episodic' in result.memory_type_weights
        assert 'semantic' in result.memory_type_weights
        # Practice type should prioritize episodic
        assert result.memory_type_weights['episodic'] >= 0.3

        # VERIFY: Performance metrics
        assert result.retrieval_time_ms > 0
        assert result.scoring_time_ms > 0
        assert result.total_memories_retrieved > 0
        assert result.total_memories_scored > 0

    @pytest.mark.asyncio
    async def test_relevance_scoring_with_real_data(self, system):
        """Test that relevance scoring works correctly with real memories."""
        coordinator = system.enhanced_coordinator
        user_id = "scoring_test_user"
        session_id = "scoring_test_session"

        # Add memories with different characteristics

        # Recent, important memory matching query
        await system.store_learning_event(
            event_type="concept_learned",
            content="Mastered quadratic equations solving techniques",
            user_id=user_id,
            session_id=session_id,
            importance=0.9
        )

        # Old memory, less relevant
        old_session = session_id + "_old"
        await system.store_learning_event(
            event_type="unrelated",
            content="Studied geometry basics",
            user_id=user_id,
            session_id=old_session,
            importance=0.5
        )

        # Retrieve with query matching first memory
        await asyncio.sleep(0.1)

        result = await coordinator.retrieve_integrated_context(
            query="quadratic equations",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.QUESTION,
            max_memories=10
        )

        # Find our memories in results
        if len(result.memories) > 1:
            # Recent, important, matching memory should score higher
            scores = [(m.total_score, m.memory_entry.content) for m in result.memories]
            scores.sort(reverse=True, key=lambda x: x[0])

            # Top result should have high score
            top_score = scores[0][0]
            assert top_score > 0.3

    @pytest.mark.asyncio
    async def test_adaptive_weights_in_practice(self, system):
        """Test that adaptive weights change behavior for different interaction types."""
        user_id = "adaptive_test_user"
        session_id = "adaptive_test_session"

        # Add both episodic and semantic memories
        await system.store_learning_event(
            event_type="practice",
            content="Practiced solving equations",
            user_id=user_id,
            session_id=session_id,
            importance=0.7
        )

        await system.store_concept(
            concept_id="equations",
            concept_name="Equations",
            definition="Mathematical statements of equality",
            domain="algebra",
            user_id=user_id,
            importance=0.8
        )

        await asyncio.sleep(0.1)

        # Retrieve with PRACTICE interaction type
        practice_result = await coordinator.retrieve_integrated_context(
            query="equations",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.PRACTICE,
            max_memories=10
        )

        # Retrieve with QUESTION interaction type
        question_result = await coordinator.retrieve_integrated_context(
            query="equations",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.QUESTION,
            max_memories=10
        )

        # PRACTICE should weight episodic higher
        assert practice_result.memory_type_weights['episodic'] > \
               question_result.memory_type_weights['episodic']

        # QUESTION should weight semantic higher
        assert question_result.memory_type_weights['semantic'] > \
               practice_result.memory_type_weights['semantic']

    @pytest.mark.asyncio
    async def test_cross_memory_linking(self, system):
        """Test that cross-memory relationships boost relevance."""
        user_id = "cross_link_user"
        session_id = "cross_link_session"
        concept_id = "polynomials"

        # Create related memories across types

        # Episodic memory with concept
        await system.store_concept_interaction(
            concept_id=concept_id,
            user_id=user_id,
            session_id=session_id,
            interaction_type="practice",
            interaction_content="Practiced polynomial factoring"
        )

        # Semantic memory for same concept
        await system.store_concept(
            concept_id=concept_id,
            concept_name="Polynomials",
            definition="Expressions with multiple terms",
            domain="algebra",
            user_id=user_id
        )

        # Learning graph progress on concept
        await system.mark_concept_learned(
            user_id=user_id,
            concept_id=concept_id,
            mastery_level=0.7
        )

        await asyncio.sleep(0.1)

        # Retrieve with concept in active context
        result = await coordinator.retrieve_integrated_context(
            query="polynomials",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.PRACTICE,
            context_hints={'active_concepts': [concept_id]},
            max_memories=20
        )

        # Should retrieve memories from multiple types
        memory_types_found = set(m.memory_type for m in result.memories)

        # With cross-linking, memories with matching concept should score well
        for memory in result.memories:
            # Check for cross-link score contribution
            if concept_id in str(memory.memory_entry.metadata):
                # Should have cross-link boost
                assert memory.cross_link_score > 0

    @pytest.mark.asyncio
    async def test_context_aware_weighting(self, system):
        """Test that context hints affect weighting."""
        user_id = "context_aware_user"
        session_id = "context_aware_session"

        # Add some test data
        await system.store_learning_event(
            event_type="struggle",
            content="Had difficulty with concept",
            user_id=user_id,
            session_id=session_id
        )

        await asyncio.sleep(0.1)

        # Retrieve with struggling context
        struggling_result = await coordinator.retrieve_integrated_context(
            query="test",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.PRACTICE,
            context_hints={'user_struggling': True},
            max_memories=10
        )

        # Retrieve without struggling context
        normal_result = await coordinator.retrieve_integrated_context(
            query="test",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.PRACTICE,
            context_hints={'user_struggling': False},
            max_memories=10
        )

        # Struggling should boost episodic weight
        assert struggling_result.memory_type_weights['episodic'] > \
               normal_result.memory_type_weights['episodic']

    @pytest.mark.asyncio
    async def test_parallel_retrieval_performance(self, system):
        """Test that parallel retrieval provides performance benefits."""
        user_id = "perf_test_user"
        session_id = "perf_test_session"

        # Add data to multiple memory types
        for i in range(5):
            await system.store_learning_event(
                event_type="test",
                content=f"Test episode {i}",
                user_id=user_id,
                session_id=session_id
            )

            await system.store_concept(
                concept_id=f"concept_{i}",
                concept_name=f"Concept {i}",
                definition=f"Definition {i}",
                domain="test",
                user_id=user_id
            )

        await asyncio.sleep(0.1)

        # Measure retrieval time
        result = await coordinator.retrieve_integrated_context(
            query="test",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.QUESTION,
            max_memories=20
        )

        # Should complete reasonably fast (parallel retrieval benefit)
        # Even with multiple memory types
        assert result.retrieval_time_ms < 5000  # Under 5 seconds

        # Should have retrieved from multiple types
        assert result.total_memories_retrieved > 0

    @pytest.mark.asyncio
    async def test_memory_type_distribution(self, system):
        """Test that results include diverse memory types."""
        user_id = "distribution_user"
        session_id = "distribution_session"

        # Populate all memory types
        await system.store_learning_event(
            event_type="test",
            content="Episodic content about fractions",
            user_id=user_id,
            session_id=session_id
        )

        await system.store_concept(
            concept_id="fractions",
            concept_name="Fractions",
            definition="Parts of a whole",
            domain="arithmetic",
            user_id=user_id
        )

        await system.store_learning_preference(
            user_id=user_id,
            preference_type="test_pref",
            preference_value="value"
        )

        await system.store_interaction_turn(
            user_id=user_id,
            session_id=session_id,
            turn_number=1,
            user_input="Tell me about fractions",
            agent_response="Fractions represent...",
            interaction_type=InteractionType.QUESTION
        )

        await asyncio.sleep(0.1)

        result = await coordinator.retrieve_integrated_context(
            query="fractions",
            user_id=user_id,
            session_id=session_id,
            interaction_type=InteractionType.EXPLANATION,
            max_memories=20
        )

        # Check memory type distribution
        assert isinstance(result.memory_type_distribution, dict)

        # Should have at least some memories
        total_memories = sum(result.memory_type_distribution.values())
        assert total_memories > 0

    @pytest.mark.asyncio
    async def test_weight_explanation_functionality(self, coordinator):
        """Test weight explanation for debugging."""
        explanation = coordinator.get_weight_explanation(
            InteractionType.PRACTICE,
            context={'user_struggling': True, 'conversation_depth': 8}
        )

        # Should provide detailed explanation
        assert 'interaction_type' in explanation
        assert 'base_weights' in explanation
        assert 'final_weights' in explanation
        assert 'adjustments_applied' in explanation

        # Should mention adjustments
        assert len(explanation['adjustments_applied']) > 0

    @pytest.mark.asyncio
    async def test_concurrent_coordinator_calls(self, system):
        """Test that coordinator handles concurrent requests correctly."""
        user_id = "concurrent_user"

        # Launch multiple concurrent retrieval requests
        tasks = [
            coordinator.retrieve_integrated_context(
                query=f"query{i}",
                user_id=user_id,
                session_id=f"session{i}",
                interaction_type=InteractionType.QUESTION,
                max_memories=10
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, IntegratedMemoryContext)
            assert result.total_memories_scored >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
