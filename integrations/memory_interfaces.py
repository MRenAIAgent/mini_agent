"""
Memory Backend Integration Interfaces

Standardized interfaces for integrating different memory backends
(Memgraph, Neo4j, in-memory, etc.) with the core agent memory system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MemoryBackendType(Enum):
    """Types of memory backends."""
    IN_MEMORY = "in_memory"
    MEMGRAPH = "memgraph"
    NEO4J = "neo4j"
    REDIS = "redis"
    SQLITE = "sqlite"
    GRAPHITI = "graphiti"


@dataclass
class MemoryConnection:
    """Memory backend connection configuration."""

    backend_type: MemoryBackendType
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    ssl_enabled: bool = False
    connection_timeout: float = 30.0
    pool_size: int = 10
    extra_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}


@dataclass
class MemoryEntry:
    """Standard memory entry format."""

    id: str
    content: str
    importance: float
    timestamp: datetime
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None
    relationships: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.relationships is None:
            self.relationships = []


@dataclass
class MemoryQuery:
    """Memory query specification."""

    query_text: str
    session_id: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = None
    similarity_threshold: float = 0.7

    def __post_init__(self):
        if self.metadata_filters is None:
            self.metadata_filters = {}


@dataclass
class MemoryStats:
    """Memory backend statistics."""

    total_entries: int
    sessions_count: int
    average_importance: float
    storage_size_mb: float
    query_count: int
    avg_query_time_ms: float
    backend_type: str
    connection_status: str


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""

    def __init__(self, connection: MemoryConnection):
        self.connection = connection
        self.is_connected = False
        self.query_count = 0
        self.total_query_time = 0.0

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the memory backend.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the memory backend."""
        pass

    @abstractmethod
    async def store_entry(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry.

        Args:
            entry: Memory entry to store

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def retrieve_entries(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Retrieve memory entries based on query.

        Args:
            query: Memory query specification

        Returns:
            List of matching memory entries
        """
        pass

    @abstractmethod
    async def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory entry.

        Args:
            entry_id: ID of entry to update
            updates: Fields to update

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a memory entry.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def create_relationship(
        self,
        from_entry_id: str,
        to_entry_id: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a relationship between memory entries.

        Args:
            from_entry_id: Source entry ID
            to_entry_id: Target entry ID
            relationship_type: Type of relationship
            metadata: Optional relationship metadata

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_related_entries(
        self,
        entry_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 1
    ) -> List[Tuple[MemoryEntry, str, int]]:
        """
        Get entries related to a given entry.

        Args:
            entry_id: Source entry ID
            relationship_types: Types of relationships to follow
            max_depth: Maximum traversal depth

        Returns:
            List of (entry, relationship_type, depth) tuples
        """
        pass

    @abstractmethod
    async def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        session_id: Optional[str] = None
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Search for entries by embedding similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            session_id: Optional session filter

        Returns:
            List of (entry, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of a session's memories.

        Args:
            session_id: Session ID

        Returns:
            Session summary dictionary
        """
        pass

    @abstractmethod
    async def cleanup_old_entries(
        self,
        max_age_days: int,
        min_importance: float = 0.0
    ) -> int:
        """
        Clean up old memory entries.

        Args:
            max_age_days: Maximum age in days
            min_importance: Minimum importance to keep

        Returns:
            Number of entries deleted
        """
        pass

    @abstractmethod
    async def get_backend_stats(self) -> MemoryStats:
        """
        Get memory backend statistics.

        Returns:
            Memory statistics
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the memory backend.

        Returns:
            Health status dictionary
        """
        try:
            # Basic connectivity test
            if not self.is_connected:
                await self.connect()

            # Test query performance
            import time
            start_time = time.time()

            test_query = MemoryQuery(
                query_text="health_check",
                limit=1
            )
            await self.retrieve_entries(test_query)

            query_time = (time.time() - start_time) * 1000

            stats = await self.get_backend_stats()

            return {
                "status": "healthy",
                "connected": self.is_connected,
                "backend_type": self.connection.backend_type.value,
                "test_query_time_ms": query_time,
                "total_entries": stats.total_entries,
                "storage_size_mb": stats.storage_size_mb
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "backend_type": self.connection.backend_type.value
            }

    def _update_query_stats(self, query_time_ms: float) -> None:
        """Update query statistics."""
        self.query_count += 1
        self.total_query_time += query_time_ms


class InMemoryBackend(MemoryBackend):
    """In-memory backend for testing and development."""

    def __init__(self, connection: Optional[MemoryConnection] = None):
        if connection is None:
            connection = MemoryConnection(backend_type=MemoryBackendType.IN_MEMORY)
        super().__init__(connection)

        self.entries: Dict[str, MemoryEntry] = {}
        self.relationships: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}

    async def connect(self) -> bool:
        """Connect to in-memory backend."""
        self.is_connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from in-memory backend."""
        self.is_connected = False

    async def store_entry(self, entry: MemoryEntry) -> bool:
        """Store memory entry in memory."""
        try:
            self.entries[entry.id] = entry
            return True
        except Exception:
            return False

    async def retrieve_entries(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve entries from memory."""
        import time
        start_time = time.time()

        try:
            results = []
            query_lower = query.query_text.lower()

            for entry in self.entries.values():
                # Apply filters
                if query.session_id and entry.session_id != query.session_id:
                    continue

                if entry.importance < query.min_importance:
                    continue

                if query.start_time and entry.timestamp < query.start_time:
                    continue

                if query.end_time and entry.timestamp > query.end_time:
                    continue

                # Metadata filters
                if query.metadata_filters:
                    matches = all(
                        entry.metadata.get(k) == v
                        for k, v in query.metadata_filters.items()
                    )
                    if not matches:
                        continue

                # Simple text matching
                if query_lower in entry.content.lower():
                    results.append(entry)

                if len(results) >= query.limit:
                    break

            # Sort by relevance (importance + recency)
            results.sort(
                key=lambda e: (e.importance, e.timestamp),
                reverse=True
            )

            query_time = (time.time() - start_time) * 1000
            self._update_query_stats(query_time)

            return results[:query.limit]

        except Exception:
            return []

    async def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory entry."""
        if entry_id not in self.entries:
            return False

        try:
            entry = self.entries[entry_id]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            return True
        except Exception:
            return False

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete memory entry."""
        try:
            if entry_id in self.entries:
                del self.entries[entry_id]

            # Clean up relationships
            if entry_id in self.relationships:
                del self.relationships[entry_id]

            for relations in self.relationships.values():
                self.relationships[entry_id] = [
                    (to_id, rel_type, meta)
                    for to_id, rel_type, meta in relations
                    if to_id != entry_id
                ]

            return True
        except Exception:
            return False

    async def create_relationship(
        self,
        from_entry_id: str,
        to_entry_id: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create relationship between entries."""
        if (from_entry_id not in self.entries or
            to_entry_id not in self.entries):
            return False

        try:
            if from_entry_id not in self.relationships:
                self.relationships[from_entry_id] = []

            self.relationships[from_entry_id].append((
                to_entry_id,
                relationship_type,
                metadata or {}
            ))
            return True
        except Exception:
            return False

    async def get_related_entries(
        self,
        entry_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 1
    ) -> List[Tuple[MemoryEntry, str, int]]:
        """Get related entries."""
        if entry_id not in self.entries:
            return []

        results = []
        visited = set()
        to_visit = [(entry_id, 0)]

        while to_visit:
            current_id, depth = to_visit.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            if current_id in self.relationships:
                for to_id, rel_type, _ in self.relationships[current_id]:
                    if (relationship_types is None or
                        rel_type in relationship_types):

                        if to_id in self.entries:
                            results.append((
                                self.entries[to_id],
                                rel_type,
                                depth + 1
                            ))

                            if depth + 1 < max_depth:
                                to_visit.append((to_id, depth + 1))

        return results

    async def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        session_id: Optional[str] = None
    ) -> List[Tuple[MemoryEntry, float]]:
        """Search by embedding similarity (mock implementation)."""
        # Mock similarity calculation
        results = []

        for entry in self.entries.values():
            if session_id and entry.session_id != session_id:
                continue

            if entry.embedding:
                # Simple dot product similarity
                similarity = sum(
                    a * b for a, b in zip(query_embedding, entry.embedding)
                ) / (len(query_embedding) * len(entry.embedding))

                if similarity >= threshold:
                    results.append((entry, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary."""
        session_entries = [
            entry for entry in self.entries.values()
            if entry.session_id == session_id
        ]

        if not session_entries:
            return {"session_id": session_id, "entry_count": 0}

        avg_importance = sum(e.importance for e in session_entries) / len(session_entries)
        latest_timestamp = max(e.timestamp for e in session_entries)
        earliest_timestamp = min(e.timestamp for e in session_entries)

        return {
            "session_id": session_id,
            "entry_count": len(session_entries),
            "average_importance": avg_importance,
            "earliest_entry": earliest_timestamp.isoformat(),
            "latest_entry": latest_timestamp.isoformat(),
            "total_relationships": sum(
                len(rels) for rels in self.relationships.values()
            )
        }

    async def cleanup_old_entries(
        self,
        max_age_days: int,
        min_importance: float = 0.0
    ) -> int:
        """Clean up old entries."""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0

        entries_to_delete = [
            entry_id for entry_id, entry in self.entries.items()
            if (entry.timestamp < cutoff_date and
                entry.importance < min_importance)
        ]

        for entry_id in entries_to_delete:
            await self.delete_entry(entry_id)
            deleted_count += 1

        return deleted_count

    async def get_backend_stats(self) -> MemoryStats:
        """Get backend statistics."""
        total_entries = len(self.entries)
        sessions = set(
            entry.session_id for entry in self.entries.values()
            if entry.session_id
        )

        avg_importance = (
            sum(entry.importance for entry in self.entries.values()) / total_entries
            if total_entries > 0 else 0.0
        )

        avg_query_time = (
            self.total_query_time / self.query_count
            if self.query_count > 0 else 0.0
        )

        return MemoryStats(
            total_entries=total_entries,
            sessions_count=len(sessions),
            average_importance=avg_importance,
            storage_size_mb=0.1,  # Rough estimate for in-memory
            query_count=self.query_count,
            avg_query_time_ms=avg_query_time,
            backend_type="in_memory",
            connection_status="connected" if self.is_connected else "disconnected"
        )


class MemoryBackendFactory:
    """Factory for creating memory backends."""

    _backends = {
        MemoryBackendType.IN_MEMORY: InMemoryBackend
    }

    @classmethod
    def register_backend(cls, backend_type: MemoryBackendType, backend_class: type) -> None:
        """Register a new memory backend."""
        cls._backends[backend_type] = backend_class

    @classmethod
    def create_backend(cls, connection: MemoryConnection) -> MemoryBackend:
        """Create a memory backend instance."""
        backend_class = cls._backends.get(connection.backend_type)

        if not backend_class:
            raise ValueError(f"Unknown memory backend: {connection.backend_type}")

        return backend_class(connection)

    @classmethod
    def list_backends(cls) -> List[MemoryBackendType]:
        """List available backends."""
        return list(cls._backends.keys())