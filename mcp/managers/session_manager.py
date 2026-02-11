"""
Session management for MCP operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class MCPSession:
    """Represents an MCP session."""
    session_id: str
    agent_id: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manage MCP sessions."""

    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}

    def create_session(self, agent_id: str) -> MCPSession:
        """Create a new session."""
        import uuid
        session_id = str(uuid.uuid4())
        session = MCPSession(session_id=session_id, agent_id=agent_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str):
        """Close and remove a session."""
        self.sessions.pop(session_id, None)
