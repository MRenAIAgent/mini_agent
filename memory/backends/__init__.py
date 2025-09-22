"""
Memory backend registry and factory.

This module provides a registry for different memory backend implementations
and a factory for creating backend instances based on configuration.
Constitutional compliance: simple registry pattern.
"""

from typing import Dict, Type, Any, Optional
from abc import ABC, abstractmethod

# Import backends with fallback for missing dependencies
try:
    from .memgraph_backend import MemgraphBackend
except ImportError:
    MemgraphBackend = None

try:
    from .redis_backend import RedisBackend
except ImportError:
    RedisBackend = None


class MemoryBackend(ABC):
    """
    Abstract base class for memory backends.
    Defines the interface that all memory backends must implement.
    """

    @abstractmethod
    async def store_memory(self, memory_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory entry."""
        pass

    @abstractmethod
    async def retrieve_memory(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory entry by ID."""
        pass

    @abstractmethod
    async def search_memory(self, query: str, limit: int = 10) -> list:
        """Search for memory entries matching query."""
        pass

    @abstractmethod
    async def delete_memory(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all memory entries."""
        pass


class BackendRegistry:
    """
    Registry for memory backend implementations.
    Constitutional compliance: simple registry pattern without complex factories.
    """

    _backends: Dict[str, Type[MemoryBackend]] = {}

    @classmethod
    def register_backend(cls, name: str, backend_class: Type[MemoryBackend]) -> None:
        """
        Register a memory backend implementation.

        Args:
            name: Backend name (e.g., 'memgraph', 'redis')
            backend_class: Backend class implementation
        """
        cls._backends[name] = backend_class

    @classmethod
    def get_backend_class(cls, name: str) -> Optional[Type[MemoryBackend]]:
        """
        Get backend class by name.

        Args:
            name: Backend name

        Returns:
            Backend class or None if not found
        """
        return cls._backends.get(name)

    @classmethod
    def list_backends(cls) -> list:
        """
        List all registered backend names.

        Returns:
            List of backend names
        """
        return list(cls._backends.keys())

    @classmethod
    def create_backend(cls, backend_type: str, config: Dict[str, Any]) -> MemoryBackend:
        """
        Create backend instance from configuration.

        Args:
            backend_type: Type of backend ('memgraph', 'redis', etc.)
            config: Backend configuration

        Returns:
            Initialized backend instance

        Raises:
            ValueError: If backend type is not supported
            ImportError: If required dependencies are missing
        """
        backend_class = cls.get_backend_class(backend_type)

        if not backend_class:
            available = ", ".join(cls.list_backends())
            raise ValueError(
                f"Unsupported backend type: {backend_type}. "
                f"Available backends: {available}"
            )

        try:
            return backend_class(config)
        except ImportError as e:
            raise ImportError(
                f"Cannot create {backend_type} backend: {e}. "
                f"Please install required dependencies."
            )


# Register available backends
def _register_backends() -> None:
    """Register all available backend implementations."""
    if MemgraphBackend:
        BackendRegistry.register_backend("memgraph", MemgraphBackend)

    if RedisBackend:
        BackendRegistry.register_backend("redis", RedisBackend)

    # Add in-memory backend for development/testing
    class InMemoryBackend(MemoryBackend):
        """Simple in-memory backend for testing."""

        def __init__(self, config: Dict[str, Any]):
            self.memories: Dict[str, Dict[str, Any]] = {}
            self.config = config

        async def store_memory(self, memory_entry: Dict[str, Any]) -> Dict[str, Any]:
            entry_id = memory_entry.get("entry_id", "")
            self.memories[entry_id] = memory_entry.copy()
            return {"entry_id": entry_id, "status": "stored", "backend": "in_memory"}

        async def retrieve_memory(self, entry_id: str) -> Optional[Dict[str, Any]]:
            return self.memories.get(entry_id)

        async def search_memory(self, query: str, limit: int = 10) -> list:
            results = []
            query_lower = query.lower()

            for memory in self.memories.values():
                content = memory.get("content", "").lower()
                if query_lower in content:
                    memory_copy = memory.copy()
                    memory_copy["relevance_score"] = 1.0
                    results.append(memory_copy)

                if len(results) >= limit:
                    break

            return results

        async def delete_memory(self, entry_id: str) -> bool:
            if entry_id in self.memories:
                del self.memories[entry_id]
                return True
            return False

        async def clear_all(self) -> None:
            self.memories.clear()

    BackendRegistry.register_backend("in_memory", InMemoryBackend)

    # PostgreSQL backend placeholder (constitutional compliance: document planned backend)
    # Will be implemented if needed: BackendRegistry.register_backend("postgresql", PostgreSQLBackend)


# Initialize registry
_register_backends()


# Convenience functions
def create_backend(backend_type: str, config: Dict[str, Any]) -> MemoryBackend:
    """
    Create memory backend instance.

    Args:
        backend_type: Backend type ('memgraph', 'redis', 'in_memory')
        config: Backend configuration

    Returns:
        Memory backend instance
    """
    return BackendRegistry.create_backend(backend_type, config)


def list_available_backends() -> list:
    """
    List all available memory backend types.

    Returns:
        List of backend type names
    """
    return BackendRegistry.list_backends()


def validate_backend_config(backend_type: str, config: Dict[str, Any]) -> bool:
    """
    Validate backend configuration.

    Args:
        backend_type: Backend type
        config: Configuration to validate

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    if backend_type == "memgraph":
        required_fields = ["host", "port"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Memgraph backend requires '{field}' in config")

    elif backend_type == "redis":
        # Redis can work with just URL, other fields are optional
        if "url" not in config:
            raise ValueError("Redis backend requires 'url' in config")

    elif backend_type == "in_memory":
        # In-memory backend has no required configuration
        pass

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    return True


# Export public interface
__all__ = [
    "MemoryBackend",
    "BackendRegistry",
    "create_backend",
    "list_available_backends",
    "validate_backend_config",
    "MemgraphBackend",
    "RedisBackend"
]