"""Educational retrieval strategies for learning-optimized memory search."""

import asyncio
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

from ..memory.retrieval_strategy import RetrievalStrategy
from ..memory.memory_store import MemoryEntry
from .data_models import (
    LearningMemoryEntry,
    StudentProfile,
    MasteryLevel,
    DifficultyLevel,
    LearningStyle
)


class EducationalRetrievalStrategy(RetrievalStrategy):
    """
    Abstract base class for educational retrieval strategies.

    Extends the standard RetrievalStrategy with learning-specific
    capabilities and student-aware ranking.
    """

    def __init__(self, student_model: Optional[Any] = None):
        """
        Initialize educational retrieval strategy.

        Args:
            student_model: StudentModel instance for personalization
        """
        self.student_model = student_model

    @abstractmethod
    async def retrieve_for_learning(
        self,
        query: str,
        entries: List[MemoryEntry],
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """
        Retrieve entries optimized for learning outcomes.

        Args:
            query: Search query
            entries: Available memory entries
            student_profile: Student profile for personalization
            learning_context: Current learning context
            limit: Maximum number of results
            filters: Optional filters to apply

        Returns:
            List of relevant memory entries optimized for learning
        """
        pass

    @abstractmethod
    def calculate_educational_relevance(
        self,
        query: str,
        entry: MemoryEntry,
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate educational relevance score for a memory entry.

        Args:
            query: Search query
            entry: Memory entry to score
            student_profile: Student profile for personalization
            learning_context: Current learning context

        Returns:
            Educational relevance score (0.0 to 1.0)
        """
        pass

    async def retrieve(
        self,
        query: str,
        entries: List[MemoryEntry],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Standard retrieve method for compatibility."""
        return await self.retrieve_for_learning(
            query, entries, None, None, limit, filters
        )

    def calculate_relevance_score(
        self,
        query: str,
        entry: MemoryEntry,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Standard relevance calculation for compatibility."""
        return self.calculate_educational_relevance(query, entry, None, context)

    def _convert_to_learning_entry(self, entry: MemoryEntry) -> LearningMemoryEntry:
        """Convert standard MemoryEntry to LearningMemoryEntry if needed."""
        if isinstance(entry, LearningMemoryEntry):
            return entry

        # Convert with default educational metadata
        learning_entry = LearningMemoryEntry(
            id=entry.id,
            content=entry.content,
            metadata=entry.metadata,
            timestamp=entry.timestamp,
            embedding=entry.embedding,
            importance=entry.importance,
            access_count=entry.access_count,
            last_accessed=entry.last_accessed
        )

        return learning_entry


class SpacedRepetitionRetrieval(EducationalRetrievalStrategy):
    """
    Retrieval strategy optimized for spaced repetition scheduling.

    Prioritizes content based on spaced repetition algorithms and
    optimal review timing for maximum retention.
    """

    def __init__(self, student_model: Optional[Any] = None, algorithm: str = "sm2"):
        """
        Initialize spaced repetition retrieval.

        Args:
            student_model: StudentModel instance
            algorithm: Spaced repetition algorithm ("sm2", "fsrs")
        """
        super().__init__(student_model)
        self.algorithm = algorithm

    async def retrieve_for_learning(
        self,
        query: str,
        entries: List[MemoryEntry],
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve entries optimized for spaced repetition."""

        # Convert to learning entries
        learning_entries = [self._convert_to_learning_entry(entry) for entry in entries]

        # Apply filters first
        if filters:
            learning_entries = self._apply_educational_filters(learning_entries, filters)

        # Calculate educational scores
        scored_entries = []
        for entry in learning_entries:
            relevance_score = self.calculate_educational_relevance(
                query, entry, student_profile, learning_context
            )
            spaced_repetition_score = self._calculate_spaced_repetition_priority(
                entry, student_profile
            )

            # Combine scores (weighted average)
            combined_score = (0.4 * relevance_score + 0.6 * spaced_repetition_score)
            scored_entries.append((combined_score, entry))

        # Sort by combined score and return top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def calculate_educational_relevance(
        self,
        query: str,
        entry: MemoryEntry,
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate educational relevance with spaced repetition focus."""

        learning_entry = self._convert_to_learning_entry(entry)
        score = 0.0

        # Base text relevance (reduced weight for spaced repetition)
        text_similarity = self._calculate_text_similarity(query, learning_entry.content)
        score += text_similarity * 0.3

        # Review timing priority
        if learning_entry.is_due_for_review:
            score += 0.4

        # Mastery level consideration
        mastery_factor = self._calculate_mastery_factor(learning_entry, student_profile)
        score += mastery_factor * 0.2

        # Concept relevance
        if learning_context and 'focus_concepts' in learning_context:
            focus_concepts = set(learning_context['focus_concepts'])
            if learning_entry.concept_tags.intersection(focus_concepts):
                score += 0.1

        return min(1.0, score)

    def _calculate_spaced_repetition_priority(
        self,
        entry: LearningMemoryEntry,
        student_profile: Optional[StudentProfile] = None
    ) -> float:
        """Calculate priority based on spaced repetition algorithm."""

        # Check if due for review
        if not entry.is_due_for_review:
            return 0.1  # Low priority if not due

        # Calculate overdue factor
        if entry.next_review_date:
            days_overdue = (datetime.now() - entry.next_review_date).days
            overdue_factor = min(1.0, max(0.0, days_overdue / 7))  # Scale over a week
        else:
            overdue_factor = 1.0  # New content gets high priority

        # Factor in difficulty (harder content gets more priority)
        difficulty_factor = entry.difficulty_level.value / 4.0

        # Success rate factor (lower success = higher priority)
        success_rate = entry.success_rate
        difficulty_adjustment = 1.0 - (success_rate * 0.5)

        # Combine factors
        priority = (0.4 * overdue_factor +
                   0.3 * difficulty_factor +
                   0.3 * difficulty_adjustment)

        return min(1.0, priority)

    def _calculate_mastery_factor(
        self,
        entry: LearningMemoryEntry,
        student_profile: Optional[StudentProfile]
    ) -> float:
        """Calculate factor based on current mastery level."""
        if not student_profile:
            return 0.5

        # Check mastery for related concepts
        mastery_scores = []
        for concept in entry.concept_tags:
            mastery_level = student_profile.concept_mastery.get(concept, MasteryLevel.UNKNOWN)
            # Lower mastery = higher priority for review
            mastery_score = 1.0 - (mastery_level.value / MasteryLevel.MASTERED.value)
            mastery_scores.append(mastery_score)

        return sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.5

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """Simple text similarity calculation."""
        query_lower = query.lower()
        content_lower = content.lower()

        if query_lower in content_lower:
            return 1.0

        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words:
            return 0.0

        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)

        return len(intersection) / len(union) if union else 0.0

    def _apply_educational_filters(
        self,
        entries: List[LearningMemoryEntry],
        filters: Dict[str, Any]
    ) -> List[LearningMemoryEntry]:
        """Apply educational-specific filters."""
        filtered = []

        for entry in entries:
            passes_filter = True

            # Difficulty level filter
            if 'difficulty_level' in filters:
                if entry.difficulty_level != filters['difficulty_level']:
                    passes_filter = False

            # Mastery level filter
            if 'max_mastery_level' in filters:
                if entry.mastery_level.value > filters['max_mastery_level'].value:
                    passes_filter = False

            # Concept tags filter
            if 'required_concepts' in filters:
                required = set(filters['required_concepts'])
                if not entry.concept_tags.intersection(required):
                    passes_filter = False

            # Due for review filter
            if 'due_for_review_only' in filters and filters['due_for_review_only']:
                if not entry.is_due_for_review:
                    passes_filter = False

            if passes_filter:
                filtered.append(entry)

        return filtered


class MasteryBasedRetrieval(EducationalRetrievalStrategy):
    """
    Retrieval strategy that prioritizes content based on mastery gaps
    and learning objectives.
    """

    async def retrieve_for_learning(
        self,
        query: str,
        entries: List[MemoryEntry],
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve entries optimized for mastery development."""

        learning_entries = [self._convert_to_learning_entry(entry) for entry in entries]

        # Apply filters
        if filters:
            learning_entries = self._apply_educational_filters(learning_entries, filters)

        # Calculate mastery-based scores
        scored_entries = []
        for entry in learning_entries:
            relevance_score = self.calculate_educational_relevance(
                query, entry, student_profile, learning_context
            )
            mastery_score = self._calculate_mastery_priority(
                entry, student_profile, learning_context
            )

            # Weight towards mastery gaps
            combined_score = (0.3 * relevance_score + 0.7 * mastery_score)
            scored_entries.append((combined_score, entry))

        # Sort and return
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def calculate_educational_relevance(
        self,
        query: str,
        entry: MemoryEntry,
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate relevance focused on mastery development."""

        learning_entry = self._convert_to_learning_entry(entry)
        score = 0.0

        # Text relevance
        text_similarity = self._calculate_text_similarity(query, learning_entry.content)
        score += text_similarity * 0.4

        # Knowledge gap alignment
        if student_profile:
            knowledge_gaps = set(student_profile.get_knowledge_gaps())
            concept_overlap = learning_entry.concept_tags.intersection(knowledge_gaps)
            if concept_overlap:
                score += 0.4

        # Learning objective alignment
        if learning_context and 'learning_objectives' in learning_context:
            objectives = set(learning_context['learning_objectives'])
            objective_overlap = set(learning_entry.learning_objectives).intersection(objectives)
            if objective_overlap:
                score += 0.2

        return min(1.0, score)

    def _calculate_mastery_priority(
        self,
        entry: LearningMemoryEntry,
        student_profile: Optional[StudentProfile],
        learning_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate priority based on mastery development needs."""

        if not student_profile:
            return 0.5

        priority = 0.0

        # Knowledge gap priority
        knowledge_gaps = set(student_profile.get_knowledge_gaps())
        gap_overlap = entry.concept_tags.intersection(knowledge_gaps)
        if gap_overlap:
            priority += 0.5

        # Prerequisite readiness
        prereq_ready = self._check_prerequisite_readiness(entry, student_profile)
        if prereq_ready:
            priority += 0.3
        elif entry.prerequisites:
            priority += 0.1  # Some priority for future readiness

        # Difficulty appropriateness
        difficulty_match = self._calculate_difficulty_appropriateness(
            entry, student_profile
        )
        priority += difficulty_match * 0.2

        return min(1.0, priority)

    def _check_prerequisite_readiness(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> bool:
        """Check if student is ready for this content based on prerequisites."""
        if not entry.prerequisites:
            return True

        for prereq in entry.prerequisites:
            mastery = student_profile.concept_mastery.get(prereq, MasteryLevel.UNKNOWN)
            if mastery.value < MasteryLevel.PROFICIENT.value:
                return False

        return True

    def _calculate_difficulty_appropriateness(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Calculate how appropriate the difficulty is for the student."""

        # Get student's overall performance level
        overall_mastery = student_profile.overall_mastery_score / 100.0

        # Map mastery to preferred difficulty
        if overall_mastery >= 0.8:
            preferred_difficulty = DifficultyLevel.ADVANCED
        elif overall_mastery >= 0.6:
            preferred_difficulty = DifficultyLevel.INTERMEDIATE
        else:
            preferred_difficulty = DifficultyLevel.BEGINNER

        # Calculate match score
        difficulty_diff = abs(entry.difficulty_level.value - preferred_difficulty.value)
        appropriateness = max(0.0, 1.0 - (difficulty_diff / 3.0))

        return appropriateness

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """Calculate text similarity between query and content."""
        query_lower = query.lower()
        content_lower = content.lower()

        if query_lower in content_lower:
            return 1.0

        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words:
            return 0.0

        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)

    def _apply_educational_filters(
        self,
        entries: List[LearningMemoryEntry],
        filters: Dict[str, Any]
    ) -> List[LearningMemoryEntry]:
        """Apply educational filters."""
        # Reuse implementation from SpacedRepetitionRetrieval
        return SpacedRepetitionRetrieval._apply_educational_filters(self, entries, filters)


class AdaptiveRetrieval(EducationalRetrievalStrategy):
    """
    Adaptive retrieval strategy that personalizes based on learning patterns,
    style preferences, and real-time performance.
    """

    async def retrieve_for_learning(
        self,
        query: str,
        entries: List[MemoryEntry],
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve entries with adaptive personalization."""

        learning_entries = [self._convert_to_learning_entry(entry) for entry in entries]

        # Apply filters
        if filters:
            learning_entries = self._apply_educational_filters(learning_entries, filters)

        # Calculate adaptive scores
        scored_entries = []
        for entry in learning_entries:
            base_relevance = self.calculate_educational_relevance(
                query, entry, student_profile, learning_context
            )
            adaptive_score = self._calculate_adaptive_score(
                entry, student_profile, learning_context
            )

            # Combine with adaptive weighting
            combined_score = (0.5 * base_relevance + 0.5 * adaptive_score)
            scored_entries.append((combined_score, entry))

        # Sort and return
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def calculate_educational_relevance(
        self,
        query: str,
        entry: MemoryEntry,
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate base educational relevance."""

        learning_entry = self._convert_to_learning_entry(entry)
        score = 0.0

        # Text relevance
        text_similarity = self._calculate_text_similarity(query, learning_entry.content)
        score += text_similarity * 0.3

        # Learning style match
        if student_profile:
            style_match = self._calculate_learning_style_match(
                learning_entry, student_profile
            )
            score += style_match * 0.3

        # Difficulty preference match
        if student_profile:
            difficulty_match = self._calculate_difficulty_preference_match(
                learning_entry, student_profile
            )
            score += difficulty_match * 0.2

        # Context relevance
        if learning_context:
            context_match = self._calculate_context_match(learning_entry, learning_context)
            score += context_match * 0.2

        return min(1.0, score)

    def _calculate_adaptive_score(
        self,
        entry: LearningMemoryEntry,
        student_profile: Optional[StudentProfile],
        learning_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate adaptive personalization score."""

        if not student_profile:
            return 0.5

        score = 0.0

        # Performance-based adaptation
        performance_factor = self._calculate_performance_adaptation(
            entry, student_profile
        )
        score += performance_factor * 0.4

        # Learning velocity adaptation
        velocity_factor = self._calculate_velocity_adaptation(
            entry, student_profile
        )
        score += velocity_factor * 0.3

        # Exploration vs exploitation balance
        exploration_factor = self._calculate_exploration_factor(
            entry, student_profile
        )
        score += exploration_factor * 0.3

        return min(1.0, score)

    def _calculate_learning_style_match(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Calculate how well content matches student's learning style."""

        # This would ideally analyze content type and format
        # For now, use simplified metadata-based matching
        preferred_style = student_profile.preferred_learning_style

        # Check if content metadata indicates style compatibility
        content_styles = entry.metadata.get('learning_styles', [])
        if preferred_style.value in content_styles:
            return 1.0
        elif 'multimodal' in content_styles:
            return 0.8
        else:
            return 0.5  # Neutral for unspecified

    def _calculate_difficulty_preference_match(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Calculate difficulty preference match."""

        preferred_difficulty = student_profile.preferred_difficulty
        content_difficulty = entry.difficulty_level

        # Perfect match
        if preferred_difficulty == content_difficulty:
            return 1.0

        # Close match
        difficulty_diff = abs(preferred_difficulty.value - content_difficulty.value)
        if difficulty_diff == 1:
            return 0.7
        elif difficulty_diff == 2:
            return 0.4
        else:
            return 0.2

    def _calculate_context_match(
        self,
        entry: LearningMemoryEntry,
        learning_context: Dict[str, Any]
    ) -> float:
        """Calculate match with current learning context."""

        score = 0.0

        # Session goals match
        if 'session_goals' in learning_context:
            session_goals = set(learning_context['session_goals'])
            content_objectives = set(entry.learning_objectives)
            overlap = session_goals.intersection(content_objectives)
            if overlap:
                score += 0.5

        # Time constraint match
        if 'available_time_minutes' in learning_context:
            available_time = learning_context['available_time_minutes']
            if entry.estimated_time_minutes:
                if entry.estimated_time_minutes <= available_time:
                    score += 0.3
                else:
                    score += 0.1  # Some penalty for time mismatch

        # Focus area match
        if 'focus_areas' in learning_context:
            focus_areas = set(learning_context['focus_areas'])
            concept_overlap = entry.concept_tags.intersection(focus_areas)
            if concept_overlap:
                score += 0.2

        return min(1.0, score)

    def _calculate_performance_adaptation(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Adapt based on student's performance patterns."""

        # If student is struggling, prioritize easier content
        if student_profile.average_session_score < 0.6:
            if entry.difficulty_level in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]:
                return 0.8
            else:
                return 0.3

        # If student is excelling, prioritize challenging content
        elif student_profile.average_session_score > 0.8:
            if entry.difficulty_level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
                return 0.8
            else:
                return 0.4

        # Balanced performance - maintain current level
        else:
            return 0.6

    def _calculate_velocity_adaptation(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Adapt based on learning velocity."""

        velocity = student_profile.learning_velocity

        # Fast learners get more content or harder content
        if velocity > 1.5:
            return 0.8

        # Slow learners get focused, reinforcing content
        elif velocity < 0.7:
            # Prioritize review content
            if entry.repetition_count > 0:
                return 0.8
            else:
                return 0.4

        # Average velocity
        else:
            return 0.6

    def _calculate_exploration_factor(
        self,
        entry: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Balance exploration of new content vs exploitation of known content."""

        exploration_tendency = student_profile.exploration_tendency

        # Check if this is new content for the student
        studied_concepts = student_profile.concepts_mastered.union(
            student_profile.concepts_in_progress
        )

        is_new_content = not entry.concept_tags.intersection(studied_concepts)

        if is_new_content:
            # Exploration score based on tendency
            return exploration_tendency
        else:
            # Exploitation score (inverse of exploration)
            return 1.0 - exploration_tendency

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """Calculate text similarity."""
        # Reuse implementation from other classes
        query_lower = query.lower()
        content_lower = content.lower()

        if query_lower in content_lower:
            return 1.0

        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words:
            return 0.0

        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)

    def _apply_educational_filters(
        self,
        entries: List[LearningMemoryEntry],
        filters: Dict[str, Any]
    ) -> List[LearningMemoryEntry]:
        """Apply educational filters."""
        # Reuse implementation from SpacedRepetitionRetrieval
        return SpacedRepetitionRetrieval._apply_educational_filters(self, entries, filters)


class HybridEducationalRetrieval(EducationalRetrievalStrategy):
    """
    Hybrid retrieval strategy that combines multiple educational strategies
    with configurable weights and automatic strategy selection.
    """

    def __init__(
        self,
        strategies: Optional[List[Tuple[EducationalRetrievalStrategy, float]]] = None,
        student_model: Optional[Any] = None
    ):
        """
        Initialize hybrid educational retrieval.

        Args:
            strategies: List of (strategy, weight) tuples
            student_model: StudentModel instance
        """
        super().__init__(student_model)

        if strategies is None:
            # Default strategy combination
            strategies = [
                (SpacedRepetitionRetrieval(student_model), 0.4),
                (MasteryBasedRetrieval(student_model), 0.4),
                (AdaptiveRetrieval(student_model), 0.2)
            ]

        self.strategies = strategies
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Normalize strategy weights to sum to 1.0."""
        total_weight = sum(weight for _, weight in self.strategies)
        if total_weight > 0:
            self.strategies = [
                (strategy, weight / total_weight)
                for strategy, weight in self.strategies
            ]

    async def retrieve_for_learning(
        self,
        query: str,
        entries: List[MemoryEntry],
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve using hybrid strategy combination."""

        # Get results from each strategy
        strategy_results = []
        for strategy, weight in self.strategies:
            try:
                results = await strategy.retrieve_for_learning(
                    query, entries, student_profile, learning_context, limit * 2, filters
                )
                strategy_results.append((results, weight))
            except Exception:
                # Skip failed strategy
                continue

        if not strategy_results:
            return []

        # Combine scores using rank-based fusion
        entry_scores = {}
        for results, weight in strategy_results:
            for rank, entry in enumerate(results):
                # Higher rank = lower rank value, so invert
                rank_score = (len(results) - rank) / len(results)
                weighted_score = rank_score * weight

                entry_id = entry.id
                if entry_id in entry_scores:
                    entry_scores[entry_id] = (
                        entry_scores[entry_id][0] + weighted_score,
                        entry
                    )
                else:
                    entry_scores[entry_id] = (weighted_score, entry)

        # Sort by combined score
        scored_entries = [
            (score, entry) for score, entry in entry_scores.values()
        ]
        scored_entries.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in scored_entries[:limit]]

    def calculate_educational_relevance(
        self,
        query: str,
        entry: MemoryEntry,
        student_profile: Optional[StudentProfile] = None,
        learning_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate hybrid educational relevance score."""

        total_score = 0.0
        total_weight = 0.0

        for strategy, weight in self.strategies:
            try:
                score = strategy.calculate_educational_relevance(
                    query, entry, student_profile, learning_context
                )
                total_score += score * weight
                total_weight += weight
            except Exception:
                continue

        return total_score / total_weight if total_weight > 0 else 0.0

    def add_strategy(
        self,
        strategy: EducationalRetrievalStrategy,
        weight: float
    ) -> None:
        """Add a new strategy to the hybrid combination."""
        self.strategies.append((strategy, weight))
        self._normalize_weights()

    def remove_strategy(self, strategy_class: type) -> bool:
        """Remove a strategy by class type."""
        original_length = len(self.strategies)
        self.strategies = [
            (strategy, weight)
            for strategy, weight in self.strategies
            if not isinstance(strategy, strategy_class)
        ]

        if len(self.strategies) < original_length:
            self._normalize_weights()
            return True
        return False

    def update_strategy_weight(self, strategy_class: type, new_weight: float) -> bool:
        """Update weight for a specific strategy."""
        for i, (strategy, weight) in enumerate(self.strategies):
            if isinstance(strategy, strategy_class):
                self.strategies[i] = (strategy, new_weight)
                self._normalize_weights()
                return True
        return False