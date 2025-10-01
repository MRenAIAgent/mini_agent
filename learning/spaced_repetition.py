"""Spaced repetition engine for optimal learning retention."""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .data_models import LearningMemoryEntry, MasteryLevel


@dataclass
class SpacedRepetitionSchedule:
    """Schedule for spaced repetition reviews."""

    entry_id: str
    next_review_date: datetime
    interval_days: int
    ease_factor: float
    repetition_count: int
    estimated_retention: float


class SpacedRepetitionEngine:
    """
    Advanced spaced repetition engine supporting multiple algorithms.

    Implements SM-2, SM-15, and FSRS algorithms for optimal review scheduling
    to maximize long-term retention while minimizing study time.
    """

    def __init__(self, algorithm: str = "sm2", initial_ease: float = 2.5):
        """
        Initialize spaced repetition engine.

        Args:
            algorithm: Algorithm to use ("sm2", "sm15", "fsrs")
            initial_ease: Initial ease factor for new content
        """
        self.algorithm = algorithm.lower()
        self.initial_ease = initial_ease

        # Algorithm-specific parameters
        self.sm2_params = {
            "initial_interval": 1,
            "second_interval": 6,
            "ease_threshold": 1.3,
            "ease_adjustment": 0.1
        }

        self.fsrs_params = {
            "request_retention": 0.9,
            "maximum_interval": 36500,  # 100 years
            "w": [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61]
        }

    async def calculate_next_review(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float,
        response_time_seconds: Optional[float] = None
    ) -> SpacedRepetitionSchedule:
        """
        Calculate next review schedule based on performance.

        Args:
            entry: Learning memory entry
            performance_rating: Performance rating (0.0 = failed, 1.0 = perfect)
            response_time_seconds: Time taken to respond

        Returns:
            SpacedRepetitionSchedule with next review timing
        """
        if self.algorithm == "sm2":
            return await self._calculate_sm2_schedule(entry, performance_rating)
        elif self.algorithm == "sm15":
            return await self._calculate_sm15_schedule(entry, performance_rating, response_time_seconds)
        elif self.algorithm == "fsrs":
            return await self._calculate_fsrs_schedule(entry, performance_rating, response_time_seconds)
        else:
            # Default to SM-2
            return await self._calculate_sm2_schedule(entry, performance_rating)

    async def record_review(
        self,
        entry: LearningMemoryEntry,
        success: bool,
        response_time_seconds: Optional[float] = None,
        difficulty_rating: Optional[float] = None
    ) -> LearningMemoryEntry:
        """
        Record a review session and update spaced repetition data.

        Args:
            entry: Learning memory entry
            success: Whether the review was successful
            response_time_seconds: Time taken for response
            difficulty_rating: Subjective difficulty rating (0.0-1.0)

        Returns:
            Updated learning memory entry
        """
        # Convert success/difficulty to performance rating
        performance_rating = self._calculate_performance_rating(
            success, response_time_seconds, difficulty_rating
        )

        # Calculate next review schedule
        schedule = await self.calculate_next_review(
            entry, performance_rating, response_time_seconds
        )

        # Update entry with new spaced repetition data
        entry.repetition_count += 1
        entry.ease_factor = schedule.ease_factor
        entry.interval_days = schedule.interval_days
        entry.next_review_date = schedule.next_review_date
        entry.last_review_date = datetime.now()

        # Update performance tracking
        entry.total_attempts += 1
        if success:
            entry.correct_attempts += 1

        # Update average response time
        if response_time_seconds:
            if entry.average_response_time_seconds is None:
                entry.average_response_time_seconds = response_time_seconds
            else:
                # Exponential moving average
                alpha = 0.3
                entry.average_response_time_seconds = (
                    alpha * response_time_seconds +
                    (1 - alpha) * entry.average_response_time_seconds
                )

        return entry

    async def get_due_reviews(
        self,
        entries: List[LearningMemoryEntry],
        max_reviews: int = 50
    ) -> List[LearningMemoryEntry]:
        """
        Get entries that are due for review.

        Args:
            entries: List of learning memory entries
            max_reviews: Maximum number of reviews to return

        Returns:
            List of entries due for review, sorted by priority
        """
        now = datetime.now()
        due_entries = []

        for entry in entries:
            if entry.is_due_for_review:
                priority = self._calculate_review_priority(entry, now)
                due_entries.append((priority, entry))

        # Sort by priority (highest first)
        due_entries.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in due_entries[:max_reviews]]

    async def predict_retention(
        self,
        entry: LearningMemoryEntry,
        days_ahead: int = 1
    ) -> float:
        """
        Predict retention probability after specified days.

        Args:
            entry: Learning memory entry
            days_ahead: Number of days to predict ahead

        Returns:
            Predicted retention probability (0.0 to 1.0)
        """
        if self.algorithm == "fsrs":
            return self._predict_fsrs_retention(entry, days_ahead)
        else:
            return self._predict_sm2_retention(entry, days_ahead)

    async def optimize_review_schedule(
        self,
        entries: List[LearningMemoryEntry],
        available_time_minutes: int,
        target_retention: float = 0.9
    ) -> List[LearningMemoryEntry]:
        """
        Optimize review schedule for available time and target retention.

        Args:
            entries: List of learning memory entries
            available_time_minutes: Available study time
            target_retention: Target retention rate

        Returns:
            Optimized list of entries to review
        """
        # Get entries that need review
        candidates = await self.get_due_reviews(entries, len(entries))

        if not candidates:
            return []

        # Calculate time estimates and retention impact
        review_plans = []
        for entry in candidates:
            estimated_time = entry.estimated_time_minutes or 5
            retention_impact = await self._calculate_retention_impact(entry)
            efficiency = retention_impact / estimated_time  # Impact per minute

            review_plans.append({
                'entry': entry,
                'time': estimated_time,
                'impact': retention_impact,
                'efficiency': efficiency
            })

        # Sort by efficiency (impact per minute)
        review_plans.sort(key=lambda x: x['efficiency'], reverse=True)

        # Select entries within time budget
        selected_entries = []
        total_time = 0

        for plan in review_plans:
            if total_time + plan['time'] <= available_time_minutes:
                selected_entries.append(plan['entry'])
                total_time += plan['time']

        return selected_entries

    # Algorithm-specific implementations

    async def _calculate_sm2_schedule(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float
    ) -> SpacedRepetitionSchedule:
        """Calculate SM-2 algorithm schedule."""
        ease_factor = entry.ease_factor
        interval = entry.interval_days
        repetition_count = entry.repetition_count

        # SM-2 algorithm logic
        if performance_rating < 0.6:  # Failed review
            # Reset interval and repetition count
            interval = 1
            repetition_count = 0
        else:
            if repetition_count == 0:
                interval = self.sm2_params["initial_interval"]
            elif repetition_count == 1:
                interval = self.sm2_params["second_interval"]
            else:
                interval = int(interval * ease_factor)

            # Adjust ease factor based on performance
            ease_adjustment = (0.1 - (5 - performance_rating * 5) *
                             (0.08 + (5 - performance_rating * 5) * 0.02))
            ease_factor = max(self.sm2_params["ease_threshold"],
                            ease_factor + ease_adjustment)

        next_review_date = datetime.now() + timedelta(days=interval)
        estimated_retention = self._estimate_sm2_retention(interval, ease_factor)

        return SpacedRepetitionSchedule(
            entry_id=entry.id,
            next_review_date=next_review_date,
            interval_days=interval,
            ease_factor=ease_factor,
            repetition_count=repetition_count + 1,
            estimated_retention=estimated_retention
        )

    async def _calculate_sm15_schedule(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float,
        response_time_seconds: Optional[float]
    ) -> SpacedRepetitionSchedule:
        """Calculate SM-15 algorithm schedule (enhanced SM-2)."""
        # SM-15 incorporates response time and difficulty adjustments
        base_schedule = await self._calculate_sm2_schedule(entry, performance_rating)

        # Adjust for response time
        if response_time_seconds and entry.average_response_time_seconds:
            time_ratio = response_time_seconds / entry.average_response_time_seconds
            if time_ratio > 1.5:  # Took significantly longer
                base_schedule.interval_days = int(base_schedule.interval_days * 0.8)
            elif time_ratio < 0.7:  # Much faster than usual
                base_schedule.interval_days = int(base_schedule.interval_days * 1.2)

        # Recalculate next review date
        base_schedule.next_review_date = datetime.now() + timedelta(
            days=base_schedule.interval_days
        )

        return base_schedule

    async def _calculate_fsrs_schedule(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float,
        response_time_seconds: Optional[float]
    ) -> SpacedRepetitionSchedule:
        """Calculate FSRS (Free Spaced Repetition Scheduler) schedule."""
        # Simplified FSRS implementation
        # In production, this would use the full FSRS algorithm

        difficulty = self._estimate_difficulty(entry, performance_rating)
        stability = self._calculate_stability(entry, performance_rating)

        # Calculate optimal interval for target retention
        target_retention = self.fsrs_params["request_retention"]
        interval = int(stability * math.log(target_retention) / math.log(0.9))
        interval = max(1, min(interval, self.fsrs_params["maximum_interval"]))

        next_review_date = datetime.now() + timedelta(days=interval)
        estimated_retention = math.exp(-interval / stability)

        return SpacedRepetitionSchedule(
            entry_id=entry.id,
            next_review_date=next_review_date,
            interval_days=interval,
            ease_factor=entry.ease_factor,  # FSRS doesn't use ease factor
            repetition_count=entry.repetition_count + 1,
            estimated_retention=estimated_retention
        )

    def _calculate_performance_rating(
        self,
        success: bool,
        response_time_seconds: Optional[float],
        difficulty_rating: Optional[float]
    ) -> float:
        """Convert review metrics to performance rating."""
        if not success:
            return 0.3  # Failed reviews get low rating

        rating = 0.8  # Base rating for successful review

        # Adjust for difficulty rating if provided
        if difficulty_rating is not None:
            # Lower difficulty experienced = higher performance
            rating += (1.0 - difficulty_rating) * 0.2

        return min(1.0, rating)

    def _calculate_review_priority(
        self,
        entry: LearningMemoryEntry,
        current_time: datetime
    ) -> float:
        """Calculate priority score for review scheduling."""
        priority = 0.0

        # Time overdue factor
        if entry.next_review_date:
            days_overdue = (current_time - entry.next_review_date).days
            if days_overdue > 0:
                priority += min(1.0, days_overdue / 7.0) * 0.5

        # Importance factor
        priority += entry.importance * 0.3

        # Difficulty factor (harder content gets higher priority)
        priority += (entry.difficulty_level.value / 4.0) * 0.2

        return priority

    def _predict_sm2_retention(
        self,
        entry: LearningMemoryEntry,
        days_ahead: int
    ) -> float:
        """Predict retention using SM-2 parameters."""
        if entry.next_review_date:
            days_since_due = (
                datetime.now() + timedelta(days=days_ahead) - entry.next_review_date
            ).days
            # Simple exponential decay model
            decay_rate = 1.0 / entry.interval_days
            retention = math.exp(-decay_rate * max(0, days_since_due))
            return max(0.0, min(1.0, retention))
        return 0.5

    def _predict_fsrs_retention(
        self,
        entry: LearningMemoryEntry,
        days_ahead: int
    ) -> float:
        """Predict retention using FSRS model."""
        stability = self._calculate_stability(entry, entry.success_rate)
        retention = math.exp(-days_ahead / stability)
        return max(0.0, min(1.0, retention))

    def _estimate_difficulty(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float
    ) -> float:
        """Estimate item difficulty for FSRS."""
        # Combine intrinsic difficulty with performance history
        base_difficulty = entry.difficulty_level.value / 4.0
        performance_factor = 1.0 - performance_rating
        return min(1.0, base_difficulty + performance_factor * 0.3)

    def _calculate_stability(
        self,
        entry: LearningMemoryEntry,
        performance_rating: float
    ) -> float:
        """Calculate memory stability for FSRS."""
        # Simplified stability calculation
        base_stability = entry.interval_days
        if entry.repetition_count > 0:
            success_rate = entry.success_rate
            stability_factor = 1.0 + success_rate * performance_rating
            return base_stability * stability_factor
        return base_stability

    def _estimate_sm2_retention(
        self,
        interval_days: int,
        ease_factor: float
    ) -> float:
        """Estimate retention probability for SM-2."""
        # Simple model based on interval and ease
        decay_rate = 1.0 / (interval_days * ease_factor)
        return math.exp(-decay_rate)

    async def _calculate_retention_impact(
        self,
        entry: LearningMemoryEntry
    ) -> float:
        """Calculate impact of reviewing this entry on overall retention."""
        current_retention = await self.predict_retention(entry, 0)
        future_retention = await self.predict_retention(entry, 7)  # 7 days ahead

        # Impact is the retention loss that would be prevented
        impact = current_retention - future_retention

        # Weight by importance
        return impact * entry.importance

    def get_algorithm_stats(self) -> Dict[str, Any]:
        """Get statistics about the spaced repetition algorithm."""
        return {
            "algorithm": self.algorithm,
            "initial_ease": self.initial_ease,
            "parameters": {
                "sm2": self.sm2_params,
                "fsrs": self.fsrs_params
            }
        }