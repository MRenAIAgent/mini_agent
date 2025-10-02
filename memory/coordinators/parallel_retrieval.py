"""Parallel retrieval engine for multi-memory-type retrieval."""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass
import asyncio

from ..memory_store import MemoryEntry

if TYPE_CHECKING:
    from ..learning_memory_system import LearningMemorySystem


@dataclass
class ParallelRetrievalResult:
    """Result from parallel memory retrieval across all memory types."""
    episodic_memories: List[MemoryEntry]
    semantic_memories: List[MemoryEntry]
    profile_memories: List[MemoryEntry]
    interaction_memories: List[MemoryEntry]
    graph_memories: List[MemoryEntry]
    retrieval_time_ms: float
    retrieval_metadata: Dict[str, Any]
    errors: Dict[str, str]  # Track any retrieval errors


class ParallelRetrievalEngine:
    """Retrieves memories from multiple types in parallel using asyncio.gather.

    This engine coordinates simultaneous retrieval from all five memory types:
    1. Episodic - Learning episodes and experiences
    2. Semantic - Concepts, facts, and knowledge
    3. Profile - User preferences and characteristics
    4. Interaction - Conversation history
    5. Graph - Learning graph and concept relationships
    """

    def __init__(self, learning_system: 'LearningMemorySystem'):
        """Initialize the parallel retrieval engine.

        Args:
            learning_system: Reference to the learning memory system
        """
        self.system = learning_system

    async def retrieve_all(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Dict[str, Any],
        limits: Optional[Dict[str, int]] = None
    ) -> ParallelRetrievalResult:
        """Retrieve from all memory types in parallel.

        Uses asyncio.gather to retrieve from all memory types simultaneously,
        significantly reducing total retrieval time compared to sequential retrieval.

        Args:
            query: Search query string
            user_id: User identifier
            session_id: Session identifier
            context: Context dictionary with domain, interaction type, etc.
            limits: Optional limits for each memory type

        Returns:
            ParallelRetrievalResult with all retrieved memories
        """
        start_time = datetime.now()

        # Set default limits if not provided
        if limits is None:
            limits = {
                'episodic': 10,
                'semantic': 10,
                'profile': 5,
                'interaction': 10,
                'graph': 5
            }

        # Execute all retrievals in parallel using asyncio.gather
        # return_exceptions=True ensures one failure doesn't break all retrievals
        results = await asyncio.gather(
            self._retrieve_episodic(query, user_id, context, limits['episodic']),
            self._retrieve_semantic(query, user_id, context, limits['semantic']),
            self._retrieve_profile(user_id, context, limits['profile']),
            self._retrieve_interaction(session_id, context, limits['interaction']),
            self._retrieve_graph(user_id, context, limits['graph']),
            return_exceptions=True
        )

        # Unpack results and handle exceptions
        errors = {}

        episodic = results[0] if not isinstance(results[0], Exception) else []
        if isinstance(results[0], Exception):
            errors['episodic'] = str(results[0])

        semantic = results[1] if not isinstance(results[1], Exception) else []
        if isinstance(results[1], Exception):
            errors['semantic'] = str(results[1])

        profile = results[2] if not isinstance(results[2], Exception) else []
        if isinstance(results[2], Exception):
            errors['profile'] = str(results[2])

        interaction = results[3] if not isinstance(results[3], Exception) else []
        if isinstance(results[3], Exception):
            errors['interaction'] = str(results[3])

        graph = results[4] if not isinstance(results[4], Exception) else []
        if isinstance(results[4], Exception):
            errors['graph'] = str(results[4])

        # Calculate total retrieval time
        retrieval_time = (datetime.now() - start_time).total_seconds() * 1000

        return ParallelRetrievalResult(
            episodic_memories=episodic,
            semantic_memories=semantic,
            profile_memories=profile,
            interaction_memories=interaction,
            graph_memories=graph,
            retrieval_time_ms=retrieval_time,
            retrieval_metadata={
                'query': query,
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'limits': limits
            },
            errors=errors
        )

    async def _retrieve_episodic(
        self, query: str, user_id: str, context: Dict[str, Any], limit: int
    ) -> List[MemoryEntry]:
        """Retrieve episodic memories.

        Args:
            query: Search query
            user_id: User identifier
            context: Context dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of episodic memory entries
        """
        # Get recent learning episodes
        try:
            episodes = await self.system.get_learning_episodes(
                user_id=user_id,
                limit=limit
            )
            return episodes
        except Exception as e:
            # Re-raise to be caught by gather
            raise

    async def _retrieve_semantic(
        self, query: str, user_id: str, context: Dict[str, Any], limit: int
    ) -> List[MemoryEntry]:
        """Retrieve semantic memories (concepts, facts, knowledge).

        Args:
            query: Search query
            user_id: User identifier
            context: Context dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of semantic memory entries
        """
        domain = context.get('domain')

        try:
            # Search for relevant concepts
            concepts = await self.system.search_concepts(
                query=query,
                domain=domain,
                user_id=user_id,
                limit=limit
            )
            return concepts
        except Exception as e:
            raise

    async def _retrieve_profile(
        self, user_id: str, context: Dict[str, Any], limit: int
    ) -> List[MemoryEntry]:
        """Retrieve profile memories (preferences, learning style, etc.).

        Args:
            user_id: User identifier
            context: Context dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of profile memory entries
        """
        try:
            # Get user preferences as memory entries
            preferences = await self.system.get_user_preferences(user_id)

            # Get learning style
            style = await self.system.get_learning_style(user_id)

            # Get performance patterns
            patterns = await self.system.get_performance_patterns(
                user_id, limit=limit
            )

            # Convert these to memory entries
            # For now, return empty list - in full implementation,
            # would convert these structured data to MemoryEntry objects
            return []

        except Exception as e:
            raise

    async def _retrieve_interaction(
        self, session_id: str, context: Dict[str, Any], limit: int
    ) -> List[MemoryEntry]:
        """Retrieve interaction memories (conversation history).

        Args:
            session_id: Session identifier
            context: Context dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of interaction memory entries
        """
        try:
            # Get recent conversation history
            history = await self.system.get_session_history(
                session_id=session_id,
                limit=limit,
                include_context=True
            )

            # Convert history to memory entries
            # For now, return empty list - in full implementation,
            # would convert history to MemoryEntry objects
            return []

        except Exception as e:
            raise

    async def _retrieve_graph(
        self, user_id: str, context: Dict[str, Any], limit: int
    ) -> List[MemoryEntry]:
        """Retrieve learning graph memories (concept relationships, learning paths).

        Args:
            user_id: User identifier
            context: Context dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of graph memory entries
        """
        try:
            domain = context.get('domain')

            # Get next recommended concepts
            next_concepts = await self.system.get_next_concepts(
                user_id=user_id,
                domain=domain,
                limit=limit
            )

            # Convert to memory entries
            # For now, return empty list - in full implementation,
            # would convert recommendations to MemoryEntry objects
            return []

        except Exception as e:
            raise

    async def retrieve_specific_types(
        self,
        memory_types: List[str],
        query: str,
        user_id: str,
        session_id: str,
        context: Dict[str, Any],
        limits: Optional[Dict[str, int]] = None
    ) -> Dict[str, List[MemoryEntry]]:
        """Retrieve only specific memory types in parallel.

        Args:
            memory_types: List of memory types to retrieve
            query: Search query
            user_id: User identifier
            session_id: Session identifier
            context: Context dictionary
            limits: Optional limits for each memory type

        Returns:
            Dictionary mapping memory type to retrieved entries
        """
        if limits is None:
            limits = {t: 10 for t in memory_types}

        # Build retrieval tasks for requested types
        tasks = []
        type_names = []

        for mem_type in memory_types:
            if mem_type == 'episodic':
                tasks.append(
                    self._retrieve_episodic(
                        query, user_id, context, limits.get('episodic', 10)
                    )
                )
                type_names.append('episodic')
            elif mem_type == 'semantic':
                tasks.append(
                    self._retrieve_semantic(
                        query, user_id, context, limits.get('semantic', 10)
                    )
                )
                type_names.append('semantic')
            elif mem_type == 'profile':
                tasks.append(
                    self._retrieve_profile(
                        user_id, context, limits.get('profile', 5)
                    )
                )
                type_names.append('profile')
            elif mem_type == 'interaction':
                tasks.append(
                    self._retrieve_interaction(
                        session_id, context, limits.get('interaction', 10)
                    )
                )
                type_names.append('interaction')
            elif mem_type == 'graph':
                tasks.append(
                    self._retrieve_graph(
                        user_id, context, limits.get('graph', 5)
                    )
                )
                type_names.append('graph')

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        result_dict = {}
        for type_name, result in zip(type_names, results):
            if not isinstance(result, Exception):
                result_dict[type_name] = result
            else:
                result_dict[type_name] = []

        return result_dict
