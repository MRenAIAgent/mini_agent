"""Core memory abstractions and interfaces.

This package provides the foundational abstractions for the memory system:

- MemoryStore: Abstract storage interface
- InMemoryStore: Default in-memory implementation
- MemoryEntry: Data model for individual memories
- MemoryContext: Session context management
- ConversationTurn: Individual conversation turn
- RetrievalStrategy: Pluggable ranking algorithms
"""

from .memory_store import (
    MemoryStore,
    MemoryEntry,
    InMemoryStore
)
from .memory_context import (
    MemoryContext,
    ConversationTurn
)
from .retrieval_strategy import (
    RetrievalStrategy,
    SimilarityRetrieval
)

__all__ = [
    # Storage
    'MemoryStore',
    'MemoryEntry',
    'InMemoryStore',

    # Context
    'MemoryContext',
    'ConversationTurn',

    # Retrieval
    'RetrievalStrategy',
    'SimilarityRetrieval',
]
