"""
Policy Engine for MCP Security

Evaluates security policies to allow/deny/require approval for MCP tool execution.
"""

import re
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Set, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions that can be taken by policy engine."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    action: PolicyAction
    reason: str
    matched_rules: List[str]


@dataclass
class PolicyRule:
    """Individual security rule."""
    name: str
    condition: str  # Python expression to evaluate
    action: str  # "allow", "deny", "require_approval"
    reason: str  # Human-readable explanation
    priority: int = 0  # Higher priority rules evaluated first


@dataclass
class SecurityPolicy:
    """Collection of security rules."""
    name: str
    description: str
    rules: List[PolicyRule]
    enabled: bool = True


@dataclass
class SecurityContext:
    """Context for security decisions."""
    agent_id: str
    agent_role: str
    session_id: str
    user_id: Optional[str]
    permissions: Set[str]
    data_labels: Set[str]  # e.g., {"sensitive", "pii", "public"}
    environment: str  # "production", "staging", "development"
    rate_limits: Dict[str, int]
    call_count: int = 0
    timestamp: Optional[str] = None

    def has_permission(self, permission: str) -> bool:
        """Check if context has required permission."""
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True
        # Check wildcard permissions (e.g., "read:*")
        if ":" in permission:
            category = permission.split(":")[0]
            if f"{category}:*" in self.permissions:
                return True
        return False

    def has_data_label(self, label: str) -> bool:
        """Check if context has a specific data label."""
        return label.lower() in {l.lower() for l in self.data_labels}


