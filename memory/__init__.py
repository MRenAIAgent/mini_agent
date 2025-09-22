"""
Core Memory Management System

Lightweight memory management for agent context and long-term storage.
Provides interfaces for different memory backends without implementation dependencies.
"""

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryStore, MemoryEntry
from .memory_context import MemoryContext
from .context_manager import ContextManager
from .retrieval_strategy import RetrievalStrategy, SimilarityRetrieval

__all__ = [
    "CoreMemoryManager",
    "MemoryStore",
    "MemoryEntry",
    "MemoryContext",
    "ContextManager",
    "RetrievalStrategy",
    "SimilarityRetrieval"
]