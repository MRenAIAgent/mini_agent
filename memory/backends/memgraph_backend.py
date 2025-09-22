"""
Memgraph backend for knowledge graph memory storage.

This backend provides graph-based memory storage using Memgraph for complex
relationship modeling and efficient graph traversal queries.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

try:
    import memgraph
except ImportError:
    memgraph = None


class MemgraphBackend:
    """
    Memory backend using Memgraph for knowledge graph storage.

    Provides relationship-aware memory storage with graph querying capabilities.
    Constitutional compliance: simple interface, extends existing memory system.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Memgraph backend.

        Args:
            config: Configuration dict with host, port, username, password
        """
        if memgraph is None:
            raise ImportError("memgraph package not installed. Run: pip install memgraph")

        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 7687)
        self.username = config.get("username", "")
        self.password = config.get("password", "")

        self.connection = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connection to Memgraph."""
        if self._initialized:
            return

        try:
            # Create connection using bolt protocol
            connection_string = f"bolt://{self.host}:{self.port}"
            self.connection = memgraph.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )
            self._initialized = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Memgraph: {e}")

    async def store_memory(self, memory_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store memory entry as graph nodes and relationships.

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

        try:
            cursor = self.connection.cursor()

            # Create memory node
            create_query = """
            CREATE (m:Memory {
                entry_id: $entry_id,
                content: $content,
                entry_type: $entry_type,
                importance_score: $importance_score,
                created_at: $created_at,
                metadata: $metadata
            })
            RETURN m.entry_id as entry_id
            """

            cursor.execute(create_query, {
                "entry_id": entry_id,
                "content": content,
                "entry_type": entry_type,
                "importance_score": importance_score,
                "created_at": created_at,
                "metadata": str(metadata)  # Convert to string for storage
            })

            result = cursor.fetchone()
            cursor.close()

            return {
                "entry_id": result[0] if result else entry_id,
                "status": "stored",
                "backend": "memgraph"
            }

        except Exception as e:
            raise RuntimeError(f"Failed to store memory in Memgraph: {e}")

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
            cursor = self.connection.cursor()

            query = """
            MATCH (m:Memory {entry_id: $entry_id})
            RETURN m.entry_id, m.content, m.entry_type, m.importance_score,
                   m.created_at, m.metadata
            """

            cursor.execute(query, {"entry_id": entry_id})
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return None

            return {
                "entry_id": result[0],
                "content": result[1],
                "entry_type": result[2],
                "importance_score": result[3],
                "created_at": result[4],
                "metadata": eval(result[5]) if result[5] else {}  # Parse metadata
            }

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve memory from Memgraph: {e}")

    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories using graph queries and text matching.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching memory entries with relevance scores
        """
        await self.initialize()

        try:
            cursor = self.connection.cursor()

            # Simple text search in content
            search_query = """
            MATCH (m:Memory)
            WHERE m.content CONTAINS $query
            RETURN m.entry_id, m.content, m.entry_type, m.importance_score,
                   m.created_at, m.metadata
            ORDER BY m.importance_score DESC
            LIMIT $limit
            """

            cursor.execute(search_query, {"query": query, "limit": limit})
            results = cursor.fetchall()
            cursor.close()

            memories = []
            for result in results:
                # Calculate simple relevance score based on importance and text match
                content = result[1] or ""
                relevance_score = result[3] * (query.lower() in content.lower() and 1.5 or 1.0)

                memories.append({
                    "entry_id": result[0],
                    "content": result[1],
                    "entry_type": result[2],
                    "importance_score": result[3],
                    "created_at": result[4],
                    "metadata": eval(result[5]) if result[5] else {},
                    "relevance_score": relevance_score
                })

            return memories

        except Exception as e:
            raise RuntimeError(f"Failed to search memories in Memgraph: {e}")

    async def delete_memory(self, entry_id: str) -> bool:
        """
        Delete memory entry and related relationships.

        Args:
            entry_id: ID of memory entry to delete

        Returns:
            True if deleted, False if not found
        """
        await self.initialize()

        try:
            cursor = self.connection.cursor()

            # Delete node and all relationships
            delete_query = """
            MATCH (m:Memory {entry_id: $entry_id})
            DETACH DELETE m
            RETURN count(m) as deleted_count
            """

            cursor.execute(delete_query, {"entry_id": entry_id})
            result = cursor.fetchone()
            cursor.close()

            return result[0] > 0 if result else False

        except Exception as e:
            raise RuntimeError(f"Failed to delete memory from Memgraph: {e}")

    async def clear_all(self) -> None:
        """Clear all memory entries."""
        await self.initialize()

        try:
            cursor = self.connection.cursor()

            # Delete all Memory nodes
            cursor.execute("MATCH (m:Memory) DETACH DELETE m")
            cursor.close()

        except Exception as e:
            raise RuntimeError(f"Failed to clear memories from Memgraph: {e}")

    # Graph-specific methods for knowledge relationships
    async def create_relationship(self, from_id: str, to_id: str,
                                 relationship_type: str,
                                 properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create relationship between memory entries.

        Args:
            from_id: Source memory entry ID
            to_id: Target memory entry ID
            relationship_type: Type of relationship (e.g., "RELATES_TO", "CAUSES")
            properties: Optional relationship properties

        Returns:
            True if relationship created successfully
        """
        await self.initialize()

        try:
            cursor = self.connection.cursor()

            # Create relationship between existing nodes
            props_str = ""
            if properties:
                props_list = [f"{k}: ${k}" for k in properties.keys()]
                props_str = "{" + ", ".join(props_list) + "}"

            query = f"""
            MATCH (m1:Memory {{entry_id: $from_id}})
            MATCH (m2:Memory {{entry_id: $to_id}})
            CREATE (m1)-[r:{relationship_type} {props_str}]->(m2)
            RETURN id(r) as rel_id
            """

            params = {"from_id": from_id, "to_id": to_id}
            if properties:
                params.update(properties)

            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()

            return result is not None

        except Exception as e:
            raise RuntimeError(f"Failed to create relationship in Memgraph: {e}")

    async def query_graph(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute custom Cypher query on the memory graph.

        Args:
            cypher_query: Cypher query string
            params: Optional query parameters

        Returns:
            List of query results
        """
        await self.initialize()

        try:
            cursor = self.connection.cursor()
            cursor.execute(cypher_query, params or {})

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Get results
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

        except Exception as e:
            raise RuntimeError(f"Failed to execute graph query: {e}")

    async def create_concept_node(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create concept node for knowledge graph organization.

        Args:
            concept: Concept data with id, name, type, definition

        Returns:
            Created concept information
        """
        await self.initialize()

        concept_id = concept.get("concept_id", str(uuid.uuid4()))
        name = concept.get("name", "")
        concept_type = concept.get("type", "entity")
        definition = concept.get("definition", "")

        try:
            cursor = self.connection.cursor()

            query = """
            CREATE (c:Concept {
                concept_id: $concept_id,
                name: $name,
                type: $concept_type,
                definition: $definition,
                created_at: $created_at
            })
            RETURN c.concept_id as concept_id
            """

            cursor.execute(query, {
                "concept_id": concept_id,
                "name": name,
                "concept_type": concept_type,
                "definition": definition,
                "created_at": datetime.now().isoformat()
            })

            result = cursor.fetchone()
            cursor.close()

            return {
                "concept_id": result[0] if result else concept_id,
                "status": "created",
                "backend": "memgraph"
            }

        except Exception as e:
            raise RuntimeError(f"Failed to create concept node: {e}")

    async def close(self) -> None:
        """Close connection to Memgraph."""
        if self.connection:
            self.connection.close()
            self._initialized = False