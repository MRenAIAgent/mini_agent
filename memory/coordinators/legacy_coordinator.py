"""Legacy memory coordinator for backward compatibility.

This coordinator provides the original coordination logic between memory types.
For new code, use EnhancedMemoryCoordinator instead.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..system.learning_memory_system import LearningMemorySystem
    from ..types.interaction_memory import InteractionRecord


class MemoryCoordinator:
    """Coordinates between different memory types (legacy implementation).

    This is maintained for backward compatibility. New code should use
    the EnhancedMemoryCoordinator from enhanced_coordinator.py which provides:
    - Parallel retrieval
    - Cross-memory relevance scoring
    - Adaptive weighting
    """

    def __init__(self, learning_system: 'LearningMemorySystem'):
        """Initialize the legacy coordinator.

        Args:
            learning_system: Reference to the learning memory system
        """
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
        """Generate response using insights from all memory types.

        Args:
            interaction: Current interaction record
            episodic_context: Relevant episodic memories
            semantic_context: Relevant semantic knowledge
            user_profile: User profile information
            conversation_context: Current conversation state
            learning_recommendations: Recommended next steps

        Returns:
            Contextualized response with insights from all memory types
        """

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

    def _analyze_episodic_context(
        self,
        episodes: List[Any],
        interaction: 'InteractionRecord'
    ) -> List[str]:
        """Analyze episodic context for insights.

        Args:
            episodes: List of relevant episodic memories
            interaction: Current interaction

        Returns:
            List of insights from episodic analysis
        """
        insights = []
        if episodes:
            insights.append(f"Found {len(episodes)} similar recent learning episodes")

            # Analyze patterns in episodes
            successful_episodes = [ep for ep in episodes
                                 if ep.metadata.get('context', {}).get('was_successful', False)]
            if successful_episodes:
                insights.append(f"{len(successful_episodes)} previous successful attempts on similar topics")

        return insights

    def _analyze_semantic_context(
        self,
        knowledge: List[Any],
        interaction: 'InteractionRecord'
    ) -> List[str]:
        """Analyze semantic context for insights.

        Args:
            knowledge: List of relevant knowledge items
            interaction: Current interaction

        Returns:
            List of insights from semantic analysis
        """
        insights = []
        if knowledge:
            insights.append(f"Retrieved {len(knowledge)} relevant knowledge items")

            # Analyze knowledge types
            concepts = [k for k in knowledge
                       if k.metadata.get('entry_type') == 'concept']
            if concepts:
                insights.append(f"Including {len(concepts)} core concepts")

        return insights

    def _analyze_profile_context(
        self,
        profile: Dict[str, Any],
        interaction: 'InteractionRecord'
    ) -> List[str]:
        """Analyze profile context for insights.

        Args:
            profile: User profile information
            interaction: Current interaction

        Returns:
            List of insights from profile analysis
        """
        insights = []
        learning_style = profile.get('learning_style')
        if learning_style:
            insights.append(f"Applied personalization based on learning style")

        preferences = profile.get('preferences', {})
        if preferences:
            insights.append(f"Adapted to {len(preferences)} user preferences")

        return insights

    async def _generate_integrated_response(
        self,
        interaction: 'InteractionRecord',
        episodic_insights: List[str],
        semantic_insights: List[str],
        profile_insights: List[str],
        learning_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate integrated response text.

        This is a simplified implementation. In practice, this would:
        - Use sophisticated NLP/LLM integration
        - Generate contextual, personalized responses
        - Incorporate all insights coherently

        Args:
            interaction: Current interaction
            episodic_insights: Insights from episodic memory
            semantic_insights: Insights from semantic memory
            profile_insights: Insights from profile
            learning_recommendations: Recommended next steps

        Returns:
            Generated response text
        """
        # Simple template-based response for now
        response = f"Based on your question about {interaction.user_input[:50]}..., "

        if semantic_insights:
            response += "I can help you understand this concept. "

        if episodic_insights:
            response += "Looking at your recent learning, "

        if learning_recommendations:
            first_rec = learning_recommendations[0]
            concept = first_rec.get('concept_id', 'the next concept')
            response += f"I recommend focusing on {concept} next."

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
        """Predict learning success based on all memory types.

        Combines information from:
        - Learning graph (readiness)
        - User profile (preferences and patterns)
        - Episodic memory (similar past experiences)

        Args:
            user_id: User identifier
            target_concept: Concept to learn
            readiness: Readiness assessment from learning graph
            user_profile: User profile data
            similar_episodes: Similar past learning episodes
            session_type: Type of planned session

        Returns:
            Success prediction with probability and factors
        """

        # Base prediction on readiness
        base_prediction = readiness.get('readiness_score', 0.5)

        # Adjust based on profile
        profile_factor = 1.0
        if user_profile.get('preferences', {}).get('session_success_pattern'):
            profile_factor = 1.1  # Slight boost for known successful patterns

        # Adjust based on similar episodes
        episode_factor = 1.0
        if similar_episodes:
            successful_count = sum(
                1 for ep in similar_episodes
                if ep.metadata.get('context', {}).get('was_successful', False)
            )
            success_rate = successful_count / len(similar_episodes)
            episode_factor = 0.8 + (success_rate * 0.4)  # Scale between 0.8-1.2

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
                "Start with prerequisite review" if readiness.get('readiness_score', 0) < 0.7
                else "Ready to proceed",
                f"Estimated session time: {30 + (1-final_prediction) * 30:.0f} minutes"
            ]
        }
