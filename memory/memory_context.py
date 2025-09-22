"""Memory context for managing conversation and session state."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""

    user_input: str
    agent_response: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_input": self.user_input,
            "agent_response": self.agent_response,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "turn_id": self.turn_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        """Create from dictionary."""
        return cls(
            user_input=data["user_input"],
            agent_response=data["agent_response"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            turn_id=data.get("turn_id", str(uuid.uuid4()))
        )


@dataclass
class MemoryContext:
    """Context for managing memory across conversations and sessions."""

    # Session info
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    context_name: str = "default"

    # Conversation state
    conversation_turns: List[ConversationTurn] = field(default_factory=list)
    current_turn: Optional[ConversationTurn] = None

    # Context limits
    max_turns: int = 50
    max_context_length: int = 4000  # characters

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_turn(self, user_input: str, agent_response: str, **metadata) -> ConversationTurn:
        """Add a new conversation turn."""
        turn = ConversationTurn(
            user_input=user_input,
            agent_response=agent_response,
            metadata=metadata
        )

        self.conversation_turns.append(turn)
        self.current_turn = turn
        self.updated_at = datetime.now()

        # Maintain turn limit
        if len(self.conversation_turns) > self.max_turns:
            self.conversation_turns = self.conversation_turns[-self.max_turns:]

        return turn

    def get_recent_turns(self, count: int = 5) -> List[ConversationTurn]:
        """Get the most recent conversation turns."""
        return self.conversation_turns[-count:] if self.conversation_turns else []

    def get_conversation_text(self, max_length: Optional[int] = None) -> str:
        """Get conversation as formatted text."""
        if max_length is None:
            max_length = self.max_context_length

        conversation_parts = []
        total_length = 0

        # Add turns in reverse order until we hit length limit
        for turn in reversed(self.conversation_turns):
            turn_text = f"User: {turn.user_input}\nAssistant: {turn.agent_response}\n"
            if total_length + len(turn_text) > max_length:
                break
            conversation_parts.insert(0, turn_text)
            total_length += len(turn_text)

        return "\n".join(conversation_parts)

    def get_summary_context(self) -> str:
        """Get a summary of the conversation context."""
        if not self.conversation_turns:
            return "No conversation history."

        recent_turns = self.get_recent_turns(3)
        turn_summaries = []

        for turn in recent_turns:
            user_summary = turn.user_input[:100] + "..." if len(turn.user_input) > 100 else turn.user_input
            agent_summary = turn.agent_response[:100] + "..." if len(turn.agent_response) > 100 else turn.agent_response
            turn_summaries.append(f"User: {user_summary}\nAssistant: {agent_summary}")

        return "\n\n".join(turn_summaries)

    def get_context_keywords(self) -> List[str]:
        """Extract keywords from the conversation context."""
        all_text = " ".join([
            turn.user_input + " " + turn.agent_response
            for turn in self.conversation_turns
        ])

        # Simple keyword extraction (could be enhanced)
        words = all_text.lower().split()
        # Remove common words and get unique words
        common_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
            "do", "does", "did", "will", "would", "could", "should", "may", "might", "can",
            "this", "that", "these", "those", "what", "where", "when", "why", "how"
        }

        keywords = [word for word in set(words) if len(word) > 3 and word not in common_words]
        return keywords[:20]  # Return top 20 keywords

    def update_metadata(self, **metadata) -> None:
        """Update context metadata."""
        self.metadata.update(metadata)
        self.updated_at = datetime.now()

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_turns.clear()
        self.current_turn = None
        self.updated_at = datetime.now()

    def get_context_size(self) -> int:
        """Get the size of the context in characters."""
        return len(self.get_conversation_text())

    def should_summarize(self) -> bool:
        """Check if context should be summarized to save space."""
        return (
            len(self.conversation_turns) > self.max_turns * 0.8 or
            self.get_context_size() > self.max_context_length * 0.8
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context_name": self.context_name,
            "conversation_turns": [turn.to_dict() for turn in self.conversation_turns],
            "current_turn": self.current_turn.to_dict() if self.current_turn else None,
            "max_turns": self.max_turns,
            "max_context_length": self.max_context_length,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryContext':
        """Create from dictionary."""
        context = cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            context_name=data.get("context_name", "default"),
            max_turns=data.get("max_turns", 50),
            max_context_length=data.get("max_context_length", 4000),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )

        # Load conversation turns
        if "conversation_turns" in data:
            context.conversation_turns = [
                ConversationTurn.from_dict(turn_data)
                for turn_data in data["conversation_turns"]
            ]

        # Load current turn
        if "current_turn" in data and data["current_turn"]:
            context.current_turn = ConversationTurn.from_dict(data["current_turn"])

        return context