"""
Base Sidecar Abstractions

Sidecars run alongside the agent execution, similar to Kubernetes sidecar containers.
They execute in the background after the agent completes its main execution loop,
without blocking the response to the user.

Key Characteristics:
- Non-blocking: Don't delay agent response
- Background execution: Run concurrently via asyncio
- Error isolation: Failures don't crash agent
- Context-aware: Access agent state and execution context
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Sidecar(ABC):
    """
    Base class for agent sidecars.

    Sidecars execute after the agent's main execution loop completes,
    running in the background without blocking the response to the user.

    Similar to Kubernetes sidecar containers, they:
    - Run alongside the main process
    - Don't block the main execution
    - Can fail independently
    - Have access to execution context
    """

    # Override these in subclasses
    name: str = "unnamed_sidecar"
    description: str = "No description provided"
    timeout: int = 60  # Default timeout in seconds
    enabled: bool = True  # Can be disabled without removing

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute sidecar logic in background.

        This method runs asynchronously after the agent completes execution.
        The agent does NOT wait for this to complete before returning response.

        Args:
            context: Execution context containing:
                - session_id: Agent session identifier
                - user_input: Original user input
                - response: Agent's generated response
                - execution_result: Full execution result dict
                - timestamp: When execution completed
                - agent_state: Current agent state snapshot

        Returns:
            Any result (only used for logging/debugging, not returned to user)

        Raises:
            Any exceptions are caught and logged, don't crash agent
        """
        pass

    async def on_success(self, result: Any):
        """
        Called when sidecar execution succeeds.
        Override to add custom success handling.

        Args:
            result: The return value from execute()
        """
        logger.debug(f"Sidecar {self.name} completed successfully")

    async def on_error(self, error: Exception):
        """
        Called when sidecar execution fails.
        Override to add custom error handling.

        Args:
            error: The exception that was raised
        """
        logger.error(f"Sidecar {self.name} failed: {error}")

    async def on_timeout(self):
        """
        Called when sidecar execution times out.
        Override to add custom timeout handling.
        """
        logger.warning(f"Sidecar {self.name} timed out after {self.timeout}s")

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """
        Determine if this sidecar should execute for given context.
        Override to add conditional execution logic.

        Args:
            context: Execution context

        Returns:
            True if sidecar should execute, False to skip
        """
        return self.enabled

    def __repr__(self) -> str:
        return f"<Sidecar: {self.name}>"


class SidecarContext:
    """
    Structured context passed to sidecars.
    Provides convenient access to execution data.
    """

    def __init__(
        self,
        session_id: str,
        user_input: str,
        response: str,
        execution_result: Dict[str, Any],
        timestamp: datetime,
        agent_state: Dict[str, Any],
        **kwargs
    ):
        self.session_id = session_id
        self.user_input = user_input
        self.response = response
        self.execution_result = execution_result
        self.timestamp = timestamp
        self.agent_state = agent_state
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "user_input": self.user_input,
            "response": self.response,
            "execution_result": self.execution_result,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "agent_state": self.agent_state,
            **self.extra
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SidecarContext':
        """Create context from dictionary"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            session_id=data.get("session_id", ""),
            user_input=data.get("user_input", ""),
            response=data.get("response", ""),
            execution_result=data.get("execution_result", {}),
            timestamp=timestamp or datetime.now(),
            agent_state=data.get("agent_state", {}),
            **{k: v for k, v in data.items() if k not in [
                "session_id", "user_input", "response",
                "execution_result", "timestamp", "agent_state"
            ]}
        )


class SidecarRegistry:
    """
    Registry for managing sidecar instances.
    Allows registration, lookup, and bulk operations on sidecars.
    """

    def __init__(self):
        self._sidecars: Dict[str, Sidecar] = {}
        self._execution_order: list[str] = []

    def register(self, sidecar: Sidecar, priority: int = 0):
        """
        Register a sidecar.

        Args:
            sidecar: Sidecar instance to register
            priority: Execution priority (higher = earlier). Optional.
        """
        if sidecar.name in self._sidecars:
            logger.warning(f"Sidecar {sidecar.name} already registered, overwriting")

        self._sidecars[sidecar.name] = sidecar

        # Add to execution order (simple FIFO for now)
        if sidecar.name not in self._execution_order:
            self._execution_order.append(sidecar.name)

        logger.info(f"Registered sidecar: {sidecar.name}")

    def unregister(self, name: str):
        """Remove a sidecar from registry"""
        if name in self._sidecars:
            del self._sidecars[name]
            self._execution_order.remove(name)
            logger.info(f"Unregistered sidecar: {name}")

    def get(self, name: str) -> Optional[Sidecar]:
        """Get sidecar by name"""
        return self._sidecars.get(name)

    def get_all(self) -> list[Sidecar]:
        """Get all registered sidecars in execution order"""
        return [self._sidecars[name] for name in self._execution_order if name in self._sidecars]

    def get_enabled(self) -> list[Sidecar]:
        """Get only enabled sidecars"""
        return [s for s in self.get_all() if s.enabled]

    def clear(self):
        """Remove all sidecars"""
        self._sidecars.clear()
        self._execution_order.clear()

    def __len__(self) -> int:
        return len(self._sidecars)

    def __contains__(self, name: str) -> bool:
        return name in self._sidecars
