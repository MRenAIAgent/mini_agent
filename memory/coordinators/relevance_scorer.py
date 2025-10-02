"""Cross-memory relevance scoring system."""

from typing import Dict, Any, Set, Optional
from datetime import datetime
from dataclasses import dataclass
import math

from ..memory_store import MemoryEntry


@dataclass
class MemoryRelevanceScore:
    """Detailed relevance score for a memory entry."""
    memory_entry: MemoryEntry
    total_score: float
    semantic_similarity: float
    recency_score: float
    importance_score: float
    frequency_score: float
    cross_link_score: float
    context_alignment: float
    memory_type: str
    scoring_metadata: Dict[str, Any]


class CrossMemoryRelevanceScorer:
    """Scores memories across different memory types for relevance.

    This scorer combines multiple signals to determine how relevant
    a memory is to a given query and context:

    1. Semantic similarity - How well the content matches the query
    2. Recency - How recently the memory was created
    3. Importance - The stored importance score
    4. Frequency - How often the memory has been accessed
    5. Cross-links - Relationships to other relevant memories
    6. Context alignment - Alignment with current context
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the relevance scorer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Configurable weights for each scoring factor
        self.weights = self.config.get('weights', {
            'semantic_similarity': 0.30,
            'recency': 0.20,
            'importance': 0.20,
            'frequency': 0.10,
            'cross_links': 0.15,
            'context_alignment': 0.05
        })

        # Recency decay parameter (half-life in hours)
        self.recency_half_life_hours = self.config.get(
            'recency_half_life_hours', 168  # 7 days default
        )

    async def score_memory(
        self,
        memory: MemoryEntry,
        query: str,
        context: Dict[str, Any],
        cross_memory_data: Dict[str, Any]
    ) -> MemoryRelevanceScore:
        """Score a single memory for relevance.

        Args:
            memory: Memory entry to score
            query: Query string
            context: Current context dictionary
            cross_memory_data: Data about related memories

        Returns:
            MemoryRelevanceScore with detailed scoring breakdown
        """

        # Calculate each scoring component
        semantic_sim = self._calculate_semantic_similarity(
            memory.content, query
        )

        recency = self._calculate_recency_score(memory.timestamp)

        importance = memory.importance

        frequency = self._calculate_frequency_score(memory.access_count)

        cross_links = self._calculate_cross_link_score(
            memory, cross_memory_data
        )

        context_align = self._calculate_context_alignment(
            memory, context
        )

        # Calculate weighted total score
        total = (
            semantic_sim * self.weights['semantic_similarity'] +
            recency * self.weights['recency'] +
            importance * self.weights['importance'] +
            frequency * self.weights['frequency'] +
            cross_links * self.weights['cross_links'] +
            context_align * self.weights['context_alignment']
        )

        return MemoryRelevanceScore(
            memory_entry=memory,
            total_score=min(total, 1.0),
            semantic_similarity=semantic_sim,
            recency_score=recency,
            importance_score=importance,
            frequency_score=frequency,
            cross_link_score=cross_links,
            context_alignment=context_align,
            memory_type=memory.metadata.get('memory_type', 'unknown'),
            scoring_metadata={
                'query': query,
                'scored_at': datetime.now().isoformat(),
                'weights_used': self.weights.copy()
            }
        )

    def _calculate_semantic_similarity(
        self,
        content: str,
        query: str
    ) -> float:
        """Calculate semantic similarity between content and query.

        Currently uses simple keyword overlap. In production, this should
        use embedding-based similarity (e.g., cosine similarity of embeddings).

        Args:
            content: Memory content
            query: Query string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not query or not content:
            return 0.0

        content_lower = content.lower()
        query_lower = query.lower()
        query_words = set(query_lower.split())

        if not query_words:
            return 0.0

        # Count matching words
        matches = sum(1 for word in query_words if word in content_lower)

        # Normalize by query length
        similarity = matches / len(query_words)

        return min(similarity, 1.0)

    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """Calculate recency score with exponential decay.

        Uses exponential decay function: score = e^(-age / half_life)

        Args:
            timestamp: Timestamp of the memory

        Returns:
            Recency score between 0.0 and 1.0
        """
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600

        # Exponential decay: score = e^(-age / half_life)
        # half_life is when score reaches 0.5
        decay_rate = math.log(2) / self.recency_half_life_hours
        recency_score = math.exp(-age_hours * decay_rate)

        return min(recency_score, 1.0)

    def _calculate_frequency_score(self, access_count: int) -> float:
        """Calculate frequency score with logarithmic scaling.

        Uses logarithmic scaling to prevent overweighting of highly
        accessed memories while still rewarding frequent access.

        Args:
            access_count: Number of times memory has been accessed

        Returns:
            Frequency score between 0.0 and 1.0
        """
        # Log scaling: prevents domination by high-frequency items
        # log(1 + count) / 10 gives reasonable scaling
        frequency_score = math.log(1 + access_count) / 10.0

        return min(frequency_score, 1.0)

    def _calculate_cross_link_score(
        self,
        memory: MemoryEntry,
        cross_memory_data: Dict[str, Any]
    ) -> float:
        """Calculate cross-memory relationship score.

        Boosts score based on relationships to other relevant memories:
        - Shared concepts
        - Same session
        - Same user

        Args:
            memory: Memory entry to score
            cross_memory_data: Data about related memories

        Returns:
            Cross-link score between 0.0 and 1.0
        """
        score = 0.0

        # Boost if memory links to active concepts
        if 'active_concepts' in cross_memory_data:
            memory_concepts = self._extract_concept_ids(memory)
            active_concepts = set(cross_memory_data['active_concepts'])
            overlap = len(memory_concepts & active_concepts)
            # Each overlapping concept adds 0.25, max 0.5
            score += min(overlap * 0.25, 0.5)

        # Boost if memory is from current session
        if 'session_id' in cross_memory_data:
            if memory.metadata.get('session_id') == cross_memory_data['session_id']:
                score += 0.3

        # Boost if memory relates to current user
        if 'user_id' in cross_memory_data:
            if memory.metadata.get('user_id') == cross_memory_data['user_id']:
                score += 0.2

        return min(score, 1.0)

    def _calculate_context_alignment(
        self,
        memory: MemoryEntry,
        context: Dict[str, Any]
    ) -> float:
        """Calculate alignment with current context.

        Checks for alignment with:
        - Domain
        - Interaction type
        - Other contextual factors

        Args:
            memory: Memory entry to score
            context: Current context dictionary

        Returns:
            Context alignment score between 0.0 and 1.0
        """
        score = 0.0

        # Check domain alignment
        if 'domain' in context and 'domain' in memory.metadata:
            if context['domain'] == memory.metadata['domain']:
                score += 0.5

        # Check interaction type alignment
        if 'interaction_type' in context and 'interaction_type' in memory.metadata:
            if context['interaction_type'] == memory.metadata.get('interaction_type'):
                score += 0.5

        return min(score, 1.0)

    def _extract_concept_ids(self, memory: MemoryEntry) -> Set[str]:
        """Extract concept IDs from memory metadata.

        Args:
            memory: Memory entry to extract concepts from

        Returns:
            Set of concept IDs found in the memory
        """
        concepts = set()

        # Check various metadata fields for concept IDs
        if 'concept_id' in memory.metadata:
            concepts.add(memory.metadata['concept_id'])

        if 'related_concepts' in memory.metadata:
            related = memory.metadata['related_concepts']
            if isinstance(related, (list, set)):
                concepts.update(related)

        if 'context' in memory.metadata:
            ctx = memory.metadata['context']
            if isinstance(ctx, dict):
                if 'concept_id' in ctx:
                    concepts.add(ctx['concept_id'])
                if 'concepts' in ctx:
                    if isinstance(ctx['concepts'], (list, set)):
                        concepts.update(ctx['concepts'])

        return concepts

    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update scoring weights.

        Args:
            new_weights: Dictionary of new weights
        """
        self.weights.update(new_weights)

        # Normalize to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
