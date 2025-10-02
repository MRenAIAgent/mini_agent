"""Memory coordination layer.

This package provides coordination between different memory types:

- EnhancedMemoryCoordinator: Main coordinator with parallel retrieval, relevance
  scoring, and adaptive weighting (Phase 1)
- MemoryCoordinator (legacy): Original coordinator for backward compatibility
- LearningAnalytics: Analytics and insights across all memory types
- ParallelRetrievalEngine: Concurrent memory retrieval
- CrossMemoryRelevanceScorer: Multi-factor relevance scoring
- AdaptiveWeightSystem: Context-aware memory type weighting
"""

from .relevance_scorer import (
    CrossMemoryRelevanceScorer,
    MemoryRelevanceScore
)
from .parallel_retrieval import (
    ParallelRetrievalEngine,
    ParallelRetrievalResult
)
from .adaptive_weights import (
    AdaptiveWeightSystem
)
from .enhanced_coordinator import (
    EnhancedMemoryCoordinator,
    IntegratedMemoryContext
)
from .legacy_coordinator import (
    MemoryCoordinator
)
from .learning_analytics import (
    LearningAnalytics
)

__all__ = [
    # Enhanced coordinator (Phase 1)
    'EnhancedMemoryCoordinator',
    'IntegratedMemoryContext',
    'ParallelRetrievalEngine',
    'ParallelRetrievalResult',
    'CrossMemoryRelevanceScorer',
    'MemoryRelevanceScore',
    'AdaptiveWeightSystem',

    # Legacy components
    'MemoryCoordinator',
    'LearningAnalytics',
]
