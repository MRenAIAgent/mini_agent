"""Optimization metrics for evaluating prompt performance."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import re


class OptimizationMetric(ABC):
    """Abstract base class for optimization metrics."""

    @abstractmethod
    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Evaluate the quality of a prediction.

        Args:
            predicted: The predicted/generated output
            expected: The expected/target output
            context: Optional context information

        Returns:
            Score between 0.0 and 1.0 (higher is better)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this metric."""
        pass

    def get_description(self) -> str:
        """Get a description of this metric."""
        return f"{self.get_name()} metric"


class AccuracyMetric(OptimizationMetric):
    """Simple accuracy metric based on exact or fuzzy matching."""

    def __init__(
        self,
        case_sensitive: bool = False,
        strip_whitespace: bool = True,
        fuzzy_threshold: float = 0.8
    ):
        self.case_sensitive = case_sensitive
        self.strip_whitespace = strip_whitespace
        self.fuzzy_threshold = fuzzy_threshold

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate using exact or fuzzy string matching."""
        if not predicted or not expected:
            return 0.0

        # Normalize strings
        pred = self._normalize_string(predicted)
        exp = self._normalize_string(expected)

        # Exact match
        if pred == exp:
            return 1.0

        # Fuzzy match using simple similarity
        similarity = self._calculate_similarity(pred, exp)
        return 1.0 if similarity >= self.fuzzy_threshold else similarity

    def _normalize_string(self, text: str) -> str:
        """Normalize string for comparison."""
        if self.strip_whitespace:
            text = text.strip()

        if not self.case_sensitive:
            text = text.lower()

        return text

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity."""
        if not str1 or not str2:
            return 0.0

        # Jaccard similarity on words
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 and not words2:
            return 1.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def get_name(self) -> str:
        return "accuracy"

    def get_description(self) -> str:
        return f"Accuracy metric (case_sensitive={self.case_sensitive}, fuzzy_threshold={self.fuzzy_threshold})"


class EfficiencyMetric(OptimizationMetric):
    """Metric that considers both accuracy and efficiency."""

    def __init__(
        self,
        accuracy_weight: float = 0.7,
        efficiency_weight: float = 0.3,
        max_tokens: int = 1000
    ):
        self.accuracy_weight = accuracy_weight
        self.efficiency_weight = efficiency_weight
        self.max_tokens = max_tokens
        self.accuracy_metric = AccuracyMetric()

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate considering both accuracy and efficiency."""
        # Calculate accuracy
        accuracy_score = self.accuracy_metric.evaluate(predicted, expected, context)

        # Calculate efficiency (inverse of token count)
        token_count = len(predicted.split())
        efficiency_score = max(0.0, 1.0 - (token_count / self.max_tokens))

        # Weighted combination
        combined_score = (
            self.accuracy_weight * accuracy_score +
            self.efficiency_weight * efficiency_score
        )

        return combined_score

    def get_name(self) -> str:
        return "efficiency"

    def get_description(self) -> str:
        return f"Efficiency metric (accuracy_weight={self.accuracy_weight}, efficiency_weight={self.efficiency_weight})"


class NumericMetric(OptimizationMetric):
    """Metric for numeric outputs with tolerance."""

    def __init__(self, tolerance: float = 0.01, relative: bool = False):
        self.tolerance = tolerance
        self.relative = relative

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate numeric predictions."""
        try:
            # Extract numbers from strings
            pred_num = self._extract_number(predicted)
            exp_num = self._extract_number(expected)

            if pred_num is None or exp_num is None:
                # Fall back to string comparison if not numeric
                return 1.0 if predicted.strip() == expected.strip() else 0.0

            # Calculate difference
            if self.relative and exp_num != 0:
                diff = abs((pred_num - exp_num) / exp_num)
            else:
                diff = abs(pred_num - exp_num)

            # Check if within tolerance
            if diff <= self.tolerance:
                return 1.0
            else:
                # Gradual decline based on how far off
                return max(0.0, 1.0 - (diff / self.tolerance))

        except Exception:
            return 0.0

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract the first number from text."""
        # Look for number patterns
        number_pattern = r'-?\d+\.?\d*'
        matches = re.findall(number_pattern, text)

        if matches:
            try:
                return float(matches[0])
            except ValueError:
                pass

        return None

    def get_name(self) -> str:
        return "numeric"

    def get_description(self) -> str:
        return f"Numeric metric (tolerance={self.tolerance}, relative={self.relative})"


class ClassificationMetric(OptimizationMetric):
    """Metric for classification tasks."""

    def __init__(self, valid_classes: List[str], case_sensitive: bool = False):
        self.valid_classes = [cls.lower() if not case_sensitive else cls for cls in valid_classes]
        self.case_sensitive = case_sensitive

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate classification predictions."""
        pred = predicted.strip()
        exp = expected.strip()

        if not self.case_sensitive:
            pred = pred.lower()
            exp = exp.lower()

        # Check if both are valid classes
        if exp not in self.valid_classes:
            # Invalid expected class, use string comparison
            return 1.0 if pred == exp else 0.0

        # Exact match
        if pred == exp:
            return 1.0

        # Check if prediction contains the expected class
        if exp in pred:
            return 0.8

        # Check if prediction is a valid class (partial credit)
        if pred in self.valid_classes:
            return 0.2

        return 0.0

    def get_name(self) -> str:
        return "classification"

    def get_description(self) -> str:
        return f"Classification metric with {len(self.valid_classes)} classes"


