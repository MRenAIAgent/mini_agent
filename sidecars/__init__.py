"""
Sidecar System for Mini Agent

Sidecars run alongside the agent execution, similar to Kubernetes sidecar containers.
They execute in the background after the agent completes its main execution loop,
without blocking the response to the user.

Usage:
    from sidecars import Sidecar, SidecarExecutor
    from sidecars.implementations import MemoryStoreSidecar

    # Create sidecar
    memory_sidecar = MemoryStoreSidecar(memory_manager)

    # Register with agent
    agent.register_sidecar(memory_sidecar)

    # Sidecars automatically run after agent.run() completes
    response = await agent.run("Hello")  # Returns immediately
    # Memory storage happens in background
"""

from .base import (
    Sidecar,
    SidecarContext,
    SidecarRegistry,
)

from .executor import (
    SidecarExecutor,
    get_default_executor,
    set_default_executor,
)

from .implementations import (
    MemoryStoreSidecar,
    AnalyticsSidecar,
    LoggingSidecar,
    MetricsSidecar,
    NotificationSidecar,
    EpisodeMemorySidecar,
)

__all__ = [
    # Base classes
    "Sidecar",
    "SidecarContext",
    "SidecarRegistry",

    # Executor
    "SidecarExecutor",
    "get_default_executor",
    "set_default_executor",

    # Implementations
    "MemoryStoreSidecar",
    "AnalyticsSidecar",
    "LoggingSidecar",
    "MetricsSidecar",
    "NotificationSidecar",
    "EpisodeMemorySidecar",
]
