"""Test-compatible ExecutionContext for unit tests."""

from typing import Dict, List, Any, Optional
from datetime import datetime


class ExecutionContext:
    """Test-compatible execution context."""

    def __init__(
        self,
        messages: List[Dict[str, str]] = None,
        tools: List[str] = None,
        metadata: Dict[str, Any] = None,
        max_iterations: int = 10,
        current_iteration: int = 0
    ):
        """Initialize execution context."""
        self.messages = messages or []
        self.tools = tools or []
        self.metadata = metadata or {}
        self.max_iterations = max_iterations
        self.current_iteration = current_iteration

    def add_message(self, role: str, content: str):
        """Add a message to the context."""
        self.messages.append({"role": role, "content": content})

    def increment_iteration(self):
        """Increment the current iteration."""
        self.current_iteration += 1

    def is_max_iterations_reached(self) -> bool:
        """Check if max iterations reached."""
        return self.current_iteration >= self.max_iterations

    def get_latest_message(self) -> Optional[Dict[str, str]]:
        """Get the latest message."""
        return self.messages[-1] if self.messages else None

    def get_messages_by_role(self, role: str) -> List[Dict[str, str]]:
        """Get messages by role."""
        return [msg for msg in self.messages if msg.get("role") == role]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messages": self.messages,
            "tools": self.tools,
            "metadata": self.metadata,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionContext':
        """Create from dictionary."""
        return cls(
            messages=data.get("messages", []),
            tools=data.get("tools", []),
            metadata=data.get("metadata", {}),
            max_iterations=data.get("max_iterations", 10),
            current_iteration=data.get("current_iteration", 0)
        )