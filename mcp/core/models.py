"""
Core data models for MCP operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class ToolStatus(Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    category: str = "general"
    risk_level: str = "low"
    required_permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_name: str
    call_id: Optional[str]
    status: ToolStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "call_id": self.call_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ConnectionInfo:
    """Information about an MCP connection."""
    server_name: str
    connection_type: str  # stdio, http, websocket, etc.
    host: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerCapabilities:
    """Capabilities supported by an MCP server."""
    supports_tools: bool = True
    supports_resources: bool = False
    supports_prompts: bool = False
    supports_sampling: bool = False
    experimental_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
