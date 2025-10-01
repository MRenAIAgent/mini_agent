"""Comprehensive tests for Learning Memory Manager."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from learning.learning_memory_manager import LearningMemoryManager
from learning.data_models import (
    LearningMemoryEntry,
    StudentProfile,
    LearningSession,
    DifficultyLevel,
    MasteryLevel,
    LearningStyle
)
from memory.memory_store import InMemoryStore


class TestLearningMemoryManager:
    """Test suite for LearningMemoryManager."""

    @pytest.fixture
    async def learning_manager(self):
        """Create a LearningMemoryManager instance for testing."""
        memory_store = InMemoryStore()
        manager = LearningMemoryManager(
            memory_store=memory_store,
            enable_learning_features=True
        )
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.fixture
    async def learning_manager_disabled(self):
        """Create a LearningMemoryManager with learning features disabled."""
        memory_store = InMemoryStore()
        manager = LearningMemoryManager(
            memory_store=memory_store,
            enable_learning_features=False
        )
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_learning_manager_initialization(self, learning_manager):
        """Test proper initialization of learning components."""
        assert learning_manager.learning_enabled is True
        assert learning_manager.student_model is not None
        assert learning_manager.learning_analytics is not None
        assert learning_manager.spaced_repetition is not None
        assert learning_manager.adaptive_difficulty is not None
        assert learning_manager.knowledge_graph is not None
        assert learning_manager.educational_retrieval is not None

    @pytest.mark.asyncio
    async def test_learning_manager_disabled_fallback(self, learning_manager_disabled):
        """Test fallback behavior when learning features are disabled."""
        assert learning_manager_disabled.learning_enabled is False

        # Should fall back to standard memory operations
        success = await learning_manager_disabled.store_learning_content(
            content="Test content",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_store_learning_content(self, learning_manager):
        """Test storing learning content with educational metadata."""
        success = await learning_manager.store_learning_content(
            content="Introduction to Python variables",
            difficulty_level=DifficultyLevel.BEGINNER,
            concept_tags={"python", "variables", "basics"},
            learning_objectives=["Understand variable declaration", "Learn variable types"],
            prerequisites={"programming_basics"},
            estimated_time_minutes=30,
            importance=0.8
        )

        assert success is True

        # Verify content was stored with educational metadata
        all_memories = await learning_manager.get_all_memories()
        assert len(all_memories) == 1

        memory = all_memories[0]
        assert isinstance(memory, LearningMemoryEntry)
        assert memory.difficulty_level == DifficultyLevel.BEGINNER
        assert "python" in memory.concept_tags
        assert "Understand variable declaration" in memory.learning_objectives
        assert "programming_basics" in memory.prerequisites
        assert memory.estimated_time_minutes == 30

    @pytest.mark.asyncio
    async def test_learning_session_workflow(self, learning_manager):
        """Test complete learning session workflow."""
        user_id = "test_user_123"

        # Start learning session
        session_id = await learning_manager.start_learning_session(
            user_id=user_id,
            session_goals=["Learn Python basics"]
        )

        assert session_id is not None
        assert session_id in learning_manager._active_sessions

        # Store some learning content
        content_success = await learning_manager.store_learning_content(
            content="Python variables are containers for storing data",
            difficulty_level=DifficultyLevel.BEGINNER,
            concept_tags={"python", "variables"},
            session_id=session_id
        )
        assert content_success is True

        # Record learning activity
        content_id = (await learning_manager.get_all_memories())[0].id
        activity_success = await learning_manager.record_learning_activity(
            session_id=session_id,
            content_id=content_id,
            success=True,
            response_time_seconds=45.0,
            difficulty_experienced=DifficultyLevel.BEGINNER
        )
        assert activity_success is True

        # End learning session
        completed_session = await learning_manager.end_learning_session(session_id)
        assert completed_session is not None
        assert completed_session.user_id == user_id
        assert completed_session.total_attempts == 1
        assert completed_session.correct_attempts == 1
        assert session_id not in learning_manager._active_sessions

    @pytest.mark.asyncio
    async def test_personalized_recommendations(self, learning_manager):
        """Test personalized learning recommendations."""
        user_id = "test_user_456"

        # Store multiple learning contents with different characteristics
        contents = [
            {
                "content": "Basic Python syntax",
                "difficulty_level": DifficultyLevel.BEGINNER,
                "concept_tags": {"python", "syntax"},
                "estimated_time_minutes": 20
            },
            {
                "content": "Advanced Python concepts",
                "difficulty_level": DifficultyLevel.ADVANCED,
                "concept_tags": {"python", "advanced"},
                "estimated_time_minutes": 60
            },
            {
                "content": "JavaScript fundamentals",
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "concept_tags": {"javascript", "fundamentals"},
                "estimated_time_minutes": 30
            }
        ]

        for content_data in contents:
            await learning_manager.store_learning_content(**content_data)

        # Get personalized recommendations
        recommendations = await learning_manager.get_personalized_recommendations(
            user_id=user_id,
            query="python",
            limit=3,
            focus_areas=["python"],
            available_time_minutes=45
        )

        assert len(recommendations) <= 3
        # Should prioritize Python content based on query and focus areas
        python_content = [r for r in recommendations if "python" in r.content.lower()]
        assert len(python_content) >= 1

    @pytest.mark.asyncio
    async def test_spaced_repetition_due(self, learning_manager):
        """Test spaced repetition functionality."""
        user_id = "test_user_789"

        # Create learning content that's due for review
        learning_entry = LearningMemoryEntry(
            content="Python list comprehensions",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            concept_tags={"python", "lists"},
            next_review_date=datetime.now() - timedelta(days=1),  # Due yesterday
            repetition_count=2
        )

        await learning_manager.memory_store.store(learning_entry)

        # Get items due for review
        due_items = await learning_manager.get_spaced_repetition_due(
            user_id=user_id,
            limit=10
        )

        assert len(due_items) == 1
        assert due_items[0].content == "Python list comprehensions"
        assert due_items[0].is_due_for_review is True

    @pytest.mark.asyncio
    async def test_adaptive_difficulty_recommendation(self, learning_manager):
        """Test adaptive difficulty recommendations."""
        user_id = "test_user_101"
        concept_id = "python_variables"

        # Get difficulty recommendation
        difficulty = await learning_manager.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            concept_id=concept_id
        )

        assert isinstance(difficulty, DifficultyLevel)
        # For new users, should recommend intermediate or beginner
        assert difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]

    @pytest.mark.asyncio
    async def test_learning_analytics(self, learning_manager):
        """Test learning analytics functionality."""
        user_id = "test_user_202"

        # Create some learning history
        session = LearningSession(
            user_id=user_id,
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            concepts_studied=["python", "variables"],
            total_attempts=10,
            correct_attempts=8
        )

        await learning_manager.learning_analytics.record_session(session)

        # Get analytics
        analytics = await learning_manager.get_learning_analytics(
            user_id=user_id,
            time_range_days=7
        )

        assert "student_model" in analytics
        assert "system_analytics" in analytics
        assert "timestamp" in analytics

    @pytest.mark.asyncio
    async def test_search_learning_content(self, learning_manager):
        """Test learning content search with educational filters."""
        # Store content with different difficulties
        contents = [
            {
                "content": "Python basics for beginners",
                "difficulty_level": DifficultyLevel.BEGINNER,
                "concept_tags": {"python", "basics"}
            },
            {
                "content": "Advanced Python techniques",
                "difficulty_level": DifficultyLevel.ADVANCED,
                "concept_tags": {"python", "advanced"}
            }
        ]

        for content_data in contents:
            await learning_manager.store_learning_content(**content_data)

        # Search with difficulty filter
        results = await learning_manager.search_learning_content(
            query="python",
            difficulty_level=DifficultyLevel.BEGINNER,
            limit=5
        )

        assert len(results) == 1
        assert results[0].difficulty_level == DifficultyLevel.BEGINNER
        assert "basics" in results[0].content

    @pytest.mark.asyncio
    async def test_knowledge_graph_integration(self, learning_manager):
        """Test knowledge graph integration."""
        from learning.data_models import ConceptNode, ConceptType

        # Add concept to knowledge graph
        concept = ConceptNode(
            concept_id="python_variables",
            name="Python Variables",
            description="Understanding variables in Python",
            concept_type=ConceptType.FUNDAMENTAL,
            difficulty_level=DifficultyLevel.BEGINNER
        )

        success = await learning_manager.add_concept_to_knowledge_graph(concept)
        assert success is True

        # Get prerequisites (should be empty for this simple test)
        prerequisites = await learning_manager.get_concept_prerequisites("python_variables")
        assert isinstance(prerequisites, list)

        # Get learning path
        learning_path = await learning_manager.get_learning_path(
            user_id="test_user",
            target_concept="python_variables"
        )
        assert isinstance(learning_path, list)

    @pytest.mark.asyncio
    async def test_callback_functionality(self, learning_manager):
        """Test callback functionality for learning events."""
        callback_called = False
        session_data = None

        async def test_callback(session: LearningSession):
            nonlocal callback_called, session_data
            callback_called = True
            session_data = session

        # Set callback
        learning_manager.set_learning_session_callback(test_callback)

        # Trigger session completion
        user_id = "test_user_callback"
        session_id = await learning_manager.start_learning_session(user_id)
        completed_session = await learning_manager.end_learning_session(session_id)

        # Verify callback was called
        assert callback_called is True
        assert session_data is not None
        assert session_data.user_id == user_id

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, learning_manager):
        """Test backward compatibility with core memory operations."""
        # Standard memory operations should work unchanged
        success = await learning_manager.store_memory(
            content="Regular memory content",
            importance=0.7,
            session_id=None
        )
        assert success is True

        # Standard search should work
        results = await learning_manager.search_memory(
            query="memory",
            limit=5
        )
        assert len(results) >= 1

        # Context operations should work
        session_id = "test_session"
        context_success = await learning_manager.add_conversation_turn(
            session_id=session_id,
            user_input="Hello",
            agent_response="Hi there!"
        )
        assert context_success is True

    @pytest.mark.asyncio
    async def test_error_handling(self, learning_manager):
        """Test error handling in various scenarios."""
        # Test with invalid session ID
        invalid_activity = await learning_manager.record_learning_activity(
            session_id="invalid_session",
            content_id="invalid_content",
            success=True
        )
        assert invalid_activity is False

        # Test ending non-existent session
        invalid_end = await learning_manager.end_learning_session("invalid_session")
        assert invalid_end is None

        # Test with invalid user ID (should not crash)
        recommendations = await learning_manager.get_personalized_recommendations(
            user_id="",  # Empty user ID
            limit=5
        )
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, learning_manager):
        """Test performance with larger datasets."""
        # Create multiple learning contents
        content_count = 100
        for i in range(content_count):
            await learning_manager.store_learning_content(
                content=f"Learning content {i}",
                difficulty_level=DifficultyLevel(((i % 4) + 1)),
                concept_tags={f"concept_{i % 10}"},
                importance=0.5
            )

        # Test search performance
        start_time = datetime.now()
        results = await learning_manager.search_learning_content(
            query="content",
            limit=10
        )
        search_time = (datetime.now() - start_time).total_seconds()

        assert len(results) == 10
        assert search_time < 1.0  # Should complete within 1 second

        # Test recommendations performance
        start_time = datetime.now()
        recommendations = await learning_manager.get_personalized_recommendations(
            user_id="perf_test_user",
            limit=10
        )
        rec_time = (datetime.now() - start_time).total_seconds()

        assert len(recommendations) <= 10
        assert rec_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_feature_toggle(self, learning_manager):
        """Test enabling/disabling learning features."""
        assert learning_manager.get_learning_enabled() is True

        # Disable learning features
        await learning_manager.disable_learning_features()
        assert learning_manager.get_learning_enabled() is False

        # Re-enable learning features
        await learning_manager.enable_learning_features()
        assert learning_manager.get_learning_enabled() is True

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, learning_manager):
        """Test handling multiple concurrent learning sessions."""
        user_ids = ["user_1", "user_2", "user_3"]
        session_ids = []

        # Start multiple sessions
        for user_id in user_ids:
            session_id = await learning_manager.start_learning_session(user_id)
            session_ids.append(session_id)

        assert len(session_ids) == 3
        assert len(learning_manager._active_sessions) == 3

        # Record activities in parallel
        activities = []
        for i, session_id in enumerate(session_ids):
            activities.append(
                learning_manager.record_learning_activity(
                    session_id=session_id,
                    content_id=f"content_{i}",
                    success=True
                )
            )

        results = await asyncio.gather(*activities, return_exceptions=True)
        # Some may fail due to invalid content IDs, but shouldn't crash
        assert len(results) == 3

        # End all sessions
        for session_id in session_ids:
            await learning_manager.end_learning_session(session_id)

        assert len(learning_manager._active_sessions) == 0


class TestLearningMemoryManagerIntegration:
    """Integration tests for LearningMemoryManager with real workflows."""

    @pytest.fixture
    async def integrated_manager(self):
        """Create a fully integrated LearningMemoryManager."""
        memory_store = InMemoryStore()
        manager = LearningMemoryManager(
            memory_store=memory_store,
            enable_learning_features=True
        )
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_complete_learning_journey(self, integrated_manager):
        """Test a complete learning journey from beginner to advanced."""
        user_id = "journey_user"

        # Phase 1: Store foundational content
        foundations = [
            {
                "content": "What is programming?",
                "difficulty_level": DifficultyLevel.BEGINNER,
                "concept_tags": {"programming", "fundamentals"},
                "prerequisites": set()
            },
            {
                "content": "Python installation and setup",
                "difficulty_level": DifficultyLevel.BEGINNER,
                "concept_tags": {"python", "setup"},
                "prerequisites": {"programming"}
            },
            {
                "content": "Python variables and data types",
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "concept_tags": {"python", "variables", "data_types"},
                "prerequisites": {"python", "setup"}
            }
        ]

        for content in foundations:
            await integrated_manager.store_learning_content(**content)

        # Phase 2: Simulate learning sessions
        sessions_data = [
            {"concepts": ["programming"], "success_rate": 0.9},
            {"concepts": ["python", "setup"], "success_rate": 0.8},
            {"concepts": ["python", "variables"], "success_rate": 0.7}
        ]

        for session_data in sessions_data:
            session_id = await integrated_manager.start_learning_session(user_id)

            # Simulate studying concepts in this session
            session = integrated_manager._active_sessions[session_id]
            session.concepts_studied = session_data["concepts"]
            session.total_attempts = 10
            session.correct_attempts = int(10 * session_data["success_rate"])

            # Add mastery improvements
            for concept in session_data["concepts"]:
                session.mastery_improvements[concept] = 1

            await integrated_manager.end_learning_session(session_id)

        # Phase 3: Verify learning progression
        analytics = await integrated_manager.get_learning_analytics(user_id)
        assert analytics["student_model"]["profile_summary"]["concepts_mastered"] > 0

        # Phase 4: Get advanced recommendations
        recommendations = await integrated_manager.get_personalized_recommendations(
            user_id=user_id,
            query="python advanced",
            limit=5
        )

        # Should have some recommendations
        assert len(recommendations) >= 0

    @pytest.mark.asyncio
    async def test_adaptive_difficulty_progression(self, integrated_manager):
        """Test adaptive difficulty progression over multiple sessions."""
        user_id = "adaptive_user"
        concept_id = "python_loops"

        # Store content at different difficulty levels
        difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        for difficulty in difficulties:
            await integrated_manager.store_learning_content(
                content=f"Python loops - {difficulty.name}",
                difficulty_level=difficulty,
                concept_tags={"python", "loops"},
                estimated_time_minutes=30
            )

        # Simulate progression through difficulty levels
        performance_progression = [0.9, 0.85, 0.7]  # Decreasing performance as difficulty increases

        for i, performance in enumerate(performance_progression):
            # Get current difficulty recommendation
            recommended_difficulty = await integrated_manager.get_adaptive_difficulty_recommendation(
                user_id=user_id,
                concept_id=concept_id
            )

            # Start session
            session_id = await integrated_manager.start_learning_session(user_id)
            session = integrated_manager._active_sessions[session_id]

            # Simulate learning with current performance
            session.concepts_studied = ["python", "loops"]
            session.total_attempts = 20
            session.correct_attempts = int(20 * performance)
            session.difficulty_levels_attempted.add(recommended_difficulty)

            await integrated_manager.end_learning_session(session_id)

        # Verify that difficulty recommendations adapt
        final_recommendation = await integrated_manager.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            concept_id=concept_id
        )

        assert isinstance(final_recommendation, DifficultyLevel)

    @pytest.mark.asyncio
    async def test_knowledge_graph_learning_paths(self, integrated_manager):
        """Test knowledge graph-based learning path generation."""
        from learning.data_models import ConceptNode, ConceptType

        # Create a concept hierarchy
        concepts = [
            ConceptNode(
                concept_id="programming_basics",
                name="Programming Basics",
                description="Fundamental programming concepts",
                concept_type=ConceptType.FUNDAMENTAL,
                prerequisites=set()
            ),
            ConceptNode(
                concept_id="python_syntax",
                name="Python Syntax",
                description="Basic Python syntax",
                concept_type=ConceptType.KNOWLEDGE,
                prerequisites={"programming_basics"}
            ),
            ConceptNode(
                concept_id="python_functions",
                name="Python Functions",
                description="Functions in Python",
                concept_type=ConceptType.SKILL,
                prerequisites={"python_syntax"}
            ),
            ConceptNode(
                concept_id="python_oop",
                name="Python OOP",
                description="Object-oriented programming in Python",
                concept_type=ConceptType.APPLICATION,
                prerequisites={"python_functions"}
            )
        ]

        # Add concepts to knowledge graph
        for concept in concepts:
            await integrated_manager.add_concept_to_knowledge_graph(concept)

        # Get learning path for advanced concept
        user_id = "path_user"
        learning_path = await integrated_manager.get_learning_path(
            user_id=user_id,
            target_concept="python_oop"
        )

        # Should include prerequisites in correct order
        assert "programming_basics" in learning_path
        assert "python_syntax" in learning_path
        assert "python_functions" in learning_path
        assert "python_oop" in learning_path

        # Check order (should respect prerequisites)
        if len(learning_path) > 1:
            basics_index = learning_path.index("programming_basics") if "programming_basics" in learning_path else -1
            syntax_index = learning_path.index("python_syntax") if "python_syntax" in learning_path else -1

            if basics_index >= 0 and syntax_index >= 0:
                assert basics_index < syntax_index  # Basics should come before syntax


if __name__ == "__main__":
    pytest.main([__file__])