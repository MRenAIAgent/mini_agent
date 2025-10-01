"""Episodic memory manager for learning experiences and specific events."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryEntry


class EpisodicMemoryManager(CoreMemoryManager):
    """
    Episodic memory manager that extends CoreMemoryManager for learning experiences.

    Handles storage and retrieval of specific learning events, experiences,
    and contextual episodes in the learning process.
    """

    def __init__(self, **kwargs):
        """Initialize episodic memory manager."""
        super().__init__(**kwargs)
        self.memory_type = "episodic"

    async def store_learning_event(
        self,
        event_type: str,
        content: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        importance: float = 0.7,
        **metadata
    ) -> bool:
        """
        Store a specific learning event/experience.

        Args:
            event_type: Type of learning event (e.g., 'problem_solved', 'concept_learned', 'mistake_made')
            content: Description of the learning event
            user_id: User identifier
            session_id: Learning session identifier
            context: Additional context about the learning state
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        episodic_metadata = {
            'memory_type': self.memory_type,
            'event_type': event_type,
            'user_id': user_id,
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            **metadata
        }

        return await self.store_memory(
            content=content,
            importance=importance,
            session_id=session_id,
            **episodic_metadata
        )

    async def store_problem_attempt(
        self,
        problem_id: str,
        user_id: str,
        session_id: str,
        attempt_content: str,
        was_successful: bool,
        solution_steps: Optional[List[str]] = None,
        errors_made: Optional[List[str]] = None,
        time_spent: Optional[float] = None,
        difficulty_level: Optional[str] = None,
        **metadata
    ) -> bool:
        """
        Store a specific problem-solving attempt.

        Args:
            problem_id: Identifier of the problem attempted
            user_id: User identifier
            session_id: Learning session identifier
            attempt_content: The actual attempt/solution provided
            was_successful: Whether the attempt was successful
            solution_steps: Steps taken in the solution process
            errors_made: List of errors identified in the attempt
            time_spent: Time spent on the problem (in seconds)
            difficulty_level: Perceived difficulty level
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        context = {
            'problem_id': problem_id,
            'was_successful': was_successful,
            'solution_steps': solution_steps or [],
            'errors_made': errors_made or [],
            'time_spent': time_spent,
            'difficulty_level': difficulty_level
        }

        return await self.store_learning_event(
            event_type='problem_attempt',
            content=attempt_content,
            user_id=user_id,
            session_id=session_id,
            context=context,
            importance=0.8 if was_successful else 0.6,
            **metadata
        )

    async def store_concept_interaction(
        self,
        concept_id: str,
        user_id: str,
        session_id: str,
        interaction_type: str,
        interaction_content: str,
        understanding_level: Optional[float] = None,
        prerequisites_met: Optional[List[str]] = None,
        **metadata
    ) -> bool:
        """
        Store an interaction with a specific concept.

        Args:
            concept_id: Identifier of the concept
            user_id: User identifier
            session_id: Learning session identifier
            interaction_type: Type of interaction (e.g., 'explanation_request', 'practice', 'review')
            interaction_content: Description of the interaction
            understanding_level: Assessed understanding level (0.0 to 1.0)
            prerequisites_met: List of prerequisite concepts that were met
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        context = {
            'concept_id': concept_id,
            'interaction_type': interaction_type,
            'understanding_level': understanding_level,
            'prerequisites_met': prerequisites_met or []
        }

        importance = 0.7
        if understanding_level is not None:
            # Higher importance for breakthrough moments or struggle points
            if understanding_level > 0.8 or understanding_level < 0.3:
                importance = 0.9

        return await self.store_learning_event(
            event_type='concept_interaction',
            content=interaction_content,
            user_id=user_id,
            session_id=session_id,
            context=context,
            importance=importance,
            **metadata
        )

    async def get_learning_episodes(
        self,
        user_id: str,
        event_type: Optional[str] = None,
        time_range: Optional[tuple] = None,
        limit: int = 50
    ) -> List[MemoryEntry]:
        """
        Retrieve learning episodes for a user.

        Args:
            user_id: User identifier
            event_type: Optional filter by event type
            time_range: Optional tuple of (start_time, end_time) as datetime objects
            limit: Maximum number of episodes to return

        Returns:
            List of episodic memory entries
        """
        filters = {
            'memory_type': self.memory_type,
            'user_id': user_id
        }

        if event_type:
            filters['event_type'] = event_type

        # For time range filtering, we'll need to implement this in the search logic
        # For now, get all and filter in memory
        episodes = await self.search_memory(
            query=f"user:{user_id}",
            limit=limit * 2,
            filters=filters
        )

        # Apply time range filter if specified
        if time_range:
            start_time, end_time = time_range
            filtered_episodes = []
            for episode in episodes:
                episode_time = datetime.fromisoformat(episode.metadata.get('timestamp', ''))
                if start_time <= episode_time <= end_time:
                    filtered_episodes.append(episode)
            episodes = filtered_episodes

        return episodes[:limit]

    async def get_problem_history(
        self,
        user_id: str,
        problem_id: Optional[str] = None,
        successful_only: bool = False,
        limit: int = 20
    ) -> List[MemoryEntry]:
        """
        Get problem-solving history for a user.

        Args:
            user_id: User identifier
            problem_id: Optional specific problem ID
            successful_only: Whether to return only successful attempts
            limit: Maximum number of attempts to return

        Returns:
            List of problem attempt episodes
        """
        filters = {
            'memory_type': self.memory_type,
            'user_id': user_id,
            'event_type': 'problem_attempt'
        }

        query = f"user:{user_id} problem_attempt"
        if problem_id:
            query += f" problem:{problem_id}"

        attempts = await self.search_memory(
            query=query,
            limit=limit * 2,
            filters=filters
        )

        # Filter by success if requested
        if successful_only:
            attempts = [
                attempt for attempt in attempts
                if attempt.metadata.get('context', {}).get('was_successful', False)
            ]

        return attempts[:limit]

    async def get_concept_learning_journey(
        self,
        user_id: str,
        concept_id: str,
        limit: int = 30
    ) -> List[MemoryEntry]:
        """
        Get the learning journey for a specific concept.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            limit: Maximum number of interactions to return

        Returns:
            List of concept interaction episodes, chronologically ordered
        """
        filters = {
            'memory_type': self.memory_type,
            'user_id': user_id,
            'event_type': 'concept_interaction'
        }

        query = f"user:{user_id} concept:{concept_id}"

        interactions = await self.search_memory(
            query=query,
            limit=limit,
            filters=filters
        )

        # Sort by timestamp to show learning progression
        interactions.sort(key=lambda x: x.metadata.get('timestamp', ''))

        return interactions

    async def analyze_learning_patterns(
        self,
        user_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze learning patterns from episodic memory.

        Args:
            user_id: User identifier
            days_back: Number of days to analyze

        Returns:
            Dictionary containing learning pattern analysis
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        episodes = await self.get_learning_episodes(
            user_id=user_id,
            time_range=(start_time, end_time),
            limit=1000
        )

        # Analyze patterns
        event_types = {}
        daily_activity = {}
        success_rates = {}
        concept_focus = {}

        for episode in episodes:
            # Event type distribution
            event_type = episode.metadata.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1

            # Daily activity
            timestamp = episode.metadata.get('timestamp', '')
            if timestamp:
                date = datetime.fromisoformat(timestamp).date()
                daily_activity[str(date)] = daily_activity.get(str(date), 0) + 1

            # Success rates for problem attempts
            if event_type == 'problem_attempt':
                was_successful = episode.metadata.get('context', {}).get('was_successful', False)
                if 'problem_attempts' not in success_rates:
                    success_rates['problem_attempts'] = {'total': 0, 'successful': 0}
                success_rates['problem_attempts']['total'] += 1
                if was_successful:
                    success_rates['problem_attempts']['successful'] += 1

            # Concept focus
            if event_type == 'concept_interaction':
                concept_id = episode.metadata.get('context', {}).get('concept_id')
                if concept_id:
                    concept_focus[concept_id] = concept_focus.get(concept_id, 0) + 1

        # Calculate success rate percentage
        if 'problem_attempts' in success_rates:
            total = success_rates['problem_attempts']['total']
            successful = success_rates['problem_attempts']['successful']
            success_rates['problem_attempts']['rate'] = successful / total if total > 0 else 0

        return {
            'event_type_distribution': event_types,
            'daily_activity': daily_activity,
            'success_rates': success_rates,
            'concept_focus_areas': concept_focus,
            'total_episodes': len(episodes),
            'analysis_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days_back
            }
        }