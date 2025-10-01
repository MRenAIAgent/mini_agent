"""Knowledge graph for tracking concept relationships and learning paths."""

import asyncio
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import defaultdict, deque
from dataclasses import asdict

from .data_models import ConceptNode, ConceptType, MasteryLevel, DifficultyLevel


class KnowledgeGraph:
    """
    Knowledge graph system for managing concept relationships,
    prerequisites, and learning path generation.
    """

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize knowledge graph.

        Args:
            storage_backend: Optional backend for persistent storage
        """
        self.storage_backend = storage_backend

        # In-memory graph representation
        self._concepts: Dict[str, ConceptNode] = {}
        self._prerequisite_graph: Dict[str, Set[str]] = defaultdict(set)  # concept -> prerequisites
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)   # concept -> dependents

        # Cached paths and relationships
        self._path_cache: Dict[Tuple[str, str], List[str]] = {}
        self._prerequisite_cache: Dict[str, Set[str]] = {}

    async def add_concept(self, concept: ConceptNode) -> bool:
        """
        Add a concept to the knowledge graph.

        Args:
            concept: ConceptNode to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Store concept
            self._concepts[concept.concept_id] = concept

            # Update prerequisite relationships
            for prereq_id in concept.prerequisites:
                self._prerequisite_graph[concept.concept_id].add(prereq_id)
                self._dependency_graph[prereq_id].add(concept.concept_id)

            # Update enabled relationships
            for enabled_id in concept.enables:
                self._prerequisite_graph[enabled_id].add(concept.concept_id)
                self._dependency_graph[concept.concept_id].add(enabled_id)

            # Persist to storage if available
            if self.storage_backend:
                await self.storage_backend.store_concept(concept)

            # Clear relevant caches
            self._clear_caches_for_concept(concept.concept_id)

            return True

        except Exception as e:
            print(f"Error adding concept to knowledge graph: {e}")
            return False

    async def get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        """
        Get a concept by ID.

        Args:
            concept_id: Concept identifier

        Returns:
            ConceptNode if found, None otherwise
        """
        if concept_id in self._concepts:
            return self._concepts[concept_id]

        # Try to load from storage
        if self.storage_backend:
            try:
                concept_data = await self.storage_backend.get_concept(concept_id)
                if concept_data:
                    concept = ConceptNode(**concept_data)
                    self._concepts[concept_id] = concept
                    return concept
            except Exception:
                pass

        return None

    async def has_concept(self, concept_id: str) -> bool:
        """
        Check if a concept exists in the graph.

        Args:
            concept_id: Concept identifier

        Returns:
            True if concept exists, False otherwise
        """
        return concept_id in self._concepts or (
            self.storage_backend and
            await self.storage_backend.has_concept(concept_id)
        )

    async def add_prerequisite_relationship(
        self,
        concept_id: str,
        prerequisite_id: str
    ) -> bool:
        """
        Add a prerequisite relationship between concepts.

        Args:
            concept_id: Target concept ID
            prerequisite_id: Prerequisite concept ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for circular dependencies
            if await self._would_create_cycle(prerequisite_id, concept_id):
                print(f"Cannot add prerequisite {prerequisite_id} -> {concept_id}: would create cycle")
                return False

            # Add relationship
            self._prerequisite_graph[concept_id].add(prerequisite_id)
            self._dependency_graph[prerequisite_id].add(concept_id)

            # Update concept nodes if they exist
            if concept_id in self._concepts:
                self._concepts[concept_id].add_prerequisite(prerequisite_id)

            if prerequisite_id in self._concepts:
                self._concepts[prerequisite_id].add_enables(concept_id)

            # Clear caches
            self._clear_caches_for_concept(concept_id)
            self._clear_caches_for_concept(prerequisite_id)

            return True

        except Exception as e:
            print(f"Error adding prerequisite relationship: {e}")
            return False

    async def get_prerequisites(
        self,
        concept_id: str,
        recursive: bool = False
    ) -> List[ConceptNode]:
        """
        Get prerequisites for a concept.

        Args:
            concept_id: Concept identifier
            recursive: Whether to get all transitive prerequisites

        Returns:
            List of prerequisite concepts
        """
        try:
            if recursive:
                prereq_ids = await self._get_all_prerequisites(concept_id)
            else:
                prereq_ids = self._prerequisite_graph.get(concept_id, set())

            prerequisites = []
            for prereq_id in prereq_ids:
                concept = await self.get_concept(prereq_id)
                if concept:
                    prerequisites.append(concept)

            return prerequisites

        except Exception as e:
            print(f"Error getting prerequisites: {e}")
            return []

    async def get_dependents(
        self,
        concept_id: str,
        recursive: bool = False
    ) -> List[ConceptNode]:
        """
        Get concepts that depend on this concept.

        Args:
            concept_id: Concept identifier
            recursive: Whether to get all transitive dependents

        Returns:
            List of dependent concepts
        """
        try:
            if recursive:
                dependent_ids = await self._get_all_dependents(concept_id)
            else:
                dependent_ids = self._dependency_graph.get(concept_id, set())

            dependents = []
            for dep_id in dependent_ids:
                concept = await self.get_concept(dep_id)
                if concept:
                    dependents.append(concept)

            return dependents

        except Exception as e:
            print(f"Error getting dependents: {e}")
            return []

    async def generate_learning_path(
        self,
        target_concept: str,
        current_mastery: Dict[str, MasteryLevel],
        optimization_criteria: str = "shortest"
    ) -> List[str]:
        """
        Generate optimal learning path to target concept.

        Args:
            target_concept: Target concept to learn
            current_mastery: Current mastery levels for concepts
            optimization_criteria: "shortest", "easiest", "balanced"

        Returns:
            List of concept IDs in learning order
        """
        try:
            # Get all prerequisites for target
            all_prerequisites = await self._get_all_prerequisites(target_concept)

            # Filter unmastered prerequisites
            unmastered_prereqs = [
                prereq for prereq in all_prerequisites
                if current_mastery.get(prereq, MasteryLevel.UNKNOWN).value < MasteryLevel.PROFICIENT.value
            ]

            # Add target concept if not mastered
            if current_mastery.get(target_concept, MasteryLevel.UNKNOWN).value < MasteryLevel.PROFICIENT.value:
                unmastered_prereqs.append(target_concept)

            if not unmastered_prereqs:
                return []  # Already mastered

            # Generate topologically sorted path
            learning_path = await self._topological_sort_with_optimization(
                unmastered_prereqs, optimization_criteria
            )

            return learning_path

        except Exception as e:
            print(f"Error generating learning path: {e}")
            return [target_concept]

    async def find_learning_gaps(
        self,
        target_concepts: List[str],
        current_mastery: Dict[str, MasteryLevel]
    ) -> Dict[str, List[str]]:
        """
        Find learning gaps for multiple target concepts.

        Args:
            target_concepts: List of target concept IDs
            current_mastery: Current mastery levels

        Returns:
            Dictionary mapping target concepts to their missing prerequisites
        """
        gaps = {}

        for target in target_concepts:
            try:
                # Get all prerequisites
                all_prereqs = await self._get_all_prerequisites(target)

                # Find unmastered prerequisites
                missing_prereqs = [
                    prereq for prereq in all_prereqs
                    if current_mastery.get(prereq, MasteryLevel.UNKNOWN).value < MasteryLevel.PROFICIENT.value
                ]

                gaps[target] = missing_prereqs

            except Exception as e:
                print(f"Error finding gaps for {target}: {e}")
                gaps[target] = []

        return gaps

    async def suggest_next_concepts(
        self,
        current_mastery: Dict[str, MasteryLevel],
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Suggest next concepts to learn based on current mastery.

        Args:
            current_mastery: Current mastery levels
            limit: Maximum number of suggestions

        Returns:
            List of (concept_id, priority_score) tuples
        """
        try:
            suggestions = []

            for concept_id in self._concepts:
                # Skip if already mastered
                if current_mastery.get(concept_id, MasteryLevel.UNKNOWN).value >= MasteryLevel.PROFICIENT.value:
                    continue

                # Check if prerequisites are satisfied
                concept = self._concepts[concept_id]
                if concept.is_prerequisite_satisfied(current_mastery):
                    priority = await self._calculate_concept_priority(
                        concept_id, current_mastery
                    )
                    suggestions.append((concept_id, priority))

            # Sort by priority and return top suggestions
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return suggestions[:limit]

        except Exception as e:
            print(f"Error suggesting next concepts: {e}")
            return []

    async def get_concept_difficulty_progression(
        self,
        concept_id: str
    ) -> List[str]:
        """
        Get difficulty progression for a concept.

        Args:
            concept_id: Concept identifier

        Returns:
            List of content IDs ordered by difficulty
        """
        try:
            concept = await self.get_concept(concept_id)
            if not concept:
                return []

            # Return the difficulty progression if available
            return concept.difficulty_progression

        except Exception as e:
            print(f"Error getting difficulty progression: {e}")
            return []

    async def analyze_concept_clusters(self) -> Dict[str, List[str]]:
        """
        Analyze concept clusters based on relationships.

        Returns:
            Dictionary mapping cluster names to concept lists
        """
        try:
            # Simple clustering based on concept types and relationships
            clusters = defaultdict(list)

            for concept_id, concept in self._concepts.items():
                # Cluster by concept type
                cluster_name = concept.concept_type.value
                clusters[cluster_name].append(concept_id)

            return dict(clusters)

        except Exception as e:
            print(f"Error analyzing concept clusters: {e}")
            return {}

    async def validate_graph_integrity(self) -> Dict[str, Any]:
        """
        Validate knowledge graph integrity.

        Returns:
            Dictionary with validation results
        """
        issues = []
        stats = {}

        try:
            # Check for cycles
            cycles = await self._detect_cycles()
            if cycles:
                issues.append(f"Detected {len(cycles)} cycles in prerequisite graph")

            # Check for orphaned concepts
            orphaned = await self._find_orphaned_concepts()
            if orphaned:
                issues.append(f"Found {len(orphaned)} orphaned concepts")

            # Check for missing prerequisites
            missing_prereqs = await self._find_missing_prerequisites()
            if missing_prereqs:
                issues.append(f"Found {len(missing_prereqs)} references to missing concepts")

            # Calculate graph statistics
            stats = {
                "total_concepts": len(self._concepts),
                "total_relationships": sum(len(prereqs) for prereqs in self._prerequisite_graph.values()),
                "concept_types": {
                    concept_type.value: sum(1 for c in self._concepts.values() if c.concept_type == concept_type)
                    for concept_type in ConceptType
                },
                "average_prerequisites": (
                    sum(len(prereqs) for prereqs in self._prerequisite_graph.values()) / len(self._concepts)
                    if self._concepts else 0
                )
            }

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "statistics": stats
            }

        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Validation error: {e}"],
                "statistics": {}
            }

    # Private helper methods

    async def _get_all_prerequisites(self, concept_id: str) -> Set[str]:
        """Get all transitive prerequisites for a concept."""
        if concept_id in self._prerequisite_cache:
            return self._prerequisite_cache[concept_id].copy()

        visited = set()
        queue = deque([concept_id])
        all_prereqs = set()

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            prereqs = self._prerequisite_graph.get(current, set())

            for prereq in prereqs:
                if prereq not in all_prereqs:
                    all_prereqs.add(prereq)
                    queue.append(prereq)

        self._prerequisite_cache[concept_id] = all_prereqs
        return all_prereqs.copy()

    async def _get_all_dependents(self, concept_id: str) -> Set[str]:
        """Get all transitive dependents for a concept."""
        visited = set()
        queue = deque([concept_id])
        all_dependents = set()

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            dependents = self._dependency_graph.get(current, set())

            for dependent in dependents:
                if dependent not in all_dependents:
                    all_dependents.add(dependent)
                    queue.append(dependent)

        return all_dependents

    async def _would_create_cycle(self, from_concept: str, to_concept: str) -> bool:
        """Check if adding a relationship would create a cycle."""
        # Check if to_concept can reach from_concept
        reachable = await self._get_all_dependents(to_concept)
        return from_concept in reachable

    async def _topological_sort_with_optimization(
        self,
        concept_ids: List[str],
        optimization_criteria: str
    ) -> List[str]:
        """Perform topological sort with optimization criteria."""
        # Build subgraph for concepts to learn
        subgraph = {concept_id: set() for concept_id in concept_ids}
        for concept_id in concept_ids:
            prereqs = self._prerequisite_graph.get(concept_id, set())
            subgraph[concept_id] = prereqs.intersection(set(concept_ids))

        # Kahn's algorithm with optimization
        in_degree = {concept_id: len(prereqs) for concept_id, prereqs in subgraph.items()}
        queue = deque([concept_id for concept_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            # Choose next concept based on optimization criteria
            if optimization_criteria == "easiest":
                current = await self._choose_easiest_concept(list(queue))
            elif optimization_criteria == "balanced":
                current = await self._choose_balanced_concept(list(queue))
            else:  # shortest
                current = queue.popleft()

            queue.remove(current)
            result.append(current)

            # Update in-degrees
            for dependent in self._dependency_graph.get(current, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    async def _choose_easiest_concept(self, candidates: List[str]) -> str:
        """Choose the easiest concept from candidates."""
        # Prefer concepts with lower difficulty
        easiest = candidates[0]
        easiest_difficulty = DifficultyLevel.EXPERT

        for candidate in candidates:
            concept = await self.get_concept(candidate)
            if concept and concept.difficulty_level.value < easiest_difficulty.value:
                easiest = candidate
                easiest_difficulty = concept.difficulty_level

        return easiest

    async def _choose_balanced_concept(self, candidates: List[str]) -> str:
        """Choose concept based on balanced criteria."""
        # Balance between difficulty and learning impact
        best_candidate = candidates[0]
        best_score = -1

        for candidate in candidates:
            concept = await self.get_concept(candidate)
            if concept:
                # Score based on enables count and inverse difficulty
                enables_count = len(self._dependency_graph.get(candidate, set()))
                difficulty_penalty = concept.difficulty_level.value / 4.0
                score = enables_count * (1 - difficulty_penalty)

                if score > best_score:
                    best_score = score
                    best_candidate = candidate

        return best_candidate

    async def _calculate_concept_priority(
        self,
        concept_id: str,
        current_mastery: Dict[str, MasteryLevel]
    ) -> float:
        """Calculate priority score for a concept."""
        priority = 0.0

        try:
            concept = await self.get_concept(concept_id)
            if not concept:
                return 0.0

            # Factor 1: Number of concepts this enables
            enabled_concepts = self._dependency_graph.get(concept_id, set())
            unmastered_enabled = sum(
                1 for enabled in enabled_concepts
                if current_mastery.get(enabled, MasteryLevel.UNKNOWN).value < MasteryLevel.PROFICIENT.value
            )
            priority += unmastered_enabled * 0.4

            # Factor 2: Concept type importance
            type_weights = {
                ConceptType.FUNDAMENTAL: 0.9,
                ConceptType.SKILL: 0.7,
                ConceptType.KNOWLEDGE: 0.6,
                ConceptType.APPLICATION: 0.8,
                ConceptType.SYNTHESIS: 0.5
            }
            priority += type_weights.get(concept.concept_type, 0.5) * 0.3

            # Factor 3: Inverse of difficulty (easier concepts get higher priority)
            difficulty_factor = (5 - concept.difficulty_level.value) / 4.0
            priority += difficulty_factor * 0.2

            # Factor 4: Learning analytics (if available)
            if concept.total_learners > 0 and concept.average_mastery_time_hours:
                # Prefer concepts with good success rates
                success_indicator = min(1.0, concept.total_learners / 100.0)
                priority += success_indicator * 0.1

            return min(1.0, priority)

        except Exception:
            return 0.0

    async def _detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the prerequisite graph."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for prereq in self._prerequisite_graph.get(node, set()):
                dfs(prereq, path + [node])

            rec_stack.remove(node)

        for concept_id in self._concepts:
            if concept_id not in visited:
                dfs(concept_id, [])

        return cycles

    async def _find_orphaned_concepts(self) -> List[str]:
        """Find concepts with no relationships."""
        orphaned = []

        for concept_id in self._concepts:
            has_prereqs = len(self._prerequisite_graph.get(concept_id, set())) > 0
            has_dependents = len(self._dependency_graph.get(concept_id, set())) > 0

            if not has_prereqs and not has_dependents:
                orphaned.append(concept_id)

        return orphaned

    async def _find_missing_prerequisites(self) -> List[str]:
        """Find references to concepts that don't exist."""
        missing = set()

        for concept_id, prereqs in self._prerequisite_graph.items():
            for prereq in prereqs:
                if prereq not in self._concepts:
                    missing.add(prereq)

        return list(missing)

    def _clear_caches_for_concept(self, concept_id: str) -> None:
        """Clear caches related to a concept."""
        # Clear prerequisite cache
        if concept_id in self._prerequisite_cache:
            del self._prerequisite_cache[concept_id]

        # Clear path cache entries involving this concept
        keys_to_remove = [
            key for key in self._path_cache.keys()
            if concept_id in key
        ]
        for key in keys_to_remove:
            del self._path_cache[key]

    async def export_graph(self) -> Dict[str, Any]:
        """Export the entire knowledge graph."""
        return {
            "concepts": {
                concept_id: asdict(concept)
                for concept_id, concept in self._concepts.items()
            },
            "relationships": {
                "prerequisites": {
                    concept_id: list(prereqs)
                    for concept_id, prereqs in self._prerequisite_graph.items()
                },
                "dependencies": {
                    concept_id: list(deps)
                    for concept_id, deps in self._dependency_graph.items()
                }
            }
        }

    async def import_graph(self, graph_data: Dict[str, Any]) -> bool:
        """Import knowledge graph from data."""
        try:
            # Clear existing graph
            self._concepts.clear()
            self._prerequisite_graph.clear()
            self._dependency_graph.clear()
            self._path_cache.clear()
            self._prerequisite_cache.clear()

            # Import concepts
            for concept_id, concept_data in graph_data.get("concepts", {}).items():
                concept = ConceptNode(**concept_data)
                self._concepts[concept_id] = concept

            # Import relationships
            relationships = graph_data.get("relationships", {})
            prereq_data = relationships.get("prerequisites", {})

            for concept_id, prereq_list in prereq_data.items():
                self._prerequisite_graph[concept_id] = set(prereq_list)

            # Rebuild dependency graph
            for concept_id, prereqs in self._prerequisite_graph.items():
                for prereq in prereqs:
                    self._dependency_graph[prereq].add(concept_id)

            return True

        except Exception as e:
            print(f"Error importing knowledge graph: {e}")
            return False