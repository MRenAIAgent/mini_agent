"""
MCP Selection Engine

Intelligently selects and loads MCP servers based on agent system prompts,
roles, and capabilities.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from functools import lru_cache
import numpy as np
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class MCPMetadata:
    """Extended metadata for MCP selection and security."""

    name: str
    description: str
    categories: List[str]
    capabilities: List[str]
    required_permissions: List[str]
    risk_level: str  # "low", "medium", "high"
    connection: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    usage_patterns: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Validate risk level."""
        if self.risk_level not in ["low", "medium", "high"]:
            raise ValueError(f"Invalid risk_level: {self.risk_level}")


class LRUCache:
    """Simple LRU cache for selection results."""

    def __init__(self, maxsize: int = 100):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)


class MCPSelectionEngine:
    """
    Analyzes agent context and selects relevant MCP servers.

    Uses multiple strategies:
    1. Semantic similarity (if embedding model available)
    2. Keyword extraction and matching
    3. Role-based filtering
    4. Usage pattern analysis
    """

    def __init__(self, use_embeddings: bool = False):
        """
        Initialize selection engine.

        Args:
            use_embeddings: Whether to use semantic embeddings (requires sentence-transformers)
        """
        self.mcp_registry: Dict[str, MCPMetadata] = {}
        self.selection_cache = LRUCache(maxsize=100)
        self.use_embeddings = use_embeddings

        # Try to load embedding model if requested
        self.embedding_model = None
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model for semantic matching")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, falling back to keyword matching"
                )
                self.use_embeddings = False

    def register_mcp(self, metadata: MCPMetadata) -> None:
        """
        Register an MCP server in the registry.

        Args:
            metadata: MCP metadata including capabilities and permissions
        """
        # Compute embedding if model available
        if self.embedding_model and metadata.embedding is None:
            text = f"{metadata.description} {' '.join(metadata.capabilities)}"
            metadata.embedding = self.embedding_model.encode(text)

        self.mcp_registry[metadata.name] = metadata
        logger.info(f"Registered MCP: {metadata.name} with {len(metadata.capabilities)} capabilities")

    def load_registry_from_config(self, config: Dict[str, Any]) -> None:
        """
        Load MCP registry from configuration dictionary.

        Args:
            config: Configuration dict with 'mcp_servers' key
        """
        mcp_servers = config.get('mcp_servers', {})

        for name, server_config in mcp_servers.items():
            metadata = MCPMetadata(
                name=name,
                description=server_config['description'],
                categories=server_config.get('categories', []),
                capabilities=server_config.get('capabilities', []),
                required_permissions=server_config.get('required_permissions', []),
                risk_level=server_config.get('risk_level', 'medium'),
                connection=server_config.get('connection', {})
            )
            self.register_mcp(metadata)

        logger.info(f"Loaded {len(self.mcp_registry)} MCPs from configuration")

    async def select_mcps_for_agent(
        self,
        system_prompt: str,
        agent_role: str,
        agent_permissions: Set[str],
        task_context: Optional[str] = None,
        max_mcps: int = 5
    ) -> List[str]:
        """
        Select best-matching MCPs for an agent.

        Algorithm:
        1. Extract capabilities from system prompt
        2. Compute relevance scores (semantic or keyword-based)
        3. Apply role-based filtering
        4. Check permission requirements
        5. Rank by score and risk level
        6. Return top-K MCPs

        Args:
            system_prompt: Agent's system prompt
            agent_role: Agent's role (e.g., "analyst", "developer")
            agent_permissions: Set of permissions agent has
            task_context: Optional task-specific context
            max_mcps: Maximum number of MCPs to select

        Returns:
            List of selected MCP names
        """
        # Check cache
        cache_key = f"{hash(system_prompt)}:{agent_role}:{max_mcps}"
        cached = self.selection_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for agent role: {agent_role}")
            return cached

        # Extract capabilities from prompt
        required_capabilities = self.extract_capabilities(system_prompt)
        if task_context:
            required_capabilities.update(self.extract_capabilities(task_context))

        logger.info(
            f"Extracted capabilities from prompt: {required_capabilities}"
        )

        # Score all MCPs
        scored_mcps = []
        for mcp_name, mcp_metadata in self.mcp_registry.items():
            # Check permissions first (hard filter)
            if not self._has_required_permissions(
                agent_permissions,
                mcp_metadata.required_permissions
            ):
                logger.debug(
                    f"Skipping {mcp_name}: missing permissions {mcp_metadata.required_permissions}"
                )
                continue

            # Compute relevance score
            if self.use_embeddings and self.embedding_model:
                score = self.compute_semantic_match(
                    system_prompt,
                    mcp_metadata
                )
            else:
                score = self.compute_keyword_match(
                    required_capabilities,
                    mcp_metadata
                )

            # Adjust score based on risk level (prefer lower risk)
            risk_penalty = {
                "low": 0.0,
                "medium": 0.1,
                "high": 0.2
            }
            score -= risk_penalty.get(mcp_metadata.risk_level, 0.0)

            scored_mcps.append((mcp_name, score))

        # Sort by score descending
        scored_mcps.sort(key=lambda x: x[1], reverse=True)

        # Select top-K
        selected = [name for name, score in scored_mcps[:max_mcps]]

        logger.info(
            f"Selected {len(selected)} MCPs for role {agent_role}: {selected}"
        )

        # Cache result
        self.selection_cache.set(cache_key, selected)

        return selected

    def extract_capabilities(self, text: str) -> Set[str]:
        """
        Extract capability keywords from text.

        Looks for action verbs and domain nouns that indicate
        what the agent needs to do.

        Args:
            text: System prompt or task description

        Returns:
            Set of capability keywords
        """
        text = text.lower()
        capabilities = set()

        # Common capability patterns
        patterns = {
            "data": [r"\bdata\b", r"\bdatabase\b", r"\bquery\b", r"\bsql\b"],
            "computation": [r"\bcalculat\w*", r"\bcompute\b", r"\bmath\b", r"\bstatistic\w*"],
            "files": [r"\bfile\b", r"\bread\b", r"\bwrite\b", r"\bstorage\b"],
            "network": [r"\bapi\b", r"\bhttp\b", r"\brequest\b", r"\bweb\b"],
            "weather": [r"\bweather\b", r"\bforecast\b", r"\btemperature\b"],
            "email": [r"\bemail\b", r"\bsend\b.*\bmessage\b", r"\bsmtp\b"],
            "visualization": [r"\bplot\b", r"\bchart\b", r"\bgraph\b", r"\bvisuali\w*"],
            "git": [r"\bgit\b", r"\bversion control\b", r"\brepository\b"],
            "code": [r"\bcode\b", r"\bexecute\b", r"\brun\b.*\bscript\b"],
        }

        for capability, regex_list in patterns.items():
            for regex in regex_list:
                if re.search(regex, text):
                    capabilities.add(capability)
                    break

        return capabilities

    def compute_semantic_match(
        self,
        prompt: str,
        mcp_metadata: MCPMetadata
    ) -> float:
        """
        Compute semantic similarity using embeddings.

        Args:
            prompt: Agent system prompt
            mcp_metadata: MCP metadata with embedding

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not self.embedding_model or mcp_metadata.embedding is None:
            return 0.0

        prompt_embedding = self.embedding_model.encode(prompt)

        # Cosine similarity
        similarity = np.dot(prompt_embedding, mcp_metadata.embedding) / (
            np.linalg.norm(prompt_embedding) * np.linalg.norm(mcp_metadata.embedding)
        )

        return float(similarity)

    def compute_keyword_match(
        self,
        required_capabilities: Set[str],
        mcp_metadata: MCPMetadata
    ) -> float:
        """
        Compute match score based on keyword overlap.

        Args:
            required_capabilities: Capabilities extracted from prompt
            mcp_metadata: MCP metadata

        Returns:
            Match score (0.0 to 1.0)
        """
        # Convert MCP capabilities and categories to set
        mcp_capabilities = set(
            cap.lower() for cap in mcp_metadata.capabilities
        )
        mcp_categories = set(
            cat.lower() for cat in mcp_metadata.categories
        )

        # Compute overlap
        capability_overlap = len(required_capabilities & mcp_capabilities)
        category_overlap = len(required_capabilities & mcp_categories)

        total_overlap = capability_overlap + category_overlap

        if not required_capabilities:
            return 0.0

        # Normalize by size of required set
        score = total_overlap / len(required_capabilities)

        # Cap at 1.0
        return min(score, 1.0)

    def _has_required_permissions(
        self,
        agent_permissions: Set[str],
        required_permissions: List[str]
    ) -> bool:
        """
        Check if agent has all required permissions.

        Args:
            agent_permissions: Permissions agent has
            required_permissions: Permissions MCP requires

        Returns:
            True if agent has all required permissions
        """
        # Wildcard permission grants everything
        if "*" in agent_permissions:
            return True

        # Check each required permission
        for perm in required_permissions:
            if perm not in agent_permissions:
                # Check for wildcard in category (e.g., "read:*")
                category = perm.split(":")[0] if ":" in perm else perm
                if f"{category}:*" not in agent_permissions:
                    return False

        return True

    def get_mcp_metadata(self, mcp_name: str) -> Optional[MCPMetadata]:
        """
        Get metadata for a specific MCP.

        Args:
            mcp_name: Name of MCP

        Returns:
            MCP metadata or None if not found
        """
        return self.mcp_registry.get(mcp_name)

    def list_all_mcps(self) -> List[str]:
        """Get list of all registered MCP names."""
        return list(self.mcp_registry.keys())

    def get_mcps_by_category(self, category: str) -> List[str]:
        """
        Get all MCPs in a specific category.

        Args:
            category: Category name (e.g., "data", "computation")

        Returns:
            List of MCP names in that category
        """
        return [
            name
            for name, metadata in self.mcp_registry.items()
            if category.lower() in [c.lower() for c in metadata.categories]
        ]

    def get_mcps_by_risk_level(self, risk_level: str) -> List[str]:
        """
        Get all MCPs at a specific risk level.

        Args:
            risk_level: "low", "medium", or "high"

        Returns:
            List of MCP names at that risk level
        """
        return [
            name
            for name, metadata in self.mcp_registry.items()
            if metadata.risk_level == risk_level
        ]
