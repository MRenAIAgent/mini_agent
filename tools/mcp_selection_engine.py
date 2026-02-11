"""
MCP Selection Engine

Intelligently selects and loads MCP servers based on agent system prompts,
roles, capabilities, AND user queries (dynamic selection).

Supports:
- Static selection from system prompt (baseline capabilities)
- Dynamic selection from user queries (runtime needs)
- Hot-loading MCPs during conversation
- Session-based MCP management
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Callable
from functools import lru_cache
import numpy as np
from collections import OrderedDict
from datetime import datetime

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


@dataclass
class MCPSession:
    """Tracks loaded MCPs for an agent session."""

    agent_id: str
    session_id: str
    loaded_mcps: Set[str] = field(default_factory=set)
    baseline_mcps: Set[str] = field(default_factory=set)  # From system prompt
    dynamic_mcps: Set[str] = field(default_factory=set)   # From user queries
    query_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_mcp(self, mcp_name: str, is_dynamic: bool = False) -> None:
        """Add an MCP to the session."""
        self.loaded_mcps.add(mcp_name)
        if is_dynamic:
            self.dynamic_mcps.add(mcp_name)
        else:
            self.baseline_mcps.add(mcp_name)
        self.last_updated = datetime.now()

    def remove_mcp(self, mcp_name: str) -> None:
        """Remove an MCP from the session."""
        self.loaded_mcps.discard(mcp_name)
        self.baseline_mcps.discard(mcp_name)
        self.dynamic_mcps.discard(mcp_name)
        self.last_updated = datetime.now()

    def is_loaded(self, mcp_name: str) -> bool:
        """Check if MCP is already loaded."""
        return mcp_name in self.loaded_mcps


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

    Supports both:
    - Static selection: From system prompt at agent initialization
    - Dynamic selection: From user queries during conversation

    Uses multiple strategies:
    1. Semantic similarity (if embedding model available)
    2. Keyword extraction and matching
    3. Role-based filtering
    4. Usage pattern analysis
    5. Query-based hot-loading
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

        # Session management for dynamic loading
        self.sessions: Dict[str, MCPSession] = {}
        self.mcp_loader: Optional[Callable] = None  # Callback to load MCP

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

    def set_mcp_loader(self, loader: Callable) -> None:
        """
        Set callback function for loading MCPs dynamically.

        Args:
            loader: Async function that loads an MCP: async def(mcp_name, metadata) -> bool
        """
        self.mcp_loader = loader
        logger.info("MCP loader callback registered for dynamic loading")

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

    async def select_mcps_for_query(
        self,
        user_query: str,
        session_id: str,
        agent_permissions: Set[str],
        max_new_mcps: int = 3,
        confidence_threshold: float = 0.3
    ) -> List[str]:
        """
        Dynamically select MCPs based on user query.

        This enables hot-loading of MCPs during conversation when
        the user asks for something not covered by baseline MCPs.

        Args:
            user_query: User's question or request
            session_id: Session ID to track loaded MCPs
            agent_permissions: Permissions the agent has
            max_new_mcps: Maximum new MCPs to load
            confidence_threshold: Minimum score to trigger loading

        Returns:
            List of newly selected MCP names (not already loaded)

        Example:
            System prompt: "You are a data analyst"
            Baseline MCPs: [calculator, database]

            User query: "What's the weather in NYC?"
            → Detects "weather" capability
            → Returns: ["weather"]
            → Hot-loads weather MCP
        """
        # Get or create session
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"No session found for {session_id}, creating new one")
            session = MCPSession(
                agent_id="unknown",
                session_id=session_id
            )
            self.sessions[session_id] = session

        # Add query to history
        session.query_history.append(user_query)

        # Extract capabilities from query
        required_capabilities = self.extract_capabilities(user_query)

        logger.info(
            f"Query capabilities: {required_capabilities} | "
            f"Already loaded: {session.loaded_mcps}"
        )

        # Score all MCPs
        scored_mcps = []
        for mcp_name, mcp_metadata in self.mcp_registry.items():
            # Skip if already loaded
            if session.is_loaded(mcp_name):
                logger.debug(f"Skipping {mcp_name}: already loaded")
                continue

            # Check permissions
            if not self._has_required_permissions(
                agent_permissions,
                mcp_metadata.required_permissions
            ):
                logger.debug(
                    f"Skipping {mcp_name}: missing permissions"
                )
                continue

            # Compute relevance score
            if self.use_embeddings and self.embedding_model:
                score = self.compute_semantic_match(
                    user_query,
                    mcp_metadata
                )
            else:
                score = self.compute_keyword_match(
                    required_capabilities,
                    mcp_metadata
                )

            # Only consider MCPs above threshold
            if score >= confidence_threshold:
                scored_mcps.append((mcp_name, score))

        # Sort by score descending
        scored_mcps.sort(key=lambda x: x[1], reverse=True)

        # Select top-K new MCPs
        new_mcps = [name for name, score in scored_mcps[:max_new_mcps]]

        if new_mcps:
            logger.info(
                f"Query triggered loading of new MCPs: {new_mcps}"
            )
        else:
            logger.debug(
                f"No new MCPs needed for query (loaded: {session.loaded_mcps})"
            )

        return new_mcps

    async def load_mcps_dynamically(
        self,
        session_id: str,
        mcp_names: List[str]
    ) -> Dict[str, bool]:
        """
        Hot-load MCPs during conversation.

        Args:
            session_id: Session ID
            mcp_names: List of MCP names to load

        Returns:
            Dict mapping MCP name to success status

        Raises:
            RuntimeError: If MCP loader not set
        """
        if not self.mcp_loader:
            raise RuntimeError(
                "MCP loader callback not set. Call set_mcp_loader() first."
            )

        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        results = {}

        for mcp_name in mcp_names:
            metadata = self.mcp_registry.get(mcp_name)
            if not metadata:
                logger.error(f"Unknown MCP: {mcp_name}")
                results[mcp_name] = False
                continue

            try:
                # Call loader callback
                success = await self.mcp_loader(mcp_name, metadata)

                if success:
                    session.add_mcp(mcp_name, is_dynamic=True)
                    logger.info(f"✓ Hot-loaded MCP: {mcp_name}")
                else:
                    logger.warning(f"✗ Failed to load MCP: {mcp_name}")

                results[mcp_name] = success

            except Exception as e:
                logger.error(f"Error loading MCP {mcp_name}: {e}")
                results[mcp_name] = False

        return results

    def create_session(
        self,
        agent_id: str,
        session_id: str,
        baseline_mcps: List[str]
    ) -> MCPSession:
        """
        Create a new session for an agent.

        Args:
            agent_id: Agent identifier
            session_id: Unique session identifier
            baseline_mcps: MCPs loaded from system prompt

        Returns:
            Created session
        """
        session = MCPSession(
            agent_id=agent_id,
            session_id=session_id
        )

        # Mark baseline MCPs as loaded
        for mcp_name in baseline_mcps:
            session.add_mcp(mcp_name, is_dynamic=False)

        self.sessions[session_id] = session

        logger.info(
            f"Created session {session_id} for agent {agent_id} "
            f"with {len(baseline_mcps)} baseline MCPs"
        )

        return session

    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close and remove a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Closed session {session_id}")

    async def auto_select_for_query(
        self,
        user_query: str,
        session_id: str,
        agent_permissions: Set[str],
        auto_load: bool = True,
        max_new_mcps: int = 3
    ) -> List[str]:
        """
        Convenience method: select AND load MCPs for a query in one call.

        Args:
            user_query: User's question
            session_id: Session ID
            agent_permissions: Agent permissions
            auto_load: If True, automatically load selected MCPs
            max_new_mcps: Maximum new MCPs to select

        Returns:
            List of newly loaded MCP names
        """
        # Select MCPs for query
        new_mcps = await self.select_mcps_for_query(
            user_query=user_query,
            session_id=session_id,
            agent_permissions=agent_permissions,
            max_new_mcps=max_new_mcps
        )

        if not new_mcps:
            return []

        # Auto-load if requested
        if auto_load and self.mcp_loader:
            results = await self.load_mcps_dynamically(
                session_id=session_id,
                mcp_names=new_mcps
            )
            # Return only successfully loaded MCPs
            return [name for name, success in results.items() if success]
        else:
            return new_mcps

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

        # Common capability patterns (expanded for query detection)
        patterns = {
            "data": [r"\bdata\b", r"\bdatabase\b", r"\bquery\b", r"\bsql\b", r"\btable\b", r"\bselect\b"],
            "computation": [r"\bcalculat\w*", r"\bcompute\b", r"\bmath\w*", r"\bstatistic\w*", r"\baverage\b", r"\bsum\b", r"\bmean\b"],
            "files": [r"\bfile\b", r"\bread\b", r"\bwrite\b", r"\bstorage\b", r"\bdirectory\b", r"\bfolder\b"],
            "filesystem": [r"\bfile\b", r"\bread\b", r"\bwrite\b", r"\bstorage\b", r"\bdirectory\b", r"\bfolder\b"],
            "network": [r"\bapi\b", r"\bhttp\b", r"\brequest\b", r"\bweb\b", r"\bfetch\b", r"\bdownload\b"],
            "weather": [r"\bweather\b", r"\bforecast\b", r"\btemperature\b", r"\bclimate\b", r"\brain\b", r"\bsun\b"],
            "email": [r"\bemail\b", r"\bsend\b.*\bmessage\b", r"\bsmtp\b", r"\bmail\b", r"\bnotify\b"],
            "communication": [r"\bemail\b", r"\bsend\b.*\bmessage\b", r"\bsmtp\b", r"\bmail\b", r"\bnotify\b", r"\bslack\b", r"\bmessage\b"],
            "visualization": [r"\bplot\b", r"\bchart\b", r"\bgraph\b", r"\bvisuali\w*", r"\bdraw\b", r"\bdiagram\b"],
            "git": [r"\bgit\b", r"\bversion control\b", r"\brepository\b", r"\bcommit\b", r"\bbranch\b", r"\brepo\b"],
            "code": [r"\bcode\b", r"\bexecute\b", r"\brun\b.*\bscript\b", r"\bpython\b", r"\bjavascript\b"],
            "search": [r"\bsearch\b", r"\bfind\b", r"\blookup\b", r"\bgoogle\b", r"\bweb\s+search\b"],
            "slack": [r"\bslack\b", r"\bchannel\b", r"\bmessage\b.*\bslack\b"],
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
