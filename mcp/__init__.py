"""
MCP (Model Context Protocol) Security Layer

This module provides a secure, extensible framework for managing MCP servers
and tools with comprehensive security controls, intelligent selection, and
robust error handling.

Architecture:
- Core: Base classes and interfaces
- Security: Policy engine, input validation, audit logging
- Selection: Intelligent MCP/tool selection based on context
- Protocols: MCP protocol implementations (stdio, HTTP, etc.)
- Managers: Connection, session, and lifecycle management
- Utils: Shared utilities and helpers
"""

from .core import MCPError, MCPSecurityError, MCPConnectionError
from .security import SecurityContext, PolicyEngine, InputValidator, AuditLogger
from .selection import MCPSelectionEngine, MCPSession
from .managers import MCPManager, ConnectionPool
from .protocols import MCPProtocol, StdioProtocol

__version__ = "1.0.0"

__all__ = [
    # Core
    "MCPError",
    "MCPSecurityError",
    "MCPConnectionError",

    # Security
    "SecurityContext",
    "PolicyEngine",
    "InputValidator",
    "AuditLogger",

    # Selection
    "MCPSelectionEngine",
    "MCPSession",

    # Managers
    "MCPManager",
    "ConnectionPool",

    # Protocols
    "MCPProtocol",
    "StdioProtocol",
]