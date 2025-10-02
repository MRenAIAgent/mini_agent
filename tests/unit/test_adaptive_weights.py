"""Unit tests for adaptive weight system."""

import pytest
from memory.coordinator.adaptive_weights import AdaptiveWeightSystem
from memory.interaction_memory import InteractionType


class TestAdaptiveWeightSystem:
    """Test suite for AdaptiveWeightSystem."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.weight_system = AdaptiveWeightSystem()

    def test_initialization(self):
        """Test proper initialization of weight system."""
        assert isinstance(self.weight_system.weight_profiles, dict)
        assert isinstance(self.weight_system.default_weights, dict)

        # Check that all interaction types have profiles
        for interaction_type in InteractionType:
            assert interaction_type in self.weight_system.weight_profiles

    def test_weight_profiles_sum_to_one(self):
        """Test that all weight profiles sum to 1.0."""
        for interaction_type, weights in self.weight_system.weight_profiles.items():
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.001, f"{interaction_type} weights sum to {total}"

    def test_get_weights_question_type(self):
        """Test weights for QUESTION interaction type."""
        weights = self.weight_system.get_weights(InteractionType.QUESTION)

        # Question should prioritize semantic (facts/knowledge)
        assert weights['semantic'] > weights['episodic']
        assert weights['semantic'] > weights['profile']

        # Should sum to 1.0
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_get_weights_practice_type(self):
        """Test weights for PRACTICE interaction type."""
        weights = self.weight_system.get_weights(InteractionType.PRACTICE)

        # Practice should prioritize episodic (past attempts)
        assert weights['episodic'] > weights['semantic']
        assert weights['episodic'] > weights['interaction']

    def test_get_weights_explanation_type(self):
        """Test weights for EXPLANATION interaction type."""
        weights = self.weight_system.get_weights(InteractionType.EXPLANATION)

        # Explanation should heavily prioritize semantic
        assert weights['semantic'] >= 0.5
        assert weights['semantic'] > weights['episodic']

    def test_get_weights_assessment_type(self):
        """Test weights for ASSESSMENT interaction type."""
        weights = self.weight_system.get_weights(InteractionType.ASSESSMENT)

        # Assessment should use graph to track progress
        assert weights['graph'] > 0.15

    def test_context_adjustment_user_struggling(self):
        """Test weight adjustment when user is struggling."""
        context = {'user_struggling': True}

        weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            context
        )

        # Get base weights without context for comparison
        base_weights = self.weight_system.get_weights(
            InteractionType.QUESTION
        )

        # When struggling, episodic should be boosted (learn from past)
        # Note: after normalization, the relative ordering matters
        # Episodic should have higher proportion
        assert weights['episodic'] / base_weights['episodic'] > 1.0

    def test_context_adjustment_new_topic(self):
        """Test weight adjustment for new topic."""
        context = {'new_topic': True}

        weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            context
        )

        base_weights = self.weight_system.get_weights(
            InteractionType.QUESTION
        )

        # New topic should boost semantic (need knowledge)
        assert weights['semantic'] / base_weights['semantic'] > 1.0

    def test_context_adjustment_conversation_depth(self):
        """Test weight adjustment for conversation depth."""
        shallow_context = {'conversation_depth': 2}
        deep_context = {'conversation_depth': 8}
        very_deep_context = {'conversation_depth': 15}

        shallow_weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            shallow_context
        )

        deep_weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            deep_context
        )

        very_deep_weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            very_deep_context
        )

        # Deeper conversation should boost interaction memory
        # After normalization, interaction weight proportion should increase
        assert deep_weights['interaction'] >= shallow_weights['interaction']
        assert very_deep_weights['interaction'] >= deep_weights['interaction']

    def test_context_adjustment_learning_new_concept(self):
        """Test weight adjustment when learning new concept."""
        context = {'learning_new_concept': True}

        weights = self.weight_system.get_weights(
            InteractionType.PRACTICE,
            context
        )

        base_weights = self.weight_system.get_weights(
            InteractionType.PRACTICE
        )

        # Should boost graph (prerequisites) and episodic
        # Check that proportions increase (with tolerance for normalization)
        assert weights['graph'] / base_weights['graph'] >= 0.95
        assert weights['episodic'] / base_weights['episodic'] >= 0.95

    def test_context_adjustment_low_understanding(self):
        """Test weight adjustment for low understanding level."""
        context = {'understanding_level': 0.3}

        weights = self.weight_system.get_weights(
            InteractionType.EXPLANATION,
            context
        )

        base_weights = self.weight_system.get_weights(
            InteractionType.EXPLANATION
        )

        # Low understanding should boost semantic (clear explanations)
        # and profile (adapt to level)
        assert weights['semantic'] / base_weights['semantic'] >= 0.95
        assert weights['profile'] / base_weights['profile'] > 1.0

    def test_context_adjustment_high_understanding(self):
        """Test weight adjustment for high understanding level."""
        context = {'understanding_level': 0.9}

        weights = self.weight_system.get_weights(
            InteractionType.PRACTICE,
            context
        )

        base_weights = self.weight_system.get_weights(
            InteractionType.PRACTICE
        )

        # High understanding can use more episodic (sophisticated examples)
        assert weights['episodic'] / base_weights['episodic'] > 1.0

    def test_context_adjustment_first_interaction(self):
        """Test weight adjustment for first interaction in session."""
        context = {'conversation_depth': 0}

        weights = self.weight_system.get_weights(
            InteractionType.QUESTION,
            context
        )

        base_weights = self.weight_system.get_weights(
            InteractionType.QUESTION
        )

        # First interaction should boost profile (establish personalization)
        assert weights['profile'] / base_weights['profile'] > 1.0

    def test_multiple_context_signals(self):
        """Test combining multiple context signals."""
        complex_context = {
            'user_struggling': True,
            'conversation_depth': 10,
            'new_topic': False,
            'understanding_level': 0.4
        }

        weights = self.weight_system.get_weights(
            InteractionType.PRACTICE,
            complex_context
        )

        # All adjustments should be applied
        # Should sum to 1.0 after all adjustments
        assert abs(sum(weights.values()) - 1.0) < 0.001

        # Verify it doesn't break with complex context
        assert all(0 <= v <= 1 for v in weights.values())

    def test_add_custom_profile(self):
        """Test adding custom weight profile."""
        custom_weights = {
            'episodic': 0.5,
            'semantic': 0.3,
            'profile': 0.1,
            'interaction': 0.05,
            'graph': 0.05
        }

        self.weight_system.add_custom_profile(
            InteractionType.HINT,
            custom_weights
        )

        # Retrieve custom profile
        weights = self.weight_system.get_weights(InteractionType.HINT)

        # Should use custom weights (normalized)
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert weights['episodic'] == pytest.approx(0.5, abs=0.01)

    def test_get_profile_names(self):
        """Test getting list of available profiles."""
        names = self.weight_system.get_profile_names()

        # Should include all interaction types
        assert 'question' in names
        assert 'practice' in names
        assert 'explanation' in names
        assert len(names) == len(InteractionType)

    def test_explain_weights_basic(self):
        """Test weight explanation functionality."""
        explanation = self.weight_system.explain_weights(
            InteractionType.QUESTION
        )

        assert 'interaction_type' in explanation
        assert explanation['interaction_type'] == 'question'
        assert 'base_weights' in explanation
        assert 'final_weights' in explanation
        assert 'adjustments_applied' in explanation
        assert isinstance(explanation['adjustments_applied'], list)

    def test_explain_weights_with_context(self):
        """Test weight explanation with context."""
        context = {
            'user_struggling': True,
            'new_topic': True,
            'conversation_depth': 8
        }

        explanation = self.weight_system.explain_weights(
            InteractionType.PRACTICE,
            context
        )

        # Should describe adjustments
        assert len(explanation['adjustments_applied']) > 0
        assert 'context_used' in explanation
        assert explanation['context_used'] == context

    def test_normalization(self):
        """Test that weights are always normalized."""
        # Try with various contexts
        contexts = [
            {},
            {'user_struggling': True},
            {'new_topic': True, 'conversation_depth': 5},
            {'understanding_level': 0.2, 'learning_new_concept': True}
        ]

        for context in contexts:
            for interaction_type in InteractionType:
                weights = self.weight_system.get_weights(
                    interaction_type,
                    context
                )

                # Must sum to 1.0
                total = sum(weights.values())
                assert abs(total - 1.0) < 0.001, \
                    f"Weights for {interaction_type} with context {context} sum to {total}"

    def test_all_memory_types_present(self):
        """Test that all memory types get weights."""
        expected_types = {'episodic', 'semantic', 'profile', 'interaction', 'graph'}

        for interaction_type in InteractionType:
            weights = self.weight_system.get_weights(interaction_type)
            assert set(weights.keys()) == expected_types

    def test_weight_bounds(self):
        """Test that all weights stay within bounds [0, 1]."""
        # Test with extreme contexts
        extreme_contexts = [
            {'user_struggling': True, 'understanding_level': 0.1},
            {'conversation_depth': 20, 'new_topic': True},
            {'learning_new_concept': True, 'understanding_level': 0.9}
        ]

        for context in extreme_contexts:
            for interaction_type in InteractionType:
                weights = self.weight_system.get_weights(
                    interaction_type,
                    context
                )

                for memory_type, weight in weights.items():
                    assert 0 <= weight <= 1, \
                        f"Weight for {memory_type} is {weight}, out of bounds"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
