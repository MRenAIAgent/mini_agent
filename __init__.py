"""
Core Agent System

This module contains the essential components of a lightweight agent framework:
- ReAct execution loop for reasoning and acting
- Memory management system for context and long-term storage
- Prompt optimization framework for adaptive improvement
- Tool/MCP abstraction layer for external capabilities

The core system is designed to be minimal, efficient, and extensible.
"""

from .execution import ReactExecutor, ExecutionContext, ExecutionResult
from .execution.execution_patterns import ExecutionPatternType
from .execution.pattern_executor import PatternExecutor
from .memory import CoreMemoryManager, MemoryStore, MemoryContext
from .optimization import CoreOptimizer, OptimizationContext, TrainingExample, OptimizationResult
from .tools import ToolManager, ToolCall, ToolResult, ToolDefinition
from .agent import CoreAgent

# Integration interfaces
from .integrations import (
    LLMProvider, LLMResponse, LLMConfig,
    MemoryBackend, MemoryConnection,
    ExternalToolProvider, ToolConnection
)

__all__ = [
    # Execution
    "ReactExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionPatternType",
    "PatternExecutor",

    # Memory
    "CoreMemoryManager",
    "MemoryStore",
    "MemoryContext",

    # Optimization
    "CoreOptimizer",
    "OptimizationContext",
    "TrainingExample",
    "OptimizationResult",

    # Tools
    "ToolManager",
    "ToolCall",
    "ToolResult",
    "ToolDefinition",

    # Main Agent
    "CoreAgent",

    # Integration Interfaces
    "LLMProvider",
    "LLMResponse",
    "LLMConfig",
    "MemoryBackend",
    "MemoryConnection",
    "ExternalToolProvider",
    "ToolConnection"
]