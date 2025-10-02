"""Memory type implementations.

This package provides specialized memory type managers:

- EpisodicMemoryManager: Learning experiences and specific events
- SemanticMemoryManager: Structured knowledge and concepts
- UserProfileMemoryManager: Learner characteristics and preferences
- InteractionMemoryManager: Conversation history and dialogue state
- LearningGraphMemory: Graph-based learning path tracking
"""

from .episodic_memory import EpisodicMemoryManager
from .semantic_memory import SemanticMemoryManager
from .user_profile_memory import UserProfileMemoryManager
from .interaction_memory import (
    InteractionMemoryManager,
    InteractionType,
    InteractionRecord
)
from .learning_graph_memory import (
    LearningGraphMemory,
    ConceptStatus
)

__all__ = [
    # Memory managers
    'EpisodicMemoryManager',
    'SemanticMemoryManager',
    'UserProfileMemoryManager',
    'InteractionMemoryManager',
    'LearningGraphMemory',

    # Supporting types
    'InteractionType',
    'InteractionRecord',
    'ConceptStatus',
]
