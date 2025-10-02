"""Functional test cases derived from design document.

Tests cover all functional requirements specified in:
/memory/docs/MEMORY_SYSTEM_DESIGN.md

Test Categories:
1. Core Storage Operations
2. Memory Type Operations
3. Enhanced Coordinator (Phase 1)
4. Session Consolidation
5. Learning Insights
6. Cross-Memory Operations
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

# These imports will work once we fix the paths
from memory import (
    LearningMemorySystem,
    LearningSystemConfig,
    MemoryEntry,
    InteractionType,
    ConceptStatus
)


class TestCoreStorageOperations:
    """Test core storage operations from design section 3.1"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self):
        """Design: MemoryStore.store() and retrieve() operations"""
        system = LearningMemorySystem()
        await system.start()

        # Store a memory
        result = await system.store_memory(
            content="User learned quadratic equations",
            importance=0.8,
            session_id="session_001",
            user_id="user_123",
            memory_type="episodic"
        )

        assert result is True

        # Retrieve by search
        memories = await system.search_memory(
            query="quadratic",
            limit=5,
            filters={"user_id": "user_123"}
        )

        assert len(memories) > 0
        assert "quadratic" in memories[0].content.lower()

    @pytest.mark.asyncio
    async def test_memory_entry_fields(self):
        """Design: MemoryEntry must have 8 required fields"""
        system = LearningMemorySystem()
        await system.start()

        await system.store_memory(
            content="Test content",
            importance=0.5,
            session_id="s1",
            user_id="u1"
        )

        memories = await system.search_memory("Test", limit=1)
        entry = memories[0]

        # Verify all 8 fields from design
        assert hasattr(entry, 'id')
        assert hasattr(entry, 'content')
        assert hasattr(entry, 'metadata')
        assert hasattr(entry, 'timestamp')
        assert hasattr(entry, 'embedding')
        assert hasattr(entry, 'importance')
        assert hasattr(entry, 'access_count')
        assert hasattr(entry, 'last_accessed')

        assert entry.content == "Test content"
        assert entry.importance == 0.5


