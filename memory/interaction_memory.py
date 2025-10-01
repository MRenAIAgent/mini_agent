"""Interaction memory manager for conversational context and dialogue history."""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from enum import Enum
from dataclasses import dataclass

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryEntry


class InteractionType(Enum):
    """Types of interactions tracked in memory."""
    QUESTION = "question"
    EXPLANATION = "explanation"
    PRACTICE = "practice"
    FEEDBACK = "feedback"
    ASSESSMENT = "assessment"
    CLARIFICATION = "clarification"
    HINT = "hint"
    ERROR_CORRECTION = "error_correction"


@dataclass
class InteractionRecord:
    """Record of a single interaction between user and agent."""
    user_id: str
    session_id: str
    user_input: str
    agent_response: Optional[str] = None
    interaction_type: InteractionType = InteractionType.QUESTION
    timestamp: datetime = None
    context: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    understanding_indicators: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.context is None:
            self.context = {}


class InteractionMemoryManager(CoreMemoryManager):
    """
    Interaction memory manager that extends CoreMemoryManager for dialogue context.

    Handles storage and retrieval of conversation history, interaction patterns,
    contextual information, and dialogue state management.
    """

    def __init__(self, **kwargs):
        """Initialize interaction memory manager."""
        super().__init__(**kwargs)
        self.memory_type = "interaction"

    async def store_interaction_turn(
        self,
        user_id: str,
        session_id: str,
        turn_number: int,
        user_input: str,
        agent_response: str,
        interaction_type: InteractionType,
        context: Optional[Dict[str, Any]] = None,
        sentiment: Optional[str] = None,
        understanding_indicators: Optional[Dict[str, float]] = None,
        importance: float = 0.6,
        **metadata
    ) -> bool:
        """
        Store a complete interaction turn (user input + agent response).

        Args:
            user_id: User identifier
            session_id: Session identifier
            turn_number: Sequential turn number in the session
            user_input: User's input/message
            agent_response: Agent's response
            interaction_type: Type of interaction
            context: Additional context about the interaction
            sentiment: Detected sentiment of the interaction
            understanding_indicators: Indicators of user understanding
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        interaction_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'interaction_turn',
            'user_id': user_id,
            'turn_number': turn_number,
            'interaction_type': interaction_type.value,
            'context': context or {},
            'sentiment': sentiment,
            'understanding_indicators': understanding_indicators or {},
            'timestamp': datetime.now().isoformat(),
            **metadata
        }

        # Create comprehensive content
        content = f"Turn {turn_number} ({interaction_type.value}):\nUser: {user_input}\nAgent: {agent_response}"
        if sentiment:
            content += f"\nSentiment: {sentiment}"

        return await self.store_memory(
            content=content,
            importance=importance,
            session_id=session_id,
            **interaction_metadata
        )

    async def store_dialogue_state(
        self,
        user_id: str,
        session_id: str,
        current_topic: Optional[str] = None,
        active_concepts: Optional[List[str]] = None,
        user_goals: Optional[List[str]] = None,
        context_stack: Optional[List[Dict[str, Any]]] = None,
        dialogue_phase: str = "active",
        **metadata
    ) -> bool:
        """
        Store current dialogue state information.

        Args:
            user_id: User identifier
            session_id: Session identifier
            current_topic: Current topic being discussed
            active_concepts: List of concepts currently in focus
            user_goals: List of user goals for this session
            context_stack: Stack of context information
            dialogue_phase: Current phase of dialogue (e.g., 'opening', 'active', 'closing')
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        state_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'dialogue_state',
            'user_id': user_id,
            'session_id': session_id,
            'current_topic': current_topic,
            'active_concepts': active_concepts or [],
            'user_goals': user_goals or [],
            'context_stack': context_stack or [],
            'dialogue_phase': dialogue_phase,
            'state_timestamp': datetime.now().isoformat(),
            **metadata
        }

        content = f"Dialogue state for session {session_id}: topic={current_topic}, phase={dialogue_phase}"
        if active_concepts:
            content += f", concepts=[{', '.join(active_concepts)}]"

        return await self.store_memory(
            content=content,
            importance=0.7,
            session_id=session_id,
            **state_metadata
        )

    async def store_context_reference(
        self,
        user_id: str,
        session_id: str,
        reference_type: str,
        reference_target: str,
        reference_context: str,
        turn_number: Optional[int] = None,
        **metadata
    ) -> bool:
        """
        Store contextual references made during conversation.

        Args:
            user_id: User identifier
            session_id: Session identifier
            reference_type: Type of reference (e.g., 'anaphora', 'topic_shift', 'callback')
            reference_target: What is being referenced
            reference_context: Context of the reference
            turn_number: Turn where reference was made
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        reference_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'context_reference',
            'user_id': user_id,
            'session_id': session_id,
            'reference_type': reference_type,
            'reference_target': reference_target,
            'turn_number': turn_number,
            'reference_timestamp': datetime.now().isoformat(),
            **metadata
        }

        content = f"Context reference: {reference_type} -> {reference_target} ({reference_context})"

        return await self.store_memory(
            content=content,
            importance=0.5,
            session_id=session_id,
            **reference_metadata
        )

    async def store_interaction_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_description: str,
        frequency: int,
        examples: Optional[List[str]] = None,
        confidence: float = 0.8,
        time_period: Optional[str] = None,
        **metadata
    ) -> bool:
        """
        Store identified interaction patterns for a user.

        Args:
            user_id: User identifier
            pattern_type: Type of pattern (e.g., 'question_style', 'help_seeking', 'error_recovery')
            pattern_description: Description of the pattern
            frequency: How often this pattern occurs
            examples: Example instances of the pattern
            confidence: Confidence in the pattern identification
            time_period: Time period over which pattern was observed
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        pattern_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'interaction_pattern',
            'user_id': user_id,
            'pattern_type': pattern_type,
            'frequency': frequency,
            'examples': examples or [],
            'confidence': confidence,
            'time_period': time_period,
            'identified_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Interaction pattern for {user_id}: {pattern_type} - {pattern_description} (frequency: {frequency})"

        return await self.store_memory(
            content=content,
            importance=0.7,
            **pattern_metadata
        )

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of turns to return
            include_context: Whether to include contextual information

        Returns:
            List of interaction turns with metadata
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'interaction_turn',
            'session_id': session_id
        }

        turns = await self.search_memory(
            query=f"session:{session_id}",
            limit=limit,
            filters=filters
        )

        # Sort by turn number
        turns.sort(key=lambda x: x.metadata.get('turn_number', 0))

        history = []
        for turn in turns:
            turn_data = {
                'turn_number': turn.metadata.get('turn_number'),
                'interaction_type': turn.metadata.get('interaction_type'),
                'content': turn.content,
                'timestamp': turn.metadata.get('timestamp'),
                'sentiment': turn.metadata.get('sentiment'),
                'understanding_indicators': turn.metadata.get('understanding_indicators', {})
            }

            if include_context:
                turn_data['context'] = turn.metadata.get('context', {})

            history.append(turn_data)

        return history

    async def get_recent_context(
        self,
        session_id: str,
        turns_back: int = 5
    ) -> Dict[str, Any]:
        """
        Get recent conversation context for a session.

        Args:
            session_id: Session identifier
            turns_back: Number of recent turns to include

        Returns:
            Dictionary containing recent context
        """
        recent_turns = await self.get_session_history(
            session_id=session_id,
            limit=turns_back,
            include_context=True
        )

        if not recent_turns:
            return {}

        # Extract current state
        latest_turn = recent_turns[-1] if recent_turns else {}
        current_topic = None
        active_concepts = []

        # Look for latest dialogue state
        state_filters = {
            'memory_type': self.memory_type,
            'entry_type': 'dialogue_state',
            'session_id': session_id
        }

        states = await self.search_memory(
            query=f"session:{session_id} dialogue_state",
            limit=1,
            filters=state_filters
        )

        if states:
            latest_state = states[0]
            current_topic = latest_state.metadata.get('current_topic')
            active_concepts = latest_state.metadata.get('active_concepts', [])

        return {
            'session_id': session_id,
            'recent_turns': recent_turns,
            'current_topic': current_topic,
            'active_concepts': active_concepts,
            'last_interaction_type': latest_turn.get('interaction_type'),
            'last_sentiment': latest_turn.get('sentiment'),
            'context_timestamp': datetime.now().isoformat()
        }

    async def get_user_interaction_patterns(
        self,
        user_id: str,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get interaction patterns for a user.

        Args:
            user_id: User identifier
            pattern_type: Optional filter by pattern type
            min_confidence: Minimum confidence threshold

        Returns:
            List of interaction patterns
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'interaction_pattern',
            'user_id': user_id
        }

        if pattern_type:
            filters['pattern_type'] = pattern_type

        patterns = await self.search_memory(
            query=f"user:{user_id} interaction_pattern",
            limit=100,
            filters=filters
        )

        # Filter by confidence and return structured data
        filtered_patterns = []
        for pattern in patterns:
            confidence = pattern.metadata.get('confidence', 0.0)
            if confidence >= min_confidence:
                filtered_patterns.append({
                    'pattern_type': pattern.metadata.get('pattern_type'),
                    'description': pattern.content,
                    'frequency': pattern.metadata.get('frequency'),
                    'confidence': confidence,
                    'examples': pattern.metadata.get('examples', []),
                    'time_period': pattern.metadata.get('time_period'),
                    'identified_at': pattern.metadata.get('identified_at')
                })

        return filtered_patterns

    async def analyze_interaction_quality(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the quality of interactions in a session.

        Args:
            session_id: Session identifier
            user_id: Optional user identifier for cross-session analysis

        Returns:
            Dictionary containing interaction quality metrics
        """
        history = await self.get_session_history(session_id, limit=1000)

        if not history:
            return {'error': 'No interaction history found'}

        # Analyze various quality metrics
        total_turns = len(history)
        interaction_types = {}
        sentiments = {}
        understanding_progression = []

        for turn in history:
            # Interaction type distribution
            int_type = turn.get('interaction_type', 'unknown')
            interaction_types[int_type] = interaction_types.get(int_type, 0) + 1

            # Sentiment distribution
            sentiment = turn.get('sentiment')
            if sentiment:
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

            # Understanding indicators over time
            understanding = turn.get('understanding_indicators', {})
            if understanding:
                avg_understanding = sum(understanding.values()) / len(understanding) if understanding else 0
                understanding_progression.append(avg_understanding)

        # Calculate quality metrics
        quality_metrics = {
            'total_turns': total_turns,
            'interaction_type_distribution': interaction_types,
            'sentiment_distribution': sentiments,
            'understanding_progression': understanding_progression,
            'average_understanding': sum(understanding_progression) / len(understanding_progression) if understanding_progression else 0,
            'interaction_diversity': len(interaction_types) / max(total_turns, 1),
            'session_duration_turns': total_turns
        }

        # Add temporal analysis
        if len(understanding_progression) > 1:
            understanding_trend = understanding_progression[-1] - understanding_progression[0]
            quality_metrics['understanding_trend'] = understanding_trend

        return quality_metrics

    async def get_cross_session_context(
        self,
        user_id: str,
        current_session_id: str,
        days_back: int = 7,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get relevant context from previous sessions for better continuity.

        Args:
            user_id: User identifier
            current_session_id: Current session identifier
            days_back: Number of days to look back
            limit: Maximum number of context items to return

        Returns:
            Dictionary containing cross-session context
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        # Get recent interactions from other sessions
        filters = {
            'memory_type': self.memory_type,
            'user_id': user_id
        }

        recent_interactions = await self.search_memory(
            query=f"user:{user_id}",
            limit=limit * 2,
            filters=filters
        )

        # Filter by date and exclude current session
        relevant_context = []
        session_topics = {}

        for interaction in recent_interactions:
            timestamp_str = interaction.metadata.get('timestamp')
            session_id = interaction.metadata.get('session_id')

            if session_id == current_session_id:
                continue

            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
                if start_time <= timestamp <= end_time:
                    relevant_context.append(interaction)

                    # Track topics by session
                    if session_id not in session_topics:
                        session_topics[session_id] = set()

                    # Extract topics from dialogue states
                    if interaction.metadata.get('entry_type') == 'dialogue_state':
                        topic = interaction.metadata.get('current_topic')
                        if topic:
                            session_topics[session_id].add(topic)

        # Organize context by relevance
        return {
            'user_id': user_id,
            'context_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days_back': days_back
            },
            'recent_interactions': relevant_context[:limit],
            'session_topics': {sid: list(topics) for sid, topics in session_topics.items()},
            'total_relevant_interactions': len(relevant_context)
        }

    async def update_dialogue_state(
        self,
        session_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update the current dialogue state for a session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            updates: Dictionary of state updates

        Returns:
            True if successful, False otherwise
        """
        # Get current state first
        current_context = await self.get_recent_context(session_id)

        # Merge updates with current state
        new_state = {
            'current_topic': updates.get('current_topic', current_context.get('current_topic')),
            'active_concepts': updates.get('active_concepts', current_context.get('active_concepts', [])),
            'user_goals': updates.get('user_goals', []),
            'dialogue_phase': updates.get('dialogue_phase', 'active')
        }

        return await self.store_dialogue_state(
            user_id=user_id,
            session_id=session_id,
            **new_state
        )