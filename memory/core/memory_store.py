"""Abstract memory store interface and basic implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    importance: float = 1.0  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "embedding": self.embedding,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            embedding=data.get("embedding"),
            importance=data.get("importance", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if "last_accessed" in data else datetime.now()
        )


class MemoryStore(ABC):
    """Abstract interface for memory storage backends."""

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        pass

    @abstractmethod
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry by ID."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Search for relevant memory entries."""
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """List recent memory entries."""
        pass

    @abstractmethod
    async def update(self, entry: MemoryEntry) -> bool:
        """Update an existing memory entry."""
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all memory entries."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        pass


class InMemoryStore(MemoryStore):
    """Simple in-memory storage implementation."""

    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}

    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        try:
            self._entries[entry.id] = entry
            return True
        except Exception:
            return False

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry by ID."""
        entry = self._entries.get(entry_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now()
        return entry

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Search for relevant memory entries using simple text matching."""
        query_lower = query.lower()
        results = []

        for entry in self._entries.values():
            # Apply filters if provided
            if filters:
                match = True
                for key, value in filters.items():
                    # Check in metadata
                    if entry.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            # Simple text matching - empty query matches all (for filter-only searches)
            if not query or query_lower in entry.content.lower():
                score = self._calculate_relevance_score(query_lower, entry) if query else entry.importance
                results.append((score, entry))

        # Sort by relevance and limit
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:limit]]

    async def list_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """List recent memory entries."""
        entries = list(self._entries.values())
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]

    async def update(self, entry: MemoryEntry) -> bool:
        """Update an existing memory entry."""
        if entry.id in self._entries:
            self._entries[entry.id] = entry
            return True
        return False

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def clear(self) -> bool:
        """Clear all memory entries."""
        self._entries.clear()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        total_entries = len(self._entries)
        total_size = sum(len(entry.content) for entry in self._entries.values())

        return {
            "total_entries": total_entries,
            "total_size_chars": total_size,
            "store_type": "in_memory"
        }

    def _calculate_relevance_score(self, query: str, entry: MemoryEntry) -> float:
        """Calculate relevance score for search results."""
        content_lower = entry.content.lower()

        # Basic scoring factors
        score = 0.0

        # Exact matches
        if query in content_lower:
            score += 1.0

        # Word matches
        query_words = query.split()
        content_words = content_lower.split()
        word_matches = sum(1 for word in query_words if word in content_words)
        score += (word_matches / len(query_words)) * 0.5

        # Recency factor
        age_days = (datetime.now() - entry.timestamp).days
        recency_score = max(0, 1 - (age_days / 30))  # Decay over 30 days
        score += recency_score * 0.2

        # Importance factor
        score += entry.importance * 0.3

        return score


class FileStore(MemoryStore):
    """Simple file-based storage implementation."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._entries: Dict[str, MemoryEntry] = {}
        self._loaded = False

    async def _load_if_needed(self) -> None:
        """Load entries from file if not already loaded."""
        if self._loaded:
            return

        try:
            import json
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self._entries = {
                    entry_id: MemoryEntry.from_dict(entry_data)
                    for entry_id, entry_data in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is invalid, start fresh
            self._entries = {}

        self._loaded = True

    async def _save(self) -> None:
        """Save entries to file."""
        try:
            import json
            import os
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

            data = {
                entry_id: entry.to_dict()
                for entry_id, entry in self._entries.items()
            }

            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Fail silently for now

    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        await self._load_if_needed()
        try:
            self._entries[entry.id] = entry
            await self._save()
            return True
        except Exception:
            return False

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry by ID."""
        await self._load_if_needed()
        entry = self._entries.get(entry_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            await self._save()
        return entry

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """Search for relevant memory entries."""
        await self._load_if_needed()
        # Delegate to in-memory search logic
        in_memory_store = InMemoryStore()
        in_memory_store._entries = self._entries
        return await in_memory_store.search(query, limit, filters)

    async def list_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """List recent memory entries."""
        await self._load_if_needed()
        entries = list(self._entries.values())
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]

    async def update(self, entry: MemoryEntry) -> bool:
        """Update an existing memory entry."""
        await self._load_if_needed()
        if entry.id in self._entries:
            self._entries[entry.id] = entry
            await self._save()
            return True
        return False

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        await self._load_if_needed()
        if entry_id in self._entries:
            del self._entries[entry_id]
            await self._save()
            return True
        return False

    async def clear(self) -> bool:
        """Clear all memory entries."""
        await self._load_if_needed()
        self._entries.clear()
        await self._save()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        await self._load_if_needed()
        total_entries = len(self._entries)
        total_size = sum(len(entry.content) for entry in self._entries.values())

        return {
            "total_entries": total_entries,
            "total_size_chars": total_size,
            "store_type": "file",
            "file_path": self.file_path
        }