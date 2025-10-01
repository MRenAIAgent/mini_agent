"""Main Learning Memory Manager that extends CoreMemoryManager."""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Awaitable, Set, Tuple
from datetime import datetime, timedelta

from ..memory.memory_manager import CoreMemoryManager
from ..memory.memory_store import MemoryEntry, MemoryStore
from ..memory.retrieval_strategy import RetrievalStrategy

from .data_models import (
    LearningMemoryEntry,
    StudentProfile,
    LearningSession,
    ConceptNode,
    MasteryRecord,
    DifficultyLevel,
    LearningStyle,
    MasteryLevel
)
from .student_model import StudentModel
from .learning_analytics import LearningAnalytics
from .spaced_repetition import SpacedRepetitionEngine
from .adaptive_difficulty import AdaptiveDifficultyEngine
from .knowledge_graph import KnowledgeGraph
from .educational_retrieval import (
    EducationalRetrievalStrategy,
    HybridEducationalRetrieval,
    SpacedRepetitionRetrieval,
    MasteryBasedRetrieval,
    AdaptiveRetrieval
)


class LearningMemoryManager(CoreMemoryManager):
    """
    Enhanced memory manager with comprehensive learning capabilities.

    Extends CoreMemoryManager to provide educational intelligence,
    personalized learning, and sophisticated student modeling while
    maintaining full backward compatibility.
    """

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        retrieval_strategy: Optional[RetrievalStrategy] = None,
        auto_save_interval: int = 300,
        backend_config: Optional[Dict[str, Any]] = None,
        enable_learning_features: bool = True
    ):
        """
        Initialize the learning memory manager.

        Args:
            memory_store: Backend store for persistent memory
            retrieval_strategy: Strategy for memory retrieval and ranking
            auto_save_interval: Automatic save interval in seconds
            backend_config: Configuration for memory backend switching
            enable_learning_features: Whether to enable learning-specific features
        """
        # Initialize base CoreMemoryManager
        super().__init__(memory_store, retrieval_strategy, auto_save_interval, backend_config)

        # Learning-specific configuration
        self.learning_enabled = enable_learning_features

        if self.learning_enabled:
            # Initialize learning components
            self.student_model = StudentModel(storage_backend=self.current_backend)
            self.learning_analytics = LearningAnalytics(storage_backend=self.current_backend)
            self.spaced_repetition = SpacedRepetitionEngine()
            self.adaptive_difficulty = AdaptiveDifficultyEngine(self.student_model)
            self.knowledge_graph = KnowledgeGraph(storage_backend=self.current_backend)

            # Set up educational retrieval strategy if not provided
            if not isinstance(self.retrieval_strategy, EducationalRetrievalStrategy):
                self.educational_retrieval = HybridEducationalRetrieval(
                    student_model=self.student_model
                )
            else:
                self.educational_retrieval = self.retrieval_strategy

            # Learning-specific callbacks
            self._on_learning_session_completed: Optional[Callable[[LearningSession], Awaitable[None]]] = None
            self._on_mastery_level_changed: Optional[Callable[[str, str, MasteryLevel], Awaitable[None]]] = None
            self._on_learning_goal_achieved: Optional[Callable[[str, str], Awaitable[None]]] = None

            # Active learning sessions
            self._active_sessions: Dict[str, LearningSession] = {}

    # Core Learning Methods

    async def store_learning_content(
        self,
        content: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        concept_tags: Optional[Set[str]] = None,
        learning_objectives: Optional[List[str]] = None,
        prerequisites: Optional[Set[str]] = None,
        estimated_time_minutes: Optional[int] = None,
        importance: float = 1.0,
        session_id: Optional[str] = None,
        **metadata
    ) -> bool:
        """
        Store learning content with educational metadata.

        Args:
            content: The learning content to store
            difficulty_level: Difficulty level of the content
            concept_tags: Set of concept tags
            learning_objectives: List of learning objectives
            prerequisites: Set of prerequisite concepts
            estimated_time_minutes: Estimated time to complete
            importance: Importance score (0.0 to 1.0)
            session_id: Optional session ID for context
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.learning_enabled:
            # Fall back to standard memory storage
            return await self.store_memory(content, importance, session_id, **metadata)

        try:
            # Create learning memory entry
            learning_entry = LearningMemoryEntry(
                content=content,
                importance=importance,
                difficulty_level=difficulty_level,
                concept_tags=concept_tags or set(),
                learning_objectives=learning_objectives or [],
                prerequisites=prerequisites or set(),
                estimated_time_minutes=estimated_time_minutes,
                metadata=metadata
            )

            # Store in memory store
            success = await self.memory_store.store(learning_entry)

            if success:
                # Update knowledge graph
                await self._update_knowledge_graph_from_entry(learning_entry)

                # Add session context if available
                if session_id:
                    await self._add_to_learning_session(session_id, learning_entry)

                # Trigger learning callback
                if self._on_memory_stored:
                    await self._on_memory_stored(learning_entry)

            return success

        except Exception as e:
            print(f"Error storing learning content: {e}")
            return False

    async def get_personalized_recommendations(
        self,
        user_id: str,
        query: Optional[str] = None,
        limit: int = 5,
        focus_areas: Optional[List[str]] = None,
        available_time_minutes: Optional[int] = None
    ) -> List[LearningMemoryEntry]:
        """
        Get personalized learning recommendations for a student.

        Args:
            user_id: Student identifier
            query: Optional search query
            limit: Maximum number of recommendations
            focus_areas: Optional list of concept areas to focus on
            available_time_minutes: Available study time

        Returns:
            List of personalized learning content recommendations
        """
        if not self.learning_enabled:
            # Fall back to standard search
            if query:
                return await self.search_memory(query, limit)
            else:
                return await self.get_all_memories()[:limit]

        try:
            # Get student profile
            student_profile = await self.student_model.get_or_create_profile(user_id)

            # Get all learning entries
            all_entries = await self.get_all_memories()
            learning_entries = [
                entry for entry in all_entries
                if isinstance(entry, LearningMemoryEntry)
            ]

            # Create learning context
            learning_context = {
                'focus_areas': focus_areas or [],
                'available_time_minutes': available_time_minutes,
                'session_goals': student_profile.learning_goals
            }

            # Use educational retrieval for recommendations
            recommendations = await self.educational_retrieval.retrieve_for_learning(
                query=query or "",
                entries=learning_entries,
                student_profile=student_profile,
                learning_context=learning_context,
                limit=limit
            )

            return recommendations

        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
            return []

    async def start_learning_session(
        self,
        user_id: str,
        session_goals: Optional[List[str]] = None
    ) -> str:
        """
        Start a new learning session for a student.

        Args:
            user_id: Student identifier
            session_goals: Optional learning goals for this session

        Returns:
            Session ID for the new learning session
        """
        if not self.learning_enabled:
            return f"session_{datetime.now().timestamp()}"

        try:
            # Create new learning session
            session = LearningSession(
                user_id=user_id,
                start_time=datetime.now()
            )

            # Set session goals if provided
            if session_goals:
                session.activities_completed = []  # Initialize for goal tracking

            # Store active session
            self._active_sessions[session.session_id] = session

            return session.session_id

        except Exception as e:
            print(f"Error starting learning session: {e}")
            return f"session_{datetime.now().timestamp()}"

    async def record_learning_activity(
        self,
        session_id: str,
        content_id: str,
        success: bool,
        response_time_seconds: Optional[float] = None,
        difficulty_experienced: Optional[DifficultyLevel] = None
    ) -> bool:
        """
        Record a learning activity within a session.

        Args:
            session_id: Learning session ID
            content_id: ID of the content that was studied
            success: Whether the activity was successful
            response_time_seconds: Time taken to complete
            difficulty_experienced: Actual difficulty experienced

        Returns:
            True if successful, False otherwise
        """
        if not self.learning_enabled:
            return True  # No-op if learning features disabled

        try:
            # Get active session
            if session_id not in self._active_sessions:
                return False

            session = self._active_sessions[session_id]

            # Update session with activity
            session.total_attempts += 1
            if success:
                session.correct_attempts += 1

            # Update response time
            if response_time_seconds:
                if session.average_response_time is None:
                    session.average_response_time = response_time_seconds
                else:
                    # Running average
                    session.average_response_time = (
                        (session.average_response_time * (session.total_attempts - 1) +
                         response_time_seconds) / session.total_attempts
                    )

            # Record difficulty if provided
            if difficulty_experienced:
                session.difficulty_levels_attempted.add(difficulty_experienced)

            # Get content entry for concept tracking
            content_entry = await self.memory_store.retrieve(content_id)
            if isinstance(content_entry, LearningMemoryEntry):
                # Track concepts studied
                for concept in content_entry.concept_tags:
                    if concept not in session.concepts_studied:
                        session.concepts_studied.append(concept)

                # Update spaced repetition data
                await self.spaced_repetition.record_review(
                    content_entry, success, response_time_seconds
                )

            return True

        except Exception as e:
            print(f"Error recording learning activity: {e}")
            return False

    async def end_learning_session(self, session_id: str) -> Optional[LearningSession]:
        """
        End a learning session and update student model.

        Args:
            session_id: Learning session ID

        Returns:
            Completed LearningSession if successful, None otherwise
        """
        if not self.learning_enabled or session_id not in self._active_sessions:
            return None

        try:
            # Get and end session
            session = self._active_sessions[session_id]
            session.end_session()

            # Record session in student model
            await self.student_model.record_learning_session(session.user_id, session)

            # Update learning analytics
            await self.learning_analytics.record_session(session)

            # Check for mastery level changes
            await self._check_mastery_improvements(session)

            # Remove from active sessions
            del self._active_sessions[session_id]

            # Trigger completion callback
            if self._on_learning_session_completed:
                await self._on_learning_session_completed(session)

            return session

        except Exception as e:
            print(f"Error ending learning session: {e}")
            return None

    async def get_spaced_repetition_due(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[LearningMemoryEntry]:
        """
        Get content due for spaced repetition review.

        Args:
            user_id: Student identifier
            limit: Maximum number of items to return

        Returns:
            List of content due for review
        """
        if not self.learning_enabled:
            return []

        try:
            # Get all learning entries
            all_entries = await self.get_all_memories()
            learning_entries = [
                entry for entry in all_entries
                if isinstance(entry, LearningMemoryEntry)
            ]

            # Filter for items due for review
            due_entries = [
                entry for entry in learning_entries
                if entry.is_due_for_review
            ]

            # Sort by priority (overdue items first)
            due_entries.sort(key=lambda entry: (
                entry.next_review_date or datetime.min,
                -entry.importance
            ))

            return due_entries[:limit]

        except Exception as e:
            print(f"Error getting spaced repetition due items: {e}")
            return []

    async def get_adaptive_difficulty_recommendation(
        self,
        user_id: str,
        concept_id: str
    ) -> DifficultyLevel:
        """
        Get adaptive difficulty recommendation for a student and concept.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier

        Returns:
            Recommended difficulty level
        """
        if not self.learning_enabled:
            return DifficultyLevel.INTERMEDIATE

        try:
            return await self.adaptive_difficulty.recommend_difficulty(
                user_id, concept_id
            )
        except Exception as e:
            print(f"Error getting adaptive difficulty recommendation: {e}")
            return DifficultyLevel.INTERMEDIATE

    async def get_learning_analytics(
        self,
        user_id: str,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive learning analytics for a student.

        Args:
            user_id: Student identifier
            time_range_days: Number of days to include in analytics

        Returns:
            Dictionary containing learning analytics
        """
        if not self.learning_enabled:
            return {}

        try:
            # Get analytics from various components
            student_analytics = await self.student_model.get_learning_analytics(user_id)
            system_analytics = await self.learning_analytics.get_user_analytics(
                user_id, time_range_days
            )

            # Combine analytics
            combined_analytics = {
                'student_model': student_analytics,
                'system_analytics': system_analytics,
                'timestamp': datetime.now().isoformat()
            }

            return combined_analytics

        except Exception as e:
            print(f"Error getting learning analytics: {e}")
            return {}

    async def search_learning_content(
        self,
        query: str,
        user_id: Optional[str] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        concept_tags: Optional[Set[str]] = None,
        limit: int = 10
    ) -> List[LearningMemoryEntry]:
        """
        Search for learning content with educational filters.

        Args:
            query: Search query
            user_id: Optional user for personalization
            difficulty_level: Optional difficulty filter
            concept_tags: Optional concept tags filter
            limit: Maximum number of results

        Returns:
            List of relevant learning content
        """
        if not self.learning_enabled:
            # Fall back to standard search
            results = await self.search_memory(query, limit)
            return [
                entry for entry in results
                if isinstance(entry, LearningMemoryEntry)
            ]

        try:
            # Build educational filters
            filters = {}
            if difficulty_level:
                filters['difficulty_level'] = difficulty_level
            if concept_tags:
                filters['required_concepts'] = list(concept_tags)

            # Get student profile for personalization
            student_profile = None
            if user_id:
                student_profile = await self.student_model.get_or_create_profile(user_id)

            # Get all learning entries
            all_entries = await self.get_all_memories()
            learning_entries = [
                entry for entry in all_entries
                if isinstance(entry, LearningMemoryEntry)
            ]

            # Use educational retrieval
            results = await self.educational_retrieval.retrieve_for_learning(
                query=query,
                entries=learning_entries,
                student_profile=student_profile,
                learning_context=None,
                limit=limit,
                filters=filters
            )

            return results

        except Exception as e:
            print(f"Error searching learning content: {e}")
            return []

    # Knowledge Graph Methods

    async def add_concept_to_knowledge_graph(
        self,
        concept: ConceptNode
    ) -> bool:
        """
        Add a concept to the knowledge graph.

        Args:
            concept: ConceptNode to add

        Returns:
            True if successful, False otherwise
        """
        if not self.learning_enabled:
            return True  # No-op if learning features disabled

        return await self.knowledge_graph.add_concept(concept)

    async def get_concept_prerequisites(
        self,
        concept_id: str
    ) -> List[ConceptNode]:
        """
        Get prerequisites for a concept.

        Args:
            concept_id: Concept identifier

        Returns:
            List of prerequisite concepts
        """
        if not self.learning_enabled:
            return []

        return await self.knowledge_graph.get_prerequisites(concept_id)

    async def get_learning_path(
        self,
        user_id: str,
        target_concept: str
    ) -> List[str]:
        """
        Get personalized learning path to a target concept.

        Args:
            user_id: Student identifier
            target_concept: Target concept to learn

        Returns:
            List of concept IDs in learning order
        """
        if not self.learning_enabled:
            return [target_concept]

        try:
            student_profile = await self.student_model.get_or_create_profile(user_id)
            return await self.knowledge_graph.generate_learning_path(
                target_concept, student_profile.concept_mastery
            )
        except Exception as e:
            print(f"Error getting learning path: {e}")
            return [target_concept]

    # Callback Management

    def set_learning_session_callback(
        self,
        callback: Callable[[LearningSession], Awaitable[None]]
    ) -> None:
        """Set callback for when learning sessions are completed."""
        self._on_learning_session_completed = callback

    def set_mastery_level_callback(
        self,
        callback: Callable[[str, str, MasteryLevel], Awaitable[None]]
    ) -> None:
        """Set callback for when mastery levels change."""
        self._on_mastery_level_changed = callback

    def set_learning_goal_callback(
        self,
        callback: Callable[[str, str], Awaitable[None]]
    ) -> None:
        """Set callback for when learning goals are achieved."""
        self._on_learning_goal_achieved = callback

    # Override Methods for Learning Integration

    async def search_memory(
        self,
        query: str,
        limit: int = 10,
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """
        Enhanced search with optional learning personalization.

        Falls back to standard search if learning features are disabled
        or no user context is available.
        """
        if not self.learning_enabled:
            return await super().search_memory(query, limit, session_id, filters)

        try:
            # Try to get user context from session
            user_id = None
            if session_id:
                context = await self.get_context_memory(session_id)
                user_id = context.user_id

            # Use learning-aware search if user context available
            if user_id:
                return await self.search_learning_content(
                    query, user_id, limit=limit
                )
            else:
                # Fall back to standard search
                return await super().search_memory(query, limit, session_id, filters)

        except Exception:
            # Fall back to standard search on any error
            return await super().search_memory(query, limit, session_id, filters)

    # Private Helper Methods

    async def _update_knowledge_graph_from_entry(
        self,
        entry: LearningMemoryEntry
    ) -> None:
        """Update knowledge graph based on learning entry data."""
        try:
            # Create concept nodes for any new concepts
            for concept_tag in entry.concept_tags:
                if not await self.knowledge_graph.has_concept(concept_tag):
                    concept_node = ConceptNode(
                        concept_id=concept_tag,
                        name=concept_tag.replace('_', ' ').title(),
                        description=f"Concept: {concept_tag}",
                        concept_type=ConceptType.KNOWLEDGE,  # Default type
                        difficulty_level=entry.difficulty_level
                    )
                    concept_node.content_entries.add(entry.id)
                    await self.knowledge_graph.add_concept(concept_node)

                # Add prerequisite relationships
                for prereq in entry.prerequisites:
                    await self.knowledge_graph.add_prerequisite_relationship(
                        concept_tag, prereq
                    )

        except Exception as e:
            print(f"Error updating knowledge graph: {e}")

    async def _add_to_learning_session(
        self,
        session_id: str,
        entry: LearningMemoryEntry
    ) -> None:
        """Add content to active learning session."""
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            for concept in entry.concept_tags:
                if concept not in session.concepts_studied:
                    session.concepts_studied.append(concept)

    async def _check_mastery_improvements(
        self,
        session: LearningSession
    ) -> None:
        """Check for mastery level improvements and trigger callbacks."""
        try:
            for concept, improvement in session.mastery_improvements.items():
                if improvement > 0 and self._on_mastery_level_changed:
                    # Get current mastery level
                    student_profile = await self.student_model.get_or_create_profile(
                        session.user_id
                    )
                    current_level = student_profile.concept_mastery.get(
                        concept, MasteryLevel.UNKNOWN
                    )
                    await self._on_mastery_level_changed(
                        session.user_id, concept, current_level
                    )

        except Exception as e:
            print(f"Error checking mastery improvements: {e}")

    # Compatibility Methods

    def get_learning_enabled(self) -> bool:
        """Check if learning features are enabled."""
        return self.learning_enabled

    async def disable_learning_features(self) -> None:
        """Disable learning features and fall back to core functionality."""
        self.learning_enabled = False

    async def enable_learning_features(self) -> None:
        """Re-enable learning features if they were disabled."""
        if not hasattr(self, 'student_model'):
            # Re-initialize learning components
            self.student_model = StudentModel(storage_backend=self.current_backend)
            self.learning_analytics = LearningAnalytics(storage_backend=self.current_backend)
            self.spaced_repetition = SpacedRepetitionEngine()
            self.adaptive_difficulty = AdaptiveDifficultyEngine(self.student_model)
            self.knowledge_graph = KnowledgeGraph(storage_backend=self.current_backend)
            self.educational_retrieval = HybridEducationalRetrieval(
                student_model=self.student_model
            )

        self.learning_enabled = True