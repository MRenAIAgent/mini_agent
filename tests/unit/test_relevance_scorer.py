"""Unit tests for cross-memory relevance scorer."""

import pytest
from datetime import datetime, timedelta
from memory.coordinator.relevance_scorer import (
    CrossMemoryRelevanceScorer,
    MemoryRelevanceScore
)
from memory.memory_store import MemoryEntry


class TestCrossMemoryRelevanceScorer:
    """Test suite for CrossMemoryRelevanceScorer."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.scorer = CrossMemoryRelevanceScorer()

    def create_test_memory(
        self,
        content: str = "test content",
        importance: float = 0.5,
        access_count: int = 0,
        age_hours: float = 0,
        memory_type: str = "episodic",
        metadata: dict = None
    ) -> MemoryEntry:
        """Create a test memory entry."""
        timestamp = datetime.now() - timedelta(hours=age_hours)
        meta = metadata or {}
        meta['memory_type'] = memory_type

        return MemoryEntry(
            content=content,
            importance=importance,
            timestamp=timestamp,
            access_count=access_count,
            metadata=meta
        )

    @pytest.mark.asyncio
    async def test_score_memory_basic(self):
        """Test basic memory scoring functionality."""
        memory = self.create_test_memory(
            content="algebra linear equations",
            importance=0.8
        )

        score = await self.scorer.score_memory(
            memory=memory,
            query="linear equations",
            context={},
            cross_memory_data={}
        )

        # Verify score structure
        assert isinstance(score, MemoryRelevanceScore)
        assert score.memory_entry == memory
        assert 0.0 <= score.total_score <= 1.0
        assert 0.0 <= score.semantic_similarity <= 1.0
        assert 0.0 <= score.recency_score <= 1.0
        assert score.importance_score == 0.8

    @pytest.mark.asyncio
    async def test_semantic_similarity_scoring(self):
        """Test semantic similarity calculation."""
        # High similarity case
        memory1 = self.create_test_memory(
            content="linear equations and quadratic formulas"
        )

        score1 = await self.scorer.score_memory(
            memory1, "linear equations", {}, {}
        )

        # Should have high semantic similarity (2/2 words match)
        assert score1.semantic_similarity == 1.0

        # Partial similarity case
        memory2 = self.create_test_memory(
            content="algebra and geometry concepts"
        )

        score2 = await self.scorer.score_memory(
            memory2, "algebra calculus", {}, {}
        )

        # Should have partial similarity (1/2 words match)
        assert score2.semantic_similarity == 0.5

        # No similarity case
        memory3 = self.create_test_memory(
            content="history of mathematics"
        )

        score3 = await self.scorer.score_memory(
            memory3, "physics quantum", {}, {}
        )

        # Should have no similarity
        assert score3.semantic_similarity == 0.0

    @pytest.mark.asyncio
    async def test_recency_scoring(self):
        """Test recency score with exponential decay."""
        # Very recent memory (1 hour old)
        recent_memory = self.create_test_memory(age_hours=1)
        recent_score = await self.scorer.score_memory(
            recent_memory, "test", {}, {}
        )

        # Old memory (1 week = 168 hours = half-life)
        old_memory = self.create_test_memory(age_hours=168)
        old_score = await self.scorer.score_memory(
            old_memory, "test", {}, {}
        )

        # Very old memory (4 weeks)
        very_old_memory = self.create_test_memory(age_hours=672)
        very_old_score = await self.scorer.score_memory(
            very_old_memory, "test", {}, {}
        )

        # Recent should have higher score than old
        assert recent_score.recency_score > old_score.recency_score
        assert old_score.recency_score > very_old_score.recency_score

        # At half-life (1 week), score should be ~0.5
        assert 0.45 < old_score.recency_score < 0.55

    @pytest.mark.asyncio
    async def test_frequency_scoring(self):
        """Test frequency score with logarithmic scaling."""
        # Never accessed
        never = self.create_test_memory(access_count=0)
        score_never = await self.scorer.score_memory(never, "test", {}, {})

        # Accessed a few times
        few = self.create_test_memory(access_count=10)
        score_few = await self.scorer.score_memory(few, "test", {}, {})

        # Accessed many times
        many = self.create_test_memory(access_count=100)
        score_many = await self.scorer.score_memory(many, "test", {}, {})

        # More accesses should increase score (but with diminishing returns)
        assert score_never.frequency_score < score_few.frequency_score
        assert score_few.frequency_score < score_many.frequency_score

        # Logarithmic scaling means 100 accesses < 10x score of 10 accesses
        assert score_many.frequency_score < score_few.frequency_score * 2

    @pytest.mark.asyncio
    async def test_cross_link_scoring(self):
        """Test cross-memory link scoring."""
        memory = self.create_test_memory(
            metadata={
                'concept_id': 'linear_equations',
                'user_id': 'user123',
                'session_id': 'session456'
            }
        )

        # Test with matching user and session
        cross_data = {
            'user_id': 'user123',
            'session_id': 'session456',
            'active_concepts': ['linear_equations', 'quadratic']
        }

        score = await self.scorer.score_memory(
            memory, "test", {}, cross_data
        )

        # Should have high cross-link score
        # 0.25 (concept overlap) + 0.3 (session) + 0.2 (user) = 0.75
        assert score.cross_link_score >= 0.7

        # Test with no matches
        no_match_data = {
            'user_id': 'other_user',
            'session_id': 'other_session',
            'active_concepts': []
        }

        score_no_match = await self.scorer.score_memory(
            memory, "test", {}, no_match_data
        )

        assert score_no_match.cross_link_score == 0.0

    @pytest.mark.asyncio
    async def test_context_alignment_scoring(self):
        """Test context alignment scoring."""
        memory = self.create_test_memory(
            metadata={
                'domain': 'algebra',
                'interaction_type': 'practice'
            }
        )

        # Fully aligned context
        aligned_context = {
            'domain': 'algebra',
            'interaction_type': 'practice'
        }

        score_aligned = await self.scorer.score_memory(
            memory, "test", aligned_context, {}
        )

        # Should have max context alignment
        assert score_aligned.context_alignment == 1.0

        # Partially aligned context
        partial_context = {
            'domain': 'algebra',
            'interaction_type': 'question'
        }

        score_partial = await self.scorer.score_memory(
            memory, "test", partial_context, {}
        )

        # Should have partial alignment
        assert score_partial.context_alignment == 0.5

        # No alignment
        no_align_context = {
            'domain': 'geometry',
            'interaction_type': 'question'
        }

        score_none = await self.scorer.score_memory(
            memory, "test", no_align_context, {}
        )

        assert score_none.context_alignment == 0.0

    @pytest.mark.asyncio
    async def test_weighted_total_score(self):
        """Test that total score is properly weighted combination."""
        memory = self.create_test_memory(
            content="algebra linear equations",
            importance=1.0,
            access_count=50,
            age_hours=1,
            metadata={
                'domain': 'algebra',
                'user_id': 'user123'
            }
        )

        context = {'domain': 'algebra'}
        cross_data = {'user_id': 'user123'}

        score = await self.scorer.score_memory(
            memory, "linear equations", context, cross_data
        )

        # Manually calculate expected score
        expected = (
            score.semantic_similarity * 0.30 +
            score.recency_score * 0.20 +
            score.importance_score * 0.20 +
            score.frequency_score * 0.10 +
            score.cross_link_score * 0.15 +
            score.context_alignment * 0.05
        )

        # Total should match weighted sum
        assert abs(score.total_score - expected) < 0.001

        # Total should not exceed 1.0
        assert score.total_score <= 1.0

    @pytest.mark.asyncio
    async def test_concept_extraction(self):
        """Test extraction of concept IDs from memory metadata."""
        memory = self.create_test_memory(
            metadata={
                'concept_id': 'concept1',
                'related_concepts': ['concept2', 'concept3'],
                'context': {
                    'concepts': ['concept4', 'concept5']
                }
            }
        )

        concepts = self.scorer._extract_concept_ids(memory)

        # Should extract all concept IDs
        assert 'concept1' in concepts
        assert 'concept2' in concepts
        assert 'concept3' in concepts
        assert 'concept4' in concepts
        assert 'concept5' in concepts
        assert len(concepts) == 5

    def test_update_weights(self):
        """Test updating scorer weights."""
        # Update weights
        new_weights = {
            'semantic_similarity': 0.50,
            'recency': 0.30
        }

        self.scorer.update_weights(new_weights)

        # Weights should be normalized to sum to 1.0
        total = sum(self.scorer.weights.values())
        assert abs(total - 1.0) < 0.001

        # Semantic similarity should have highest weight (after normalization)
        assert self.scorer.weights['semantic_similarity'] > 0.35

    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        memory = self.create_test_memory()

        # Empty query
        score_empty_query = await self.scorer.score_memory(
            memory, "", {}, {}
        )
        assert score_empty_query.semantic_similarity == 0.0

        # Empty content
        empty_memory = self.create_test_memory(content="")
        score_empty_content = await self.scorer.score_memory(
            empty_memory, "test query", {}, {}
        )
        assert score_empty_content.semantic_similarity == 0.0

        # Very high access count
        high_access = self.create_test_memory(access_count=10000)
        score_high = await self.scorer.score_memory(
            high_access, "test", {}, {}
        )
        # Should be capped at 1.0
        assert score_high.frequency_score <= 1.0

    @pytest.mark.asyncio
    async def test_scoring_metadata(self):
        """Test that scoring metadata is properly included."""
        memory = self.create_test_memory()
        query = "test query"

        score = await self.scorer.score_memory(
            memory, query, {}, {}
        )

        # Check metadata
        assert 'query' in score.scoring_metadata
        assert score.scoring_metadata['query'] == query
        assert 'scored_at' in score.scoring_metadata
        assert 'weights_used' in score.scoring_metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
