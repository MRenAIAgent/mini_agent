"""
Enhanced policy engine with secure evaluation and comprehensive rules.
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Set, Optional, Callable
from enum import Enum
from datetime import datetime
import hashlib
import json

from ..core.exceptions import MCPSecurityError
from .context import SecurityContext

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions that can be taken by policy engine."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    AUDIT = "audit"
    RATE_LIMIT = "rate_limit"


@dataclass
class PolicyDecision:
    """Enhanced policy decision with detailed information."""
    action: PolicyAction
    reason: str
    matched_rules: List[str]
    risk_score: float = 0.0
    confidence: float = 1.0
    conditions: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    audit_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "action": self.action.value,
            "reason": self.reason,
            "matched_rules": self.matched_rules,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "audit_required": self.audit_required,
            "metadata": self.metadata,
        }


@dataclass
class PolicyRule:
    """Enhanced security rule with safe evaluation."""
    name: str
    description: str
    condition: str  # Safe Python expression or custom DSL
    action: PolicyAction
    reason: str
    priority: int = 50
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    mitigations: List[str] = field(default_factory=list)
    risk_impact: float = 0.0
    confidence_threshold: float = 0.8

    def __post_init__(self):
        """Validate rule configuration."""
        if not self.name:
            raise ValueError("Rule name is required")
        if not self.condition:
            raise ValueError("Rule condition is required")
        if self.priority < 0 or self.priority > 100:
            raise ValueError("Priority must be between 0 and 100")


@dataclass
class SecurityPolicy:
    """Collection of security rules with metadata."""
    name: str
    description: str
    rules: List[PolicyRule]
    enabled: bool = True
    version: str = "1.0.0"
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)


class SafeEvaluator:
    """
    Safe expression evaluator using AST parsing instead of eval().
    Supports a limited set of operations for security.
    """

    ALLOWED_NAMES = {
        "True", "False", "None",
        "len", "str", "int", "float", "bool",
        "any", "all", "min", "max",
    }

    ALLOWED_NODE_TYPES = {
        ast.Expression,  # Root node for eval mode
        ast.BoolOp, ast.And, ast.Or,
        ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.In, ast.NotIn, ast.Is, ast.IsNot,
        ast.UnaryOp, ast.Not,
        ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
        ast.Name, ast.Load, ast.Constant, ast.Store,
        ast.List, ast.Tuple, ast.Set,
        ast.Attribute,
        ast.Call,
        ast.Subscript, ast.Index, ast.Slice,
    }

    def __init__(self):
        self.custom_functions: Dict[str, Callable] = {}
        self._register_default_functions()

    def _register_default_functions(self):
        """Register default safe functions."""
        self.custom_functions.update({
            "has_permission": lambda ctx, perm: ctx.has_permission(perm),
            "has_data_label": lambda ctx, label: ctx.has_data_label(label),
            "contains": lambda haystack, needle: needle in haystack,
            "starts_with": lambda s, prefix: s.startswith(prefix),
            "ends_with": lambda s, suffix: s.endswith(suffix),
            "matches": lambda s, pattern: bool(re.match(pattern, s)),
        })

    def evaluate(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate expression using AST.

        Args:
            expression: Python expression to evaluate
            context: Variables available in expression

        Returns:
            Boolean result of evaluation

        Raises:
            MCPSecurityError: If expression contains unsafe operations
        """
        try:
            # Parse expression to AST
            tree = ast.parse(expression, mode='eval')

            # Validate AST nodes (pass context for name validation)
            self._validate_ast(tree, context)

            # Compile and evaluate
            code = compile(tree, '<policy>', 'eval')

            # Create safe evaluation context
            safe_context = {
                "__builtins__": {},
                **self.custom_functions,
                **context,
            }

            result = eval(code, safe_context)
            return bool(result)

        except SyntaxError as e:
            logger.error(f"Syntax error in expression: {e}")
            return False
        except Exception as e:
            logger.error(f"Error evaluating expression: {e}")
            return False

    def _validate_ast(self, node: ast.AST, context: Dict[str, Any] = None) -> None:
        """
        Validate AST node for safety.

        Args:
            node: AST node to validate
            context: Variables available in expression (optional)

        Raises:
            MCPSecurityError: If unsafe operations detected
        """
        if context is None:
            context = {}

        if type(node) not in self.ALLOWED_NODE_TYPES:
            raise MCPSecurityError(
                f"Unsafe operation: {type(node).__name__} not allowed"
            )

        # Recursively validate child nodes
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                # Allow names that are:
                # 1. In ALLOWED_NAMES (built-ins)
                # 2. In custom_functions (safe functions)
                # 3. In the provided context (variables)
                # 4. Start with safe prefixes (context, tool, arguments)
                if (child.id not in self.ALLOWED_NAMES and
                    child.id not in self.custom_functions and
                    child.id not in context):
                    # Allow context variables with common prefixes
                    if not child.id.startswith(('context', 'tool', 'arguments')):
                        raise MCPSecurityError(
                            f"Unsafe name access: {child.id}"
                        )

            elif isinstance(child, ast.Attribute):
                # Validate attribute access (prevent __xxx__ access)
                if hasattr(child, 'attr') and child.attr.startswith('__'):
                    raise MCPSecurityError(
                        f"Unsafe attribute access: {child.attr}"
                    )


