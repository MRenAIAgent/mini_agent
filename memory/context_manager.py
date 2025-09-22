"""Context manager for handling memory contexts."""

from typing import Dict, Optional, List, Any
import asyncio
from datetime import datetime, timedelta

from .memory_context import MemoryContext
from .memory_store import MemoryStore, MemoryEntry


class ContextManager:
    """Manages memory contexts and their lifecycle."""

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self._active_contexts: Dict[str, MemoryContext] = {}
        self._context_timeout = timedelta(hours=1)  # Default timeout

    async def get_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        context_name: str = "default"
    ) -> MemoryContext:
        """Get or create a memory context."""

        # Check if context is already active
        if session_id in self._active_contexts:
            context = self._active_contexts[session_id]
            context.updated_at = datetime.now()
            return context

        # Try to load from memory store
        context = await self._load_context(session_id, user_id, context_name)
        if context is None:
            # Create new context
            context = MemoryContext(
                session_id=session_id,
                user_id=user_id,
                context_name=context_name
            )

        # Activate context
        self._active_contexts[session_id] = context
        return context

    async def save_context(self, context: MemoryContext) -> bool:
        """Save a context to persistent storage."""
        try:
            # Create memory entry for the context
            entry = MemoryEntry(
                id=f"context_{context.session_id}",
                content=context.get_conversation_text(),
                metadata={
                    "type": "context",
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "context_name": context.context_name,
                    "context_data": context.to_dict(),
                    "turn_count": len(context.conversation_turns)
                },
                importance=self._calculate_context_importance(context)
            )

            return await self.memory_store.store(entry)

        except Exception as e:
            print(f"Error saving context: {e}")
            return False

    async def _load_context(
        self,
        session_id: str,
        user_id: Optional[str],
        context_name: str
    ) -> Optional[MemoryContext]:
        """Load a context from persistent storage."""
        try:
            # Try to retrieve the specific context
            entry = await self.memory_store.retrieve(f"context_{session_id}")
            if entry and "context_data" in entry.metadata:
                return MemoryContext.from_dict(entry.metadata["context_data"])

            # If not found, try to search for similar contexts
            if user_id:
                similar_contexts = await self._find_similar_contexts(user_id, context_name)
                if similar_contexts:
                    # Return the most recent one
                    return similar_contexts[0]

        except Exception as e:
            print(f"Error loading context: {e}")

        return None

    async def _find_similar_contexts(
        self,
        user_id: str,
        context_name: str
    ) -> List[MemoryContext]:
        """Find similar contexts for the user."""
        try:
            # Search for contexts with matching user_id and context_name
            search_results = await self.memory_store.search(
                query=f"user:{user_id} context:{context_name}",
                limit=5,
                filters={"type": "context"}
            )

            contexts = []
            for entry in search_results:
                if "context_data" in entry.metadata:
                    context = MemoryContext.from_dict(entry.metadata["context_data"])
                    contexts.append(context)

            # Sort by most recent
            contexts.sort(key=lambda x: x.updated_at, reverse=True)
            return contexts

        except Exception:
            return []

    def _calculate_context_importance(self, context: MemoryContext) -> float:
        """Calculate the importance score for a context."""
        importance = 0.5  # Base importance

        # More turns = more important
        turn_score = min(len(context.conversation_turns) / 20, 0.3)
        importance += turn_score

        # Recent activity = more important
        age_hours = (datetime.now() - context.updated_at).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / 24)) * 0.2  # Decay over 24 hours
        importance += recency_score

        return min(1.0, importance)

    async def add_to_context(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        **metadata
    ) -> bool:
        """Add a conversation turn to the context."""
        try:
            context = await self.get_context(session_id)
            context.add_turn(user_input, agent_response, **metadata)

            # Save context periodically
            if len(context.conversation_turns) % 5 == 0:  # Every 5 turns
                await self.save_context(context)

            return True

        except Exception as e:
            print(f"Error adding to context: {e}")
            return False

    async def get_relevant_memories(
        self,
        session_id: str,
        query: str,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Get relevant memories for the current context."""
        try:
            context = await self.get_context(session_id)

            # Include context keywords in the search
            keywords = context.get_context_keywords()
            enhanced_query = f"{query} {' '.join(keywords[:5])}"

            # Search for relevant memories
            memories = await self.memory_store.search(
                query=enhanced_query,
                limit=limit
            )

            # Filter out the current context memory
            return [
                memory for memory in memories
                if not (memory.metadata.get("type") == "context" and
                       memory.metadata.get("session_id") == session_id)
            ]

        except Exception:
            return []

    async def store_memory(
        self,
        content: str,
        session_id: Optional[str] = None,
        importance: float = 1.0,
        **metadata
    ) -> bool:
        """Store a new memory entry."""
        try:
            entry = MemoryEntry(
                content=content,
                importance=importance,
                metadata=metadata
            )

            # Add session context if available
            if session_id and session_id in self._active_contexts:
                context = self._active_contexts[session_id]
                entry.metadata.update({
                    "session_id": session_id,
                    "user_id": context.user_id,
                    "context_name": context.context_name
                })

            return await self.memory_store.store(entry)

        except Exception as e:
            print(f"Error storing memory: {e}")
            return False

    async def cleanup_old_contexts(self) -> None:
        """Clean up old inactive contexts."""
        cutoff_time = datetime.now() - self._context_timeout
        to_remove = []

        for session_id, context in self._active_contexts.items():
            if context.updated_at < cutoff_time:
                # Save before removing
                await self.save_context(context)
                to_remove.append(session_id)

        for session_id in to_remove:
            del self._active_contexts[session_id]

    async def get_context_summary(self, session_id: str) -> str:
        """Get a summary of the current context."""
        try:
            context = await self.get_context(session_id)
            return context.get_summary_context()
        except Exception:
            return "No context available."

    async def clear_context(self, session_id: str) -> bool:
        """Clear a specific context."""
        try:
            if session_id in self._active_contexts:
                self._active_contexts[session_id].clear_conversation()
                await self.save_context(self._active_contexts[session_id])
                return True
            return False
        except Exception:
            return False

    def get_active_contexts(self) -> List[str]:
        """Get list of active context session IDs."""
        return list(self._active_contexts.keys())

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        store_stats = await self.memory_store.get_stats()

        return {
            **store_stats,
            "active_contexts": len(self._active_contexts),
            "context_timeout_hours": self._context_timeout.total_seconds() / 3600
        }