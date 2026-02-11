"""
MCP Security Layer

Provides security controls for MCP tool execution including:
- Policy-based access control
- Input validation and sanitization
- Audit logging
- Authentication management
"""

from .policy_engine import (
    PolicyEngine,
    PolicyAction,
    PolicyDecision,
    PolicyRule,
    SecurityPolicy,
    SecurityContext,
)

from .input_validator import (
    InputValidator,
    ValidationResult,
)

__all__ = [
    # Policy Engine
    "PolicyEngine",
    "PolicyAction",
    "PolicyDecision",
    "PolicyRule",
    "SecurityPolicy",
    "SecurityContext",
    # Input Validator
    "InputValidator",
    "ValidationResult",
]

__version__ = "0.1.0"