class PolicyEngine:
    """
    Enhanced policy engine with secure evaluation and caching.
    """

    def __init__(self, cache_size: int = 1000):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.evaluator = SafeEvaluator()
        self.decision_cache: Dict[str, PolicyDecision] = {}
        self.cache_size = cache_size
        self._load_default_policies()

    def _load_default_policies(self) -> None:
        """Load enhanced default security policies."""

        # Data protection policy
        self.add_policy(SecurityPolicy(
            name="data_protection",
            description="Protect sensitive data from unauthorized access",
            rules=[
                PolicyRule(
                    name="block_sensitive_exfiltration",
                    description="Prevent sensitive data from leaving the system",
                    condition="tool_category in ['network', 'api', 'communication'] and context.has_data_label('sensitive')",
                    action=PolicyAction.DENY,
                    reason="Cannot send sensitive data over network",
                    priority=100,
                    risk_impact=0.9,
                ),
                PolicyRule(
                    name="audit_pii_access",
                    description="Audit all PII data access",
                    condition="context.has_data_label('pii')",
                    action=PolicyAction.AUDIT,
                    reason="PII access requires audit trail",
                    priority=95,
                    risk_impact=0.7,
                ),
            ]
        ))

        # Rate limiting policy
        self.add_policy(SecurityPolicy(
            name="rate_limiting",
            description="Enforce rate limits to prevent abuse",
            rules=[
                PolicyRule(
                    name="enforce_api_limits",
                    description="Enforce API rate limits",
                    condition="not context.check_rate_limit(tool_category)",
                    action=PolicyAction.RATE_LIMIT,
                    reason="Rate limit exceeded",
                    priority=80,
                    risk_impact=0.3,
                ),
            ]
        ))

        # Environment-specific policy
        self.add_policy(SecurityPolicy(
            name="environment_controls",
            description="Environment-specific security controls",
            rules=[
                PolicyRule(
                    name="production_approval",
                    description="Require approval for production changes",
                    condition="context.environment == 'production' and tool_risk_level == 'high'",
                    action=PolicyAction.REQUIRE_APPROVAL,
                    reason="High-risk production operations require approval",
                    priority=90,
                    risk_impact=0.8,
                ),
            ]
        ))

        logger.info(f"Loaded {len(self.policies)} default policies")

    def add_policy(self, policy: SecurityPolicy) -> None:
        """Add a security policy."""
        self.policies[policy.name] = policy
        self._invalidate_cache()
        logger.debug(f"Added policy: {policy.name} with {len(policy.rules)} rules")

    def remove_policy(self, policy_name: str) -> None:
        """Remove a policy by name."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            self._invalidate_cache()
            logger.debug(f"Removed policy: {policy_name}")

    async def evaluate(
        self,
        context: SecurityContext,
        tool_name: str,
        tool_category: str,
        tool_permissions: List[str],
        tool_risk_level: str,
        arguments: Dict[str, Any],
        use_cache: bool = True,
    ) -> PolicyDecision:
        """
        Evaluate all applicable policies with caching.

        Args:
            context: Security context
            tool_name: Name of the tool
            tool_category: Tool category
            tool_permissions: Required permissions
            tool_risk_level: Risk level
            arguments: Tool arguments
            use_cache: Whether to use cached decisions

        Returns:
            Policy decision
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            context, tool_name, tool_category, arguments
        )

        # Check cache
        if use_cache and cache_key in self.decision_cache:
            logger.debug(f"Cache hit for policy evaluation: {cache_key}")
            return self.decision_cache[cache_key]

        # Collect all enabled rules
        all_rules = []
        for policy in self.policies.values():
            if policy.enabled:
                all_rules.extend([r for r in policy.rules if r.enabled])

        # Sort by priority (highest first)
        all_rules.sort(key=lambda r: r.priority, reverse=True)

        # Evaluation context
        eval_context = {
            "context": context,
            "tool_name": tool_name,
            "tool_category": tool_category,
            "tool_permissions": tool_permissions,
            "tool_risk_level": tool_risk_level,
            "arguments": arguments,
        }

        # Evaluate rules
        matched_rules = []
        final_action = PolicyAction.ALLOW
        final_reason = "No security concerns"
        risk_score = 0.0
        audit_required = False
        mitigations = []

        for rule in all_rules:
            try:
                if self.evaluator.evaluate(rule.condition, eval_context):
                    matched_rules.append(rule.name)
                    risk_score = max(risk_score, rule.risk_impact)

                    logger.debug(f"Rule matched: {rule.name} -> {rule.action.value}")

                    # Apply rule action
                    if rule.action == PolicyAction.DENY:
                        final_action = PolicyAction.DENY
                        final_reason = rule.reason
                        mitigations.extend(rule.mitigations)
                        break  # Deny takes precedence

                    elif rule.action == PolicyAction.REQUIRE_APPROVAL:
                        if final_action != PolicyAction.DENY:
                            final_action = PolicyAction.REQUIRE_APPROVAL
                            final_reason = rule.reason
                            mitigations.extend(rule.mitigations)

                    elif rule.action == PolicyAction.AUDIT:
                        audit_required = True

                    elif rule.action == PolicyAction.RATE_LIMIT:
                        if final_action == PolicyAction.ALLOW:
                            final_action = PolicyAction.RATE_LIMIT
                            final_reason = rule.reason

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
                # Fail closed - deny on evaluation error
                if rule.priority >= 90:  # High priority rules
                    final_action = PolicyAction.DENY
                    final_reason = f"Security evaluation failed: {str(e)}"
                    break

        # Create decision
        decision = PolicyDecision(
            action=final_action,
            reason=final_reason,
            matched_rules=matched_rules,
            risk_score=risk_score,
            audit_required=audit_required or context.audit_required,
            mitigations=mitigations,
            metadata={
                "tool_name": tool_name,
                "tool_category": tool_category,
                "environment": context.environment,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Cache decision
        if use_cache:
            self._cache_decision(cache_key, decision)

        # Log high-risk decisions
        if decision.action == PolicyAction.DENY or risk_score > 0.7:
            logger.warning(f"High-risk policy decision: {decision.to_dict()}")

        return decision

    def _generate_cache_key(
        self,
        context: SecurityContext,
        tool_name: str,
        tool_category: str,
        arguments: Dict[str, Any],
    ) -> str:
        """Generate cache key for policy decision."""
        key_data = {
            "agent_role": context.agent_role,
            "permissions": sorted(list(context.permissions)),
            "data_labels": sorted(list(context.data_labels)),
            "environment": context.environment,
            "tool_name": tool_name,
            "tool_category": tool_category,
            "arguments": json.dumps(arguments, sort_keys=True),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _cache_decision(self, key: str, decision: PolicyDecision) -> None:
        """Cache policy decision with LRU eviction."""
        if len(self.decision_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self.decision_cache))
            del self.decision_cache[oldest_key]

        self.decision_cache[key] = decision

    def _invalidate_cache(self) -> None:
        """Invalidate decision cache."""
        self.decision_cache.clear()
        logger.debug("Policy decision cache invalidated")

    def get_policy(self, name: str) -> Optional[SecurityPolicy]:
        """Get policy by name."""
        return self.policies.get(name)

    def list_policies(self) -> List[str]:
        """List all policy names."""
        return list(self.policies.keys())

    def enable_policy(self, name: str) -> None:
        """Enable a policy."""
        if name in self.policies:
            self.policies[name].enabled = True
            self._invalidate_cache()

    def disable_policy(self, name: str) -> None:
        """Disable a policy."""
        if name in self.policies:
            self.policies[name].enabled = False
            self._invalidate_cache()