"""
Core Agent Integration Interfaces

This module provides standardized interfaces for integrating the core agent
with different LLM providers, memory backends, and external systems.
"""

from .llm_interfaces import LLMProvider, LLMResponse, LLMConfig
from .memory_interfaces import MemoryBackend, MemoryConnection
from .tool_interfaces import ExternalToolProvider, ToolConnection

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMConfig",
    "MemoryBackend",
    "MemoryConnection",
    "ExternalToolProvider",
    "ToolConnection"
]