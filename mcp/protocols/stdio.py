"""
Standard I/O protocol implementation for MCP.
"""

from typing import Dict, Any, List, Optional
from ..core.interfaces import MCPProtocol, MCPTool


class StdioProtocol(MCPProtocol):
    """MCP protocol over standard I/O (subprocess communication)."""

    def __init__(self, command: str, args: List[str] = None):
        self.command = command
        self.args = args or []
        self.process = None

    async def connect(self) -> None:
        """Establish connection to MCP server via subprocess."""
        # Stub implementation
        pass

    async def disconnect(self) -> None:
        """Close subprocess connection."""
        # Stub implementation
        pass

    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send JSON-RPC request to subprocess."""
        # Stub implementation
        pass

    async def list_tools(self) -> List[MCPTool]:
        """List available tools from server."""
        # Stub implementation
        return []
