"""Learning Memory Extension for the mini-agent framework."""

from .data_models import (
    LearningMemoryEntry,
    StudentProfile,
    LearningSession,
    ConceptNode,
    MasteryRecord,
    DifficultyLevel,
    LearningStyle,
    MasteryLevel,
    ConceptType
)

from .student_model import StudentModel
from .learning_analytics import LearningAnalytics
from .spaced_repetition import SpacedRepetitionEngine
from .adaptive_difficulty import AdaptiveDifficultyEngine
from .knowledge_graph import KnowledgeGraph
from .educational_retrieval import (
    EducationalRetrievalStrategy,
    SpacedRepetitionRetrieval,
    MasteryBasedRetrieval,
    AdaptiveRetrieval,
    HybridEducationalRetrieval
)
from .learning_memory_manager import LearningMemoryManager

__version__ = "1.0.0"
__author__ = "Learning Memory Extension Team"

__all__ = [
    # Data models
    "LearningMemoryEntry",
    "StudentProfile",
    "LearningSession",
    "ConceptNode",
    "MasteryRecord",
    "DifficultyLevel",
    "LearningStyle",
    "MasteryLevel",
    "ConceptType",

    # Core components
    "StudentModel",
    "LearningAnalytics",
    "SpacedRepetitionEngine",
    "AdaptiveDifficultyEngine",
    "KnowledgeGraph",

    # Retrieval strategies
    "EducationalRetrievalStrategy",
    "SpacedRepetitionRetrieval",
    "MasteryBasedRetrieval",
    "AdaptiveRetrieval",
    "HybridEducationalRetrieval",

    # Main manager
    "LearningMemoryManager"
]