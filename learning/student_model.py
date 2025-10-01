"""Student modeling for personalized learning."""

import asyncio
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
import statistics
import math

from .data_models import (
    StudentProfile,
    LearningSession,
    MasteryRecord,
    LearningStyle,
    DifficultyLevel,
    MasteryLevel
)


class StudentModel:
    """
    Comprehensive student modeling for personalized learning.

    Tracks learning patterns, preferences, and performance to enable
    adaptive and personalized educational experiences.
    """

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize the student model.

        Args:
            storage_backend: Optional backend for persistent storage
        """
        self.storage_backend = storage_backend
        self._profiles: Dict[str, StudentProfile] = {}
        self._sessions: Dict[str, List[LearningSession]] = {}
        self._mastery_records: Dict[str, Dict[str, MasteryRecord]] = {}  # user_id -> concept_id -> record

    async def get_or_create_profile(self, user_id: str) -> StudentProfile:
        """
        Get existing student profile or create a new one.

        Args:
            user_id: Unique identifier for the student

        Returns:
            StudentProfile for the student
        """
        if user_id in self._profiles:
            return self._profiles[user_id]

        # Try to load from storage backend
        if self.storage_backend:
            try:
                profile_data = await self.storage_backend.get_student_profile(user_id)
                if profile_data:
                    profile = StudentProfile(**profile_data)
                    self._profiles[user_id] = profile
                    return profile
            except Exception:
                pass  # Continue with new profile creation

        # Create new profile
        profile = StudentProfile(user_id=user_id)
        self._profiles[user_id] = profile
        await self._save_profile(profile)
        return profile

    async def update_profile(self, profile: StudentProfile) -> bool:
        """
        Update student profile with new data.

        Args:
            profile: Updated student profile

        Returns:
            True if successful, False otherwise
        """
        try:
            profile.updated_at = datetime.now()
            self._profiles[profile.user_id] = profile
            return await self._save_profile(profile)
        except Exception:
            return False

    async def record_learning_session(
        self,
        user_id: str,
        session: LearningSession
    ) -> bool:
        """
        Record a completed learning session.

        Args:
            user_id: Student identifier
            session: Completed learning session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Store session
            if user_id not in self._sessions:
                self._sessions[user_id] = []
            self._sessions[user_id].append(session)

            # Update profile with session data
            profile = await self.get_or_create_profile(user_id)
            await self._update_profile_from_session(profile, session)

            # Update mastery records
            await self._update_mastery_records(user_id, session)

            return await self._save_profile(profile)

        except Exception:
            return False

    async def get_personalized_recommendations(
        self,
        user_id: str,
        available_concepts: List[str],
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get personalized learning recommendations for a student.

        Args:
            user_id: Student identifier
            available_concepts: List of available concept IDs
            limit: Maximum number of recommendations

        Returns:
            List of (concept_id, priority_score) tuples
        """
        profile = await self.get_or_create_profile(user_id)
        recommendations = []

        for concept_id in available_concepts:
            priority_score = await self._calculate_concept_priority(
                profile, concept_id
            )
            recommendations.append((concept_id, priority_score))

        # Sort by priority and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]

    async def predict_optimal_difficulty(
        self,
        user_id: str,
        concept_id: str
    ) -> DifficultyLevel:
        """
        Predict optimal difficulty level for a student and concept.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier

        Returns:
            Recommended difficulty level
        """
        profile = await self.get_or_create_profile(user_id)
        mastery_record = await self.get_mastery_record(user_id, concept_id)

        # Base difficulty on current mastery level
        if mastery_record:
            mastery_level = mastery_record.current_level
            if mastery_level == MasteryLevel.MASTERED:
                return DifficultyLevel.EXPERT
            elif mastery_level == MasteryLevel.PROFICIENT:
                return DifficultyLevel.ADVANCED
            elif mastery_level == MasteryLevel.DEVELOPING:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.BEGINNER
        else:
            # New concept - use student's overall performance and preference
            if profile.overall_mastery_score > 80:
                return min(DifficultyLevel.ADVANCED, profile.preferred_difficulty)
            elif profile.overall_mastery_score > 60:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.BEGINNER

    async def detect_learning_style(self, user_id: str) -> LearningStyle:
        """
        Detect student's learning style based on performance patterns.

        Args:
            user_id: Student identifier

        Returns:
            Detected learning style
        """
        profile = await self.get_or_create_profile(user_id)
        sessions = self._sessions.get(user_id, [])

        if len(sessions) < 5:
            return profile.preferred_learning_style

        # Analyze performance by learning style
        style_performance = {}
        for session in sessions[-20:]:  # Last 20 sessions
            for style in session.learning_styles_used:
                if style not in style_performance:
                    style_performance[style] = []
                style_performance[style].append(session.success_rate)

        if not style_performance:
            return profile.preferred_learning_style

        # Find style with best average performance
        best_style = max(
            style_performance.keys(),
            key=lambda s: statistics.mean(style_performance[s])
        )

        return best_style

    async def calculate_learning_velocity(self, user_id: str) -> float:
        """
        Calculate student's learning velocity (rate of mastery improvement).

        Args:
            user_id: Student identifier

        Returns:
            Learning velocity multiplier (1.0 = average)
        """
        profile = await self.get_or_create_profile(user_id)
        sessions = self._sessions.get(user_id, [])

        if len(sessions) < 3:
            return 1.0

        # Calculate mastery improvements over time
        recent_sessions = sessions[-10:]  # Last 10 sessions
        improvement_rates = []

        for session in recent_sessions:
            if session.mastery_improvements:
                total_improvement = sum(session.mastery_improvements.values())
                session_time = session.duration_minutes or 30
                rate = total_improvement / (session_time / 60)  # Improvements per hour
                improvement_rates.append(rate)

        if not improvement_rates:
            return 1.0

        avg_rate = statistics.mean(improvement_rates)
        # Normalize to 1.0 baseline (assuming 1 mastery improvement per hour is average)
        return max(0.1, min(3.0, avg_rate))

    async def get_knowledge_gaps(self, user_id: str) -> List[str]:
        """
        Identify knowledge gaps for targeted learning.

        Args:
            user_id: Student identifier

        Returns:
            List of concept IDs that need attention
        """
        profile = await self.get_or_create_profile(user_id)
        return profile.get_knowledge_gaps()

    async def get_mastery_record(
        self,
        user_id: str,
        concept_id: str
    ) -> Optional[MasteryRecord]:
        """
        Get mastery record for a specific concept and student.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier

        Returns:
            MasteryRecord if exists, None otherwise
        """
        user_records = self._mastery_records.get(user_id, {})
        return user_records.get(concept_id)

    async def predict_retention(
        self,
        user_id: str,
        concept_id: str,
        days_ahead: int = 7
    ) -> float:
        """
        Predict retention probability for a concept after specified days.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier
            days_ahead: Number of days to predict ahead

        Returns:
            Predicted retention probability (0.0 to 1.0)
        """
        profile = await self.get_or_create_profile(user_id)
        mastery_record = await self.get_mastery_record(user_id, concept_id)

        if not mastery_record:
            return 0.0

        # Use exponential decay based on historical retention
        base_retention = profile.retention_rate
        decay_rate = 0.1  # Configurable decay rate
        retention_probability = base_retention * math.exp(-decay_rate * days_ahead)

        # Adjust for mastery level
        mastery_multiplier = {
            MasteryLevel.UNKNOWN: 0.1,
            MasteryLevel.INTRODUCED: 0.3,
            MasteryLevel.DEVELOPING: 0.6,
            MasteryLevel.PROFICIENT: 0.8,
            MasteryLevel.MASTERED: 0.95
        }

        return min(1.0, retention_probability * mastery_multiplier.get(mastery_record.current_level, 0.5))

    async def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive learning analytics for a student.

        Args:
            user_id: Student identifier

        Returns:
            Dictionary containing learning analytics
        """
        profile = await self.get_or_create_profile(user_id)
        sessions = self._sessions.get(user_id, [])
        user_records = self._mastery_records.get(user_id, {})

        analytics = {
            "profile_summary": {
                "overall_mastery_score": profile.overall_mastery_score,
                "concepts_mastered": len(profile.concepts_mastered),
                "concepts_in_progress": len(profile.concepts_in_progress),
                "total_learning_time_minutes": profile.total_learning_time_minutes,
                "learning_velocity": profile.learning_velocity
            },
            "session_analytics": {
                "total_sessions": len(sessions),
                "average_session_score": profile.average_session_score,
                "last_session_date": profile.last_session_date.isoformat() if profile.last_session_date else None
            },
            "mastery_analytics": {
                "mastery_distribution": self._calculate_mastery_distribution(user_records),
                "recent_improvements": self._calculate_recent_improvements(sessions),
                "learning_streaks": self._calculate_learning_streaks(sessions)
            },
            "predictions": {
                "learning_style": await self.detect_learning_style(user_id),
                "learning_velocity": await self.calculate_learning_velocity(user_id),
                "knowledge_gaps": await self.get_knowledge_gaps(user_id)
            }
        }

        return analytics

    # Private helper methods

    async def _save_profile(self, profile: StudentProfile) -> bool:
        """Save profile to storage backend."""
        if self.storage_backend:
            try:
                return await self.storage_backend.save_student_profile(profile)
            except Exception:
                pass
        return True  # In-memory storage always succeeds

    async def _update_profile_from_session(
        self,
        profile: StudentProfile,
        session: LearningSession
    ) -> None:
        """Update profile based on session data."""
        # Update session tracking
        profile.last_session_date = session.end_time or datetime.now()
        profile.session_count += 1

        # Update learning time
        if session.duration_minutes:
            profile.total_learning_time_minutes += int(session.duration_minutes)

        # Update average session score
        session_score = session.success_rate
        if profile.session_count == 1:
            profile.average_session_score = session_score
        else:
            # Exponential moving average
            alpha = 0.2
            profile.average_session_score = (
                alpha * session_score + (1 - alpha) * profile.average_session_score
            )

        # Update concepts studied
        for concept in session.concepts_studied:
            if concept not in profile.concept_mastery:
                profile.concept_mastery[concept] = MasteryLevel.INTRODUCED

        # Update mastery improvements
        for concept, improvement in session.mastery_improvements.items():
            current_level = profile.concept_mastery.get(concept, MasteryLevel.UNKNOWN)
            new_level_value = min(MasteryLevel.MASTERED.value, current_level.value + improvement)
            new_level = MasteryLevel(new_level_value)
            profile.update_mastery(concept, new_level)

        # Recalculate overall mastery score
        profile.overall_mastery_score = profile.calculate_overall_progress()

    async def _update_mastery_records(
        self,
        user_id: str,
        session: LearningSession
    ) -> None:
        """Update mastery records based on session data."""
        if user_id not in self._mastery_records:
            self._mastery_records[user_id] = {}

        user_records = self._mastery_records[user_id]

        for concept in session.concepts_studied:
            if concept not in user_records:
                user_records[concept] = MasteryRecord(
                    user_id=user_id,
                    concept_id=concept
                )

            record = user_records[concept]

            # Update attempt counts (simplified - would need more detailed session data)
            record.record_attempt(
                success=session.success_rate > 0.7,  # Simplified success criteria
                response_time_seconds=session.average_response_time or 0.0
            )

            # Update study time
            if session.duration_minutes:
                concept_time = session.duration_minutes // len(session.concepts_studied)
                record.total_study_time_minutes += concept_time

            # Update mastery level if improved
            if concept in session.mastery_improvements:
                improvement = session.mastery_improvements[concept]
                new_level_value = min(
                    MasteryLevel.MASTERED.value,
                    record.current_level.value + improvement
                )
                record.update_mastery_level(MasteryLevel(new_level_value))

    async def _calculate_concept_priority(
        self,
        profile: StudentProfile,
        concept_id: str
    ) -> float:
        """Calculate priority score for a concept."""
        priority = 0.0

        # Knowledge gap priority
        if concept_id in profile.get_knowledge_gaps():
            priority += 0.4

        # Learning goal priority
        if concept_id in profile.learning_goals:
            priority += 0.3

        # Prerequisite satisfaction (would need knowledge graph)
        # For now, simplified logic
        current_mastery = profile.concept_mastery.get(concept_id, MasteryLevel.UNKNOWN)
        if current_mastery == MasteryLevel.UNKNOWN:
            priority += 0.2  # New concepts get some priority

        # Challenge preference adjustment
        difficulty_factor = 0.1 * profile.challenge_preference
        priority += difficulty_factor

        return min(1.0, priority)

    def _calculate_mastery_distribution(
        self,
        user_records: Dict[str, MasteryRecord]
    ) -> Dict[str, int]:
        """Calculate distribution of mastery levels."""
        distribution = {level.name: 0 for level in MasteryLevel}

        for record in user_records.values():
            distribution[record.current_level.name] += 1

        return distribution

    def _calculate_recent_improvements(
        self,
        sessions: List[LearningSession]
    ) -> List[Dict[str, Any]]:
        """Calculate recent mastery improvements."""
        improvements = []
        recent_sessions = sessions[-5:]  # Last 5 sessions

        for session in recent_sessions:
            if session.mastery_improvements:
                improvements.append({
                    "session_date": session.start_time.isoformat(),
                    "improvements": session.mastery_improvements,
                    "concepts_count": len(session.mastery_improvements)
                })

        return improvements

    def _calculate_learning_streaks(
        self,
        sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Calculate learning streaks and patterns."""
        if not sessions:
            return {"current_streak": 0, "longest_streak": 0}

        # Calculate consecutive days with sessions
        session_dates = [session.start_time.date() for session in sessions]
        session_dates = sorted(set(session_dates))

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        for i in range(1, len(session_dates)):
            if (session_dates[i] - session_dates[i-1]).days == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)

        # Current streak calculation
        today = datetime.now().date()
        if session_dates and (today - session_dates[-1]).days <= 1:
            # Count backwards from most recent session
            for i in range(len(session_dates) - 1, -1, -1):
                if i == len(session_dates) - 1:
                    current_streak = 1
                elif (session_dates[i+1] - session_dates[i]).days == 1:
                    current_streak += 1
                else:
                    break

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_active_days": len(session_dates)
        }