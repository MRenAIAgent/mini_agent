"""
Core interfaces for MCP components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class MCPProtocol(ABC):
    """Base protocol interface for MCP communication."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send request to MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List["MCPTool"]:
        """List available tools from server."""
        pass


class MCPTool(ABC):
    """Base interface for MCP tools."""

    @abstractmethod
    def get_name(self) -> str:
        """Get tool name."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get tool description."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool input schema."""
        pass

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute tool with given arguments."""
        pass


class MCPConnection(ABC):
    """Base interface for MCP connections."""

    @abstractmethod
    async def open(self) -> None:
        """Open the connection."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Check if connection is alive."""
        pass


@dataclass
class MCPMetadata:
    """Metadata for MCP servers and tools."""
    name: str
    version: str
    description: str
    author: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
