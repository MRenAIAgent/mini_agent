"""User profile memory manager for learner characteristics and preferences."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from .memory_manager import CoreMemoryManager
from .memory_store import MemoryEntry


class UserProfileMemoryManager(CoreMemoryManager):
    """
    User profile memory manager that extends CoreMemoryManager for learner characteristics.

    Handles storage and retrieval of user preferences, learning styles,
    performance patterns, and personalization data.
    """

    def __init__(self, **kwargs):
        """Initialize user profile memory manager."""
        super().__init__(**kwargs)
        self.memory_type = "user_profile"

    async def store_learning_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: Union[str, float, bool, Dict],
        confidence: float = 1.0,
        source: str = "explicit",
        importance: float = 0.8,
        **metadata
    ) -> bool:
        """
        Store a learning preference for a user.

        Args:
            user_id: User identifier
            preference_type: Type of preference (e.g., 'learning_style', 'pace', 'explanation_detail')
            preference_value: The preference value
            confidence: Confidence in this preference (0.0 to 1.0)
            source: Source of preference ('explicit', 'inferred', 'observed')
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        profile_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'preference',
            'user_id': user_id,
            'preference_type': preference_type,
            'preference_value': preference_value,
            'confidence': confidence,
            'source': source,
            'updated_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"User {user_id} preference: {preference_type} = {preference_value} (confidence: {confidence:.2f})"

        return await self.store_memory(
            content=content,
            importance=importance,
            **profile_metadata
        )

    async def store_learning_style(
        self,
        user_id: str,
        style_dimensions: Dict[str, float],
        assessment_method: str = "observed",
        confidence: float = 0.8,
        **metadata
    ) -> bool:
        """
        Store learning style assessment for a user.

        Args:
            user_id: User identifier
            style_dimensions: Dictionary of learning style dimensions and scores
                             (e.g., {'visual': 0.8, 'auditory': 0.3, 'kinesthetic': 0.6})
            assessment_method: Method used to assess style ('test', 'observed', 'self_reported')
            confidence: Confidence in the assessment
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        profile_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_style',
            'user_id': user_id,
            'style_dimensions': style_dimensions,
            'assessment_method': assessment_method,
            'confidence': confidence,
            'assessed_at': datetime.now().isoformat(),
            **metadata
        }

        # Create readable content
        style_description = ", ".join([f"{dim}: {score:.2f}" for dim, score in style_dimensions.items()])
        content = f"Learning style for {user_id}: {style_description} (method: {assessment_method})"

        return await self.store_memory(
            content=content,
            importance=0.9,
            **profile_metadata
        )

    async def store_performance_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        time_period: str,
        confidence: float = 0.8,
        **metadata
    ) -> bool:
        """
        Store identified performance patterns for a user.

        Args:
            user_id: User identifier
            pattern_type: Type of pattern (e.g., 'peak_hours', 'difficulty_progression', 'topic_affinity')
            pattern_data: Dictionary containing pattern details
            time_period: Time period for the pattern (e.g., 'daily', 'weekly', 'monthly')
            confidence: Confidence in the pattern
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        profile_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'performance_pattern',
            'user_id': user_id,
            'pattern_type': pattern_type,
            'pattern_data': pattern_data,
            'time_period': time_period,
            'confidence': confidence,
            'identified_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Performance pattern for {user_id}: {pattern_type} over {time_period} - {str(pattern_data)}"

        return await self.store_memory(
            content=content,
            importance=0.7,
            **profile_metadata
        )

    async def store_knowledge_assessment(
        self,
        user_id: str,
        domain: str,
        skill_levels: Dict[str, float],
        assessment_date: Optional[datetime] = None,
        assessment_method: str = "performance_based",
        **metadata
    ) -> bool:
        """
        Store knowledge/skill assessment for a user in a domain.

        Args:
            user_id: User identifier
            domain: Subject domain (e.g., 'algebra', 'geometry')
            skill_levels: Dictionary of skills and proficiency levels (0.0 to 1.0)
            assessment_date: Date of assessment (defaults to now)
            assessment_method: Method used for assessment
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if assessment_date is None:
            assessment_date = datetime.now()

        profile_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'knowledge_assessment',
            'user_id': user_id,
            'domain': domain,
            'skill_levels': skill_levels,
            'assessment_date': assessment_date.isoformat(),
            'assessment_method': assessment_method,
            **metadata
        }

        # Create readable content
        skills_description = ", ".join([f"{skill}: {level:.2f}" for skill, level in skill_levels.items()])
        content = f"Knowledge assessment for {user_id} in {domain}: {skills_description}"

        return await self.store_memory(
            content=content,
            importance=0.9,
            **profile_metadata
        )

    async def store_goal(
        self,
        user_id: str,
        goal_type: str,
        goal_description: str,
        target_date: Optional[datetime] = None,
        priority: str = "medium",
        status: str = "active",
        **metadata
    ) -> bool:
        """
        Store a learning goal for a user.

        Args:
            user_id: User identifier
            goal_type: Type of goal (e.g., 'mastery', 'completion', 'improvement')
            goal_description: Description of the goal
            target_date: Optional target completion date
            priority: Priority level ('high', 'medium', 'low')
            status: Goal status ('active', 'completed', 'paused', 'abandoned')
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        profile_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'goal',
            'user_id': user_id,
            'goal_type': goal_type,
            'goal_description': goal_description,
            'target_date': target_date.isoformat() if target_date else None,
            'priority': priority,
            'status': status,
            'created_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Goal for {user_id}: {goal_description} (type: {goal_type}, priority: {priority})"

        return await self.store_memory(
            content=content,
            importance=0.8,
            **profile_metadata
        )

    async def get_user_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user preferences.

        Args:
            user_id: User identifier
            preference_type: Optional filter by preference type

        Returns:
            Dictionary of user preferences
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'preference',
            'user_id': user_id
        }

        if preference_type:
            filters['preference_type'] = preference_type

        preferences = await self.search_memory(
            query=f"user:{user_id} preference",
            limit=100,
            filters=filters
        )

        # Build preferences dictionary
        prefs_dict = {}
        for pref in preferences:
            pref_type = pref.metadata.get('preference_type')
            pref_value = pref.metadata.get('preference_value')
            confidence = pref.metadata.get('confidence', 1.0)
            source = pref.metadata.get('source', 'unknown')

            prefs_dict[pref_type] = {
                'value': pref_value,
                'confidence': confidence,
                'source': source,
                'updated_at': pref.metadata.get('updated_at')
            }

        return prefs_dict

    async def get_learning_style(
        self,
        user_id: str,
        latest_only: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get learning style assessment for a user.

        Args:
            user_id: User identifier
            latest_only: Whether to return only the most recent assessment

        Returns:
            Learning style data or None if not found
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'learning_style',
            'user_id': user_id
        }

        styles = await self.search_memory(
            query=f"user:{user_id} learning_style",
            limit=1 if latest_only else 10,
            filters=filters
        )

        if not styles:
            return None

        # Return the most recent style assessment
        style = styles[0]
        return {
            'style_dimensions': style.metadata.get('style_dimensions', {}),
            'assessment_method': style.metadata.get('assessment_method'),
            'confidence': style.metadata.get('confidence'),
            'assessed_at': style.metadata.get('assessed_at')
        }

    async def get_performance_patterns(
        self,
        user_id: str,
        pattern_type: Optional[str] = None,
        time_period: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get performance patterns for a user.

        Args:
            user_id: User identifier
            pattern_type: Optional filter by pattern type
            time_period: Optional filter by time period

        Returns:
            List of performance patterns
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'performance_pattern',
            'user_id': user_id
        }

        if pattern_type:
            filters['pattern_type'] = pattern_type

        if time_period:
            filters['time_period'] = time_period

        patterns = await self.search_memory(
            query=f"user:{user_id} performance_pattern",
            limit=50,
            filters=filters
        )

        return [
            {
                'pattern_type': pattern.metadata.get('pattern_type'),
                'pattern_data': pattern.metadata.get('pattern_data'),
                'time_period': pattern.metadata.get('time_period'),
                'confidence': pattern.metadata.get('confidence'),
                'identified_at': pattern.metadata.get('identified_at')
            }
            for pattern in patterns
        ]

    async def get_knowledge_assessment(
        self,
        user_id: str,
        domain: Optional[str] = None,
        latest_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge assessments for a user.

        Args:
            user_id: User identifier
            domain: Optional filter by domain
            latest_only: Whether to return only the most recent assessment per domain

        Returns:
            List of knowledge assessments
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'knowledge_assessment',
            'user_id': user_id
        }

        if domain:
            filters['domain'] = domain

        assessments = await self.search_memory(
            query=f"user:{user_id} knowledge_assessment",
            limit=100,
            filters=filters
        )

        # Group by domain if latest_only is True
        if latest_only:
            domain_assessments = {}
            for assessment in assessments:
                domain_key = assessment.metadata.get('domain')
                assessment_date = assessment.metadata.get('assessment_date')

                if domain_key not in domain_assessments or assessment_date > domain_assessments[domain_key]['assessment_date']:
                    domain_assessments[domain_key] = {
                        'domain': domain_key,
                        'skill_levels': assessment.metadata.get('skill_levels', {}),
                        'assessment_date': assessment_date,
                        'assessment_method': assessment.metadata.get('assessment_method')
                    }

            return list(domain_assessments.values())
        else:
            return [
                {
                    'domain': assessment.metadata.get('domain'),
                    'skill_levels': assessment.metadata.get('skill_levels', {}),
                    'assessment_date': assessment.metadata.get('assessment_date'),
                    'assessment_method': assessment.metadata.get('assessment_method')
                }
                for assessment in assessments
            ]

    async def get_active_goals(
        self,
        user_id: str,
        goal_type: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active learning goals for a user.

        Args:
            user_id: User identifier
            goal_type: Optional filter by goal type
            priority: Optional filter by priority

        Returns:
            List of active goals
        """
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'goal',
            'user_id': user_id,
            'status': 'active'
        }

        if goal_type:
            filters['goal_type'] = goal_type

        if priority:
            filters['priority'] = priority

        goals = await self.search_memory(
            query=f"user:{user_id} goal active",
            limit=50,
            filters=filters
        )

        return [
            {
                'goal_type': goal.metadata.get('goal_type'),
                'goal_description': goal.metadata.get('goal_description'),
                'target_date': goal.metadata.get('target_date'),
                'priority': goal.metadata.get('priority'),
                'status': goal.metadata.get('status'),
                'created_at': goal.metadata.get('created_at')
            }
            for goal in goals
        ]

    async def update_goal_status(
        self,
        user_id: str,
        goal_description: str,
        new_status: str,
        completion_notes: Optional[str] = None
    ) -> bool:
        """
        Update the status of a user's goal.

        Args:
            user_id: User identifier
            goal_description: Description of the goal to update
            new_status: New status ('completed', 'paused', 'abandoned', 'active')
            completion_notes: Optional notes about the status change

        Returns:
            True if successful, False otherwise
        """
        # Find the goal
        filters = {
            'memory_type': self.memory_type,
            'entry_type': 'goal',
            'user_id': user_id
        }

        goals = await self.search_memory(
            query=f"user:{user_id} goal {goal_description}",
            limit=10,
            filters=filters
        )

        # Find exact match
        target_goal = None
        for goal in goals:
            if goal.metadata.get('goal_description') == goal_description:
                target_goal = goal
                break

        if not target_goal:
            return False

        # Store status update
        update_metadata = {
            'memory_type': self.memory_type,
            'entry_type': 'goal_status_update',
            'user_id': user_id,
            'goal_description': goal_description,
            'old_status': target_goal.metadata.get('status'),
            'new_status': new_status,
            'completion_notes': completion_notes,
            'updated_at': datetime.now().isoformat()
        }

        content = f"Goal status update for {user_id}: '{goal_description}' changed to {new_status}"
        if completion_notes:
            content += f" - {completion_notes}"

        return await self.store_memory(
            content=content,
            importance=0.7,
            **update_metadata
        )

    async def get_user_profile_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a user's profile.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing user profile summary
        """
        # Gather all profile components
        preferences = await self.get_user_preferences(user_id)
        learning_style = await self.get_learning_style(user_id)
        patterns = await self.get_performance_patterns(user_id)
        assessments = await self.get_knowledge_assessment(user_id)
        goals = await self.get_active_goals(user_id)

        return {
            'user_id': user_id,
            'preferences': preferences,
            'learning_style': learning_style,
            'performance_patterns': patterns,
            'knowledge_assessments': assessments,
            'active_goals': goals,
            'profile_last_updated': datetime.now().isoformat()
        }