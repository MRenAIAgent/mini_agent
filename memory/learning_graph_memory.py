"""Learning graph memory manager for graph-based learning operations."""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryEntry


class ConceptStatus(Enum):
    """Status of a concept in the learning graph."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PRACTICED = "practiced"
    MASTERED = "mastered"
    NEEDS_REVIEW = "needs_review"


class LearningGraphMemory(CoreMemoryManager):
    """
    Learning graph memory manager that extends CoreMemoryManager for graph operations.

    Handles learning graphs, concept relationships, learning paths,
    and personalized learning recommendations.
    """

    def __init__(self, **kwargs):
        """Initialize learning graph memory manager."""
        super().__init__(**kwargs)
        self.memory_type = "learning_graph"

    async def initialize_user_learning_graph(
        self,
        user_id: str,
        knowledge_graph_id: str,
        domain: str,
        initial_assessment: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Initialize a user's learning graph based on a knowledge graph.

        Args:
            user_id: User identifier
            knowledge_graph_id: Identifier of the base knowledge graph
            domain: Subject domain (e.g., 'algebra', 'geometry')
            initial_assessment: Optional initial assessment of concept understanding

        Returns:
            True if successful, False otherwise
        """
        graph_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_graph',
            'user_id': user_id,
            'knowledge_graph_id': knowledge_graph_id,
            'domain': domain,
            'initial_assessment': initial_assessment or {},
            'initialized_at': datetime.now().isoformat(),
            'concept_statuses': {},
            'learning_path': [],
            'completed_concepts': [],
            'available_concepts': []
        }

        content = f"Learning graph initialized for {user_id} in {domain} domain based on knowledge graph {knowledge_graph_id}"

        return await self.store_memory(
            content=content,
            importance=0.9,
            **graph_metadata
        )

    async def update_concept_status(
        self,
        user_id: str,
        concept_id: str,
        new_status: ConceptStatus,
        understanding_level: float,
        evidence: str,
        **metadata
    ) -> bool:
        """
        Update the status and understanding level of a concept.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            new_status: New status of the concept
            understanding_level: Understanding level (0.0 to 1.0)
            evidence: Evidence for the status update
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        status_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'concept_status',
            'user_id': user_id,
            'concept_id': concept_id,
            'status': new_status.value,
            'understanding_level': understanding_level,
            'evidence': evidence,
            'updated_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Concept {concept_id} status updated to {new_status.value} for {user_id} (understanding: {understanding_level:.2f})"

        return await self.store_memory(
            content=content,
            importance=0.8,
            **status_metadata
        )

    async def record_learning_attempt(
        self,
        user_id: str,
        concept_id: str,
        attempt_type: str,
        success_level: float,
        time_spent: Optional[float] = None,
        mistakes: Optional[List[str]] = None,
        insights: Optional[List[str]] = None,
        **metadata
    ) -> bool:
        """
        Record a learning attempt for a concept.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            attempt_type: Type of attempt (e.g., 'practice', 'assessment', 'explanation')
            success_level: Success level of the attempt (0.0 to 1.0)
            time_spent: Time spent in seconds
            mistakes: List of mistakes made
            insights: List of insights gained
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        attempt_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_attempt',
            'user_id': user_id,
            'concept_id': concept_id,
            'attempt_type': attempt_type,
            'success_level': success_level,
            'time_spent': time_spent,
            'mistakes': mistakes or [],
            'insights': insights or [],
            'attempted_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Learning attempt for {concept_id}: {attempt_type} with {success_level:.2f} success level"

        return await self.store_memory(
            content=content,
            importance=0.7,
            **attempt_metadata
        )

    async def get_next_concepts(
        self,
        user_id: str,
        domain: Optional[str] = None,
        limit: int = 5,
        difficulty_preference: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get next recommended concepts for learning.

        Args:
            user_id: User identifier
            domain: Optional domain filter
            limit: Maximum number of concepts to return
            difficulty_preference: Optional difficulty preference ('easy', 'medium', 'hard')

        Returns:
            List of recommended concepts with metadata
        """
        # Get current learning graph state
        learning_graph = await self._get_user_learning_graph(user_id, domain)
        if not learning_graph:
            return []

        # Get completed and in-progress concepts
        completed_concepts = await self._get_completed_concepts(user_id, domain)
        in_progress_concepts = await self._get_in_progress_concepts(user_id, domain)

        # Find concepts that are ready to learn (prerequisites met)
        available_concepts = []

        # This would typically query a knowledge graph to find concepts
        # where all prerequisites are in completed_concepts
        # For now, implementing a simplified version

        # Get concept attempts to determine readiness
        concept_attempts = await self._get_concept_attempts(user_id, domain)

        # Simple recommendation logic based on success patterns
        recommendations = []

        # Add concepts that have been attempted but not mastered
        for concept_id, attempts in concept_attempts.items():
            if concept_id not in completed_concepts and concept_id not in in_progress_concepts:
                avg_success = sum(attempt['success_level'] for attempt in attempts) / len(attempts)
                recommendations.append({
                    'concept_id': concept_id,
                    'recommendation_type': 'retry',
                    'confidence': avg_success,
                    'reason': f"Previously attempted with {avg_success:.2f} average success",
                    'estimated_difficulty': self._estimate_difficulty(attempts)
                })

        return recommendations[:limit]

    async def get_learning_path(
        self,
        user_id: str,
        target_concept: str,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get optimal learning path to reach a target concept.

        Args:
            user_id: User identifier
            target_concept: Target concept to reach
            domain: Optional domain filter

        Returns:
            List of concepts in optimal learning order
        """
        # Get current status
        completed_concepts = await self._get_completed_concepts(user_id, domain)
        current_understanding = await self._get_concept_understanding(user_id, target_concept)

        # If already completed, return empty path
        if target_concept in completed_concepts:
            return []

        # Build learning path (simplified implementation)
        path = []

        # Get prerequisite concepts for target
        prerequisites = await self._get_prerequisites(target_concept, domain)

        for prereq in prerequisites:
            if prereq not in completed_concepts:
                path.append({
                    'concept_id': prereq,
                    'step_type': 'prerequisite',
                    'estimated_time': await self._estimate_learning_time(user_id, prereq),
                    'difficulty': await self._get_concept_difficulty(prereq)
                })

        # Add target concept
        path.append({
            'concept_id': target_concept,
            'step_type': 'target',
            'estimated_time': await self._estimate_learning_time(user_id, target_concept),
            'difficulty': await self._get_concept_difficulty(target_concept)
        })

        return path

    async def mark_concept_learned(
        self,
        user_id: str,
        concept_id: str,
        mastery_level: float,
        evidence: str = "Learning session completed successfully"
    ) -> bool:
        """
        Mark a concept as learned/mastered.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            mastery_level: Level of mastery achieved (0.0 to 1.0)
            evidence: Evidence for the mastery

        Returns:
            True if successful, False otherwise
        """
        status = ConceptStatus.MASTERED if mastery_level >= 0.8 else ConceptStatus.PRACTICED

        return await self.update_concept_status(
            user_id=user_id,
            concept_id=concept_id,
            new_status=status,
            understanding_level=mastery_level,
            evidence=evidence
        )

    async def get_learning_analytics(
        self,
        user_id: str,
        domain: Optional[str] = None,
        time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get learning analytics for a user.

        Args:
            user_id: User identifier
            domain: Optional domain filter
            time_period: Optional time period filter

        Returns:
            Dictionary containing learning analytics
        """
        # Get learning attempts
        attempts = await self._get_concept_attempts(user_id, domain, time_period)

        # Calculate analytics
        total_attempts = sum(len(concept_attempts) for concept_attempts in attempts.values())
        concepts_attempted = len(attempts)

        # Calculate success rates
        all_success_levels = []
        for concept_attempts in attempts.values():
            all_success_levels.extend([attempt['success_level'] for attempt in concept_attempts])

        avg_success_rate = sum(all_success_levels) / len(all_success_levels) if all_success_levels else 0

        # Learning velocity (concepts per unit time)
        completed_concepts = await self._get_completed_concepts(user_id, domain)

        # Time spent analysis
        total_time_spent = 0
        for concept_attempts in attempts.values():
            for attempt in concept_attempts:
                if attempt.get('time_spent'):
                    total_time_spent += attempt['time_spent']

        return {
            'user_id': user_id,
            'domain': domain,
            'total_attempts': total_attempts,
            'concepts_attempted': concepts_attempted,
            'concepts_completed': len(completed_concepts),
            'average_success_rate': avg_success_rate,
            'total_time_spent_seconds': total_time_spent,
            'learning_velocity': len(completed_concepts) / max(1, total_time_spent / 3600),  # concepts per hour
            'most_challenging_concepts': await self._get_most_challenging_concepts(user_id, attempts),
            'breakthrough_concepts': await self._get_breakthrough_concepts(user_id, attempts),
            'analysis_timestamp': datetime.now().isoformat()
        }

    async def can_learn_concept(
        self,
        user_id: str,
        concept_id: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a user is ready to learn a specific concept.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            domain: Optional domain filter

        Returns:
            Dictionary with readiness information
        """
        # Get prerequisites
        prerequisites = await self._get_prerequisites(concept_id, domain)
        completed_concepts = await self._get_completed_concepts(user_id, domain)

        # Check prerequisite completion
        missing_prerequisites = [prereq for prereq in prerequisites if prereq not in completed_concepts]

        # Get current understanding level
        current_understanding = await self._get_concept_understanding(user_id, concept_id)

        # Determine readiness
        is_ready = len(missing_prerequisites) == 0
        readiness_score = 1.0 if is_ready else (len(prerequisites) - len(missing_prerequisites)) / len(prerequisites) if prerequisites else 1.0

        return {
            'concept_id': concept_id,
            'is_ready': is_ready,
            'readiness_score': readiness_score,
            'current_understanding': current_understanding,
            'prerequisites_total': len(prerequisites),
            'prerequisites_completed': len(prerequisites) - len(missing_prerequisites),
            'missing_prerequisites': missing_prerequisites,
            'estimated_difficulty': await self._get_concept_difficulty(concept_id),
            'recommended_prerequisite_order': missing_prerequisites  # In order of recommendation
        }

    # Helper methods
    async def _get_user_learning_graph(self, user_id: str, domain: Optional[str] = None) -> Optional[MemoryEntry]:
        """Get user's learning graph entry."""
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_graph',
            'user_id': user_id
        }

        if domain:
            filters['domain'] = domain

        graphs = await self.search_memory(
            query=f"user:{user_id} learning_graph",
            limit=1,
            filters=filters
        )

        return graphs[0] if graphs else None

    async def _get_completed_concepts(self, user_id: str, domain: Optional[str] = None) -> List[str]:
        """Get list of completed concepts for a user."""
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'concept_status',
            'user_id': user_id,
            'status': ConceptStatus.MASTERED.value
        }

        if domain:
            filters['domain'] = domain

        statuses = await self.search_memory(
            query=f"user:{user_id} concept_status mastered",
            limit=1000,
            filters=filters
        )

        return [status.metadata.get('concept_id') for status in statuses]

    async def _get_in_progress_concepts(self, user_id: str, domain: Optional[str] = None) -> List[str]:
        """Get list of concepts currently in progress."""
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'concept_status',
            'user_id': user_id,
            'status': ConceptStatus.IN_PROGRESS.value
        }

        if domain:
            filters['domain'] = domain

        statuses = await self.search_memory(
            query=f"user:{user_id} concept_status in_progress",
            limit=1000,
            filters=filters
        )

        return [status.metadata.get('concept_id') for status in statuses]

    async def _get_concept_attempts(
        self,
        user_id: str,
        domain: Optional[str] = None,
        time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, List[Dict]]:
        """Get learning attempts grouped by concept."""
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_attempt',
            'user_id': user_id
        }

        if domain:
            filters['domain'] = domain

        attempts = await self.search_memory(
            query=f"user:{user_id} learning_attempt",
            limit=10000,
            filters=filters
        )

        # Group by concept
        concept_attempts = {}
        for attempt in attempts:
            concept_id = attempt.metadata.get('concept_id')
            if concept_id not in concept_attempts:
                concept_attempts[concept_id] = []

            # Filter by time period if specified
            if time_period:
                attempt_time = datetime.fromisoformat(attempt.metadata.get('attempted_at'))
                if not (time_period[0] <= attempt_time <= time_period[1]):
                    continue

            concept_attempts[concept_id].append({
                'success_level': attempt.metadata.get('success_level', 0.0),
                'attempt_type': attempt.metadata.get('attempt_type'),
                'time_spent': attempt.metadata.get('time_spent'),
                'attempted_at': attempt.metadata.get('attempted_at')
            })

        return concept_attempts

    async def _get_concept_understanding(self, user_id: str, concept_id: str) -> float:
        """Get current understanding level for a concept."""
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'concept_status',
            'user_id': user_id,
            'concept_id': concept_id
        }

        statuses = await self.search_memory(
            query=f"user:{user_id} concept:{concept_id}",
            limit=1,
            filters=filters
        )

        if statuses:
            return statuses[0].metadata.get('understanding_level', 0.0)
        return 0.0

    async def _get_prerequisites(self, concept_id: str, domain: Optional[str] = None) -> List[str]:
        """Get prerequisites for a concept. This would typically query the knowledge graph."""
        # Simplified implementation - in practice, this would query the knowledge graph
        # For now, return empty list
        return []

    async def _estimate_learning_time(self, user_id: str, concept_id: str) -> float:
        """Estimate learning time for a concept based on user's learning patterns."""
        # Get historical learning times for similar concepts
        attempts = await self._get_concept_attempts(user_id)

        if not attempts:
            return 3600.0  # Default 1 hour

        # Calculate average time from all attempts
        total_time = 0
        total_attempts = 0

        for concept_attempts in attempts.values():
            for attempt in concept_attempts:
                if attempt.get('time_spent'):
                    total_time += attempt['time_spent']
                    total_attempts += 1

        if total_attempts > 0:
            return total_time / total_attempts

        return 3600.0  # Default 1 hour

    async def _get_concept_difficulty(self, concept_id: str) -> float:
        """Get difficulty level of a concept. This would typically come from the knowledge graph."""
        # Simplified implementation
        return 0.5  # Medium difficulty

    async def _estimate_difficulty(self, attempts: List[Dict]) -> float:
        """Estimate difficulty based on attempt patterns."""
        if not attempts:
            return 0.5

        # Lower average success indicates higher difficulty
        avg_success = sum(attempt['success_level'] for attempt in attempts) / len(attempts)
        return 1.0 - avg_success

    async def _get_most_challenging_concepts(self, user_id: str, attempts: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """Get concepts that are most challenging for the user."""
        challenging = []

        for concept_id, concept_attempts in attempts.items():
            if len(concept_attempts) >= 3:  # Only consider concepts with multiple attempts
                avg_success = sum(attempt['success_level'] for attempt in concept_attempts) / len(concept_attempts)
                if avg_success < 0.6:  # Below 60% success rate
                    challenging.append({
                        'concept_id': concept_id,
                        'average_success': avg_success,
                        'attempt_count': len(concept_attempts)
                    })

        # Sort by lowest success rate
        challenging.sort(key=lambda x: x['average_success'])
        return challenging[:5]

    async def _get_breakthrough_concepts(self, user_id: str, attempts: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """Get concepts where user had breakthroughs (improvement over time)."""
        breakthroughs = []

        for concept_id, concept_attempts in attempts.items():
            if len(concept_attempts) >= 3:
                # Sort attempts by time
                sorted_attempts = sorted(concept_attempts, key=lambda x: x['attempted_at'])

                # Check for improvement trend
                first_half_avg = sum(attempt['success_level'] for attempt in sorted_attempts[:len(sorted_attempts)//2]) / (len(sorted_attempts)//2)
                second_half_avg = sum(attempt['success_level'] for attempt in sorted_attempts[len(sorted_attempts)//2:]) / (len(sorted_attempts) - len(sorted_attempts)//2)

                improvement = second_half_avg - first_half_avg
                if improvement > 0.3:  # Significant improvement
                    breakthroughs.append({
                        'concept_id': concept_id,
                        'improvement': improvement,
                        'final_success_rate': second_half_avg
                    })

        # Sort by largest improvement
        breakthroughs.sort(key=lambda x: x['improvement'], reverse=True)
        return breakthroughs[:5]