"""Enhanced data models for learning memory extension."""

from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from ..memory.memory_store import MemoryEntry


class DifficultyLevel(Enum):
    """Difficulty levels for learning content."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


class LearningStyle(Enum):
    """Different learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class MasteryLevel(Enum):
    """Mastery levels for concepts."""
    UNKNOWN = 0
    INTRODUCED = 1
    DEVELOPING = 2
    PROFICIENT = 3
    MASTERED = 4


class ConceptType(Enum):
    """Types of concepts in the knowledge graph."""
    FUNDAMENTAL = "fundamental"
    SKILL = "skill"
    KNOWLEDGE = "knowledge"
    APPLICATION = "application"
    SYNTHESIS = "synthesis"


@dataclass
class LearningMemoryEntry(MemoryEntry):
    """Extended memory entry with educational metadata."""

    # Educational metadata
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    concept_tags: Set[str] = field(default_factory=set)
    prerequisites: Set[str] = field(default_factory=set)
    learning_objectives: List[str] = field(default_factory=list)
    estimated_time_minutes: Optional[int] = None

    # Spaced repetition data
    repetition_count: int = 0
    ease_factor: float = 2.5  # SM-2 algorithm ease factor
    interval_days: int = 1
    next_review_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None

    # Performance tracking
    mastery_level: MasteryLevel = MasteryLevel.UNKNOWN
    correct_attempts: int = 0
    total_attempts: int = 0
    average_response_time_seconds: Optional[float] = None

    # Content relationships
    related_concepts: Set[str] = field(default_factory=set)
    difficulty_progression: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this content."""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_attempts / self.total_attempts

    @property
    def is_due_for_review(self) -> bool:
        """Check if content is due for spaced repetition review."""
        if not self.next_review_date:
            return True
        return datetime.now() >= self.next_review_date

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with educational metadata."""
        base_dict = super().to_dict()
        base_dict.update({
            "difficulty_level": self.difficulty_level.value,
            "concept_tags": list(self.concept_tags),
            "prerequisites": list(self.prerequisites),
            "learning_objectives": self.learning_objectives,
            "estimated_time_minutes": self.estimated_time_minutes,
            "repetition_count": self.repetition_count,
            "ease_factor": self.ease_factor,
            "interval_days": self.interval_days,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "last_review_date": self.last_review_date.isoformat() if self.last_review_date else None,
            "mastery_level": self.mastery_level.value,
            "correct_attempts": self.correct_attempts,
            "total_attempts": self.total_attempts,
            "average_response_time_seconds": self.average_response_time_seconds,
            "related_concepts": list(self.related_concepts),
            "difficulty_progression": self.difficulty_progression
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningMemoryEntry':
        """Create from dictionary with educational metadata."""
        # Extract base MemoryEntry fields
        base_entry = MemoryEntry.from_dict(data)

        # Create learning entry with base data
        learning_entry = cls(
            id=base_entry.id,
            content=base_entry.content,
            metadata=base_entry.metadata,
            timestamp=base_entry.timestamp,
            embedding=base_entry.embedding,
            importance=base_entry.importance,
            access_count=base_entry.access_count,
            last_accessed=base_entry.last_accessed
        )

        # Add educational fields
        learning_entry.difficulty_level = DifficultyLevel(data.get("difficulty_level", DifficultyLevel.INTERMEDIATE.value))
        learning_entry.concept_tags = set(data.get("concept_tags", []))
        learning_entry.prerequisites = set(data.get("prerequisites", []))
        learning_entry.learning_objectives = data.get("learning_objectives", [])
        learning_entry.estimated_time_minutes = data.get("estimated_time_minutes")
        learning_entry.repetition_count = data.get("repetition_count", 0)
        learning_entry.ease_factor = data.get("ease_factor", 2.5)
        learning_entry.interval_days = data.get("interval_days", 1)

        if data.get("next_review_date"):
            learning_entry.next_review_date = datetime.fromisoformat(data["next_review_date"])
        if data.get("last_review_date"):
            learning_entry.last_review_date = datetime.fromisoformat(data["last_review_date"])

        learning_entry.mastery_level = MasteryLevel(data.get("mastery_level", MasteryLevel.UNKNOWN.value))
        learning_entry.correct_attempts = data.get("correct_attempts", 0)
        learning_entry.total_attempts = data.get("total_attempts", 0)
        learning_entry.average_response_time_seconds = data.get("average_response_time_seconds")
        learning_entry.related_concepts = set(data.get("related_concepts", []))
        learning_entry.difficulty_progression = data.get("difficulty_progression", [])

        return learning_entry


@dataclass
class StudentProfile:
    """Comprehensive student profile for personalized learning."""

    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Learning preferences
    preferred_learning_style: LearningStyle = LearningStyle.MULTIMODAL
    preferred_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    preferred_session_length_minutes: int = 30

    # Performance metrics
    overall_mastery_score: float = 0.0
    total_learning_time_minutes: int = 0
    concepts_mastered: Set[str] = field(default_factory=set)
    concepts_in_progress: Set[str] = field(default_factory=set)

    # Learning patterns
    optimal_review_times: List[int] = field(default_factory=lambda: [9, 13, 19])  # Hours of day
    learning_velocity: float = 1.0  # Multiplier for learning speed
    retention_rate: float = 0.8  # Historical retention performance

    # Adaptive parameters
    challenge_preference: float = 0.5  # 0.0 = easy, 1.0 = challenging
    exploration_tendency: float = 0.3  # Willingness to try new concepts

    # Knowledge state
    concept_mastery: Dict[str, MasteryLevel] = field(default_factory=dict)
    learning_goals: List[str] = field(default_factory=list)
    completed_goals: List[str] = field(default_factory=list)

    # Session tracking
    last_session_date: Optional[datetime] = None
    session_count: int = 0
    average_session_score: float = 0.0

    def update_mastery(self, concept: str, new_level: MasteryLevel) -> None:
        """Update mastery level for a concept."""
        old_level = self.concept_mastery.get(concept, MasteryLevel.UNKNOWN)
        self.concept_mastery[concept] = new_level

        # Update tracking sets
        if new_level == MasteryLevel.MASTERED:
            self.concepts_mastered.add(concept)
            self.concepts_in_progress.discard(concept)
        elif new_level in [MasteryLevel.DEVELOPING, MasteryLevel.PROFICIENT]:
            self.concepts_in_progress.add(concept)
            self.concepts_mastered.discard(concept)
        else:
            self.concepts_in_progress.discard(concept)
            self.concepts_mastered.discard(concept)

        self.updated_at = datetime.now()

    def get_knowledge_gaps(self) -> List[str]:
        """Identify concepts that need attention."""
        gaps = []
        for concept, mastery in self.concept_mastery.items():
            if mastery in [MasteryLevel.UNKNOWN, MasteryLevel.INTRODUCED]:
                gaps.append(concept)
        return gaps

    def calculate_overall_progress(self) -> float:
        """Calculate overall learning progress as percentage."""
        if not self.concept_mastery:
            return 0.0

        total_score = sum(level.value for level in self.concept_mastery.values())
        max_possible = len(self.concept_mastery) * MasteryLevel.MASTERED.value

        return (total_score / max_possible) * 100 if max_possible > 0 else 0.0


@dataclass
class LearningSession:
    """Track individual learning sessions."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Session content
    concepts_studied: List[str] = field(default_factory=list)
    activities_completed: List[str] = field(default_factory=list)

    # Performance metrics
    total_attempts: int = 0
    correct_attempts: int = 0
    average_response_time: Optional[float] = None

    # Learning outcomes
    mastery_improvements: Dict[str, int] = field(default_factory=dict)  # concept -> level increase
    new_concepts_introduced: List[str] = field(default_factory=list)

    # Session characteristics
    difficulty_levels_attempted: Set[DifficultyLevel] = field(default_factory=set)
    learning_styles_used: Set[LearningStyle] = field(default_factory=set)

    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate session duration in minutes."""
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this session."""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_attempts / self.total_attempts

    def end_session(self) -> None:
        """Mark session as ended."""
        self.end_time = datetime.now()


@dataclass
class ConceptNode:
    """Knowledge graph node representing a learning concept."""

    concept_id: str
    name: str
    description: str
    concept_type: ConceptType

    # Relationships
    prerequisites: Set[str] = field(default_factory=set)
    enables: Set[str] = field(default_factory=set)  # Concepts this enables
    related_to: Set[str] = field(default_factory=set)  # Related concepts

    # Learning metadata
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_learning_time_minutes: int = 30
    learning_objectives: List[str] = field(default_factory=list)

    # Content references
    content_entries: Set[str] = field(default_factory=set)  # MemoryEntry IDs
    assessment_entries: Set[str] = field(default_factory=set)  # Assessment content

    # Analytics
    total_learners: int = 0
    average_mastery_time_hours: Optional[float] = None
    common_difficulties: List[str] = field(default_factory=list)

    def add_prerequisite(self, prerequisite_id: str) -> None:
        """Add a prerequisite relationship."""
        self.prerequisites.add(prerequisite_id)

    def add_enables(self, concept_id: str) -> None:
        """Add an enables relationship."""
        self.enables.add(concept_id)

    def is_prerequisite_satisfied(self, student_mastery: Dict[str, MasteryLevel]) -> bool:
        """Check if all prerequisites are satisfied for a student."""
        for prereq in self.prerequisites:
            mastery = student_mastery.get(prereq, MasteryLevel.UNKNOWN)
            if mastery not in [MasteryLevel.PROFICIENT, MasteryLevel.MASTERED]:
                return False
        return True


@dataclass
class MasteryRecord:
    """Track mastery progression for a specific concept and student."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    concept_id: str = ""

    # Mastery progression
    current_level: MasteryLevel = MasteryLevel.UNKNOWN
    previous_level: MasteryLevel = MasteryLevel.UNKNOWN
    level_achieved_date: datetime = field(default_factory=datetime.now)

    # Performance data
    attempts_count: int = 0
    success_count: int = 0
    total_study_time_minutes: int = 0

    # Spaced repetition tracking
    repetition_history: List[datetime] = field(default_factory=list)
    current_interval_days: int = 1
    ease_factor: float = 2.5

    # Learning analytics
    learning_curve_data: List[Dict[str, Any]] = field(default_factory=list)
    breakthrough_moments: List[datetime] = field(default_factory=list)

    def record_attempt(self, success: bool, response_time_seconds: float) -> None:
        """Record a learning attempt."""
        self.attempts_count += 1
        if success:
            self.success_count += 1

        # Add to learning curve data
        self.learning_curve_data.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "response_time": response_time_seconds,
            "cumulative_success_rate": self.success_count / self.attempts_count
        })

    def update_mastery_level(self, new_level: MasteryLevel) -> None:
        """Update mastery level and track progression."""
        if new_level != self.current_level:
            self.previous_level = self.current_level
            self.current_level = new_level
            self.level_achieved_date = datetime.now()

            # Record breakthrough if significant improvement
            if new_level.value > self.previous_level.value + 1:
                self.breakthrough_moments.append(datetime.now())

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.attempts_count == 0:
            return 0.0
        return self.success_count / self.attempts_count