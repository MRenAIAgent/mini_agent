"""
Redis backend for fast cache-based memory storage.

This backend provides high-performance memory storage using Redis for
fast retrieval and automatic expiration of memory entries.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import uuid

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


class RedisBackend:
    """
    Memory backend using Redis for fast cache storage.

    Provides high-speed memory storage with TTL support and efficient
    key-value operations. Constitutional compliance: simple interface.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Redis backend.

        Args:
            config: Configuration dict with url, db, password, etc.
        """
        if redis is None:
            raise ImportError("redis package not installed. Run: pip install redis[asyncio]")

        self.config = config
        self.url = config.get("url", "redis://localhost:6379")
        self.db = config.get("db", 0)
        self.password = config.get("password", None)
        self.default_ttl = config.get("default_ttl", 3600)  # 1 hour default

        self.redis_client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connection to Redis."""
        if self._initialized:
            return

        try:
            self.redis_client = redis.from_url(
                self.url,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def store_memory(self, memory_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store memory entry in Redis with optional TTL.

        Args:
            memory_entry: Memory entry with content, metadata, etc.

        Returns:
            Dict with stored entry information
        """
        await self.initialize()

        entry_id = memory_entry.get("entry_id", str(uuid.uuid4()))
        content = memory_entry.get("content", "")
        entry_type = memory_entry.get("entry_type", "memory")
        importance_score = memory_entry.get("importance_score", 0.5)
        created_at = memory_entry.get("created_at", datetime.now().isoformat())
        metadata = memory_entry.get("metadata", {})

        # Calculate TTL based on importance (higher importance = longer TTL)
        ttl = int(self.default_ttl * (0.5 + importance_score))

        try:
            # Prepare memory data
            memory_data = {
                "entry_id": entry_id,
                "content": content,
                "entry_type": entry_type,
                "importance_score": importance_score,
                "created_at": created_at,
                "metadata": metadata,
                "stored_at": datetime.now().isoformat()
            }

            # Store in Redis with TTL
            key = f"memory:{entry_id}"
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(memory_data)
            )

            # Add to search index (simple implementation)
            await self._add_to_search_index(entry_id, content, entry_type)

            return {
                "entry_id": entry_id,
                "status": "stored",
                "backend": "redis",
                "ttl": ttl
            }

        except Exception as e:
            raise RuntimeError(f"Failed to store memory in Redis: {e}")

    async def retrieve_memory(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific memory entry by ID.

        Args:
            entry_id: ID of memory entry to retrieve

        Returns:
            Memory entry dict or None if not found
        """
        await self.initialize()

        try:
            key = f"memory:{entry_id}"
            data = await self.redis_client.get(key)

            if not data:
                return None

            memory_entry = json.loads(data)
            return memory_entry

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve memory from Redis: {e}")

    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories using simple text matching.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching memory entries with relevance scores
        """
        await self.initialize()

        try:
            # Get all memory keys
            memory_keys = await self.redis_client.keys("memory:*")

            if not memory_keys:
                return []

            # Get all memory entries
            memories = []
            for key in memory_keys[:limit * 2]:  # Get more than limit for filtering
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        memory_entry = json.loads(data)

                        # Simple relevance scoring
                        content = memory_entry.get("content", "").lower()
                        query_lower = query.lower()

                        if query_lower in content:
                            # Calculate relevance score
                            word_count = len(content.split())
                            query_matches = content.count(query_lower)
                            importance = memory_entry.get("importance_score", 0.5)

                            relevance_score = (query_matches / max(word_count, 1)) * importance

                            memory_entry["relevance_score"] = relevance_score
                            memories.append(memory_entry)

                except (json.JSONDecodeError, KeyError):
                    # Skip corrupted entries
                    continue

            # Sort by relevance and limit results
            memories.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return memories[:limit]

        except Exception as e:
            raise RuntimeError(f"Failed to search memories in Redis: {e}")

    async def delete_memory(self, entry_id: str) -> bool:
        """
        Delete memory entry from Redis.

        Args:
            entry_id: ID of memory entry to delete

        Returns:
            True if deleted, False if not found
        """
        await self.initialize()

        try:
            key = f"memory:{entry_id}"
            deleted_count = await self.redis_client.delete(key)

            # Remove from search index
            await self._remove_from_search_index(entry_id)

            return deleted_count > 0

        except Exception as e:
            raise RuntimeError(f"Failed to delete memory from Redis: {e}")

    async def clear_all(self) -> None:
        """Clear all memory entries."""
        await self.initialize()

        try:
            # Delete all memory keys
            memory_keys = await self.redis_client.keys("memory:*")
            if memory_keys:
                await self.redis_client.delete(*memory_keys)

            # Clear search index
            await self.redis_client.delete("search_index:*")

        except Exception as e:
            raise RuntimeError(f"Failed to clear memories from Redis: {e}")

    # Cache-specific methods
    async def set_ttl(self, entry_id: str, ttl: int) -> bool:
        """
        Set or update TTL for a memory entry.

        Args:
            entry_id: Memory entry ID
            ttl: Time to live in seconds

        Returns:
            True if TTL was set successfully
        """
        await self.initialize()

        try:
            key = f"memory:{entry_id}"
            result = await self.redis_client.expire(key, ttl)
            return result

        except Exception as e:
            raise RuntimeError(f"Failed to set TTL for memory: {e}")

    async def get_ttl(self, entry_id: str) -> Optional[int]:
        """
        Get remaining TTL for a memory entry.

        Args:
            entry_id: Memory entry ID

        Returns:
            Remaining TTL in seconds, or None if not found
        """
        await self.initialize()

        try:
            key = f"memory:{entry_id}"
            ttl = await self.redis_client.ttl(key)

            if ttl == -2:  # Key doesn't exist
                return None
            elif ttl == -1:  # Key exists but no TTL
                return -1
            else:
                return ttl

        except Exception as e:
            raise RuntimeError(f"Failed to get TTL for memory: {e}")

    async def extend_ttl(self, entry_id: str, additional_seconds: int) -> bool:
        """
        Extend TTL for a memory entry.

        Args:
            entry_id: Memory entry ID
            additional_seconds: Additional seconds to add to TTL

        Returns:
            True if TTL was extended successfully
        """
        await self.initialize()

        try:
            current_ttl = await self.get_ttl(entry_id)
            if current_ttl is None:
                return False

            new_ttl = max(current_ttl, 0) + additional_seconds
            return await self.set_ttl(entry_id, new_ttl)

        except Exception as e:
            raise RuntimeError(f"Failed to extend TTL for memory: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories.

        Returns:
            Dict with memory statistics
        """
        await self.initialize()

        try:
            memory_keys = await self.redis_client.keys("memory:*")
            total_memories = len(memory_keys)

            # Get sample of memories for statistics
            sample_size = min(total_memories, 100)
            sample_keys = memory_keys[:sample_size]

            total_size = 0
            type_counts = {}
            importance_sum = 0

            for key in sample_keys:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        memory_entry = json.loads(data)
                        total_size += len(data)

                        entry_type = memory_entry.get("entry_type", "unknown")
                        type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

                        importance_sum += memory_entry.get("importance_score", 0.5)

                except (json.JSONDecodeError, KeyError):
                    continue

            avg_importance = importance_sum / max(sample_size, 1)
            avg_size = total_size / max(sample_size, 1)

            return {
                "total_memories": total_memories,
                "average_size_bytes": avg_size,
                "average_importance": avg_importance,
                "type_distribution": type_counts,
                "backend": "redis"
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get memory statistics: {e}")

    # Helper methods
    async def _add_to_search_index(self, entry_id: str, content: str, entry_type: str) -> None:
        """Add entry to simple search index."""
        try:
            # Simple word-based indexing
            words = content.lower().split()
            for word in words[:50]:  # Limit to first 50 words
                if len(word) > 2:  # Skip very short words
                    index_key = f"search_index:{word}"
                    await self.redis_client.sadd(index_key, entry_id)
                    # Set TTL for index entries
                    await self.redis_client.expire(index_key, self.default_ttl * 2)

        except Exception:
            # Non-critical operation, don't fail if indexing fails
            pass

    async def _remove_from_search_index(self, entry_id: str) -> None:
        """Remove entry from search index."""
        try:
            # Remove from all index sets (this is inefficient but simple)
            index_keys = await self.redis_client.keys("search_index:*")
            for index_key in index_keys:
                await self.redis_client.srem(index_key, entry_id)

        except Exception:
            # Non-critical operation, don't fail if removal fails
            pass

    async def close(self) -> None:
        """Close connection to Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False