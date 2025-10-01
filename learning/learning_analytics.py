"""Learning analytics for tracking progress and generating insights."""

import asyncio
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass

from .data_models import (
    LearningSession,
    StudentProfile,
    MasteryRecord,
    MasteryLevel,
    DifficultyLevel,
    LearningStyle
)


@dataclass
class LearningInsight:
    """A single learning insight or recommendation."""

    insight_type: str
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    priority: str  # "high", "medium", "low"
    actionable_recommendations: List[str]
    supporting_data: Dict[str, Any]


@dataclass
class ProgressMetrics:
    """Comprehensive progress tracking metrics."""

    user_id: str
    time_period_days: int

    # Session metrics
    total_sessions: int
    total_study_time_minutes: int
    average_session_length_minutes: float
    session_frequency_per_week: float

    # Performance metrics
    overall_accuracy: float
    average_response_time_seconds: float
    improvement_rate: float

    # Mastery metrics
    concepts_learned: int
    concepts_mastered: int
    mastery_velocity: float  # Concepts per week

    # Engagement metrics
    consistency_score: float  # How regular the learning pattern is
    streak_days: int
    engagement_trend: str  # "improving", "stable", "declining"


class LearningAnalytics:
    """
    Comprehensive learning analytics system for tracking progress,
    identifying patterns, and generating actionable insights.
    """

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize learning analytics system.

        Args:
            storage_backend: Optional backend for persistent storage
        """
        self.storage_backend = storage_backend
        self._sessions_cache: Dict[str, List[LearningSession]] = {}
        self._insights_cache: Dict[str, List[LearningInsight]] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def record_session(self, session: LearningSession) -> bool:
        """
        Record a completed learning session for analytics.

        Args:
            session: Completed learning session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Store session data
            if self.storage_backend:
                await self.storage_backend.store_learning_session(session)

            # Update local cache
            if session.user_id not in self._sessions_cache:
                self._sessions_cache[session.user_id] = []

            self._sessions_cache[session.user_id].append(session)

            # Keep only recent sessions in cache (last 100)
            self._sessions_cache[session.user_id] = \
                self._sessions_cache[session.user_id][-100:]

            # Invalidate insights cache for this user
            self._invalidate_user_cache(session.user_id)

            return True

        except Exception as e:
            print(f"Error recording session for analytics: {e}")
            return False

    async def get_user_analytics(
        self,
        user_id: str,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user.

        Args:
            user_id: User identifier
            time_range_days: Number of days to include in analysis

        Returns:
            Dictionary containing comprehensive analytics
        """
        try:
            # Get user sessions
            sessions = await self._get_user_sessions(user_id, time_range_days)

            if not sessions:
                return self._empty_analytics_response(user_id)

            # Calculate progress metrics
            progress_metrics = await self._calculate_progress_metrics(
                user_id, sessions, time_range_days
            )

            # Generate learning insights
            insights = await self._generate_learning_insights(user_id, sessions)

            # Calculate learning patterns
            patterns = await self._analyze_learning_patterns(sessions)

            # Performance trends
            trends = await self._analyze_performance_trends(sessions)

            # Concept mastery analysis
            mastery_analysis = await self._analyze_concept_mastery(sessions)

            return {
                "user_id": user_id,
                "time_range_days": time_range_days,
                "generated_at": datetime.now().isoformat(),
                "progress_metrics": progress_metrics.__dict__,
                "learning_insights": [insight.__dict__ for insight in insights],
                "learning_patterns": patterns,
                "performance_trends": trends,
                "concept_mastery": mastery_analysis
            }

        except Exception as e:
            print(f"Error getting user analytics: {e}")
            return self._empty_analytics_response(user_id)

    async def get_learning_insights(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[LearningInsight]:
        """
        Get personalized learning insights for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of insights to return

        Returns:
            List of learning insights
        """
        # Check cache first
        cache_key = f"{user_id}_insights"
        if (cache_key in self._insights_cache and
            cache_key in self._cache_expiry and
            datetime.now() < self._cache_expiry[cache_key]):
            return self._insights_cache[cache_key][:limit]

        try:
            sessions = await self._get_user_sessions(user_id, 30)
            insights = await self._generate_learning_insights(user_id, sessions)

            # Cache insights for 1 hour
            self._insights_cache[cache_key] = insights
            self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)

            return insights[:limit]

        except Exception as e:
            print(f"Error generating learning insights: {e}")
            return []

    async def get_comparative_analytics(
        self,
        user_id: str,
        comparison_group: str = "all_users"
    ) -> Dict[str, Any]:
        """
        Get analytics comparing user performance to a group.

        Args:
            user_id: User identifier
            comparison_group: Group to compare against

        Returns:
            Comparative analytics data
        """
        try:
            user_analytics = await self.get_user_analytics(user_id)

            # Get comparison data (simplified - would need actual group data)
            comparison_data = await self._get_comparison_benchmarks(comparison_group)

            # Calculate percentiles and comparisons
            comparisons = {
                "accuracy_percentile": self._calculate_percentile(
                    user_analytics["progress_metrics"]["overall_accuracy"],
                    comparison_data["accuracy_distribution"]
                ),
                "study_time_percentile": self._calculate_percentile(
                    user_analytics["progress_metrics"]["total_study_time_minutes"],
                    comparison_data["study_time_distribution"]
                ),
                "mastery_rate_percentile": self._calculate_percentile(
                    user_analytics["progress_metrics"]["mastery_velocity"],
                    comparison_data["mastery_rate_distribution"]
                ),
                "strengths": await self._identify_relative_strengths(
                    user_analytics, comparison_data
                ),
                "improvement_areas": await self._identify_improvement_areas(
                    user_analytics, comparison_data
                )
            }

            return {
                "user_id": user_id,
                "comparison_group": comparison_group,
                "comparisons": comparisons,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error getting comparative analytics: {e}")
            return {}

    async def predict_performance(
        self,
        user_id: str,
        concept_id: str,
        days_ahead: int = 7
    ) -> Dict[str, float]:
        """
        Predict user performance for a specific concept.

        Args:
            user_id: User identifier
            concept_id: Concept identifier
            days_ahead: Number of days to predict ahead

        Returns:
            Dictionary with performance predictions
        """
        try:
            sessions = await self._get_user_sessions(user_id, 60)

            # Filter sessions for this concept
            concept_sessions = [
                s for s in sessions
                if concept_id in s.concepts_studied
            ]

            if len(concept_sessions) < 3:
                return {"confidence": 0.0, "predicted_accuracy": 0.5}

            # Simple trend analysis
            recent_accuracy = []
            for session in concept_sessions[-10:]:  # Last 10 sessions
                recent_accuracy.append(session.success_rate)

            # Calculate trend
            if len(recent_accuracy) >= 3:
                trend = self._calculate_trend(recent_accuracy)
                current_avg = statistics.mean(recent_accuracy[-3:])

                # Project forward
                predicted_accuracy = max(0.0, min(1.0, current_avg + trend * days_ahead))
                confidence = min(1.0, len(concept_sessions) / 10.0)

                return {
                    "predicted_accuracy": predicted_accuracy,
                    "confidence": confidence,
                    "trend": trend,
                    "current_accuracy": current_avg
                }

            return {"confidence": 0.3, "predicted_accuracy": statistics.mean(recent_accuracy)}

        except Exception as e:
            print(f"Error predicting performance: {e}")
            return {"confidence": 0.0, "predicted_accuracy": 0.5}

    async def identify_optimal_study_time(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Identify optimal study times for a user based on performance patterns.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with optimal study time recommendations
        """
        try:
            sessions = await self._get_user_sessions(user_id, 30)

            if len(sessions) < 5:
                return {"recommendation": "insufficient_data"}

            # Analyze performance by time of day
            hourly_performance = defaultdict(list)
            for session in sessions:
                hour = session.start_time.hour
                hourly_performance[hour].append(session.success_rate)

            # Find best performing hours
            hour_averages = {}
            for hour, performances in hourly_performance.items():
                if len(performances) >= 2:  # At least 2 sessions
                    hour_averages[hour] = statistics.mean(performances)

            if not hour_averages:
                return {"recommendation": "insufficient_data"}

            # Find optimal hours
            sorted_hours = sorted(
                hour_averages.items(),
                key=lambda x: x[1],
                reverse=True
            )

            optimal_hours = [hour for hour, _ in sorted_hours[:3]]

            # Analyze session length patterns
            optimal_duration = await self._find_optimal_session_duration(sessions)

            return {
                "optimal_hours": optimal_hours,
                "optimal_duration_minutes": optimal_duration,
                "performance_by_hour": dict(hour_averages),
                "confidence": min(1.0, len(sessions) / 20.0)
            }

        except Exception as e:
            print(f"Error identifying optimal study time: {e}")
            return {"recommendation": "error"}

    # Private helper methods

    async def _get_user_sessions(
        self,
        user_id: str,
        days_back: int
    ) -> List[LearningSession]:
        """Get user sessions from cache or storage."""
        # Check cache first
        if user_id in self._sessions_cache:
            cached_sessions = self._sessions_cache[user_id]
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return [
                s for s in cached_sessions
                if s.start_time >= cutoff_date
            ]

        # Load from storage if available
        if self.storage_backend:
            try:
                sessions = await self.storage_backend.get_user_sessions(
                    user_id, days_back
                )
                self._sessions_cache[user_id] = sessions
                return sessions
            except Exception:
                pass

        return []

    async def _calculate_progress_metrics(
        self,
        user_id: str,
        sessions: List[LearningSession],
        time_range_days: int
    ) -> ProgressMetrics:
        """Calculate comprehensive progress metrics."""
        if not sessions:
            return ProgressMetrics(
                user_id=user_id,
                time_period_days=time_range_days,
                total_sessions=0,
                total_study_time_minutes=0,
                average_session_length_minutes=0,
                session_frequency_per_week=0,
                overall_accuracy=0,
                average_response_time_seconds=0,
                improvement_rate=0,
                concepts_learned=0,
                concepts_mastered=0,
                mastery_velocity=0,
                consistency_score=0,
                streak_days=0,
                engagement_trend="stable"
            )

        # Basic session metrics
        total_sessions = len(sessions)
        total_study_time = sum(
            s.duration_minutes for s in sessions
            if s.duration_minutes
        )
        avg_session_length = total_study_time / total_sessions if total_sessions > 0 else 0

        # Session frequency
        session_frequency = (total_sessions / time_range_days) * 7  # Per week

        # Performance metrics
        overall_accuracy = statistics.mean([s.success_rate for s in sessions])
        avg_response_time = statistics.mean([
            s.average_response_time for s in sessions
            if s.average_response_time
        ]) if any(s.average_response_time for s in sessions) else 0

        # Improvement rate
        improvement_rate = self._calculate_improvement_rate(sessions)

        # Concept metrics
        all_concepts = set()
        mastered_concepts = set()
        for session in sessions:
            all_concepts.update(session.concepts_studied)
            mastered_concepts.update(session.mastery_improvements.keys())

        concepts_learned = len(all_concepts)
        concepts_mastered = len(mastered_concepts)
        mastery_velocity = (concepts_mastered / time_range_days) * 7  # Per week

        # Engagement metrics
        consistency_score = self._calculate_consistency_score(sessions)
        streak_days = self._calculate_current_streak(sessions)
        engagement_trend = self._calculate_engagement_trend(sessions)

        return ProgressMetrics(
            user_id=user_id,
            time_period_days=time_range_days,
            total_sessions=total_sessions,
            total_study_time_minutes=int(total_study_time),
            average_session_length_minutes=avg_session_length,
            session_frequency_per_week=session_frequency,
            overall_accuracy=overall_accuracy,
            average_response_time_seconds=avg_response_time,
            improvement_rate=improvement_rate,
            concepts_learned=concepts_learned,
            concepts_mastered=concepts_mastered,
            mastery_velocity=mastery_velocity,
            consistency_score=consistency_score,
            streak_days=streak_days,
            engagement_trend=engagement_trend
        )

    async def _generate_learning_insights(
        self,
        user_id: str,
        sessions: List[LearningSession]
    ) -> List[LearningInsight]:
        """Generate personalized learning insights."""
        insights = []

        if len(sessions) < 3:
            return insights

        # Performance trend insight
        performance_trend = self._calculate_improvement_rate(sessions)
        if performance_trend > 0.1:
            insights.append(LearningInsight(
                insight_type="performance_trend",
                title="Strong Learning Progress",
                description=f"Your performance has improved by {performance_trend*100:.1f}% over recent sessions.",
                confidence=0.8,
                priority="high",
                actionable_recommendations=[
                    "Continue your current study routine",
                    "Consider tackling more challenging content",
                    "Share your success with others for motivation"
                ],
                supporting_data={"improvement_rate": performance_trend}
            ))
        elif performance_trend < -0.1:
            insights.append(LearningInsight(
                insight_type="performance_decline",
                title="Performance Needs Attention",
                description="Your recent performance shows a declining trend.",
                confidence=0.7,
                priority="high",
                actionable_recommendations=[
                    "Review fundamentals in challenging areas",
                    "Take breaks to avoid burnout",
                    "Consider adjusting study schedule"
                ],
                supporting_data={"decline_rate": abs(performance_trend)}
            ))

        # Study pattern insights
        consistency_score = self._calculate_consistency_score(sessions)
        if consistency_score < 0.5:
            insights.append(LearningInsight(
                insight_type="consistency",
                title="Improve Study Consistency",
                description="More regular study sessions could improve your learning outcomes.",
                confidence=0.6,
                priority="medium",
                actionable_recommendations=[
                    "Set a regular study schedule",
                    "Use reminders to maintain consistency",
                    "Start with shorter, more frequent sessions"
                ],
                supporting_data={"consistency_score": consistency_score}
            ))

        # Optimal study time insight
        optimal_times = await self.identify_optimal_study_time(user_id)
        if optimal_times.get("optimal_hours"):
            insights.append(LearningInsight(
                insight_type="optimal_timing",
                title="Best Study Times Identified",
                description=f"You perform best when studying around {optimal_times['optimal_hours'][0]}:00.",
                confidence=optimal_times.get("confidence", 0.5),
                priority="medium",
                actionable_recommendations=[
                    f"Schedule important study sessions around {optimal_times['optimal_hours'][0]}:00",
                    "Avoid scheduling difficult content during low-performance hours"
                ],
                supporting_data=optimal_times
            ))

        return sorted(insights, key=lambda x: (x.priority == "high", x.confidence), reverse=True)

    async def _analyze_learning_patterns(
        self,
        sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze learning patterns from session data."""
        if not sessions:
            return {}

        # Time patterns
        session_hours = [s.start_time.hour for s in sessions]
        preferred_times = Counter(session_hours).most_common(3)

        # Duration patterns
        durations = [s.duration_minutes for s in sessions if s.duration_minutes]
        avg_duration = statistics.mean(durations) if durations else 0

        # Difficulty progression
        difficulty_patterns = defaultdict(list)
        for session in sessions:
            for difficulty in session.difficulty_levels_attempted:
                difficulty_patterns[difficulty.name].append(session.success_rate)

        return {
            "preferred_study_times": [{"hour": hour, "frequency": freq} for hour, freq in preferred_times],
            "average_session_duration": avg_duration,
            "difficulty_performance": {
                diff: statistics.mean(perfs) for diff, perfs in difficulty_patterns.items()
            }
        }

    async def _analyze_performance_trends(
        self,
        sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(sessions) < 3:
            return {}

        # Sort sessions by time
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)

        # Calculate rolling averages
        window_size = min(5, len(sorted_sessions) // 2)
        rolling_accuracies = []
        rolling_times = []

        for i in range(window_size, len(sorted_sessions) + 1):
            window_sessions = sorted_sessions[i-window_size:i]
            avg_accuracy = statistics.mean([s.success_rate for s in window_sessions])
            rolling_accuracies.append(avg_accuracy)
            rolling_times.append(window_sessions[-1].start_time.isoformat())

        # Overall trend
        if len(rolling_accuracies) >= 2:
            trend_slope = (rolling_accuracies[-1] - rolling_accuracies[0]) / len(rolling_accuracies)
        else:
            trend_slope = 0

        return {
            "rolling_accuracy": list(zip(rolling_times, rolling_accuracies)),
            "trend_slope": trend_slope,
            "trend_direction": "improving" if trend_slope > 0.01 else "declining" if trend_slope < -0.01 else "stable"
        }

    async def _analyze_concept_mastery(
        self,
        sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze concept mastery progression."""
        concept_progress = defaultdict(list)

        for session in sessions:
            for concept in session.concepts_studied:
                concept_progress[concept].append({
                    "timestamp": session.start_time.isoformat(),
                    "success_rate": session.success_rate
                })

        # Calculate mastery indicators
        mastery_summary = {}
        for concept, progress in concept_progress.items():
            if len(progress) >= 2:
                recent_performance = statistics.mean([
                    p["success_rate"] for p in progress[-3:]
                ])
                improvement = (
                    progress[-1]["success_rate"] - progress[0]["success_rate"]
                )

                mastery_summary[concept] = {
                    "sessions_count": len(progress),
                    "recent_performance": recent_performance,
                    "overall_improvement": improvement,
                    "mastery_level": self._estimate_mastery_level(recent_performance)
                }

        return mastery_summary

    def _calculate_improvement_rate(self, sessions: List[LearningSession]) -> float:
        """Calculate performance improvement rate."""
        if len(sessions) < 3:
            return 0.0

        # Compare first third with last third
        sessions_sorted = sorted(sessions, key=lambda s: s.start_time)
        third_size = len(sessions_sorted) // 3

        if third_size == 0:
            return 0.0

        early_performance = statistics.mean([
            s.success_rate for s in sessions_sorted[:third_size]
        ])
        recent_performance = statistics.mean([
            s.success_rate for s in sessions_sorted[-third_size:]
        ])

        return recent_performance - early_performance

    def _calculate_consistency_score(self, sessions: List[LearningSession]) -> float:
        """Calculate study consistency score."""
        if len(sessions) < 2:
            return 0.0

        # Calculate gaps between sessions
        session_dates = sorted([s.start_time.date() for s in sessions])
        gaps = []

        for i in range(1, len(session_dates)):
            gap = (session_dates[i] - session_dates[i-1]).days
            gaps.append(gap)

        if not gaps:
            return 1.0

        # Lower variance in gaps = higher consistency
        gap_variance = statistics.variance(gaps) if len(gaps) > 1 else 0
        consistency = max(0.0, 1.0 - (gap_variance / 10.0))  # Normalize

        return consistency

    def _calculate_current_streak(self, sessions: List[LearningSession]) -> int:
        """Calculate current learning streak in days."""
        if not sessions:
            return 0

        session_dates = sorted(set(s.start_time.date() for s in sessions), reverse=True)
        today = datetime.now().date()

        # Check if studied today or yesterday
        if not session_dates or (today - session_dates[0]).days > 1:
            return 0

        # Count consecutive days
        streak = 0
        expected_date = session_dates[0]

        for date in session_dates:
            if date == expected_date:
                streak += 1
                expected_date = date - timedelta(days=1)
            else:
                break

        return streak

    def _calculate_engagement_trend(self, sessions: List[LearningSession]) -> str:
        """Calculate engagement trend over time."""
        if len(sessions) < 6:
            return "stable"

        # Compare recent vs earlier engagement
        sessions_sorted = sorted(sessions, key=lambda s: s.start_time)
        half_point = len(sessions_sorted) // 2

        earlier_sessions = sessions_sorted[:half_point]
        recent_sessions = sessions_sorted[half_point:]

        earlier_freq = len(earlier_sessions) / 15  # Assume 15-day periods
        recent_freq = len(recent_sessions) / 15

        if recent_freq > earlier_freq * 1.2:
            return "improving"
        elif recent_freq < earlier_freq * 0.8:
            return "declining"
        else:
            return "stable"

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend in a series of values."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        sum_x = n * (n - 1) // 2  # Sum of indices
        sum_y = sum(values)
        sum_xy = sum(i * val for i, val in enumerate(values))
        sum_x_squared = sum(i * i for i in range(n))

        # Linear regression slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
        return slope

    async def _find_optimal_session_duration(
        self,
        sessions: List[LearningSession]
    ) -> int:
        """Find optimal session duration based on performance."""
        duration_performance = defaultdict(list)

        for session in sessions:
            if session.duration_minutes:
                # Group into duration buckets
                bucket = (session.duration_minutes // 15) * 15  # 15-minute buckets
                duration_performance[bucket].append(session.success_rate)

        if not duration_performance:
            return 30  # Default

        # Find duration with best average performance
        best_duration = max(
            duration_performance.items(),
            key=lambda x: statistics.mean(x[1]) if len(x[1]) >= 2 else 0
        )[0]

        return int(best_duration)

    def _estimate_mastery_level(self, performance: float) -> str:
        """Estimate mastery level from performance score."""
        if performance >= 0.9:
            return "mastered"
        elif performance >= 0.75:
            return "proficient"
        elif performance >= 0.6:
            return "developing"
        elif performance >= 0.4:
            return "introduced"
        else:
            return "unknown"

    def _empty_analytics_response(self, user_id: str) -> Dict[str, Any]:
        """Return empty analytics response for insufficient data."""
        return {
            "user_id": user_id,
            "message": "Insufficient data for analytics",
            "generated_at": datetime.now().isoformat()
        }

    def _invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate cached data for a user."""
        cache_key = f"{user_id}_insights"
        if cache_key in self._insights_cache:
            del self._insights_cache[cache_key]
        if cache_key in self._cache_expiry:
            del self._cache_expiry[cache_key]

    async def _get_comparison_benchmarks(
        self,
        group: str
    ) -> Dict[str, List[float]]:
        """Get benchmark data for comparison (simplified)."""
        # In production, this would query actual group statistics
        return {
            "accuracy_distribution": [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9],
            "study_time_distribution": [60, 90, 120, 150, 180, 210, 240],
            "mastery_rate_distribution": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        }

    def _calculate_percentile(self, value: float, distribution: List[float]) -> float:
        """Calculate percentile of value in distribution."""
        if not distribution:
            return 50.0

        sorted_dist = sorted(distribution)
        position = 0

        for i, val in enumerate(sorted_dist):
            if value <= val:
                position = i
                break
        else:
            position = len(sorted_dist) - 1

        return (position / len(sorted_dist)) * 100

    async def _identify_relative_strengths(
        self,
        user_analytics: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> List[str]:
        """Identify user's relative strengths."""
        strengths = []

        # Simplified strength identification
        accuracy = user_analytics["progress_metrics"]["overall_accuracy"]
        if accuracy > 0.8:
            strengths.append("High accuracy performance")

        consistency = user_analytics["progress_metrics"]["consistency_score"]
        if consistency > 0.7:
            strengths.append("Consistent study habits")

        return strengths

    async def _identify_improvement_areas(
        self,
        user_analytics: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> List[str]:
        """Identify areas for improvement."""
        areas = []

        # Simplified improvement area identification
        accuracy = user_analytics["progress_metrics"]["overall_accuracy"]
        if accuracy < 0.6:
            areas.append("Accuracy could be improved")

        frequency = user_analytics["progress_metrics"]["session_frequency_per_week"]
        if frequency < 2:
            areas.append("More frequent study sessions recommended")

        return areas