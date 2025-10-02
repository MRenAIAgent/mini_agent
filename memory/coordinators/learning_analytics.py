"""Learning analytics across all memory types.

Provides comprehensive analytics and insights by combining data from
episodic, semantic, profile, interaction, and learning graph memory.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..system.learning_memory_system import LearningMemorySystem


class LearningAnalytics:
    """Provides analytics across all memory types.

    Analyzes and synthesizes information from all memory systems to provide:
    - Learning trajectory analysis
    - Comprehensive learning plans
    - Progress tracking
    - Performance insights
    """

    def __init__(self, learning_system: 'LearningMemorySystem'):
        """Initialize learning analytics.

        Args:
            learning_system: Reference to the learning memory system
        """
        self.system = learning_system

    async def generate_learning_trajectory(
        self,
        user_id: str,
        episodic_patterns: Dict[str, Any],
        semantic_gaps: List[Dict[str, Any]],
        profile_insights: Dict[str, Any],
        interaction_patterns: List[Dict[str, Any]],
        learning_graph_analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall learning trajectory analysis.

        Synthesizes data from all memory types to create a comprehensive
        view of the user's learning journey.

        Args:
            user_id: User identifier
            episodic_patterns: Patterns from episodic memory
            semantic_gaps: Knowledge gaps from semantic memory
            profile_insights: Insights from user profile
            interaction_patterns: Patterns from interaction history
            learning_graph_analytics: Analytics from learning graph

        Returns:
            Comprehensive learning trajectory analysis
        """

        return {
            'user_id': user_id,
            'learning_velocity': learning_graph_analytics.get('learning_velocity', 0),
            'knowledge_growth': len(semantic_gaps),
            'engagement_trend': episodic_patterns.get('daily_activity', {}),
            'preferred_learning_modes': profile_insights.get('preferences', {}),
            'communication_effectiveness': len(interaction_patterns),
            'next_milestones': learning_graph_analytics.get('breakthrough_concepts', []),
            'trajectory_timestamp': datetime.now().isoformat(),
            'summary': self._generate_trajectory_summary(
                learning_graph_analytics,
                episodic_patterns,
                profile_insights
            )
        }

    def _generate_trajectory_summary(
        self,
        graph_analytics: Dict[str, Any],
        episodic_patterns: Dict[str, Any],
        profile_insights: Dict[str, Any]
    ) -> str:
        """Generate human-readable trajectory summary.

        Args:
            graph_analytics: Learning graph analytics
            episodic_patterns: Episodic memory patterns
            profile_insights: Profile insights

        Returns:
            Summary text
        """
        velocity = graph_analytics.get('learning_velocity', 0)
        activity_level = len(episodic_patterns.get('daily_activity', {}))

        if velocity > 1.5:
            pace = "excellent"
        elif velocity > 0.8:
            pace = "good"
        else:
            pace = "steady"

        learning_style = (profile_insights.get('learning_style') or {}).get('primary', 'balanced')
        return (
            f"Learning at a {pace} pace with {activity_level} days of recent activity. "
            f"Preferred learning style: {learning_style}."
        )

    async def generate_learning_plan(
        self,
        user_id: str,
        learning_goal: str,
        profile: Dict[str, Any],
        analytics: Optional[Dict[str, Any]],
        next_concepts: List[Dict[str, Any]],
        timeline_days: int
    ) -> Dict[str, Any]:
        """Generate comprehensive learning plan.

        Creates a personalized learning plan based on:
        - User's learning goal
        - Current skill level and velocity
        - Learning preferences
        - Available concepts
        - Timeline constraints

        Args:
            user_id: User identifier
            learning_goal: High-level learning goal
            profile: User profile data
            analytics: Current learning analytics (can be None)
            next_concepts: Available next concepts
            timeline_days: Timeline in days

        Returns:
            Comprehensive learning plan
        """

        # Calculate concepts per week based on learning velocity
        velocity = (analytics or {}).get('learning_velocity', 1.0)  # concepts per hour
        concepts_per_week = max(1, int(velocity * 10))  # Assume 10 hours per week

        weeks = timeline_days // 7
        total_concepts = min(len(next_concepts), concepts_per_week * weeks)

        # Generate weekly milestones
        milestones = []
        for week_num in range(min(weeks, (len(next_concepts) // concepts_per_week) + 1)):
            start_idx = week_num * concepts_per_week
            end_idx = min((week_num + 1) * concepts_per_week, len(next_concepts))

            if start_idx < len(next_concepts):
                milestones.append({
                    'week': week_num + 1,
                    'concepts': next_concepts[start_idx:end_idx],
                    'estimated_hours': len(next_concepts[start_idx:end_idx]) / velocity
                })

        return {
            'user_id': user_id,
            'goal': learning_goal,
            'timeline_days': timeline_days,
            'recommended_concepts': next_concepts[:total_concepts],
            'weekly_schedule': {
                'concepts_per_week': concepts_per_week,
                'estimated_hours_per_week': 10,
                'recommended_session_length': 60,  # minutes
                'sessions_per_week': self._calculate_sessions_per_week(
                    concepts_per_week,
                    profile
                )
            },
            'personalization': {
                'preferred_difficulty': profile.get('preferences', {}).get(
                    'difficulty_preference',
                    'medium'
                ),
                'learning_style_adaptations': profile.get('learning_style', {}),
                'motivational_factors': profile.get('active_goals', []),
                'best_learning_times': profile.get('preferences', {}).get(
                    'preferred_times',
                    []
                )
            },
            'milestones': milestones,
            'success_indicators': self._define_success_indicators(analytics, profile),
            'plan_generated_at': datetime.now().isoformat()
        }

    def _calculate_sessions_per_week(
        self,
        concepts_per_week: int,
        profile: Dict[str, Any]
    ) -> int:
        """Calculate recommended sessions per week.

        Args:
            concepts_per_week: Target concepts per week
            profile: User profile

        Returns:
            Recommended number of sessions per week
        """
        # Base calculation on concepts and session preferences
        preferred_session_length = profile.get('preferences', {}).get(
            'session_length_minutes',
            60
        )

        if preferred_session_length <= 30:
            return concepts_per_week * 2  # Short sessions, more frequent
        elif preferred_session_length >= 90:
            return max(2, concepts_per_week // 2)  # Long sessions, less frequent
        else:
            return concepts_per_week  # One concept per session

    def _define_success_indicators(
        self,
        analytics: Optional[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Define success indicators for the plan.

        Args:
            analytics: Current analytics (can be None)
            profile: User profile

        Returns:
            List of success indicators with targets
        """
        current_velocity = (analytics or {}).get('learning_velocity', 1.0)

        return [
            {
                'indicator': 'learning_velocity',
                'current': current_velocity,
                'target': current_velocity * 1.2,  # 20% improvement
                'unit': 'concepts/hour'
            },
            {
                'indicator': 'mastery_rate',
                'current': (analytics or {}).get('avg_mastery', 0.7),
                'target': 0.8,
                'unit': 'score'
            },
            {
                'indicator': 'engagement',
                'current': len(analytics.get('recent_sessions', [])),
                'target': 5,  # 5 sessions per week
                'unit': 'sessions/week'
            },
            {
                'indicator': 'retention',
                'current': analytics.get('retention_rate', 0.7),
                'target': 0.85,
                'unit': 'percentage'
            }
        ]

    async def analyze_progress(
        self,
        user_id: str,
        plan: Dict[str, Any],
        current_analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze progress against a learning plan.

        Args:
            user_id: User identifier
            plan: Original learning plan
            current_analytics: Current analytics

        Returns:
            Progress analysis
        """
        # Calculate completion percentage
        total_concepts = len(plan.get('recommended_concepts', []))
        completed_concepts = current_analytics.get('concepts_mastered', 0)
        completion_rate = completed_concepts / total_concepts if total_concepts > 0 else 0

        # Compare against success indicators
        indicator_progress = []
        for indicator in plan.get('success_indicators', []):
            current = current_analytics.get(indicator['indicator'], 0)
            target = indicator['target']
            progress = (current / target) if target > 0 else 0

            indicator_progress.append({
                'indicator': indicator['indicator'],
                'progress': min(1.0, progress),
                'on_track': progress >= 0.8,  # 80% of target considered on track
                'current_value': current,
                'target_value': target
            })

        return {
            'user_id': user_id,
            'overall_completion': completion_rate,
            'concepts_completed': completed_concepts,
            'concepts_remaining': total_concepts - completed_concepts,
            'on_schedule': completion_rate >= 0.8,  # Within 20% of expected
            'indicator_progress': indicator_progress,
            'recommendations': self._generate_progress_recommendations(
                completion_rate,
                indicator_progress,
                current_analytics
            ),
            'analyzed_at': datetime.now().isoformat()
        }

    def _generate_progress_recommendations(
        self,
        completion_rate: float,
        indicator_progress: List[Dict[str, Any]],
        analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on progress.

        Args:
            completion_rate: Overall completion rate
            indicator_progress: Progress on each indicator
            analytics: Current analytics

        Returns:
            List of recommendations
        """
        recommendations = []

        if completion_rate < 0.5:
            recommendations.append(
                "Consider increasing study time to stay on track with your goals"
            )

        # Check each indicator
        for indicator in indicator_progress:
            if not indicator['on_track']:
                if indicator['indicator'] == 'learning_velocity':
                    recommendations.append(
                        "Try shorter, more focused study sessions to improve learning velocity"
                    )
                elif indicator['indicator'] == 'engagement':
                    recommendations.append(
                        "Increase session frequency to maintain engagement"
                    )
                elif indicator['indicator'] == 'retention':
                    recommendations.append(
                        "Add more review sessions to improve retention"
                    )

        if not recommendations:
            recommendations.append("Great progress! Keep up the excellent work")

        return recommendations
