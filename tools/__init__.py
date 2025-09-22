"""
Tool/MCP Abstraction Layer

Lightweight abstraction for tool management and MCP integration.
Provides unified interfaces without specific tool implementations.
"""

from .tool_manager import ToolManager
from .tool_interfaces import ToolCall, ToolResult, ToolDefinition
from .mcp_adapter import MCPAdapter, MCPConnection
from .tool_registry import ToolRegistry

__all__ = [
    "ToolManager",
    "ToolCall",
    "ToolResult",
    "ToolDefinition",
    "MCPAdapter",
    "MCPConnection",
    "ToolRegistry"
]