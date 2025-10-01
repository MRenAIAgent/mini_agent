"""Adaptive difficulty engine for personalized content difficulty adjustment."""

import asyncio
import math
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from .data_models import (
    StudentProfile,
    LearningSession,
    DifficultyLevel,
    MasteryLevel,
    LearningMemoryEntry
)


class AdaptiveDifficultyEngine:
    """
    Intelligent difficulty adaptation system that dynamically adjusts
    content difficulty based on student performance, learning patterns,
    and educational objectives.
    """

    def __init__(self, student_model: Optional[Any] = None):
        """
        Initialize adaptive difficulty engine.

        Args:
            student_model: StudentModel instance for accessing student data
        """
        self.student_model = student_model

        # Configuration parameters
        self.config = {
            "target_success_rate": 0.75,  # Optimal challenge level
            "adaptation_sensitivity": 0.1,  # How quickly to adapt
            "min_sessions_for_adaptation": 3,  # Minimum data required
            "performance_window_sessions": 5,  # Sessions to consider for adaptation
            "difficulty_bounds": {
                "min_level": DifficultyLevel.BEGINNER,
                "max_level": DifficultyLevel.EXPERT
            },
            "zone_of_proximal_development": 0.15  # Acceptable challenge variance
        }

    async def recommend_difficulty(
        self,
        user_id: str,
        concept_id: str,
        current_session_performance: Optional[float] = None
    ) -> DifficultyLevel:
        """
        Recommend optimal difficulty level for a student and concept.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier
            current_session_performance: Real-time performance feedback

        Returns:
            Recommended difficulty level
        """
        try:
            if not self.student_model:
                return DifficultyLevel.INTERMEDIATE

            # Get student profile
            student_profile = await self.student_model.get_or_create_profile(user_id)

            # Get concept-specific mastery record
            mastery_record = await self.student_model.get_mastery_record(user_id, concept_id)

            # Calculate base difficulty from multiple factors
            base_difficulty = await self._calculate_base_difficulty(
                student_profile, concept_id, mastery_record
            )

            # Apply performance-based adjustments
            adjusted_difficulty = await self._apply_performance_adjustments(
                base_difficulty, user_id, concept_id, current_session_performance
            )

            # Apply learning velocity adjustments
            velocity_adjusted = await self._apply_velocity_adjustments(
                adjusted_difficulty, student_profile
            )

            # Ensure within bounds and educational constraints
            final_difficulty = self._apply_educational_constraints(
                velocity_adjusted, student_profile, concept_id
            )

            return final_difficulty

        except Exception as e:
            print(f"Error recommending difficulty: {e}")
            return DifficultyLevel.INTERMEDIATE

    async def adapt_difficulty_real_time(
        self,
        user_id: str,
        concept_id: str,
        current_difficulty: DifficultyLevel,
        performance_metrics: Dict[str, float]
    ) -> Tuple[DifficultyLevel, str]:
        """
        Adapt difficulty in real-time based on current performance.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier
            current_difficulty: Current difficulty level
            performance_metrics: Real-time performance data

        Returns:
            Tuple of (new_difficulty, adaptation_reason)
        """
        try:
            success_rate = performance_metrics.get('success_rate', 0.5)
            response_time_ratio = performance_metrics.get('response_time_ratio', 1.0)
            attempts_count = performance_metrics.get('attempts_count', 1)

            # Minimum attempts before adapting
            if attempts_count < 3:
                return current_difficulty, "insufficient_data"

            target_success = self.config["target_success_rate"]
            adaptation_threshold = self.config["zone_of_proximal_development"]

            adaptation_reason = "no_change"
            new_difficulty = current_difficulty

            # Performance too low - reduce difficulty
            if success_rate < target_success - adaptation_threshold:
                if current_difficulty != DifficultyLevel.BEGINNER:
                    new_difficulty = DifficultyLevel(current_difficulty.value - 1)
                    adaptation_reason = "performance_too_low"

            # Performance too high - increase difficulty
            elif success_rate > target_success + adaptation_threshold:
                # Also consider response time
                if response_time_ratio < 0.8:  # Much faster than expected
                    if current_difficulty != DifficultyLevel.EXPERT:
                        new_difficulty = DifficultyLevel(current_difficulty.value + 1)
                        adaptation_reason = "performance_too_high"

            # Response time indicates need for adjustment
            elif response_time_ratio > 2.0:  # Taking much longer than expected
                if current_difficulty != DifficultyLevel.BEGINNER:
                    new_difficulty = DifficultyLevel(current_difficulty.value - 1)
                    adaptation_reason = "response_time_slow"

            return new_difficulty, adaptation_reason

        except Exception as e:
            print(f"Error in real-time difficulty adaptation: {e}")
            return current_difficulty, "error"

    async def calculate_optimal_challenge_level(
        self,
        user_id: str,
        available_content: List[LearningMemoryEntry]
    ) -> List[Tuple[LearningMemoryEntry, float]]:
        """
        Calculate optimal challenge level for available content.

        Args:
            user_id: Student identifier
            available_content: List of available learning content

        Returns:
            List of (content, challenge_score) tuples sorted by appropriateness
        """
        try:
            if not self.student_model:
                return [(content, 0.5) for content in available_content]

            student_profile = await self.student_model.get_or_create_profile(user_id)
            scored_content = []

            for content in available_content:
                challenge_score = await self._calculate_challenge_appropriateness(
                    content, student_profile
                )
                scored_content.append((content, challenge_score))

            # Sort by challenge appropriateness
            scored_content.sort(key=lambda x: x[1], reverse=True)
            return scored_content

        except Exception as e:
            print(f"Error calculating optimal challenge level: {e}")
            return [(content, 0.5) for content in available_content]

    async def predict_performance_at_difficulty(
        self,
        user_id: str,
        concept_id: str,
        target_difficulty: DifficultyLevel
    ) -> Dict[str, float]:
        """
        Predict student performance at a specific difficulty level.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier
            target_difficulty: Target difficulty level

        Returns:
            Dictionary with performance predictions
        """
        try:
            if not self.student_model:
                return {"predicted_success_rate": 0.5, "confidence": 0.0}

            student_profile = await self.student_model.get_or_create_profile(user_id)
            mastery_record = await self.student_model.get_mastery_record(user_id, concept_id)

            # Base prediction on current mastery and target difficulty
            base_performance = self._predict_base_performance(
                student_profile, mastery_record, target_difficulty
            )

            # Adjust for learning patterns
            pattern_adjustment = await self._calculate_pattern_adjustment(
                user_id, concept_id, target_difficulty
            )

            predicted_success_rate = max(0.0, min(1.0, base_performance + pattern_adjustment))

            # Calculate prediction confidence
            confidence = self._calculate_prediction_confidence(
                student_profile, mastery_record
            )

            return {
                "predicted_success_rate": predicted_success_rate,
                "confidence": confidence,
                "base_performance": base_performance,
                "pattern_adjustment": pattern_adjustment
            }

        except Exception as e:
            print(f"Error predicting performance at difficulty: {e}")
            return {"predicted_success_rate": 0.5, "confidence": 0.0}

    async def get_difficulty_progression_path(
        self,
        user_id: str,
        concept_id: str,
        target_mastery: MasteryLevel = MasteryLevel.MASTERED
    ) -> List[Dict[str, Any]]:
        """
        Generate a difficulty progression path for mastering a concept.

        Args:
            user_id: Student identifier
            concept_id: Concept identifier
            target_mastery: Target mastery level

        Returns:
            List of difficulty progression steps
        """
        try:
            if not self.student_model:
                return []

            student_profile = await self.student_model.get_or_create_profile(user_id)
            mastery_record = await self.student_model.get_mastery_record(user_id, concept_id)

            current_mastery = mastery_record.current_level if mastery_record else MasteryLevel.UNKNOWN
            current_difficulty = await self.recommend_difficulty(user_id, concept_id)

            progression_path = []

            # Start from current state
            current_level = current_mastery
            current_diff = current_difficulty

            while current_level.value < target_mastery.value:
                # Predict time to advance
                estimated_sessions = self._estimate_sessions_to_advance(
                    current_level, current_diff
                )

                # Predict performance
                performance_prediction = await self.predict_performance_at_difficulty(
                    user_id, concept_id, current_diff
                )

                step = {
                    "mastery_level": current_level.name,
                    "difficulty_level": current_diff.name,
                    "estimated_sessions": estimated_sessions,
                    "predicted_success_rate": performance_prediction["predicted_success_rate"],
                    "confidence": performance_prediction["confidence"]
                }

                progression_path.append(step)

                # Advance to next level
                if current_level.value < MasteryLevel.MASTERED.value:
                    current_level = MasteryLevel(current_level.value + 1)

                # Potentially increase difficulty
                if performance_prediction["predicted_success_rate"] > 0.8:
                    if current_diff.value < DifficultyLevel.EXPERT.value:
                        current_diff = DifficultyLevel(current_diff.value + 1)

            return progression_path

        except Exception as e:
            print(f"Error generating difficulty progression path: {e}")
            return []

    # Private helper methods

    async def _calculate_base_difficulty(
        self,
        student_profile: StudentProfile,
        concept_id: str,
        mastery_record: Optional[Any]
    ) -> DifficultyLevel:
        """Calculate base difficulty recommendation."""

        # Factor 1: Current mastery level
        if mastery_record:
            mastery_level = mastery_record.current_level
            if mastery_level == MasteryLevel.MASTERED:
                base_from_mastery = DifficultyLevel.EXPERT
            elif mastery_level == MasteryLevel.PROFICIENT:
                base_from_mastery = DifficultyLevel.ADVANCED
            elif mastery_level == MasteryLevel.DEVELOPING:
                base_from_mastery = DifficultyLevel.INTERMEDIATE
            else:
                base_from_mastery = DifficultyLevel.BEGINNER
        else:
            base_from_mastery = DifficultyLevel.BEGINNER

        # Factor 2: Overall student performance
        overall_mastery = student_profile.overall_mastery_score / 100.0
        if overall_mastery > 0.8:
            base_from_performance = DifficultyLevel.ADVANCED
        elif overall_mastery > 0.6:
            base_from_performance = DifficultyLevel.INTERMEDIATE
        else:
            base_from_performance = DifficultyLevel.BEGINNER

        # Factor 3: Student preference
        base_from_preference = student_profile.preferred_difficulty

        # Combine factors (weighted average)
        difficulty_values = [
            base_from_mastery.value * 0.5,
            base_from_performance.value * 0.3,
            base_from_preference.value * 0.2
        ]

        combined_value = sum(difficulty_values)
        final_difficulty = DifficultyLevel(max(1, min(4, round(combined_value))))

        return final_difficulty

    async def _apply_performance_adjustments(
        self,
        base_difficulty: DifficultyLevel,
        user_id: str,
        concept_id: str,
        current_performance: Optional[float]
    ) -> DifficultyLevel:
        """Apply performance-based adjustments to difficulty."""

        if not self.student_model:
            return base_difficulty

        try:
            # Get recent performance for this concept
            recent_sessions = await self._get_recent_concept_sessions(user_id, concept_id)

            if len(recent_sessions) < self.config["min_sessions_for_adaptation"]:
                return base_difficulty

            # Calculate recent performance
            recent_performance = statistics.mean([
                session.success_rate for session in recent_sessions[-self.config["performance_window_sessions"]:]
            ])

            # Include current session if provided
            if current_performance is not None:
                performance_data = [recent_performance, current_performance]
                avg_performance = statistics.mean(performance_data)
            else:
                avg_performance = recent_performance

            # Adjust based on performance vs target
            target = self.config["target_success_rate"]
            sensitivity = self.config["adaptation_sensitivity"]

            performance_diff = avg_performance - target
            adjustment_strength = abs(performance_diff) / sensitivity

            if performance_diff < -0.1 and adjustment_strength > 1.0:
                # Performance too low, reduce difficulty
                if base_difficulty.value > 1:
                    return DifficultyLevel(base_difficulty.value - 1)
            elif performance_diff > 0.1 and adjustment_strength > 1.0:
                # Performance too high, increase difficulty
                if base_difficulty.value < 4:
                    return DifficultyLevel(base_difficulty.value + 1)

            return base_difficulty

        except Exception:
            return base_difficulty

    async def _apply_velocity_adjustments(
        self,
        difficulty: DifficultyLevel,
        student_profile: StudentProfile
    ) -> DifficultyLevel:
        """Apply learning velocity adjustments."""

        velocity = student_profile.learning_velocity

        # Fast learners can handle higher difficulty
        if velocity > 1.5 and difficulty.value < 4:
            return DifficultyLevel(min(4, difficulty.value + 1))

        # Slow learners may need reduced difficulty
        elif velocity < 0.7 and difficulty.value > 1:
            return DifficultyLevel(max(1, difficulty.value - 1))

        return difficulty

    def _apply_educational_constraints(
        self,
        difficulty: DifficultyLevel,
        student_profile: StudentProfile,
        concept_id: str
    ) -> DifficultyLevel:
        """Apply educational constraints and bounds."""

        # Ensure within configured bounds
        min_level = self.config["difficulty_bounds"]["min_level"]
        max_level = self.config["difficulty_bounds"]["max_level"]

        bounded_value = max(min_level.value, min(max_level.value, difficulty.value))

        return DifficultyLevel(bounded_value)

    async def _calculate_challenge_appropriateness(
        self,
        content: LearningMemoryEntry,
        student_profile: StudentProfile
    ) -> float:
        """Calculate how appropriate the challenge level is for the student."""

        score = 0.0

        # Factor 1: Difficulty match with student level
        student_level = student_profile.overall_mastery_score / 100.0
        content_difficulty = content.difficulty_level.value / 4.0

        # Optimal challenge is slightly above current level
        optimal_challenge = student_level + 0.1
        difficulty_match = 1.0 - abs(content_difficulty - optimal_challenge)
        score += difficulty_match * 0.4

        # Factor 2: Prerequisite satisfaction
        prerequisites_met = True
        for prereq in content.prerequisites:
            if prereq not in student_profile.concepts_mastered:
                mastery = student_profile.concept_mastery.get(prereq, MasteryLevel.UNKNOWN)
                if mastery.value < MasteryLevel.PROFICIENT.value:
                    prerequisites_met = False
                    break

        if prerequisites_met:
            score += 0.3
        else:
            score += 0.1  # Some penalty for unmet prerequisites

        # Factor 3: Learning objectives alignment
        student_goals = set(student_profile.learning_goals)
        content_objectives = set(content.learning_objectives)
        objective_overlap = len(student_goals.intersection(content_objectives))

        if student_goals:
            objective_score = objective_overlap / len(student_goals)
            score += objective_score * 0.2

        # Factor 4: Estimated time vs student preference
        if content.estimated_time_minutes:
            preferred_time = student_profile.preferred_session_length_minutes
            time_ratio = min(content.estimated_time_minutes / preferred_time, 2.0)
            time_score = 1.0 - abs(1.0 - time_ratio) / 2.0
            score += time_score * 0.1

        return max(0.0, min(1.0, score))

    def _predict_base_performance(
        self,
        student_profile: StudentProfile,
        mastery_record: Optional[Any],
        target_difficulty: DifficultyLevel
    ) -> float:
        """Predict base performance at target difficulty."""

        # Base on current mastery level
        if mastery_record:
            current_success_rate = mastery_record.success_rate
            current_mastery = mastery_record.current_level.value
        else:
            current_success_rate = 0.5
            current_mastery = MasteryLevel.UNKNOWN.value

        # Adjust for difficulty difference
        difficulty_factor = target_difficulty.value / 4.0  # Normalize to 0-1
        mastery_factor = current_mastery / MasteryLevel.MASTERED.value

        # Higher mastery = better performance at higher difficulty
        base_performance = current_success_rate * (mastery_factor + (1 - difficulty_factor)) / 2

        return max(0.1, min(0.95, base_performance))

    async def _calculate_pattern_adjustment(
        self,
        user_id: str,
        concept_id: str,
        target_difficulty: DifficultyLevel
    ) -> float:
        """Calculate adjustment based on learning patterns."""

        if not self.student_model:
            return 0.0

        try:
            # Get student's historical performance at this difficulty level
            recent_sessions = await self._get_recent_concept_sessions(user_id, concept_id)

            # Find sessions at similar difficulty
            similar_difficulty_sessions = [
                session for session in recent_sessions
                if target_difficulty in session.difficulty_levels_attempted
            ]

            if len(similar_difficulty_sessions) >= 2:
                # Calculate trend in performance at this difficulty
                performances = [s.success_rate for s in similar_difficulty_sessions]
                if len(performances) >= 3:
                    trend = (performances[-1] - performances[0]) / len(performances)
                    return trend * 0.2  # Modest adjustment based on trend

            return 0.0

        except Exception:
            return 0.0

    def _calculate_prediction_confidence(
        self,
        student_profile: StudentProfile,
        mastery_record: Optional[Any]
    ) -> float:
        """Calculate confidence in performance prediction."""

        confidence = 0.0

        # More sessions = higher confidence
        session_count = student_profile.session_count
        confidence += min(0.4, session_count / 20.0)

        # Concept-specific data
        if mastery_record and mastery_record.attempts_count > 0:
            concept_confidence = min(0.3, mastery_record.attempts_count / 10.0)
            confidence += concept_confidence

        # Overall performance stability
        if student_profile.session_count >= 5:
            confidence += 0.3

        return min(1.0, confidence)

    def _estimate_sessions_to_advance(
        self,
        current_mastery: MasteryLevel,
        difficulty: DifficultyLevel
    ) -> int:
        """Estimate sessions needed to advance mastery level."""

        # Base estimate depends on current mastery and difficulty
        base_sessions = {
            MasteryLevel.UNKNOWN: 8,
            MasteryLevel.INTRODUCED: 6,
            MasteryLevel.DEVELOPING: 5,
            MasteryLevel.PROFICIENT: 4
        }

        base = base_sessions.get(current_mastery, 6)

        # Adjust for difficulty
        difficulty_multiplier = 1 + (difficulty.value - 2) * 0.2

        return max(2, int(base * difficulty_multiplier))

    async def _get_recent_concept_sessions(
        self,
        user_id: str,
        concept_id: str,
        days_back: int = 30
    ) -> List[LearningSession]:
        """Get recent sessions for a specific concept."""

        # This would typically query the student model or session storage
        # For now, return empty list as placeholder
        return []

    def get_adaptation_config(self) -> Dict[str, Any]:
        """Get current adaptation configuration."""
        return self.config.copy()

    def update_adaptation_config(self, new_config: Dict[str, Any]) -> None:
        """Update adaptation configuration."""
        self.config.update(new_config)