"""Retrieval strategies for memory search and ranking."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math

from .memory_store import MemoryEntry


class RetrievalStrategy(ABC):
    """Abstract base class for memory retrieval strategies."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        entries: List[MemoryEntry],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve and rank relevant memory entries."""
        pass

    @abstractmethod
    def calculate_relevance_score(
        self,
        query: str,
        entry: MemoryEntry,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate relevance score for a memory entry."""
        pass


class SimilarityRetrieval(RetrievalStrategy):
    """Basic similarity-based retrieval strategy."""

    def __init__(self, embedding_function: Optional[callable] = None):
        self.embedding_function = embedding_function

    async def retrieve(
        self,
        query: str,
        entries: List[MemoryEntry],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve entries using similarity scoring."""

        # Apply filters first
        filtered_entries = self._apply_filters(entries, filters) if filters else entries

        # Calculate relevance scores
        scored_entries = []
        for entry in filtered_entries:
            score = self.calculate_relevance_score(query, entry)
            scored_entries.append((score, entry))

        # Sort by score and return top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def calculate_relevance_score(
        self,
        query: str,
        entry: MemoryEntry,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate multi-factor relevance score."""

        score = 0.0

        # Text similarity (semantic or lexical)
        text_score = self._calculate_text_similarity(query, entry.content)
        score += text_score * 0.4

        # Recency factor
        recency_score = self._calculate_recency_score(entry)
        score += recency_score * 0.2

        # Importance factor
        score += entry.importance * 0.2

        # Access frequency factor
        frequency_score = self._calculate_frequency_score(entry)
        score += frequency_score * 0.1

        # Metadata relevance
        metadata_score = self._calculate_metadata_relevance(query, entry.metadata)
        score += metadata_score * 0.1

        return min(1.0, score)

    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """Calculate text similarity between query and content."""

        if self.embedding_function and hasattr(self, '_embedding_cache'):
            # Use semantic similarity if embeddings are available
            return self._calculate_semantic_similarity(query, content)
        else:
            # Fall back to lexical similarity
            return self._calculate_lexical_similarity(query, content)

    def _calculate_lexical_similarity(self, query: str, content: str) -> float:
        """Calculate lexical similarity using word matching."""

        query_lower = query.lower()
        content_lower = content.lower()

        # Exact substring match
        if query_lower in content_lower:
            return 1.0

        # Word-level matching
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words:
            return 0.0

        # Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)

        jaccard_score = len(intersection) / len(union) if union else 0.0

        # TF-IDF-like scoring for query words
        word_scores = []
        for word in query_words:
            if word in content_words:
                # Count occurrences
                content_count = content_lower.split().count(word)
                score = min(1.0, content_count / len(content_lower.split()))
                word_scores.append(score)

        avg_word_score = sum(word_scores) / len(query_words) if word_scores else 0.0

        return (jaccard_score + avg_word_score) / 2

    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """Calculate semantic similarity using embeddings."""
        # This would require actual embedding computation
        # For now, fall back to lexical similarity
        return self._calculate_lexical_similarity(query, content)

    def _calculate_recency_score(self, entry: MemoryEntry) -> float:
        """Calculate recency score (more recent = higher score)."""

        age_seconds = (datetime.now() - entry.timestamp).total_seconds()
        age_days = age_seconds / (24 * 3600)

        # Exponential decay with half-life of 7 days
        half_life_days = 7
        decay_factor = 0.5 ** (age_days / half_life_days)

        return decay_factor

    def _calculate_frequency_score(self, entry: MemoryEntry) -> float:
        """Calculate frequency score based on access patterns."""

        # Log-scaled access count
        if entry.access_count <= 1:
            return 0.0

        # Logarithmic scaling to prevent dominance of heavily accessed items
        log_access = math.log(entry.access_count)
        max_log_access = math.log(100)  # Assume max 100 accesses for normalization

        frequency_score = min(1.0, log_access / max_log_access)

        # Factor in recency of last access
        last_access_age = (datetime.now() - entry.last_accessed).total_seconds() / (24 * 3600)
        recency_factor = max(0.1, 1 - (last_access_age / 30))  # Decay over 30 days

        return frequency_score * recency_factor

    def _calculate_metadata_relevance(self, query: str, metadata: Dict[str, Any]) -> float:
        """Calculate relevance based on metadata fields."""

        score = 0.0
        query_lower = query.lower()

        # Check various metadata fields
        searchable_fields = ['tags', 'category', 'source', 'type', 'keywords']

        for field in searchable_fields:
            if field in metadata:
                field_value = str(metadata[field]).lower()
                if query_lower in field_value:
                    score += 0.2

        # Special handling for user/session context
        if 'user_id' in metadata or 'session_id' in metadata:
            score += 0.1  # Slight boost for contextual relevance

        return min(1.0, score)

    def _apply_filters(
        self,
        entries: List[MemoryEntry],
        filters: Dict[str, Any]
    ) -> List[MemoryEntry]:
        """Apply filters to memory entries."""

        filtered = []

        for entry in entries:
            passes_filter = True

            for filter_key, filter_value in filters.items():
                if filter_key == 'min_importance':
                    if entry.importance < filter_value:
                        passes_filter = False
                        break

                elif filter_key == 'max_age_days':
                    age_days = (datetime.now() - entry.timestamp).days
                    if age_days > filter_value:
                        passes_filter = False
                        break

                elif filter_key == 'metadata':
                    # Filter by metadata fields
                    for meta_key, meta_value in filter_value.items():
                        if (meta_key not in entry.metadata or
                                entry.metadata[meta_key] != meta_value):
                            passes_filter = False
                            break
                    if not passes_filter:
                        break

                elif filter_key in entry.metadata:
                    if entry.metadata[filter_key] != filter_value:
                        passes_filter = False
                        break

            if passes_filter:
                filtered.append(entry)

        return filtered


class HybridRetrieval(RetrievalStrategy):
    """Hybrid retrieval combining multiple strategies."""

    def __init__(self, strategies: List[Tuple[RetrievalStrategy, float]]):
        """
        Initialize with weighted strategies.

        Args:
            strategies: List of (strategy, weight) tuples
        """
        self.strategies = strategies
        total_weight = sum(weight for _, weight in strategies)
        # Normalize weights
        self.strategies = [(strategy, weight / total_weight) for strategy, weight in strategies]

    async def retrieve(
        self,
        query: str,
        entries: List[MemoryEntry],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Retrieve using hybrid scoring."""

        # Get results from each strategy
        strategy_results = []
        for strategy, weight in self.strategies:
            results = await strategy.retrieve(query, entries, limit * 2, filters)
            strategy_results.append((results, weight))

        # Combine scores
        entry_scores = {}
        for results, weight in strategy_results:
            for i, entry in enumerate(results):
                # Score based on rank (higher rank = higher score)
                rank_score = (len(results) - i) / len(results)
                weighted_score = rank_score * weight

                if entry.id in entry_scores:
                    entry_scores[entry.id] += weighted_score
                else:
                    entry_scores[entry.id] = weighted_score

        # Sort by combined score
        scored_entries = [(score, entry_id) for entry_id, score in entry_scores.items()]
        scored_entries.sort(reverse=True)

        # Get entries in order
        entry_map = {entry.id: entry for entry in entries}
        result_entries = []

        for score, entry_id in scored_entries[:limit]:
            if entry_id in entry_map:
                result_entries.append(entry_map[entry_id])

        return result_entries

    def calculate_relevance_score(
        self,
        query: str,
        entry: MemoryEntry,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate hybrid relevance score."""

        total_score = 0.0
        for strategy, weight in self.strategies:
            score = strategy.calculate_relevance_score(query, entry, context)
            total_score += score * weight

        return total_score