class TestEpisodicMemory:
    """Test episodic memory from design section 4.1"""

    @pytest.mark.asyncio
    async def test_store_learning_event(self):
        """Design: store_learning_event(event_type, content, user_id, context)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_learning_event(
            event_type="problem_solved",
            content="Successfully solved linear equation: 2x + 5 = 13",
            user_id="user_123",
            session_id="session_001",
            context={
                'success': True,
                'time_spent': 45.5,
                'difficulty_level': 'medium'
            },
            importance=0.9
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_store_problem_attempt(self):
        """Design: store_problem_attempt(problem_id, attempt_content, was_successful)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_problem_attempt(
            problem_id="prob_001",
            user_id="user_123",
            session_id="session_001",
            attempt_content="x = 4",
            was_successful=True,
            solution_steps=["Subtract 5 from both sides", "Divide by 2"],
            time_spent=30.0
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_learning_episodes(self):
        """Design: get_learning_episodes(user_id, event_type, time_range)"""
        system = LearningMemorySystem()
        await system.start()

        # Store multiple episodes
        for i in range(3):
            await system.store_learning_event(
                event_type="concept_learned",
                content=f"Learned concept {i}",
                user_id="user_123",
                session_id=f"session_{i}"
            )

        episodes = await system.get_learning_episodes(
            user_id="user_123",
            event_type="concept_learned",
            limit=10
        )

        assert len(episodes) == 3


class TestSemanticMemory:
    """Test semantic memory from design section 4.2"""

    @pytest.mark.asyncio
    async def test_store_concept(self):
        """Design: store_concept(concept_id, definition, domain, prerequisites)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_concept(
            concept_id="quadratic_eq",
            definition="An equation of the form ax² + bx + c = 0",
            domain="algebra",
            prerequisites=["linear_equations", "exponents"],
            examples=["x² - 5x + 6 = 0"]
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_concept(self):
        """Design: get_concept(concept_id)"""
        system = LearningMemorySystem()
        await system.start()

        await system.store_concept(
            concept_id="pythagorean_theorem",
            definition="a² + b² = c² for right triangles",
            domain="geometry"
        )

        concept = await system.get_concept("pythagorean_theorem")

        assert concept is not None
        assert "right triangles" in concept.content

    @pytest.mark.asyncio
    async def test_get_prerequisites(self):
        """Design: get_prerequisites(concept_id)"""
        system = LearningMemorySystem()
        await system.start()

        await system.store_concept(
            concept_id="calculus",
            definition="Study of change",
            domain="mathematics",
            prerequisites=["algebra", "trigonometry"]
        )

        prereqs = await system.get_prerequisites("calculus")

        assert len(prereqs) >= 2
        assert "algebra" in [p.metadata.get('concept_id') for p in prereqs]


class TestUserProfileMemory:
    """Test user profile memory from design section 4.3"""

    @pytest.mark.asyncio
    async def test_store_learning_preference(self):
        """Design: store_learning_preference(user_id, preference_type, preference_value)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_learning_preference(
            user_id="user_123",
            preference_type="explanation_detail",
            preference_value="detailed",
            confidence=0.8,
            source="observed"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_store_learning_style(self):
        """Design: store_learning_style(user_id, style_dimensions)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_learning_style(
            user_id="user_123",
            style_dimensions={
                'visual': 0.8,
                'auditory': 0.3,
                'kinesthetic': 0.6,
                'logical': 0.9
            },
            assessment_method="test",
            confidence=0.85
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_profile_summary(self):
        """Design: get_user_profile_summary(user_id)"""
        system = LearningMemorySystem()
        await system.start()

        # Store profile data
        await system.store_learning_style(
            user_id="user_123",
            style_dimensions={'visual': 0.7, 'logical': 0.8}
        )

        profile = await system.get_user_profile_summary("user_123")

        assert profile is not None
        assert 'learning_style' in profile or 'preferences' in profile


class TestInteractionMemory:
    """Test interaction memory from design section 4.4"""

    @pytest.mark.asyncio
    async def test_store_interaction_turn(self):
        """Design: store_interaction_turn(user_id, session_id, user_input, agent_response)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.store_interaction_turn(
            user_id="user_123",
            session_id="session_001",
            user_input="How do I solve quadratic equations?",
            agent_response="You can use the quadratic formula...",
            interaction_type=InteractionType.QUESTION
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_session_history(self):
        """Design: get_session_history(session_id, limit)"""
        system = LearningMemorySystem()
        await system.start()

        # Store multiple interactions
        for i in range(5):
            await system.store_interaction_turn(
                user_id="user_123",
                session_id="session_001",
                user_input=f"Question {i}",
                agent_response=f"Answer {i}",
                interaction_type=InteractionType.QUESTION
            )

        history = await system.get_session_history("session_001", limit=10)

        assert len(history) == 5


class TestLearningGraphMemory:
    """Test learning graph memory from design section 4.5"""

    @pytest.mark.asyncio
    async def test_initialize_user_learning_graph(self):
        """Design: initialize_user_learning_graph(user_id, knowledge_graph_id, domain)"""
        system = LearningMemorySystem()
        await system.start()

        result = await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="algebra_graph",
            domain="algebra"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_concept_learned(self):
        """Design: mark_concept_learned(user_id, concept_id, mastery_level)"""
        system = LearningMemorySystem()
        await system.start()

        await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="math_graph",
            domain="mathematics"
        )

        result = await system.mark_concept_learned(
            user_id="user_123",
            concept_id="linear_equations",
            mastery_level=0.85,
            evidence="Solved 10/10 problems correctly"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_next_concepts(self):
        """Design: get_next_concepts(user_id, domain, difficulty_preference)"""
        system = LearningMemorySystem()
        await system.start()

        await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="math_graph",
            domain="mathematics"
        )

        # Mark some concepts as learned
        await system.mark_concept_learned(
            user_id="user_123",
            concept_id="arithmetic",
            mastery_level=0.9
        )

        next_concepts = await system.get_next_concepts(
            user_id="user_123",
            domain="mathematics",
            limit=5
        )

        assert isinstance(next_concepts, list)


class TestEnhancedCoordinator:
    """Test Phase 1 Enhanced Coordinator from design section 5"""

    @pytest.mark.asyncio
    async def test_retrieve_integrated_context(self):
        """Design: retrieve_integrated_context with parallel retrieval"""
        system = LearningMemorySystem()
        await system.start()

        # Store data in multiple memory types
        await system.store_learning_event(
            event_type="practice",
            content="Practiced algebra",
            user_id="user_123",
            session_id="s1"
        )

        await system.store_concept(
            concept_id="algebra",
            definition="Branch of mathematics",
            domain="mathematics"
        )

        await system.store_learning_preference(
            user_id="user_123",
            preference_type="difficulty",
            preference_value="medium"
        )

        # Use enhanced coordinator
        result = await system.enhanced_coordinator.retrieve_integrated_context(
            query="algebra practice",
            user_id="user_123",
            session_id="s1",
            interaction_type=InteractionType.PRACTICE,
            domain="mathematics",
            max_memories=20
        )

        # Verify result structure
        assert hasattr(result, 'memories')
        assert hasattr(result, 'memory_type_weights')
        assert hasattr(result, 'retrieval_time_ms')
        assert hasattr(result, 'total_memories_retrieved')

        # Should retrieve from multiple types
        assert result.total_memories_retrieved > 0

    @pytest.mark.asyncio
    async def test_parallel_retrieval_performance(self):
        """Design: Parallel retrieval should be 2-3x faster than sequential"""
        system = LearningMemorySystem()
        await system.start()

        # Store memories in all types
        await system.store_learning_event(
            event_type="test",
            content="Test episodic",
            user_id="u1",
            session_id="s1"
        )

        result = await system.enhanced_coordinator.retrieve_integrated_context(
            query="test",
            user_id="u1",
            session_id="s1",
            interaction_type=InteractionType.QUESTION
        )

        # Performance should be sub-200ms as per design
        assert result.retrieval_time_ms < 200

    @pytest.mark.asyncio
    async def test_adaptive_weights_by_interaction_type(self):
        """Design: Adaptive weights based on interaction type (Table in 5.3)"""
        system = LearningMemorySystem()
        await system.start()

        # Store some data
        await system.store_concept(
            concept_id="test",
            definition="Test concept",
            domain="test"
        )

        # QUESTION type should prioritize semantic (50%)
        result_question = await system.enhanced_coordinator.retrieve_integrated_context(
            query="test",
            user_id="u1",
            session_id="s1",
            interaction_type=InteractionType.QUESTION
        )

        # PRACTICE type should prioritize episodic (40%)
        result_practice = await system.enhanced_coordinator.retrieve_integrated_context(
            query="test",
            user_id="u1",
            session_id="s1",
            interaction_type=InteractionType.PRACTICE
        )

        # Verify weights are different for different interaction types
        # Check that QUESTION prioritizes semantic and PRACTICE prioritizes episodic
        assert result_question.memory_type_weights['semantic'] > result_question.memory_type_weights['episodic'], \
            f"QUESTION should prioritize semantic, got: {result_question.memory_type_weights}"
        assert result_practice.memory_type_weights['episodic'] > result_practice.memory_type_weights['semantic'], \
            f"PRACTICE should prioritize episodic, got: {result_practice.memory_type_weights}"

        # Also verify they're not identical
        assert result_question.memory_type_weights != result_practice.memory_type_weights, \
            f"Expected different weights but got same: {result_question.memory_type_weights}"


class TestSessionConsolidation:
    """Test session consolidation from design"""

    @pytest.mark.asyncio
    async def test_consolidate_learning_session(self):
        """Design: consolidate_learning_session creates episodes, extracts knowledge, updates profile and graph"""
        system = LearningMemorySystem()
        await system.start()

        # Have a learning session with interactions
        await system.store_interaction_turn(
            user_id="user_123",
            session_id="session_001",
            user_input="Teach me algebra",
            agent_response="Let's start with linear equations",
            interaction_type=InteractionType.EXPLANATION
        )

        # Consolidate the session
        result = await system.consolidate_learning_session(
            user_id="user_123",
            session_id="session_001",
            session_summary="Learned linear equations basics",
            concepts_learned=["linear_equations"],
            overall_success=0.85,
            user_satisfaction=0.9
        )

        # Verify result structure
        assert hasattr(result, 'episode_id')
        assert hasattr(result, 'knowledge_extracted')
        assert hasattr(result, 'profile_updated')
        assert hasattr(result, 'graph_concepts_updated')
        assert hasattr(result, 'consolidation_success')

        assert result.consolidation_success is True
        assert result.episode_id is not None


class TestLearningInsights:
    """Test comprehensive learning insights from design"""

    @pytest.mark.asyncio
    async def test_get_comprehensive_learning_insights(self):
        """Design: get_comprehensive_learning_insights returns insights from all memory types"""
        system = LearningMemorySystem()
        await system.start()

        # Create some learning history
        await system.store_learning_event(
            event_type="practice",
            content="Practice session",
            user_id="user_123",
            session_id="s1"
        )

        await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="graph1",
            domain="mathematics"
        )

        insights = await system.get_comprehensive_learning_insights(
            user_id="user_123",
            domain="mathematics",
            days_back=30
        )

        # Verify structure
        assert hasattr(insights, 'episodic_patterns')
        assert hasattr(insights, 'semantic_gaps')
        assert hasattr(insights, 'profile_insights')
        assert hasattr(insights, 'interaction_patterns')
        assert hasattr(insights, 'learning_graph_analytics')
        assert hasattr(insights, 'overall_learning_trajectory')


class TestCrossMemoryOperations:
    """Test cross-memory operations from design"""

    @pytest.mark.asyncio
    async def test_predict_learning_success(self):
        """Design: predict_learning_success uses all memory types"""
        system = LearningMemorySystem()
        await system.start()

        # Setup user data
        await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="graph1",
            domain="algebra"
        )

        await system.store_learning_style(
            user_id="user_123",
            style_dimensions={'logical': 0.8, 'visual': 0.6}
        )

        prediction = await system.predict_learning_success(
            user_id="user_123",
            target_concept="quadratic_equations",
            planned_session_type="practice",
            domain="algebra"
        )

        # Verify prediction structure
        assert 'success_probability' in prediction
        assert 'confidence' in prediction
        assert 'factors' in prediction
        assert 'recommendations' in prediction

        assert 0.0 <= prediction['success_probability'] <= 1.0

    @pytest.mark.asyncio
    async def test_get_personalized_learning_plan(self):
        """Design: get_personalized_learning_plan generates comprehensive plan"""
        system = LearningMemorySystem()
        await system.start()

        # Setup user data
        await system.initialize_user_learning_graph(
            user_id="user_123",
            knowledge_graph_id="math_graph",
            domain="mathematics"
        )

        plan = await system.get_personalized_learning_plan(
            user_id="user_123",
            learning_goal="Master algebra",
            domain="mathematics",
            timeline_days=30
        )

        # Verify plan structure
        assert 'goal' in plan
        assert 'timeline_days' in plan
        assert 'weekly_schedule' in plan
        assert 'personalization' in plan
        assert 'milestones' in plan or 'recommended_concepts' in plan


class TestBackwardCompatibility:
    """Test that legacy coordinators still work"""

    @pytest.mark.asyncio
    async def test_legacy_memory_coordinator_exists(self):
        """Verify MemoryCoordinator is accessible"""
        system = LearningMemorySystem()
        await system.start()

        assert hasattr(system, 'memory_coordinator')
        assert system.memory_coordinator is not None

    @pytest.mark.asyncio
    async def test_learning_analytics_exists(self):
        """Verify LearningAnalytics is accessible"""
        system = LearningMemorySystem()
        await system.start()

        assert hasattr(system, 'learning_analytics')
        assert system.learning_analytics is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
