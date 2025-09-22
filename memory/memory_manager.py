"""Core memory manager that orchestrates all memory operations."""

from typing import Dict, List, Optional, Any, Callable, Awaitable
import asyncio
from datetime import datetime

from .memory_store import MemoryStore, MemoryEntry, InMemoryStore
from .memory_context import MemoryContext
from .context_manager import ContextManager
from .retrieval_strategy import RetrievalStrategy, SimilarityRetrieval

# Import backend support
try:
    from .backends import create_backend, validate_backend_config, MemoryBackend
except ImportError:
    # Fallback if backends are not available
    create_backend = None
    validate_backend_config = None
    MemoryBackend = None


class CoreMemoryManager:
    """
    Core memory manager that orchestrates memory operations.

    This manager provides a unified interface for memory storage, retrieval,
    and context management. It coordinates between different memory backends
    and retrieval strategies.
    """

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        retrieval_strategy: Optional[RetrievalStrategy] = None,
        auto_save_interval: int = 300,  # 5 minutes
        backend_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the core memory manager.

        Args:
            memory_store: Backend store for persistent memory
            retrieval_strategy: Strategy for memory retrieval and ranking
            auto_save_interval: Automatic save interval in seconds
            backend_config: Configuration for memory backend switching
        """
        self.memory_store = memory_store or InMemoryStore()
        self.retrieval_strategy = retrieval_strategy or SimilarityRetrieval()
        self.context_manager = ContextManager(self.memory_store)

        # Backend switching support
        self.current_backend: Optional[MemoryBackend] = None
        self.backend_config = backend_config
        self._backend_enabled = False

        # Initialize backend if config provided
        if backend_config and create_backend:
            try:
                backend_type = backend_config.get("backend_type", "in_memory")
                self.current_backend = create_backend(backend_type, backend_config)
                self._backend_enabled = True
            except Exception:
                # Fallback to default memory store if backend fails
                pass

        self.auto_save_interval = auto_save_interval
        self._auto_save_task: Optional[asyncio.Task] = None
        self._running = False

        # Callbacks for memory events
        self._on_memory_stored: Optional[Callable[[MemoryEntry], Awaitable[None]]] = None
        self._on_context_updated: Optional[Callable[[MemoryContext], Awaitable[None]]] = None

    async def start(self) -> None:
        """Start the memory manager and background tasks."""
        if self._running:
            return

        self._running = True

        # Start auto-save task
        if self.auto_save_interval > 0:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

    async def stop(self) -> None:
        """Stop the memory manager and clean up."""
        self._running = False

        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass

        # Save all active contexts
        await self._save_all_contexts()

    async def store_memory(
        self,
        content: str,
        importance: float = 1.0,
        session_id: Optional[str] = None,
        **metadata
    ) -> bool:
        """
        Store a new memory entry.

        Args:
            content: The content to store
            importance: Importance score (0.0 to 1.0)
            session_id: Optional session ID for context
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create memory entry
            entry = MemoryEntry(
                content=content,
                importance=importance,
                metadata=metadata
            )

            # Add session context if available
            if session_id:
                context = await self.context_manager.get_context(session_id)
                entry.metadata.update({
                    'session_id': session_id,
                    'user_id': context.user_id,
                    'context_name': context.context_name
                })

            # Store in backend
            success = await self.memory_store.store(entry)

            # Trigger callback
            if success and self._on_memory_stored:
                await self._on_memory_stored(entry)

            return success

        except Exception as e:
            print(f"Error storing memory: {e}")
            return False

    async def search_memory(
        self,
        query: str,
        limit: int = 10,
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """
        Search for relevant memories.

        Args:
            query: Search query
            limit: Maximum number of results
            session_id: Optional session ID for context
            filters: Optional filters to apply

        Returns:
            List of relevant memory entries
        """
        try:
            # Get all relevant entries from store
            store_results = await self.memory_store.search(query, limit * 2, filters)

            # Use retrieval strategy to rank and filter
            ranked_results = await self.retrieval_strategy.retrieve(
                query=query,
                entries=store_results,
                limit=limit,
                filters=filters
            )

            # Update access counts
            for entry in ranked_results:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                await self.memory_store.update(entry)

            return ranked_results

        except Exception as e:
            print(f"Error searching memory: {e}")
            return []

    async def get_context_memory(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        context_name: str = "default"
    ) -> MemoryContext:
        """
        Get or create a memory context for a session.

        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            context_name: Name of the context

        Returns:
            Memory context for the session
        """
        return await self.context_manager.get_context(session_id, user_id, context_name)

    async def add_conversation_turn(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        **metadata
    ) -> bool:
        """
        Add a conversation turn to the context.

        Args:
            session_id: Session identifier
            user_input: User's input
            agent_response: Agent's response
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.context_manager.add_to_context(
                session_id, user_input, agent_response, **metadata
            )

            # Trigger callback
            if success and self._on_context_updated:
                context = await self.context_manager.get_context(session_id)
                await self._on_context_updated(context)

            return success

        except Exception as e:
            print(f"Error adding conversation turn: {e}")
            return False

    async def get_relevant_context(
        self,
        session_id: str,
        query: str,
        include_conversation: bool = True,
        include_memories: bool = True,
        memory_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for a query including conversation and memories.

        Args:
            session_id: Session identifier
            query: The query to find relevant context for
            include_conversation: Whether to include conversation history
            include_memories: Whether to include relevant memories
            memory_limit: Maximum number of memories to include

        Returns:
            Dictionary containing relevant context
        """
        context_data = {}

        try:
            # Get conversation context
            if include_conversation:
                context = await self.context_manager.get_context(session_id)
                context_data['conversation'] = {
                    'recent_turns': context.get_recent_turns(5),
                    'summary': context.get_summary_context(),
                    'keywords': context.get_context_keywords()
                }

            # Get relevant memories
            if include_memories:
                memories = await self.context_manager.get_relevant_memories(
                    session_id, query, memory_limit
                )
                context_data['memories'] = [
                    {
                        'content': memory.content,
                        'metadata': memory.metadata,
                        'importance': memory.importance,
                        'timestamp': memory.timestamp.isoformat()
                    }
                    for memory in memories
                ]

            return context_data

        except Exception as e:
            print(f"Error getting relevant context: {e}")
            return {}

    async def summarize_context(
        self,
        session_id: str,
        max_length: int = 500
    ) -> str:
        """
        Get a summarized version of the context.

        Args:
            session_id: Session identifier
            max_length: Maximum length of summary

        Returns:
            Summarized context text
        """
        try:
            context = await self.context_manager.get_context(session_id)
            summary = context.get_summary_context()

            # Truncate if necessary
            if len(summary) > max_length:
                summary = summary[:max_length - 3] + "..."

            return summary

        except Exception:
            return "No context available."

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all data for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        return await self.context_manager.clear_context(session_id)

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory system statistics.

        Returns:
            Dictionary containing memory statistics
        """
        try:
            store_stats = await self.memory_store.get_stats()
            context_stats = await self.context_manager.get_memory_stats()

            return {
                'store': store_stats,
                'context': context_stats,
                'manager': {
                    'running': self._running,
                    'auto_save_interval': self.auto_save_interval
                }
            }

        except Exception as e:
            return {'error': str(e)}

    def set_memory_callback(
        self,
        callback: Callable[[MemoryEntry], Awaitable[None]]
    ) -> None:
        """Set callback for when memories are stored."""
        self._on_memory_stored = callback

    def set_context_callback(
        self,
        callback: Callable[[MemoryContext], Awaitable[None]]
    ) -> None:
        """Set callback for when contexts are updated."""
        self._on_context_updated = callback

    # Backend switching methods
    async def set_backend(self, backend_config: Dict[str, Any]) -> None:
        """
        Switch to a different memory backend.

        Args:
            backend_config: Configuration for the new backend
        """
        if not create_backend:
            raise ImportError("Backend switching not available - missing dependencies")

        # Validate configuration
        backend_type = backend_config.get("backend_type")
        if not backend_type:
            raise ValueError("backend_type is required in backend_config")

        if validate_backend_config:
            validate_backend_config(backend_type, backend_config)

        # Create new backend
        try:
            new_backend = create_backend(backend_type, backend_config)

            # Initialize if needed
            if hasattr(new_backend, 'initialize'):
                await new_backend.initialize()

            # Update backend
            old_backend = self.current_backend
            self.current_backend = new_backend
            self.backend_config = backend_config
            self._backend_enabled = True

            # Clean up old backend
            if old_backend and hasattr(old_backend, 'close'):
                try:
                    await old_backend.close()
                except Exception:
                    pass

        except Exception as e:
            raise RuntimeError(f"Failed to switch backend: {e}")

    async def store_memory(self, content: str, importance: float = 0.5,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store memory with backend support.

        Args:
            content: Memory content
            importance: Importance score (0.0 to 1.0)
            metadata: Optional metadata

        Returns:
            Memory entry ID
        """
        if self._backend_enabled and self.current_backend:
            # Use backend for storage
            memory_entry = {
                "entry_id": f"mem_{datetime.now().timestamp()}",
                "content": content,
                "entry_type": "memory",
                "importance_score": importance,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            result = await self.current_backend.store_memory(memory_entry)
            return result.get("entry_id", memory_entry["entry_id"])
        else:
            # Fallback to original memory store
            entry = MemoryEntry(
                content=content,
                importance=importance,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            await self.memory_store.store(entry)
            return entry.id

    async def retrieve_memory(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve memory by ID with backend support.

        Args:
            entry_id: Memory entry ID

        Returns:
            Memory entry or None
        """
        if self._backend_enabled and self.current_backend:
            return await self.current_backend.retrieve_memory(entry_id)
        else:
            # Fallback to original memory store
            entry = await self.memory_store.get(entry_id)
            if entry:
                return {
                    "entry_id": entry.id,
                    "content": entry.content,
                    "importance_score": entry.importance,
                    "created_at": entry.created_at.isoformat(),
                    "metadata": entry.metadata
                }
            return None

    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories with backend support.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        if self._backend_enabled and self.current_backend:
            return await self.current_backend.search_memory(query, limit)
        else:
            # Fallback to original search
            results = await self.retrieval_strategy.retrieve(
                query, self.memory_store, limit
            )
            return [
                {
                    "entry_id": entry.id,
                    "content": entry.content,
                    "importance_score": entry.importance,
                    "created_at": entry.created_at.isoformat(),
                    "metadata": entry.metadata,
                    "relevance_score": 1.0
                }
                for entry in results
            ]

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about current backend.

        Returns:
            Backend information dict
        """
        if self._backend_enabled and self.current_backend:
            return {
                "backend_enabled": True,
                "backend_type": self.backend_config.get("backend_type", "unknown"),
                "backend_config": self.backend_config
            }
        else:
            return {
                "backend_enabled": False,
                "backend_type": "default",
                "backend_config": None
            }

    async def _auto_save_loop(self) -> None:
        """Background task for automatic saving."""
        while self._running:
            try:
                await asyncio.sleep(self.auto_save_interval)
                if self._running:
                    await self._save_all_contexts()
                    await self.context_manager.cleanup_old_contexts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in auto-save loop: {e}")

    async def _save_all_contexts(self) -> None:
        """Save all active contexts."""
        try:
            active_sessions = self.context_manager.get_active_contexts()
            for session_id in active_sessions:
                context = await self.context_manager.get_context(session_id)
                await self.context_manager.save_context(context)
        except Exception as e:
            print(f"Error saving contexts: {e}")