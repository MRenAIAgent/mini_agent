"""Learning memory system that inherits from all memory types."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
from dataclasses import dataclass, field

from .episodic_memory import EpisodicMemoryManager
from .semantic_memory import SemanticMemoryManager
from .user_profile_memory import UserProfileMemoryManager
from .interaction_memory import InteractionMemoryManager, InteractionType
from .learning_graph_memory import LearningGraphMemory, ConceptStatus


@dataclass
class LearningSystemConfig:
    """Configuration for the learning memory system."""
    episodic_config: Dict[str, Any] = field(default_factory=dict)
    semantic_config: Dict[str, Any] = field(default_factory=dict)
    profile_config: Dict[str, Any] = field(default_factory=dict)
    interaction_config: Dict[str, Any] = field(default_factory=dict)
    graph_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComprehensiveLearningResponse:
    """Response from comprehensive learning interaction processing."""
    response_text: str
    episodic_insights: List[str] = field(default_factory=list)
    semantic_knowledge_used: List[str] = field(default_factory=list)
    personalization_applied: List[str] = field(default_factory=list)
    next_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    interaction_id: Optional[str] = None
    confidence_score: float = 0.5


@dataclass
class SessionConsolidationResult:
    """Result of session consolidation across all memory types."""
    episode_id: Optional[str] = None
    knowledge_extracted: int = 0
    profile_updated: bool = False
    graph_concepts_updated: int = 0
    session_summary: str = ""
    consolidation_success: bool = True


@dataclass
class ComprehensiveLearningInsights:
    """Comprehensive insights from all memory types."""
    episodic_patterns: Dict[str, Any] = field(default_factory=dict)
    semantic_gaps: List[Dict[str, Any]] = field(default_factory=list)
    profile_insights: Dict[str, Any] = field(default_factory=dict)
    interaction_patterns: List[Dict[str, Any]] = field(default_factory=list)
    learning_graph_analytics: Dict[str, Any] = field(default_factory=dict)
    overall_learning_trajectory: Dict[str, Any] = field(default_factory=dict)


class LearningMemorySystem(
    EpisodicMemoryManager,
    SemanticMemoryManager,
    UserProfileMemoryManager,
    InteractionMemoryManager,
    LearningGraphMemory
):
    """
    Complete learning system inheriting all memory types.

    This system combines episodic, semantic, user profile, interaction,
    and learning graph memory to provide comprehensive learning support.
    """

    def __init__(self, config: Optional[LearningSystemConfig] = None):
        """Initialize learning memory system with all memory types."""
        if config is None:
            config = LearningSystemConfig()

        # Initialize all parent classes with their respective configs
        EpisodicMemoryManager.__init__(self, **config.episodic_config)
        SemanticMemoryManager.__init__(self, **config.semantic_config)
        UserProfileMemoryManager.__init__(self, **config.profile_config)
        InteractionMemoryManager.__init__(self, **config.interaction_config)
        LearningGraphMemory.__init__(self, **config.graph_config)

        # Learning system coordination
        self.system_type = "comprehensive_learning"
        self.memory_coordinator = MemoryCoordinator(self)
        self.learning_analytics = LearningAnalytics(self)

    # === UNIFIED LEARNING INTERFACE ===

    async def process_learning_interaction(
        self,
        user_id: str,
        user_input: str,
        session_id: str,
        interaction_type: Optional[InteractionType] = None,
        domain: Optional[str] = None
    ) -> ComprehensiveLearningResponse:
        """
        Process learning interaction using all memory types.

        Args:
            user_id: User identifier
            user_input: User's input/message
            session_id: Session identifier
            interaction_type: Type of interaction
            domain: Subject domain

        Returns:
            Comprehensive response using all memory systems
        """
        # Create interaction record
        from .interaction_memory import InteractionRecord

        interaction = InteractionRecord(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            interaction_type=interaction_type or InteractionType.QUESTION,
            timestamp=datetime.now()
        )

        # Get comprehensive context from all memory types

        # 1. Get similar episodes (EpisodicMemoryManager)
        recent_episodes = await self.get_learning_episodes(
            user_id=user_id,
            time_range=(datetime.now().replace(hour=0, minute=0, second=0), datetime.now()),
            limit=5
        )

        # 2. Get relevant knowledge (SemanticMemoryManager)
        # Extract concepts from user input (simplified)
        concepts = self._extract_concepts_from_text(user_input)
        semantic_context = []
        for concept in concepts:
            knowledge = await self.search_concepts(concept, domain=domain, user_id=user_id, limit=3)
            semantic_context.extend(knowledge)

        # 3. Get user profile (UserProfileMemoryManager)
        user_profile = await self.get_user_profile_summary(user_id)

        # 4. Get conversation context (InteractionMemoryManager)
        conversation_context = await self.get_recent_context(session_id, turns_back=5)

        # 5. Get learning graph context (LearningGraphMemory)
        next_concepts = await self.get_next_concepts(user_id, domain=domain, limit=3)

        # Generate comprehensive response using all contexts
        response = await self.memory_coordinator.generate_contextualized_response(
            interaction=interaction,
            episodic_context=recent_episodes,
            semantic_context=semantic_context,
            user_profile=user_profile,
            conversation_context=conversation_context,
            learning_recommendations=next_concepts
        )

        # Store interaction (InteractionMemoryManager)
        interaction.agent_response = response['text']
        interaction_id = await self.store_interaction_turn(
            user_id=user_id,
            session_id=session_id,
            turn_number=conversation_context.get('turn_count', 0) + 1,
            user_input=user_input,
            agent_response=response['text'],
            interaction_type=interaction_type or InteractionType.QUESTION,
            context={'concepts': concepts, 'domain': domain}
        )

        return ComprehensiveLearningResponse(
            response_text=response['text'],
            episodic_insights=response.get('episodic_insights', []),
            semantic_knowledge_used=response.get('semantic_knowledge_used', []),
            personalization_applied=response.get('personalization_applied', []),
            next_recommendations=next_concepts,
            interaction_id=interaction_id,
            confidence_score=response.get('confidence', 0.5)
        )

    async def complete_learning_session(
        self,
        user_id: str,
        session_id: str,
        session_summary: str,
        concepts_learned: Optional[List[str]] = None,
        overall_success: float = 0.5,
        user_satisfaction: float = 0.5
    ) -> SessionConsolidationResult:
        """
        Complete learning session and consolidate across all memory types.

        Args:
            user_id: User identifier
            session_id: Session identifier
            session_summary: Summary of the session
            concepts_learned: List of concepts learned in session
            overall_success: Overall success level (0.0 to 1.0)
            user_satisfaction: User satisfaction level (0.0 to 1.0)

        Returns:
            Consolidation result across all memory systems
        """
        concepts_learned = concepts_learned or []

        try:
            # Get all interactions from session
            conversation_history = await self.get_session_history(session_id, limit=1000)

            # Create learning episode (EpisodicMemoryManager)
            episode_id = None
            # Always create an episode, even with no conversation history
            from uuid import uuid4
            episode_id = f"episode_{uuid4().hex[:8]}"

            success = await self.store_learning_event(
                event_type='learning_session',
                content=session_summary,
                user_id=user_id,
                session_id=session_id,
                context={
                    'concepts_learned': concepts_learned,
                    'interaction_count': len(conversation_history),
                    'overall_success': overall_success,
                    'user_satisfaction': user_satisfaction,
                    'episode_id': episode_id
                },
                importance=0.8
            )

            # If storing failed, set episode_id to None
            if not success:
                episode_id = None

            # Extract and store semantic knowledge from successful interactions
            knowledge_extracted = 0
            for interaction in conversation_history:
                if interaction.get('understanding_indicators', {}).get('understanding_level', 0) > 0.7:
                    # Store knowledge about concepts that were well understood
                    for concept in concepts_learned:
                        await self.store_fact(
                            fact_content=f"User demonstrated understanding of {concept} in session {session_id}",
                            domain=interaction.get('context', {}).get('domain', 'general'),
                            related_concepts=[concept],
                            user_id=user_id,
                            confidence=overall_success
                        )
                        knowledge_extracted += 1

            # Update user profile based on session
            profile_updated = False
            if overall_success > 0.6:
                # Update learning preferences based on successful session
                await self.store_learning_preference(
                    user_id=user_id,
                    preference_type='session_success_pattern',
                    preference_value={
                        'session_length': len(conversation_history),
                        'concepts_per_session': len(concepts_learned),
                        'interaction_types': [t.get('interaction_type') for t in conversation_history]
                    },
                    confidence=overall_success,
                    source='observed'
                )
                profile_updated = True

            # Update learning graph for learned concepts
            graph_concepts_updated = 0
            for concept in concepts_learned:
                success = await self.mark_concept_learned(
                    user_id=user_id,
                    concept_id=concept,
                    mastery_level=overall_success,
                    evidence=f"Learned in session {session_id} with {overall_success:.2f} success level"
                )
                if success:
                    graph_concepts_updated += 1

            return SessionConsolidationResult(
                episode_id=episode_id,
                knowledge_extracted=knowledge_extracted,
                profile_updated=profile_updated,
                graph_concepts_updated=graph_concepts_updated,
                session_summary=session_summary,
                consolidation_success=True
            )

        except Exception as e:
            return SessionConsolidationResult(
                session_summary=f"Consolidation failed: {str(e)}",
                consolidation_success=False
            )

    async def get_comprehensive_learning_insights(
        self,
        user_id: str,
        domain: Optional[str] = None,
        days_back: int = 30
    ) -> ComprehensiveLearningInsights:
        """
        Get comprehensive insights using all memory types.

        Args:
            user_id: User identifier
            domain: Optional domain filter
            days_back: Number of days to analyze

        Returns:
            Comprehensive insights from all memory systems
        """
        # Get insights from each memory type
        episodic_patterns = await self.analyze_learning_patterns(user_id, days_back)
        semantic_gaps = await self.get_knowledge_gaps(user_id, domain or 'general')
        profile_insights = await self.get_user_profile_summary(user_id)
        interaction_patterns = await self.get_user_interaction_patterns(user_id)
        learning_graph_analytics = await self.get_learning_analytics(user_id, domain)

        # Generate overall learning trajectory
        overall_trajectory = await self.learning_analytics.generate_learning_trajectory(
            user_id, episodic_patterns, semantic_gaps, profile_insights,
            interaction_patterns, learning_graph_analytics
        )

        return ComprehensiveLearningInsights(
            episodic_patterns=episodic_patterns,
            semantic_gaps=semantic_gaps,
            profile_insights=profile_insights,
            interaction_patterns=interaction_patterns,
            learning_graph_analytics=learning_graph_analytics,
            overall_learning_trajectory=overall_trajectory
        )

    # === CROSS-MEMORY OPERATIONS ===

    async def predict_learning_success(
        self,
        user_id: str,
        target_concept: str,
        planned_session_type: str = "practice",
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict learning success using all memory types.

        Args:
            user_id: User identifier
            target_concept: Concept to learn
            planned_session_type: Type of planned session
            domain: Subject domain

        Returns:
            Success prediction with confidence and factors
        """
        # Check readiness from learning graph
        readiness = await self.can_learn_concept(user_id, target_concept, domain)

        # Get user profile preferences
        user_profile = await self.get_user_profile_summary(user_id)

        # Get similar past episodes
        similar_episodes = await self.get_learning_episodes(
            user_id=user_id,
            event_type='concept_interaction',
            limit=10
        )

        # Analyze patterns
        prediction = await self.memory_coordinator.predict_success(
            user_id, target_concept, readiness, user_profile,
            similar_episodes, planned_session_type
        )

        return prediction

    async def get_personalized_learning_plan(
        self,
        user_id: str,
        learning_goal: str,
        domain: Optional[str] = None,
        timeline_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate personalized learning plan using all memory types.

        Args:
            user_id: User identifier
            learning_goal: High-level learning goal
            domain: Subject domain
            timeline_days: Timeline for the plan

        Returns:
            Comprehensive learning plan
        """
        # Get user profile and preferences
        profile = await self.get_user_profile_summary(user_id)

        # Get current learning state
        analytics = await self.get_learning_analytics(user_id, domain)

        # Get learning path to goal
        # (This would need more sophisticated goal parsing in practice)
        next_concepts = await self.get_next_concepts(user_id, domain, limit=10)

        # Generate personalized plan
        plan = await self.learning_analytics.generate_learning_plan(
            user_id, learning_goal, profile, analytics, next_concepts, timeline_days
        )

        return plan

    # === HELPER METHODS ===

    def _extract_concepts_from_text(self, text: str) -> List[str]:
        """Extract concept keywords from text (simplified implementation)."""
        # In practice, this would use NLP techniques
        # For now, simple keyword extraction
        math_keywords = ['algebra', 'equation', 'quadratic', 'linear', 'geometry', 'calculus', 'derivative']
        concepts = []
        text_lower = text.lower()

        for keyword in math_keywords:
            if keyword in text_lower:
                concepts.append(keyword)

        return concepts


class MemoryCoordinator:
    """Coordinates between different memory types."""

    def __init__(self, learning_system: LearningMemorySystem):
        self.system = learning_system

    async def generate_contextualized_response(
        self,
        interaction: 'InteractionRecord',
        episodic_context: List[Any],
        semantic_context: List[Any],
        user_profile: Dict[str, Any],
        conversation_context: Dict[str, Any],
        learning_recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate response using insights from all memory types."""

        # Analyze context from each memory type
        episodic_insights = self._analyze_episodic_context(episodic_context, interaction)
        semantic_insights = self._analyze_semantic_context(semantic_context, interaction)
        profile_insights = self._analyze_profile_context(user_profile, interaction)

        # Generate integrated response
        response_text = await self._generate_integrated_response(
            interaction, episodic_insights, semantic_insights,
            profile_insights, learning_recommendations
        )

        return {
            'text': response_text,
            'episodic_insights': episodic_insights,
            'semantic_knowledge_used': semantic_insights,
            'personalization_applied': profile_insights,
            'confidence': 0.8  # Would be calculated based on context quality
        }

    def _analyze_episodic_context(self, episodes: List[Any], interaction: 'InteractionRecord') -> List[str]:
        """Analyze episodic context for insights."""
        insights = []
        if episodes:
            insights.append(f"Found {len(episodes)} similar recent learning episodes")
            # Add more sophisticated analysis
        return insights

    def _analyze_semantic_context(self, knowledge: List[Any], interaction: 'InteractionRecord') -> List[str]:
        """Analyze semantic context for insights."""
        insights = []
        if knowledge:
            insights.append(f"Retrieved {len(knowledge)} relevant knowledge items")
            # Add more sophisticated analysis
        return insights

    def _analyze_profile_context(self, profile: Dict[str, Any], interaction: 'InteractionRecord') -> List[str]:
        """Analyze profile context for insights."""
        insights = []
        learning_style = profile.get('learning_style')
        if learning_style:
            insights.append(f"Applied personalization based on learning style")
        return insights

    async def _generate_integrated_response(
        self,
        interaction: 'InteractionRecord',
        episodic_insights: List[str],
        semantic_insights: List[str],
        profile_insights: List[str],
        learning_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate integrated response text."""
        # This would use sophisticated NLP/LLM integration in practice
        # For now, simple template-based response

        response = f"Based on your question about {interaction.user_input[:50]}..., "

        if semantic_insights:
            response += "I can help you understand this concept. "

        if episodic_insights:
            response += "Looking at your recent learning, "

        if learning_recommendations:
            response += f"I recommend focusing on {learning_recommendations[0].get('concept_id', 'the next concept')} next."

        return response

    async def predict_success(
        self,
        user_id: str,
        target_concept: str,
        readiness: Dict[str, Any],
        user_profile: Dict[str, Any],
        similar_episodes: List[Any],
        session_type: str
    ) -> Dict[str, Any]:
        """Predict learning success based on all memory types."""

        # Base prediction on readiness
        base_prediction = readiness.get('readiness_score', 0.5)

        # Adjust based on profile
        profile_factor = 1.0
        if user_profile.get('preferences', {}).get('session_success_pattern'):
            profile_factor = 1.1  # Slight boost for known successful patterns

        # Adjust based on similar episodes
        episode_factor = 1.0
        if similar_episodes:
            avg_success = sum(ep.metadata.get('context', {}).get('was_successful', False)
                            for ep in similar_episodes) / len(similar_episodes)
            episode_factor = 0.8 + (avg_success * 0.4)  # Scale between 0.8-1.2

        final_prediction = min(1.0, base_prediction * profile_factor * episode_factor)

        return {
            'success_probability': final_prediction,
            'confidence': 0.7,
            'factors': {
                'readiness': readiness.get('readiness_score', 0.5),
                'profile_match': profile_factor,
                'historical_performance': episode_factor
            },
            'recommendations': [
                "Start with prerequisite review" if readiness.get('readiness_score', 0) < 0.7 else "Ready to proceed",
                f"Estimated session time: {30 + (1-final_prediction) * 30:.0f} minutes"
            ]
        }


class LearningAnalytics:
    """Provides analytics across all memory types."""

    def __init__(self, learning_system: LearningMemorySystem):
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
        """Generate overall learning trajectory analysis."""

        return {
            'learning_velocity': learning_graph_analytics.get('learning_velocity', 0),
            'knowledge_growth': len(semantic_gaps),
            'engagement_trend': episodic_patterns.get('daily_activity', {}),
            'preferred_learning_modes': profile_insights.get('preferences', {}),
            'communication_effectiveness': len(interaction_patterns),
            'next_milestones': learning_graph_analytics.get('breakthrough_concepts', []),
            'trajectory_timestamp': datetime.now().isoformat()
        }

    async def generate_learning_plan(
        self,
        user_id: str,
        learning_goal: str,
        profile: Dict[str, Any],
        analytics: Dict[str, Any],
        next_concepts: List[Dict[str, Any]],
        timeline_days: int
    ) -> Dict[str, Any]:
        """Generate comprehensive learning plan."""

        # Calculate concepts per week based on learning velocity
        velocity = analytics.get('learning_velocity', 1.0)  # concepts per hour
        concepts_per_week = max(1, int(velocity * 10))  # Assume 10 hours per week

        weeks = timeline_days // 7
        total_concepts = min(len(next_concepts), concepts_per_week * weeks)

        return {
            'goal': learning_goal,
            'timeline_days': timeline_days,
            'recommended_concepts': next_concepts[:total_concepts],
            'weekly_schedule': {
                'concepts_per_week': concepts_per_week,
                'estimated_hours_per_week': 10,
                'recommended_session_length': 60  # minutes
            },
            'personalization': {
                'preferred_difficulty': profile.get('preferences', {}).get('difficulty_preference', 'medium'),
                'learning_style_adaptations': profile.get('learning_style', {}),
                'motivational_factors': profile.get('active_goals', [])
            },
            'milestones': [
                {'week': w+1, 'concepts': next_concepts[w*concepts_per_week:(w+1)*concepts_per_week]}
                for w in range(min(weeks, len(next_concepts)//concepts_per_week))
            ],
            'plan_generated_at': datetime.now().isoformat()
        }