class CompositeMetric(OptimizationMetric):
    """Composite metric that combines multiple metrics."""

    def __init__(self, metrics: List[tuple]):
        """
        Initialize composite metric.

        Args:
            metrics: List of (metric, weight) tuples
        """
        self.metrics = metrics
        # Normalize weights
        total_weight = sum(weight for _, weight in metrics)
        self.metrics = [(metric, weight / total_weight) for metric, weight in metrics]

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate using weighted combination of metrics."""
        total_score = 0.0

        for metric, weight in self.metrics:
            score = metric.evaluate(predicted, expected, context)
            total_score += score * weight

        return total_score

    def get_name(self) -> str:
        metric_names = [metric.get_name() for metric, _ in self.metrics]
        return f"composite({'+'.join(metric_names)})"

    def get_description(self) -> str:
        descriptions = []
        for metric, weight in self.metrics:
            descriptions.append(f"{metric.get_name()}({weight:.2f})")
        return f"Composite metric: {' + '.join(descriptions)}"


class AnswerCorrectnessMetric(OptimizationMetric):
    """Advanced metric that evaluates answer correctness using multiple criteria."""

    def __init__(self):
        self.accuracy_metric = AccuracyMetric(fuzzy_threshold=0.7)

    def evaluate(
        self,
        predicted: str,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate answer correctness using multiple criteria."""
        if not predicted or not expected:
            return 0.0

        # Start with basic accuracy
        accuracy_score = self.accuracy_metric.evaluate(predicted, expected, context)

        # Additional scoring factors
        scores = [accuracy_score]

        # Completeness: Check if key information is present
        completeness_score = self._evaluate_completeness(predicted, expected)
        scores.append(completeness_score * 0.3)

        # Factual consistency: Basic checks
        consistency_score = self._evaluate_consistency(predicted, expected)
        scores.append(consistency_score * 0.2)

        # Return weighted average
        return sum(scores) / len(scores)

    def _evaluate_completeness(self, predicted: str, expected: str) -> float:
        """Evaluate if the prediction contains key information from expected."""
        expected_words = set(expected.lower().split())
        predicted_words = set(predicted.lower().split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are'}
        expected_content = expected_words - stop_words
        predicted_content = predicted_words - stop_words

        if not expected_content:
            return 1.0

        # Calculate coverage of important words
        coverage = len(expected_content.intersection(predicted_content)) / len(expected_content)
        return coverage

    def _evaluate_consistency(self, predicted: str, expected: str) -> float:
        """Evaluate factual consistency (basic version)."""
        # Basic consistency checks
        pred_lower = predicted.lower()
        exp_lower = expected.lower()

        # Check for contradictory patterns
        contradictions = 0

        # Number consistency
        pred_numbers = re.findall(r'\d+', predicted)
        exp_numbers = re.findall(r'\d+', expected)

        if exp_numbers and pred_numbers:
            if pred_numbers[0] != exp_numbers[0]:
                contradictions += 1

        # Simple negation check
        if 'not' in pred_lower and 'not' not in exp_lower:
            contradictions += 0.5
        elif 'not' not in pred_lower and 'not' in exp_lower:
            contradictions += 0.5

        # Return consistency score
        return max(0.0, 1.0 - contradictions)

    def get_name(self) -> str:
        return "answer_correctness"

    def get_description(self) -> str:
        return "Answer correctness metric with accuracy, completeness, and consistency"