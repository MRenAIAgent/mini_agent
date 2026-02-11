"""
Audit logger for MCP security events.
"""

import json
import logging
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import asyncio
from collections import deque
import threading

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication & Authorization
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # Tool Execution
    TOOL_EXECUTION = "tool_execution"
    TOOL_SUCCESS = "tool_success"
    TOOL_FAILURE = "tool_failure"
    TOOL_BLOCKED = "tool_blocked"

    # Policy Events
    POLICY_VIOLATION = "policy_violation"
    POLICY_OVERRIDE = "policy_override"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Security Events
    SECURITY_ALERT = "security_alert"
    INJECTION_DETECTED = "injection_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data Events
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    DATA_EXPORT = "data_export"

    # System Events
    SYSTEM_ERROR = "system_error"
    CONFIG_CHANGE = "config_change"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_FAILED = "connection_failed"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    # Core fields
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    message: str

    # Context
    agent_id: str
    session_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    # Event details
    tool_name: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None

    # Security context
    permissions: List[str] = field(default_factory=list)
    data_labels: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    threat_indicators: List[str] = field(default_factory=list)

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        data = data.copy()
        data['event_type'] = AuditEventType(data['event_type'])
        data['severity'] = AuditSeverity(data['severity'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class AuditLogger:
    """
    Comprehensive audit logger with multiple backends and buffering.
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        buffer_size: int = 1000,
        flush_interval: int = 5,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_remote: bool = False,
        remote_endpoint: Optional[str] = None,
    ):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file
            buffer_size: Size of event buffer
            flush_interval: Seconds between buffer flushes
            enable_console: Log to console
            enable_file: Log to file
            enable_remote: Send to remote endpoint
            remote_endpoint: Remote logging endpoint URL
        """
        self.log_file = log_file or Path("audit.log")
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # Backends
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_remote = enable_remote
        self.remote_endpoint = remote_endpoint

        # Event buffer
        self.event_buffer: deque = deque(maxlen=buffer_size)
        self.buffer_lock = threading.Lock()

        # Statistics
        self.event_counts: Dict[AuditEventType, int] = {}
        self.severity_counts: Dict[AuditSeverity, int] = {}

        # Start flush timer
        self._start_flush_timer()

        # Configure file handler if enabled
        if self.enable_file:
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Setup file handler for audit logs."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.file_handler = logging.FileHandler(
                self.log_file,
                mode='a',
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.file_handler.setFormatter(formatter)
        except Exception as e:
            logger.error(f"Failed to setup file handler: {e}")
            self.enable_file = False

    def _start_flush_timer(self) -> None:
        """Start periodic buffer flush."""
        async def flush_periodically():
            while True:
                await asyncio.sleep(self.flush_interval)
                self.flush_buffer()

        # Run in background (simplified for now)
        # In production, use proper async task management
        pass

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        # Update statistics
        self.event_counts[event.event_type] = \
            self.event_counts.get(event.event_type, 0) + 1
        self.severity_counts[event.severity] = \
            self.severity_counts.get(event.severity, 0) + 1

        # Add to buffer
        with self.buffer_lock:
            self.event_buffer.append(event)

        # Immediate flush for critical events
        if event.severity == AuditSeverity.CRITICAL:
            self.flush_buffer()

        # Console logging
        if self.enable_console:
            self._log_to_console(event)

    def _log_to_console(self, event: AuditEvent) -> None:
        """Log event to console."""
        log_level = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }.get(event.severity, logging.INFO)

        logger.log(
            log_level,
            f"[AUDIT] {event.event_type.value}: {event.message}",
            extra={"audit_event": event.to_dict()}
        )

    def flush_buffer(self) -> None:
        """Flush event buffer to storage."""
        with self.buffer_lock:
            events_to_flush = list(self.event_buffer)
            self.event_buffer.clear()

        if not events_to_flush:
            return

        # Write to file
        if self.enable_file:
            self._write_to_file(events_to_flush)

        # Send to remote
        if self.enable_remote:
            self._send_to_remote(events_to_flush)

    def _write_to_file(self, events: List[AuditEvent]) -> None:
        """Write events to file."""
        try:
            with open(self.log_file, 'a') as f:
                for event in events:
                    f.write(event.to_json() + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit events to file: {e}")

    def _send_to_remote(self, events: List[AuditEvent]) -> None:
        """Send events to remote endpoint."""
        # Implement remote logging (e.g., to Elasticsearch, Splunk, etc.)
        pass

    def create_event(
        self,
        event_type: AuditEventType,
        message: str,
        agent_id: str,
        session_id: str,
        severity: Optional[AuditSeverity] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Helper to create and log an audit event.

        Args:
            event_type: Type of event
            message: Event message
            agent_id: Agent identifier
            session_id: Session identifier
            severity: Event severity (auto-determined if None)
            **kwargs: Additional event fields

        Returns:
            Created audit event
        """
        # Auto-determine severity if not provided
        if severity is None:
            severity = self._determine_severity(event_type)

        # Generate event ID
        event_id = self._generate_event_id()

        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            message=message,
            agent_id=agent_id,
            session_id=session_id,
            **kwargs
        )

        # Log it
        self.log_event(event)

        return event

    def _determine_severity(self, event_type: AuditEventType) -> AuditSeverity:
        """Determine severity based on event type."""
        severity_map = {
            # Critical events
            AuditEventType.POLICY_VIOLATION: AuditSeverity.CRITICAL,
            AuditEventType.INJECTION_DETECTED: AuditSeverity.CRITICAL,
            AuditEventType.SECURITY_ALERT: AuditSeverity.CRITICAL,

            # Error events
            AuditEventType.AUTH_FAILURE: AuditSeverity.ERROR,
            AuditEventType.TOOL_FAILURE: AuditSeverity.ERROR,
            AuditEventType.PERMISSION_DENIED: AuditSeverity.ERROR,
            AuditEventType.SYSTEM_ERROR: AuditSeverity.ERROR,

            # Warning events
            AuditEventType.RATE_LIMIT_EXCEEDED: AuditSeverity.WARNING,
            AuditEventType.SUSPICIOUS_ACTIVITY: AuditSeverity.WARNING,
            AuditEventType.TOOL_BLOCKED: AuditSeverity.WARNING,

            # Info events
            AuditEventType.TOOL_SUCCESS: AuditSeverity.INFO,
            AuditEventType.AUTH_SUCCESS: AuditSeverity.INFO,
            AuditEventType.DATA_ACCESS: AuditSeverity.INFO,
        }

        return severity_map.get(event_type, AuditSeverity.INFO)

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        data = f"{datetime.now().isoformat()}:{id(self)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def log_tool_execution(
        self,
        agent_id: str,
        session_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Any] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log tool execution event.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            tool_name: Name of tool executed
            arguments: Tool arguments
            result: Execution result
            success: Whether execution succeeded
            error: Error message if failed
            **kwargs: Additional metadata
        """
        event_type = (
            AuditEventType.TOOL_SUCCESS
            if success
            else AuditEventType.TOOL_FAILURE
        )

        message = f"Tool '{tool_name}' {'succeeded' if success else 'failed'}"
        if error:
            message += f": {error}"

        self.create_event(
            event_type=event_type,
            message=message,
            agent_id=agent_id,
            session_id=session_id,
            tool_name=tool_name,
            action="execute",
            result=str(result) if result else None,
            error_details=error,
            metadata={"arguments": arguments, **kwargs}
        )

    def log_security_violation(
        self,
        agent_id: str,
        session_id: str,
        violation_type: str,
        details: str,
        tool_name: Optional[str] = None,
        threat_indicators: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        Log security violation.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            violation_type: Type of violation
            details: Violation details
            tool_name: Related tool name
            threat_indicators: Detected threat indicators
            **kwargs: Additional metadata
        """
        self.create_event(
            event_type=AuditEventType.SECURITY_ALERT,
            message=f"Security violation: {violation_type} - {details}",
            agent_id=agent_id,
            session_id=session_id,
            severity=AuditSeverity.CRITICAL,
            tool_name=tool_name,
            threat_indicators=threat_indicators or [],
            metadata={"violation_type": violation_type, **kwargs}
        )

    def log_permission_check(
        self,
        agent_id: str,
        session_id: str,
        permission: str,
        granted: bool,
        resource: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log permission check.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            permission: Permission checked
            granted: Whether permission was granted
            resource: Resource being accessed
            **kwargs: Additional metadata
        """
        event_type = (
            AuditEventType.PERMISSION_GRANTED
            if granted
            else AuditEventType.PERMISSION_DENIED
        )

        message = f"Permission '{permission}' {'granted' if granted else 'denied'}"
        if resource:
            message += f" for resource '{resource}'"

        self.create_event(
            event_type=event_type,
            message=message,
            agent_id=agent_id,
            session_id=session_id,
            resource=resource,
            permissions=[permission],
            metadata=kwargs
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics."""
        return {
            "total_events": sum(self.event_counts.values()),
            "event_counts": {
                k.value: v for k, v in self.event_counts.items()
            },
            "severity_counts": {
                k.value: v for k, v in self.severity_counts.items()
            },
            "buffer_size": len(self.event_buffer),
        }

    def search_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Search audit events (simplified implementation).

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            agent_id: Filter by agent
            session_id: Filter by session
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum results

        Returns:
            List of matching events
        """
        # This is a simplified implementation
        # In production, use proper database queries
        results = []

        # Search in buffer
        for event in self.event_buffer:
            if event_type and event.event_type != event_type:
                continue
            if severity and event.severity != severity:
                continue
            if agent_id and event.agent_id != agent_id:
                continue
            if session_id and event.session_id != session_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            results.append(event)
            if len(results) >= limit:
                break

        return results