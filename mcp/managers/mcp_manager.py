"""
Centralized MCP manager that orchestrates all components.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..core.exceptions import (
    MCPError,
    MCPSecurityError,
    MCPConnectionError,
    MCPValidationError,
)
from ..security import (
    SecurityContext,
    PolicyEngine,
    PolicyAction,
    InputValidator,
    AuditLogger,
    AuditEventType,
)
from ..selection import MCPSelectionEngine
from .connection_pool import ConnectionPool
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


@dataclass
class MCPExecutionRequest:
    """Request to execute an MCP tool."""
    tool_name: str
    arguments: Dict[str, Any]
    context: SecurityContext
    schema: Optional[Dict[str, Any]] = None
    timeout: Optional[float] = None
    retry_count: int = 0


@dataclass
class MCPExecutionResult:
    """Result of MCP tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    policy_decision: Optional[Any] = None
    validation_result: Optional[Any] = None
    metadata: Dict[str, Any] = None


class MCPManager:
    """
    Central manager for MCP operations with integrated security.

    Responsibilities:
    - Orchestrate MCP selection based on context
    - Enforce security policies before execution
    - Validate and sanitize inputs
    - Manage connections and sessions
    - Provide comprehensive audit logging
    - Handle errors and retries
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        enable_security: bool = True,
        enable_audit: bool = True,
        enable_caching: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize MCP manager.

        Args:
            config_path: Path to configuration directory
            enable_security: Enable security checks
            enable_audit: Enable audit logging
            enable_caching: Enable result caching
            max_retries: Maximum retry attempts for failed operations
        """
        self.config_path = config_path or Path("config")
        self.enable_security = enable_security
        self.enable_audit = enable_audit
        self.enable_caching = enable_caching
        self.max_retries = max_retries

        # Initialize components
        self._initialize_components()

        # Load configuration
        self._load_configuration()

        # Statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "blocked_executions": 0,
            "average_execution_time": 0.0,
        }

    def _initialize_components(self) -> None:
        """Initialize all MCP components."""
        # Security components
        self.policy_engine = PolicyEngine() if self.enable_security else None
        self.input_validator = InputValidator()
        self.audit_logger = AuditLogger() if self.enable_audit else None

        # Selection and management
        self.selection_engine = MCPSelectionEngine()
        self.connection_pool = ConnectionPool()
        self.session_manager = SessionManager()

        # Result cache
        self.result_cache: Dict[str, MCPExecutionResult] = {}

        logger.info("MCP Manager components initialized")

    def _load_configuration(self) -> None:
        """Load configuration from files."""
        try:
            # Load MCP registry
            mcp_config_path = self.config_path / "mcp_registry.yaml"
            if mcp_config_path.exists():
                import yaml
                with open(mcp_config_path) as f:
                    config = yaml.safe_load(f)
                    self.selection_engine.load_registry_from_config(config)
                    logger.info(f"Loaded MCP registry from {mcp_config_path}")

            # Load security policies
            if self.policy_engine:
                policy_config_path = self.config_path / "security_policies.yaml"
                if policy_config_path.exists():
                    with open(policy_config_path) as f:
                        config = yaml.safe_load(f)
                        self.policy_engine.load_policies_from_config(config)
                        logger.info(f"Loaded security policies from {policy_config_path}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise MCPError(f"Configuration loading failed: {e}")

    async def execute_tool(
        self,
        request: MCPExecutionRequest,
    ) -> MCPExecutionResult:
        """
        Execute an MCP tool with full security pipeline.

        Pipeline:
        1. Input validation
        2. Security policy evaluation
        3. Tool execution
        4. Result validation
        5. Audit logging

        Args:
            request: Execution request

        Returns:
            Execution result

        Raises:
            MCPSecurityError: If security checks fail
            MCPValidationError: If validation fails
            MCPError: For other errors
        """
        start_time = datetime.now()
        result = MCPExecutionResult(success=False)

        try:
            # Step 1: Input Validation
            if request.schema:
                validation_result = self.input_validator.validate_arguments(
                    tool_schema=request.schema,
                    arguments=request.arguments,
                    sanitize=True,
                    strict=self.enable_security,
                )

                result.validation_result = validation_result

                if not validation_result.is_valid:
                    self._log_validation_failure(request, validation_result)
                    raise MCPValidationError(
                        f"Input validation failed: {validation_result.errors}",
                        field_name=request.tool_name,
                    )

                # Use sanitized arguments
                if validation_result.sanitized_arguments:
                    request.arguments = validation_result.sanitized_arguments

            # Step 2: Security Policy Evaluation
            if self.enable_security and self.policy_engine:
                # Get tool metadata from registry
                tool_metadata = self.selection_engine.get_mcp_metadata(
                    request.tool_name
                )

                if not tool_metadata:
                    raise MCPError(f"Unknown tool: {request.tool_name}")

                policy_decision = await self.policy_engine.evaluate(
                    context=request.context,
                    tool_name=request.tool_name,
                    tool_category=tool_metadata.categories[0] if tool_metadata.categories else "unknown",
                    tool_permissions=tool_metadata.required_permissions,
                    tool_risk_level=tool_metadata.risk_level,
                    arguments=request.arguments,
                )

                result.policy_decision = policy_decision

                # Handle policy decision
                if policy_decision.action == PolicyAction.DENY:
                    self._log_security_block(request, policy_decision)
                    self.execution_stats["blocked_executions"] += 1
                    raise MCPSecurityError(
                        f"Tool execution denied: {policy_decision.reason}",
                        policy_name=policy_decision.matched_rules[0] if policy_decision.matched_rules else None,
                    )

                elif policy_decision.action == PolicyAction.REQUIRE_APPROVAL:
                    # In production, implement approval workflow
                    logger.warning(f"Tool {request.tool_name} requires approval: {policy_decision.reason}")
                    # For now, we'll block
                    raise MCPSecurityError(
                        f"Tool requires approval: {policy_decision.reason}",
                        policy_name="approval_required",
                    )

                elif policy_decision.action == PolicyAction.RATE_LIMIT:
                    raise MCPError(f"Rate limit exceeded: {policy_decision.reason}")

            # Step 3: Check cache
            if self.enable_caching:
                cache_key = self._generate_cache_key(request)
                if cache_key in self.result_cache:
                    logger.debug(f"Cache hit for tool {request.tool_name}")
                    cached_result = self.result_cache[cache_key]
                    cached_result.metadata = {"cache_hit": True}
                    return cached_result

            # Step 4: Execute Tool
            execution_result = await self._execute_tool_internal(request)
            result.success = execution_result.success
            result.result = execution_result.result
            result.error = execution_result.error

            # Step 5: Cache result
            if self.enable_caching and result.success:
                self.result_cache[cache_key] = result

            # Step 6: Audit logging
            if self.enable_audit:
                self._log_execution(request, result)

            # Update statistics
            self.execution_stats["total_executions"] += 1
            if result.success:
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            self._update_avg_execution_time(execution_time)

            return result

        except MCPError:
            # Re-raise MCP errors
            raise

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error executing tool {request.tool_name}: {e}")
            if self.enable_audit:
                self.audit_logger.log_tool_execution(
                    agent_id=request.context.agent_id,
                    session_id=request.context.session_id,
                    tool_name=request.tool_name,
                    arguments=request.arguments,
                    success=False,
                    error=str(e),
                )
            raise MCPError(f"Tool execution failed: {e}")

    async def _execute_tool_internal(
        self,
        request: MCPExecutionRequest,
    ) -> MCPExecutionResult:
        """
        Internal tool execution with connection management.

        Args:
            request: Execution request

        Returns:
            Execution result
        """
        # Get connection from pool
        tool_metadata = self.selection_engine.get_mcp_metadata(request.tool_name)
        if not tool_metadata:
            return MCPExecutionResult(
                success=False,
                error=f"Tool {request.tool_name} not found in registry"
            )

        connection = await self.connection_pool.get_connection(
            server_name=tool_metadata.name,
            connection_info=tool_metadata.connection,
        )

        if not connection:
            return MCPExecutionResult(
                success=False,
                error=f"Failed to get connection for {request.tool_name}"
            )

        try:
            # Execute through protocol
            result = await connection.protocol.call_tool(
                name=request.tool_name,
                arguments=request.arguments,
            )

            return MCPExecutionResult(
                success=not bool(result.get("error")),
                result=result.get("result"),
                error=result.get("error"),
            )

        except asyncio.TimeoutError:
            return MCPExecutionResult(
                success=False,
                error=f"Tool execution timed out after {request.timeout}s"
            )

        except Exception as e:
            return MCPExecutionResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

        finally:
            # Return connection to pool
            await self.connection_pool.return_connection(
                server_name=tool_metadata.name,
                connection=connection,
            )

    async def select_and_load_mcps(
        self,
        system_prompt: str,
        agent_role: str,
        agent_permissions: Set[str],
        session_id: str,
        max_mcps: int = 5,
    ) -> List[str]:
        """
        Select and load MCPs for an agent session.

        Args:
            system_prompt: Agent's system prompt
            agent_role: Agent role
            agent_permissions: Agent permissions
            session_id: Session identifier
            max_mcps: Maximum MCPs to load

        Returns:
            List of loaded MCP names
        """
        # Select MCPs
        selected_mcps = await self.selection_engine.select_mcps_for_agent(
            system_prompt=system_prompt,
            agent_role=agent_role,
            agent_permissions=agent_permissions,
            max_mcps=max_mcps,
        )

        # Create session
        session = self.selection_engine.create_session(
            agent_id=f"{agent_role}_{session_id}",
            session_id=session_id,
            baseline_mcps=selected_mcps,
        )

        # Pre-connect to selected MCPs
        for mcp_name in selected_mcps:
            metadata = self.selection_engine.get_mcp_metadata(mcp_name)
            if metadata:
                await self.connection_pool.create_connection(
                    server_name=mcp_name,
                    connection_info=metadata.connection,
                )

        logger.info(f"Loaded {len(selected_mcps)} MCPs for session {session_id}")
        return selected_mcps

    async def handle_dynamic_query(
        self,
        query: str,
        session_id: str,
        context: SecurityContext,
    ) -> List[str]:
        """
        Handle dynamic MCP selection based on user query.

        Args:
            query: User query
            session_id: Session identifier
            context: Security context

        Returns:
            List of newly loaded MCP names
        """
        # Select MCPs for query
        new_mcps = await self.selection_engine.select_mcps_for_query(
            user_query=query,
            session_id=session_id,
            agent_permissions=context.permissions,
        )

        # Load selected MCPs
        if new_mcps:
            loaded = await self.selection_engine.load_mcps_dynamically(
                session_id=session_id,
                mcp_names=new_mcps,
            )

            logger.info(f"Dynamically loaded MCPs for query: {loaded}")
            return list(loaded.keys())

        return []

    def _generate_cache_key(self, request: MCPExecutionRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        import json

        key_data = {
            "tool": request.tool_name,
            "arguments": json.dumps(request.arguments, sort_keys=True),
            "context": request.context.agent_role,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _update_avg_execution_time(self, execution_time: float) -> None:
        """Update average execution time."""
        stats = self.execution_stats
        total = stats["total_executions"]
        if total == 0:
            stats["average_execution_time"] = execution_time
        else:
            current_avg = stats["average_execution_time"]
            stats["average_execution_time"] = (
                (current_avg * (total - 1) + execution_time) / total
            )

    def _log_validation_failure(
        self,
        request: MCPExecutionRequest,
        validation_result: Any,
    ) -> None:
        """Log validation failure."""
        if self.audit_logger:
            self.audit_logger.create_event(
                event_type=AuditEventType.TOOL_BLOCKED,
                message=f"Input validation failed for {request.tool_name}",
                agent_id=request.context.agent_id,
                session_id=request.context.session_id,
                tool_name=request.tool_name,
                metadata={
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                }
            )

    def _log_security_block(
        self,
        request: MCPExecutionRequest,
        policy_decision: Any,
    ) -> None:
        """Log security block."""
        if self.audit_logger:
            self.audit_logger.log_security_violation(
                agent_id=request.context.agent_id,
                session_id=request.context.session_id,
                violation_type="policy_violation",
                details=policy_decision.reason,
                tool_name=request.tool_name,
                threat_indicators=policy_decision.matched_rules,
            )

    def _log_execution(
        self,
        request: MCPExecutionRequest,
        result: MCPExecutionResult,
    ) -> None:
        """Log tool execution."""
        if self.audit_logger:
            self.audit_logger.log_tool_execution(
                agent_id=request.context.agent_id,
                session_id=request.context.session_id,
                tool_name=request.tool_name,
                arguments=request.arguments,
                result=result.result,
                success=result.success,
                error=result.error,
                execution_time=result.execution_time,
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        stats = {
            "execution_stats": self.execution_stats,
            "cache_size": len(self.result_cache),
        }

        if self.audit_logger:
            stats["audit_stats"] = self.audit_logger.get_statistics()

        if self.connection_pool:
            stats["connection_pool"] = self.connection_pool.get_statistics()

        return stats

    async def shutdown(self) -> None:
        """Shutdown manager and cleanup resources."""
        logger.info("Shutting down MCP Manager")

        # Flush audit logs
        if self.audit_logger:
            self.audit_logger.flush_buffer()

        # Close connections
        await self.connection_pool.close_all()

        # Clear caches
        self.result_cache.clear()

        logger.info("MCP Manager shutdown complete")