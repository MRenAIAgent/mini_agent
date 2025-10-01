"""
Observability Module

Provides lightweight, local-only tracing and debugging capabilities for the agent.
Uses Rich for beautiful console output and StructLog for structured logging.
"""

try:
    from .rich_tracer import (
        configure_tracing,
        trace_agent_execution,
        trace_llm_call,
        trace_tool_call,
        get_logger,
        get_console
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    # Graceful fallback if dependencies aren't available
    def configure_tracing(*args, **kwargs):
        return None

    def trace_agent_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def trace_llm_call(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def trace_tool_call(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def get_logger():
        import logging
        return logging.getLogger(__name__)

    def get_console():
        return None

    OBSERVABILITY_AVAILABLE = False

__all__ = [
    "configure_tracing",
    "trace_agent_execution",
    "trace_llm_call",
    "trace_tool_call",
    "get_logger",
    "get_console",
    "OBSERVABILITY_AVAILABLE"
]