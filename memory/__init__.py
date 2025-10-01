"""
Core Memory Management System

Lightweight memory management for agent context and long-term storage.
Provides interfaces for different memory backends without implementation dependencies.

The system now includes a layered memory architecture with specialized memory types:
- CoreMemoryManager: Base memory functionality
- EpisodicMemoryManager: Learning experiences and episodes
- SemanticMemoryManager: Structured knowledge and concepts
- UserProfileMemoryManager: User characteristics and preferences
- InteractionMemoryManager: Conversation and dialogue context
- LearningGraphMemory: Graph-based learning operations
- LearningMemorySystem: Complete system inheriting all memory types
"""

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryStore, MemoryEntry
from .memory_context import MemoryContext
from .context_manager import ContextManager
from .retrieval_strategy import RetrievalStrategy, SimilarityRetrieval

# Specialized memory managers (agent memory extensions)
from .episodic_memory import EpisodicMemoryManager
from .semantic_memory import SemanticMemoryManager
from .user_profile_memory import UserProfileMemoryManager
from .interaction_memory import InteractionMemoryManager, InteractionType, InteractionRecord
from .learning_graph_memory import LearningGraphMemory, ConceptStatus

# Complete learning system
from .learning_memory_system import (
    LearningMemorySystem,
    LearningSystemConfig,
    ComprehensiveLearningResponse,
    SessionConsolidationResult,
    ComprehensiveLearningInsights
)

__all__ = [
    # Base memory system
    "CoreMemoryManager",
    "MemoryStore",
    "MemoryEntry",
    "MemoryContext",
    "ContextManager",
    "RetrievalStrategy",
    "SimilarityRetrieval",

    # Specialized memory managers
    "EpisodicMemoryManager",
    "SemanticMemoryManager",
    "UserProfileMemoryManager",
    "InteractionMemoryManager",
    "InteractionType",
    "InteractionRecord",
    "LearningGraphMemory",
    "ConceptStatus",

    # Complete learning system
    "LearningMemorySystem",
    "LearningSystemConfig",
    "ComprehensiveLearningResponse",
    "SessionConsolidationResult",
    "ComprehensiveLearningInsights"
]