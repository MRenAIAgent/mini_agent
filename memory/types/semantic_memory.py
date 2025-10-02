"""Semantic memory manager for structured knowledge representation."""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import asyncio

from ..managers import CoreMemoryManager
from ..core import MemoryEntry


class SemanticMemoryManager(CoreMemoryManager):
    """
    Semantic memory manager that extends CoreMemoryManager for structured knowledge.

    Handles storage and retrieval of concepts, facts, relationships,
    and structured knowledge representations.
    """

    def __init__(self, **kwargs):
        """Initialize semantic memory manager."""
        super().__init__(**kwargs)
        self.memory_type = "semantic"

    async def store_concept(
        self,
        concept_id: str,
        definition: str,
        domain: Optional[str] = None,
        prerequisites: Optional[List[str]] = None,
        related_concepts: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        concept_name: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        importance: float = 0.8,
        **metadata
    ) -> bool:
        """
        Store a concept in semantic memory.

        Args:
            concept_id: Unique identifier for the concept
            definition: Definition or description of the concept
            domain: Subject domain (e.g., 'algebra', 'geometry', 'calculus')
            prerequisites: List of prerequisite concept IDs
            related_concepts: List of related concept IDs
            examples: List of examples demonstrating the concept
            user_id: Optional user identifier (for personalized concepts)
            concept_name: Human-readable name (defaults to concept_id)
            difficulty_level: Difficulty level (e.g., 'beginner', 'intermediate', 'advanced')
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        # Use concept_id as name if not provided
        name = concept_name or concept_id

        semantic_metadata = {
            'memory_type': 'semantic',  # Explicitly set to avoid MRO issues
            'entry_type': 'concept',
            'concept_id': concept_id,
            'concept_name': name,
            'domain': domain or 'general',
            'prerequisites': prerequisites or [],
            'related_concepts': related_concepts or [],
            'examples': examples or [],
            'difficulty_level': difficulty_level,
            'created_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Concept: {name}\nDefinition: {definition}"
        if examples:
            content += f"\nExamples: {'; '.join(examples)}"

        return await self.store_memory(
            content=content,
            importance=importance,
            user_id=user_id,
            **semantic_metadata
        )

    async def store_fact(
        self,
        fact_content: str,
        domain: str,
        related_concepts: Optional[List[str]] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        user_id: Optional[str] = None,
        importance: float = 0.7,
        **metadata
    ) -> bool:
        """
        Store a factual statement in semantic memory.

        Args:
            fact_content: The factual statement or information
            domain: Subject domain
            related_concepts: List of concept IDs this fact relates to
            source: Source of the fact (textbook, lesson, etc.)
            confidence: Confidence in the fact's accuracy (0.0 to 1.0)
            user_id: Optional user identifier
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        semantic_metadata = {
            'memory_type': 'semantic',
            'entry_type': 'fact',
            'domain': domain,
            'related_concepts': related_concepts or [],
            'source': source,
            'confidence': confidence,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            **metadata
        }

        return await self.store_memory(
            content=fact_content,
            importance=importance,
            **semantic_metadata
        )

    async def store_relationship(
        self,
        concept_1: str,
        concept_2: str,
        relationship_type: str,
        description: str,
        domain: str,
        strength: float = 1.0,
        user_id: Optional[str] = None,
        importance: float = 0.6,
        **metadata
    ) -> bool:
        """
        Store a relationship between concepts.

        Args:
            concept_1: First concept ID
            concept_2: Second concept ID
            relationship_type: Type of relationship (e.g., 'prerequisite', 'related', 'example_of')
            description: Description of the relationship
            domain: Subject domain
            strength: Strength of the relationship (0.0 to 1.0)
            user_id: Optional user identifier
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        semantic_metadata = {
            'memory_type': 'semantic',
            'entry_type': 'relationship',
            'concept_1': concept_1,
            'concept_2': concept_2,
            'relationship_type': relationship_type,
            'strength': strength,
            'domain': domain,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Relationship: {concept_1} {relationship_type} {concept_2}\nDescription: {description}"

        return await self.store_memory(
            content=content,
            importance=importance,
            **semantic_metadata
        )

    async def get_concept(
        self,
        concept_id: str,
        user_id: Optional[str] = None
    ) -> Optional[MemoryEntry]:
        """
        Retrieve a specific concept.

        Args:
            concept_id: Concept identifier
            user_id: Optional user identifier for personalized concepts

        Returns:
            Concept memory entry if found, None otherwise
        """
        filters = {
            'memory_type': 'semantic',  # Explicitly set to avoid MRO issues
            'entry_type': 'concept',
            'concept_id': concept_id
        }

        if user_id:
            filters['user_id'] = user_id

        results = await self.search_memory(
            query="",  # Empty query, filter by metadata
            limit=1,
            filters=filters
        )

        return results[0] if results else None

    async def get_related_concepts(
        self,
        concept_id: str,
        relationship_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get concepts related to a given concept.

        Args:
            concept_id: Source concept identifier
            relationship_types: Optional filter by relationship types
            user_id: Optional user identifier
            limit: Maximum number of related concepts to return

        Returns:
            List of dictionaries containing related concept info and relationship details
        """
        filters = {
            'memory_type': 'semantic',
            'entry_type': 'relationship'
        }

        if user_id:
            filters['user_id'] = user_id

        # Search for relationships involving this concept
        query = f"concept relationship {concept_id}"
        relationships = await self.search_memory(
            query=query,
            limit=limit * 2,
            filters=filters
        )

        related_concepts = []
        for rel in relationships:
            rel_metadata = rel.metadata
            concept_1 = rel_metadata.get('concept_1')
            concept_2 = rel_metadata.get('concept_2')
            rel_type = rel_metadata.get('relationship_type')

            # Skip if relationship type filter doesn't match
            if relationship_types and rel_type not in relationship_types:
                continue

            # Determine which concept is the related one
            related_concept_id = None
            if concept_1 == concept_id:
                related_concept_id = concept_2
            elif concept_2 == concept_id:
                related_concept_id = concept_1

            if related_concept_id:
                # Get the actual concept details
                concept = await self.get_concept(related_concept_id, user_id)
                if concept:
                    related_concepts.append({
                        'concept_id': related_concept_id,
                        'concept_name': concept.metadata.get('concept_name'),
                        'relationship_type': rel_type,
                        'relationship_strength': rel_metadata.get('strength', 1.0),
                        'description': rel.content,
                        'domain': concept.metadata.get('domain')
                    })

        return related_concepts[:limit]

    async def get_prerequisites(
        self,
        concept_id: str,
        user_id: Optional[str] = None
    ) -> List[MemoryEntry]:
        """
        Get prerequisite concepts for a given concept.

        Args:
            concept_id: Concept identifier
            user_id: Optional user identifier

        Returns:
            List of prerequisite concept MemoryEntry objects (or stub entries if concepts don't exist)
        """
        concept = await self.get_concept(concept_id, user_id)
        if not concept:
            return []

        prereq_ids = concept.metadata.get('prerequisites', [])
        if not prereq_ids:
            return []

        # Fetch the actual prerequisite concept entries, or create stub entries if they don't exist
        prereq_concepts = []
        for prereq_id in prereq_ids:
            prereq_concept = await self.get_concept(prereq_id, user_id)
            if prereq_concept:
                prereq_concepts.append(prereq_concept)
            else:
                # Create a stub entry for prerequisites that don't exist yet
                stub_entry = MemoryEntry(
                    content=f"Prerequisite concept: {prereq_id}",
                    importance=0.5,
                    metadata={
                        'concept_id': prereq_id,
                        'concept_name': prereq_id,
                        'memory_type': 'semantic',
                        'entry_type': 'concept',
                        'is_stub': True
                    }
                )
                prereq_concepts.append(stub_entry)

        return prereq_concepts

    async def get_domain_concepts(
        self,
        domain: str,
        user_id: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """
        Get all concepts in a specific domain.

        Args:
            domain: Subject domain
            user_id: Optional user identifier
            difficulty_level: Optional filter by difficulty level
            limit: Maximum number of concepts to return

        Returns:
            List of concept memory entries
        """
        filters = {
            'memory_type': 'semantic',
            'entry_type': 'concept',
            'domain': domain
        }

        if user_id:
            filters['user_id'] = user_id

        if difficulty_level:
            filters['difficulty_level'] = difficulty_level

        return await self.search_memory(
            query=f"domain:{domain}",
            limit=limit,
            filters=filters
        )

    async def search_concepts(
        self,
        query: str,
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[MemoryEntry]:
        """
        Search for concepts by content or name.

        Args:
            query: Search query
            domain: Optional domain filter
            user_id: Optional user identifier
            limit: Maximum number of results

        Returns:
            List of matching concept memory entries
        """
        filters = {
            'memory_type': 'semantic',
            'entry_type': 'concept'
        }

        if domain:
            filters['domain'] = domain

        if user_id:
            filters['user_id'] = user_id

        return await self.search_memory(
            query=query,
            limit=limit,
            filters=filters
        )

    async def get_concept_hierarchy(
        self,
        domain: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a hierarchical structure of concepts based on prerequisites.

        Args:
            domain: Subject domain
            user_id: Optional user identifier

        Returns:
            Dictionary representing the concept hierarchy
        """
        # Get all concepts in the domain
        concepts = await self.get_domain_concepts(domain, user_id, limit=1000)

        # Build prerequisite graph
        concept_map = {}
        for concept in concepts:
            concept_id = concept.metadata.get('concept_id')
            concept_map[concept_id] = {
                'name': concept.metadata.get('concept_name'),
                'prerequisites': concept.metadata.get('prerequisites', []),
                'difficulty': concept.metadata.get('difficulty_level'),
                'children': []
            }

        # Build hierarchy by linking prerequisites to dependents
        for concept_id, concept_data in concept_map.items():
            for prereq in concept_data['prerequisites']:
                if prereq in concept_map:
                    concept_map[prereq]['children'].append(concept_id)

        # Find root concepts (those with no prerequisites)
        roots = [
            concept_id for concept_id, concept_data in concept_map.items()
            if not concept_data['prerequisites']
        ]

        return {
            'domain': domain,
            'concepts': concept_map,
            'roots': roots,
            'total_concepts': len(concepts)
        }

    async def update_concept_understanding(
        self,
        concept_id: str,
        user_id: str,
        understanding_level: float,
        evidence: str,
        **metadata
    ) -> bool:
        """
        Store or update understanding level for a concept.

        Args:
            concept_id: Concept identifier
            user_id: User identifier
            understanding_level: Understanding level (0.0 to 1.0)
            evidence: Evidence for the understanding level
            **metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        understanding_metadata = {
            'memory_type': 'semantic',
            'entry_type': 'understanding',
            'concept_id': concept_id,
            'user_id': user_id,
            'understanding_level': understanding_level,
            'updated_at': datetime.now().isoformat(),
            **metadata
        }

        content = f"Understanding of {concept_id}: {understanding_level:.2f}\nEvidence: {evidence}"

        return await self.store_memory(
            content=content,
            importance=0.8,
            **understanding_metadata
        )

    async def get_knowledge_gaps(
        self,
        user_id: str,
        domain: str,
        understanding_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Identify knowledge gaps based on concept prerequisites and understanding levels.

        Args:
            user_id: User identifier
            domain: Subject domain
            understanding_threshold: Minimum understanding level considered adequate

        Returns:
            List of knowledge gap information
        """
        # Get concept hierarchy
        hierarchy = await self.get_concept_hierarchy(domain, user_id)

        # Get understanding levels
        understanding_filters = {
            'memory_type': 'semantic',
            'entry_type': 'understanding',
            'user_id': user_id
        }

        understanding_entries = await self.search_memory(
            query=f"understanding {user_id}",
            limit=1000,
            filters=understanding_filters
        )

        # Build understanding map
        understanding_map = {}
        for entry in understanding_entries:
            concept_id = entry.metadata.get('concept_id')
            level = entry.metadata.get('understanding_level', 0.0)
            understanding_map[concept_id] = level

        # Identify gaps
        gaps = []
        for concept_id, concept_data in hierarchy['concepts'].items():
            current_understanding = understanding_map.get(concept_id, 0.0)

            # Check if this concept is below threshold
            if current_understanding < understanding_threshold:
                # Check if prerequisites are adequately understood
                prereq_understanding = [
                    understanding_map.get(prereq, 0.0)
                    for prereq in concept_data['prerequisites']
                ]

                # This is a gap if prerequisites are understood but this concept isn't
                if not prereq_understanding or min(prereq_understanding) >= understanding_threshold:
                    gaps.append({
                        'concept_id': concept_id,
                        'concept_name': concept_data['name'],
                        'current_understanding': current_understanding,
                        'gap_size': understanding_threshold - current_understanding,
                        'prerequisites_ready': len(concept_data['prerequisites']) == 0 or
                                             min(prereq_understanding) >= understanding_threshold,
                        'difficulty': concept_data['difficulty']
                    })

        # Sort by gap size (largest gaps first)
        gaps.sort(key=lambda x: x['gap_size'], reverse=True)

        return gaps