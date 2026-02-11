"""
Core Optimization Framework

Lightweight prompt optimization system based on DSPy algorithms.
Provides adaptive prompt improvement without heavy dependencies.
"""

from .core_optimizer import CoreOptimizer
from .optimization_context import OptimizationContext, TrainingExample
from .optimization_result import OptimizationResult
from .optimization_strategies import (
    BootstrapStrategy,
    CoordinateAscentStrategy,
    BayesianStrategy
)
from .mipro_bootstrap import MIPROBootstrapStrategy
from .metrics import OptimizationMetric, AccuracyMetric, EfficiencyMetric

__all__ = [
    "CoreOptimizer",
    "OptimizationContext",
    "TrainingExample",
    "OptimizationResult",
    "BootstrapStrategy",
    "MIPROBootstrapStrategy",
    "CoordinateAscentStrategy",
    "BayesianStrategy",
    "OptimizationMetric",
    "AccuracyMetric",
    "EfficiencyMetric"
]