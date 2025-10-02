"""Adaptive weight system for context-aware memory type weighting."""

from typing import Dict, Any, Optional
from ..types import InteractionType


class AdaptiveWeightSystem:
    """Dynamically adjusts memory type weights based on interaction context.

    Different interaction types benefit from different memory type priorities:
    - Questions need more semantic memory (facts/knowledge)
    - Practice needs more episodic memory (past attempts)
    - Explanations need semantic + profile (knowledge + learning style)
    - Assessments need graph memory (track progress)

    The system also adjusts weights based on contextual signals like:
    - User struggling
    - New topic
    - Conversation depth
    - Learning new concept
    """

    def __init__(self):
        """Initialize the adaptive weight system with base profiles."""

        # Base weight profiles for each interaction type
        # Each dict maps memory_type -> weight (should sum to 1.0)
        self.weight_profiles = {
            InteractionType.QUESTION: {
                'episodic': 0.15,
                'semantic': 0.50,  # High - need facts and knowledge
                'profile': 0.10,
                'interaction': 0.20,
                'graph': 0.05
            },
            InteractionType.PRACTICE: {
                'episodic': 0.40,  # High - learn from past attempts
                'semantic': 0.20,
                'profile': 0.20,   # Personalize difficulty
                'interaction': 0.10,
                'graph': 0.10
            },
            InteractionType.EXPLANATION: {
                'episodic': 0.10,
                'semantic': 0.60,  # Very high - need comprehensive knowledge
                'profile': 0.15,   # Adapt to learning style
                'interaction': 0.10,
                'graph': 0.05
            },
            InteractionType.ASSESSMENT: {
                'episodic': 0.30,  # Review performance
                'semantic': 0.25,
                'profile': 0.15,
                'interaction': 0.10,
                'graph': 0.20      # Track learning progress
            },
            InteractionType.FEEDBACK: {
                'episodic': 0.35,  # Review past performance
                'semantic': 0.15,
                'profile': 0.25,   # Consider learning preferences
                'interaction': 0.15,
                'graph': 0.10
            },
            InteractionType.CLARIFICATION: {
                'episodic': 0.20,
                'semantic': 0.40,
                'profile': 0.10,
                'interaction': 0.25,  # High - reference conversation
                'graph': 0.05
            },
            InteractionType.HINT: {
                'episodic': 0.25,
                'semantic': 0.35,
                'profile': 0.20,   # Personalize hint level
                'interaction': 0.15,
                'graph': 0.05
            },
            InteractionType.ERROR_CORRECTION: {
                'episodic': 0.40,  # High - review past mistakes
                'semantic': 0.30,
                'profile': 0.15,
                'interaction': 0.10,
                'graph': 0.05
            }
        }

        # Default fallback weights
        self.default_weights = {
            'episodic': 0.25,
            'semantic': 0.25,
            'profile': 0.20,
            'interaction': 0.20,
            'graph': 0.10
        }

    def get_weights(
        self,
        interaction_type: InteractionType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Get adaptive weights for current interaction and context.

        Args:
            interaction_type: Type of current interaction
            context: Optional context dictionary with signals like:
                - user_struggling: bool
                - new_topic: bool
                - conversation_depth: int
                - learning_new_concept: bool
                - domain: str
                - understanding_level: float

        Returns:
            Dictionary mapping memory type to weight (sums to 1.0)
        """

        # Start with base weights for this interaction type
        # Debug: Check if interaction_type is in profiles
        if interaction_type not in self.weight_profiles:
            # Fallback - try to match by value
            for profile_type, weights in self.weight_profiles.items():
                if hasattr(interaction_type, 'value') and hasattr(profile_type, 'value'):
                    if interaction_type.value == profile_type.value:
                        base_weights = weights.copy()
                        break
            else:
                base_weights = self.default_weights.copy()
        else:
            base_weights = self.weight_profiles[interaction_type].copy()

        # Apply context-based adjustments if context provided
        if context:
            base_weights = self._apply_context_adjustments(
                base_weights, context
            )

        # Normalize to ensure sum = 1.0
        total = sum(base_weights.values())
        if total > 0:
            normalized = {k: v/total for k, v in base_weights.items()}
        else:
            normalized = self.default_weights.copy()

        return normalized

    def _apply_context_adjustments(
        self,
        weights: Dict[str, float],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply context-specific weight adjustments.

        Multiplies weights based on context signals. Higher multiplier
        means that memory type becomes more important.

        Args:
            weights: Base weights to adjust
            context: Context dictionary with signals

        Returns:
            Adjusted weights (before normalization)
        """

        # If user is struggling, boost episodic (learn from past)
        # and reduce semantic (too much info might confuse)
        if context.get('user_struggling', False):
            weights['episodic'] *= 1.3
            weights['semantic'] *= 0.9
            weights['profile'] *= 1.2  # Consider learning style

        # If new topic, boost semantic (need knowledge)
        # and reduce episodic (no relevant past experiences yet)
        if context.get('new_topic', False):
            weights['semantic'] *= 1.4
            weights['episodic'] *= 0.8

        # If deep in conversation, boost interaction
        # (maintain coherence with conversation history)
        conversation_depth = context.get('conversation_depth', 0)
        if conversation_depth > 5:
            weights['interaction'] *= 1.3
        elif conversation_depth > 10:
            weights['interaction'] *= 1.5

        # If learning new concept, boost graph (track prerequisites)
        # and episodic (similar learning experiences)
        if context.get('learning_new_concept', False):
            weights['graph'] *= 1.5
            weights['episodic'] *= 1.2

        # If user has low understanding, simplify by boosting
        # semantic (clear explanations) and profile (adapt to level)
        understanding_level = context.get('understanding_level')
        if understanding_level is not None and understanding_level < 0.4:
            weights['semantic'] *= 1.2
            weights['profile'] *= 1.3
            weights['episodic'] *= 0.9

        # If user has high understanding, can use more episodic
        # (sophisticated examples from past)
        if understanding_level is not None and understanding_level > 0.8:
            weights['episodic'] *= 1.2
            weights['semantic'] *= 0.9

        # If first interaction in session, boost profile
        # (establish personalization early)
        if conversation_depth == 0:
            weights['profile'] *= 1.4

        return weights

    def add_custom_profile(
        self,
        interaction_type: InteractionType,
        weights: Dict[str, float]
    ) -> None:
        """Add or update a custom weight profile.

        Args:
            interaction_type: Interaction type for this profile
            weights: Weight dictionary (will be normalized)
        """
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            normalized = {k: v/total for k, v in weights.items()}
            self.weight_profiles[interaction_type] = normalized

    def get_profile_names(self) -> list:
        """Get list of available interaction type profiles.

        Returns:
            List of interaction type names
        """
        return [itype.value for itype in self.weight_profiles.keys()]

    def explain_weights(
        self,
        interaction_type: InteractionType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get explanation of why certain weights were chosen.

        Useful for debugging and understanding the system's behavior.

        Args:
            interaction_type: Type of interaction
            context: Optional context dictionary

        Returns:
            Dictionary with weights and explanations
        """
        base_weights = self.weight_profiles.get(
            interaction_type,
            self.default_weights
        ).copy()

        adjustments = []

        if context:
            if context.get('user_struggling'):
                adjustments.append(
                    "User struggling: boosted episodic (+30%), reduced semantic (-10%)"
                )

            if context.get('new_topic'):
                adjustments.append(
                    "New topic: boosted semantic (+40%), reduced episodic (-20%)"
                )

            depth = context.get('conversation_depth', 0)
            if depth > 5:
                adjustments.append(
                    f"Deep conversation (depth={depth}): boosted interaction (+30%)"
                )

            if context.get('learning_new_concept'):
                adjustments.append(
                    "Learning new concept: boosted graph (+50%), episodic (+20%)"
                )

            understanding = context.get('understanding_level')
            if understanding is not None:
                if understanding < 0.4:
                    adjustments.append(
                        f"Low understanding ({understanding:.2f}): boosted semantic (+20%), profile (+30%)"
                    )
                elif understanding > 0.8:
                    adjustments.append(
                        f"High understanding ({understanding:.2f}): boosted episodic (+20%)"
                    )

        final_weights = self.get_weights(interaction_type, context)

        return {
            'interaction_type': interaction_type.value,
            'base_weights': base_weights,
            'final_weights': final_weights,
            'adjustments_applied': adjustments,
            'context_used': context or {}
        }
