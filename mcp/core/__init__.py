"""
Core MCP components and base classes.
"""

from .exceptions import (
    MCPError,
    MCPSecurityError,
    MCPConnectionError,
    MCPValidationError,
    MCPTimeoutError,
    MCPConfigurationError,
)

from .interfaces import (
    MCPProtocol,
    MCPTool,
    MCPConnection,
    MCPMetadata,
)

from .models import (
    ToolCall,
    ToolResult,
    ToolDefinition,
    ConnectionInfo,
    ServerCapabilities,
)

__all__ = [
    # Exceptions
    "MCPError",
    "MCPSecurityError",
    "MCPConnectionError",
    "MCPValidationError",
    "MCPTimeoutError",
    "MCPConfigurationError",

    # Interfaces
    "MCPProtocol",
    "MCPTool",
    "MCPConnection",
    "MCPMetadata",

    # Models
    "ToolCall",
    "ToolResult",
    "ToolDefinition",
    "ConnectionInfo",
    "ServerCapabilities",
]