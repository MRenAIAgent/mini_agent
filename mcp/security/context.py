"""
Security context for MCP operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Set, Dict, Any, Optional, List
import hashlib
import json


class SecurityLevel(Enum):
    """Security levels for MCP operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityContext:
    """
    Enhanced security context for MCP operations with comprehensive tracking.
    """

    # Identity
    agent_id: str
    agent_role: str
    session_id: str
    user_id: Optional[str] = None

    # Permissions and access control
    permissions: Set[str] = field(default_factory=set)
    denied_permissions: Set[str] = field(default_factory=set)
    temporary_permissions: Dict[str, datetime] = field(default_factory=dict)

    # Data classification
    data_labels: Set[str] = field(default_factory=set)
    data_sources: List[str] = field(default_factory=list)
    data_destinations: List[str] = field(default_factory=list)

    # Environment and deployment
    environment: str = "development"  # production, staging, development
    deployment_id: Optional[str] = None
    region: Optional[str] = None

    # Rate limiting and quotas
    rate_limits: Dict[str, int] = field(default_factory=dict)
    quota_limits: Dict[str, int] = field(default_factory=dict)
    call_counts: Dict[str, int] = field(default_factory=dict)

    # Security tracking
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    risk_score: float = 0.0
    threat_indicators: List[str] = field(default_factory=list)
    audit_required: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and initialize security context."""
        if not self.agent_id:
            raise ValueError("agent_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")

        # Generate request ID if not provided
        if not self.request_id:
            self.request_id = self._generate_request_id()

        # Initialize default rate limits if not provided
        if not self.rate_limits:
            self.rate_limits = self._get_default_rate_limits()

    def has_permission(self, permission: str) -> bool:
        """
        Check if context has required permission with wildcard support.

        Args:
            permission: Permission to check (e.g., "read:database")

        Returns:
            True if permission is granted
        """
        # Check if permission is explicitly denied
        if permission in self.denied_permissions:
            return False

        # Check for wildcard permission
        if "*" in self.permissions:
            return True

        # Check exact permission
        if permission in self.permissions:
            return True

        # Check category wildcard (e.g., "read:*" for "read:database")
        if ":" in permission:
            category = permission.split(":")[0]
            if f"{category}:*" in self.permissions:
                return True

        # Check temporary permissions
        if permission in self.temporary_permissions:
            if self.temporary_permissions[permission] > datetime.now():
                return True
            else:
                # Expired temporary permission
                del self.temporary_permissions[permission]

        return False

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if context has any of the required permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if context has all required permissions."""
        return all(self.has_permission(p) for p in permissions)

    def has_data_label(self, label: str) -> bool:
        """
        Check if context has a specific data label.

        Args:
            label: Data label to check (e.g., "sensitive", "pii")

        Returns:
            True if label is present
        """
        return label.lower() in {l.lower() for l in self.data_labels}

    def add_data_label(self, label: str) -> None:
        """Add a data classification label."""
        self.data_labels.add(label.lower())
        self.last_updated = datetime.now()

        # Update risk score based on data sensitivity
        if label.lower() in ["sensitive", "pii", "confidential"]:
            self.risk_score = min(1.0, self.risk_score + 0.2)

    def increment_call_count(self, resource: str) -> int:
        """
        Increment call count for a resource.

        Args:
            resource: Resource name (e.g., "api", "database")

        Returns:
            New call count
        """
        if resource not in self.call_counts:
            self.call_counts[resource] = 0
        self.call_counts[resource] += 1
        self.last_updated = datetime.now()
        return self.call_counts[resource]

    def check_rate_limit(self, resource: str) -> bool:
        """
        Check if rate limit is exceeded for a resource.

        Args:
            resource: Resource name

        Returns:
            True if within rate limit, False if exceeded
        """
        if resource not in self.rate_limits:
            return True  # No limit defined

        current_count = self.call_counts.get(resource, 0)
        limit = self.rate_limits[resource]
        return current_count < limit

    def grant_temporary_permission(
        self,
        permission: str,
        duration_seconds: int = 300
    ) -> None:
        """
        Grant temporary permission for a limited time.

        Args:
            permission: Permission to grant
            duration_seconds: Duration in seconds (default 5 minutes)
        """
        expiry = datetime.now().timestamp() + duration_seconds
        self.temporary_permissions[permission] = datetime.fromtimestamp(expiry)
        self.last_updated = datetime.now()

    def revoke_permission(self, permission: str) -> None:
        """Revoke a permission and add to denied list."""
        self.permissions.discard(permission)
        self.denied_permissions.add(permission)
        self.temporary_permissions.pop(permission, None)
        self.last_updated = datetime.now()

    def elevate_security_level(self) -> None:
        """Elevate security level by one tier."""
        levels = list(SecurityLevel)
        current_index = levels.index(self.security_level)
        if current_index < len(levels) - 1:
            self.security_level = levels[current_index + 1]
            self.audit_required = True
            self.last_updated = datetime.now()

    def add_threat_indicator(self, indicator: str) -> None:
        """Add a threat indicator and update risk score."""
        self.threat_indicators.append(indicator)
        self.risk_score = min(1.0, self.risk_score + 0.1)
        self.last_updated = datetime.now()

        # Auto-elevate security for critical threats
        if len(self.threat_indicators) >= 3:
            self.elevate_security_level()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "permissions": list(self.permissions),
            "denied_permissions": list(self.denied_permissions),
            "data_labels": list(self.data_labels),
            "environment": self.environment,
            "security_level": self.security_level.value,
            "risk_score": self.risk_score,
            "call_counts": self.call_counts,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "request_id": self.request_id,
            "metadata": self.metadata,
        }

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        data = f"{self.agent_id}:{self.session_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _get_default_rate_limits(self) -> Dict[str, int]:
        """Get default rate limits based on environment."""
        if self.environment == "production":
            return {
                "api": 1000,
                "database": 500,
                "email": 100,
                "high_risk": 50,
            }
        elif self.environment == "staging":
            return {
                "api": 500,
                "database": 200,
                "email": 50,
                "high_risk": 20,
            }
        else:  # development
            return {
                "api": 100,
                "database": 50,
                "email": 10,
                "high_risk": 5,
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityContext":
        """Create SecurityContext from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            agent_role=data.get("agent_role", "user"),
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            permissions=set(data.get("permissions", [])),
            denied_permissions=set(data.get("denied_permissions", [])),
            data_labels=set(data.get("data_labels", [])),
            environment=data.get("environment", "development"),
            security_level=SecurityLevel(data.get("security_level", "medium")),
            risk_score=data.get("risk_score", 0.0),
            metadata=data.get("metadata", {}),
        )