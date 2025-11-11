"""
MCP-specific exceptions with detailed error information.
"""

from typing import Optional, Dict, Any


class MCPError(Exception):
    """Base exception for all MCP-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class MCPSecurityError(MCPError):
    """Raised when security policies are violated."""

    def __init__(
        self,
        message: str,
        policy_name: Optional[str] = None,
        rule_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="SECURITY_VIOLATION", **kwargs)
        self.details.update({
            "policy_name": policy_name,
            "rule_name": rule_name,
        })


class MCPConnectionError(MCPError):
    """Raised when MCP connection fails."""

    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        connection_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="CONNECTION_ERROR", **kwargs)
        self.details.update({
            "server_name": server_name,
            "connection_type": connection_type,
        })


class MCPValidationError(MCPError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.details.update({
            "field_name": field_name,
            "validation_type": validation_type,
        })


class MCPTimeoutError(MCPError):
    """Raised when MCP operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.details.update({
            "timeout_seconds": timeout_seconds,
            "operation": operation,
        })


class MCPConfigurationError(MCPError):
    """Raised when MCP configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        self.details.update({
            "config_key": config_key,
            "config_file": config_file,
        })