class PolicyEngine:
    """
    Evaluates security policies before MCP tool execution.

    Supports:
    - Condition-based rules (Python expressions)
    - Priority-based evaluation
    - Multiple actions (allow, deny, require_approval)
    - Flexible context matching
    """

    def __init__(self):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.load_default_policies()

    def load_default_policies(self) -> None:
        """Load default security policies."""

        # Policy 1: Prevent data exfiltration
        self.add_policy(SecurityPolicy(
            name="prevent_data_exfiltration",
            description="Prevent sending sensitive data over network",
            rules=[
                PolicyRule(
                    name="block_sensitive_network",
                    condition="tool_category == 'network' and context.has_data_label('sensitive')",
                    action="deny",
                    reason="Cannot send sensitive data over network",
                    priority=100
                ),
                PolicyRule(
                    name="block_pii_external",
                    condition="tool_category in ['email', 'api'] and context.has_data_label('pii')",
                    action="deny",
                    reason="Cannot send PII to external services",
                    priority=100
                )
            ]
        ))

        # Policy 2: Require approval for high-risk operations
        self.add_policy(SecurityPolicy(
            name="require_approval_for_high_risk",
            description="Require human approval for high-risk operations",
            rules=[
                PolicyRule(
                    name="approve_high_risk_writes",
                    condition="tool_risk_level == 'high' and 'write' in tool_permissions",
                    action="require_approval",
                    reason="High-risk write operations require human approval",
                    priority=90
                ),
                PolicyRule(
                    name="approve_production_modifications",
                    condition="context.environment == 'production' and tool_category in ['database', 'files']",
                    action="require_approval",
                    reason="Production data modifications require approval",
                    priority=90
                )
            ]
        ))

        # Policy 3: Rate limiting
        self.add_policy(SecurityPolicy(
            name="rate_limiting",
            description="Prevent excessive API calls",
            rules=[
                PolicyRule(
                    name="limit_api_calls",
                    condition="tool_category == 'api' and context.call_count > 100",
                    action="deny",
                    reason="API rate limit exceeded (100 calls per session)",
                    priority=80
                ),
                PolicyRule(
                    name="limit_high_risk_calls",
                    condition="tool_risk_level == 'high' and context.call_count > 10",
                    action="deny",
                    reason="High-risk operation rate limit exceeded",
                    priority=85
                )
            ]
        ))

        # Policy 4: Development environment restrictions
        self.add_policy(SecurityPolicy(
            name="development_restrictions",
            description="Restrict certain operations in development",
            rules=[
                PolicyRule(
                    name="no_email_in_dev",
                    condition="context.environment == 'development' and tool_category == 'email'",
                    action="deny",
                    reason="Email sending disabled in development environment",
                    priority=70
                )
            ]
        ))

        logger.info(f"Loaded {len(self.policies)} default policies")

    def add_policy(self, policy: SecurityPolicy) -> None:
        """
        Add a security policy.

        Args:
            policy: Security policy to add
        """
        self.policies[policy.name] = policy
        logger.debug(f"Added policy: {policy.name} with {len(policy.rules)} rules")

    def remove_policy(self, policy_name: str) -> None:
        """Remove a policy by name."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            logger.debug(f"Removed policy: {policy_name}")

    def load_policies_from_config(self, config: Dict[str, Any]) -> None:
        """
        Load policies from configuration dictionary.

        Args:
            config: Configuration with 'policies' key
        """
        for policy_config in config.get('policies', []):
            rules = [
                PolicyRule(
                    name=rule.get('name', f"rule_{i}"),
                    condition=rule['condition'],
                    action=rule['action'],
                    reason=rule['reason'],
                    priority=rule.get('priority', 50)
                )
                for i, rule in enumerate(policy_config.get('rules', []))
            ]

            policy = SecurityPolicy(
                name=policy_config['name'],
                description=policy_config.get('description', ''),
                rules=rules,
                enabled=policy_config.get('enabled', True)
            )

            self.add_policy(policy)

        logger.info(f"Loaded {len(config.get('policies', []))} policies from configuration")

    async def evaluate(
        self,
        context: SecurityContext,
        tool_name: str,
        tool_category: str,
        tool_permissions: List[str],
        tool_risk_level: str,
        arguments: Dict[str, Any]
    ) -> PolicyDecision:
        """
        Evaluate all applicable policies.

        Args:
            context: Security context for the request
            tool_name: Name of the tool being executed
            tool_category: Category of the tool (e.g., "data", "network")
            tool_permissions: Permissions required by tool
            tool_risk_level: Risk level of tool ("low", "medium", "high")
            arguments: Tool arguments

        Returns:
            PolicyDecision with action to take
        """
        # Collect all rules from enabled policies
        all_rules = []
        for policy in self.policies.values():
            if policy.enabled:
                all_rules.extend(policy.rules)

        # Sort by priority (highest first)
        all_rules.sort(key=lambda r: r.priority, reverse=True)

        matched_rules = []
        final_action = PolicyAction.ALLOW
        final_reason = "No policies matched"

        # Evaluate each rule
        for rule in all_rules:
            try:
                # Build evaluation context
                eval_context = {
                    'context': context,
                    'tool_name': tool_name,
                    'tool_category': tool_category,
                    'tool_permissions': tool_permissions,
                    'tool_risk_level': tool_risk_level,
                    'arguments': arguments,
                    'has_permission': context.has_permission,
                }

                # Evaluate condition
                if self._safe_eval(rule.condition, eval_context):
                    matched_rules.append(rule.name)
                    logger.debug(f"Rule matched: {rule.name}")

                    # Map action string to enum
                    action = PolicyAction(rule.action)

                    # Apply action (first matching DENY or REQUIRE_APPROVAL wins)
                    if action == PolicyAction.DENY:
                        final_action = PolicyAction.DENY
                        final_reason = rule.reason
                        logger.warning(
                            f"Tool {tool_name} DENIED by rule {rule.name}: {rule.reason}"
                        )
                        break  # Stop on first deny
                    elif action == PolicyAction.REQUIRE_APPROVAL:
                        if final_action != PolicyAction.DENY:
                            final_action = PolicyAction.REQUIRE_APPROVAL
                            final_reason = rule.reason
                            logger.info(
                                f"Tool {tool_name} REQUIRES APPROVAL by rule {rule.name}: {rule.reason}"
                            )
                    # Continue evaluating for higher-priority denies

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
                continue

        return PolicyDecision(
            action=final_action,
            reason=final_reason,
            matched_rules=matched_rules
        )

    def _safe_eval(
        self,
        condition: str,
        eval_context: Dict[str, Any]
    ) -> bool:
        """
        Safely evaluate a condition expression.

        Only allows simple comparisons and attribute access.
        Blocks dangerous operations like imports, exec, etc.

        Args:
            condition: Python expression to evaluate
            eval_context: Variables available in the expression

        Returns:
            Boolean result of evaluation
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            r'__import__',
            r'\bexec\b',
            r'\beval\b',
            r'\bopen\b',
            r'\bfile\b',
            r'__',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, condition):
                logger.warning(f"Blocked dangerous pattern in condition: {pattern}")
                return False

        try:
            # Use eval with restricted globals/locals
            result = eval(
                condition,
                {"__builtins__": {}},
                eval_context
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def enable_policy(self, policy_name: str) -> None:
        """Enable a policy."""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = True
            logger.info(f"Enabled policy: {policy_name}")

    def disable_policy(self, policy_name: str) -> None:
        """Disable a policy."""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = False
            logger.info(f"Disabled policy: {policy_name}")

    def list_policies(self) -> List[str]:
        """Get list of all policy names."""
        return list(self.policies.keys())

    def get_policy(self, policy_name: str) -> Optional[SecurityPolicy]:
        """Get a specific policy by name."""
        return self.policies.get(policy_name)
