"""
Tests for PolicyEngine.
"""

import pytest
from mcp.security.policy_engine import (
    PolicyEngine,
    PolicyRule,
    SecurityPolicy,
    PolicyAction,
    SafeEvaluator,
)
from mcp.security.context import SecurityContext
from mcp.core.exceptions import MCPSecurityError


class TestSafeEvaluator:
    """Test SafeEvaluator functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.evaluator = SafeEvaluator()

    def test_simple_comparisons(self):
        """Test simple comparison expressions."""
        context = {"x": 5, "y": 10}

        assert self.evaluator.evaluate("x < y", context)
        assert self.evaluator.evaluate("x == 5", context)
        assert not self.evaluator.evaluate("x > y", context)

    def test_boolean_operations(self):
        """Test boolean operations."""
        context = {"a": True, "b": False, "c": True}

        assert self.evaluator.evaluate("a and c", context)
        assert not self.evaluator.evaluate("a and b", context)
        assert self.evaluator.evaluate("a or b", context)
        assert self.evaluator.evaluate("not b", context)

    def test_string_operations(self):
        """Test string operations with custom functions."""
        context = {"category": "database", "name": "postgres"}

        assert self.evaluator.evaluate("category == 'database'", context)
        assert self.evaluator.evaluate("starts_with(name, 'post')", context)
        assert self.evaluator.evaluate("contains(category, 'data')", context)

    def test_list_membership(self):
        """Test list membership checks."""
        context = {"category": "network", "allowed": ["api", "network", "data"]}

        assert self.evaluator.evaluate("category in allowed", context)
        assert not self.evaluator.evaluate("category in ['api', 'data']", context)

    def test_security_context_methods(self):
        """Test calling security context methods."""
        ctx = SecurityContext(
            agent_id="test",
            agent_role="analyst",
            session_id="123",
            permissions={"read:data"},
            data_labels={"sensitive"}
        )

        context = {"context": ctx}

        assert self.evaluator.evaluate("has_permission(context, 'read:data')", context)
        assert self.evaluator.evaluate("has_data_label(context, 'sensitive')", context)

    def test_unsafe_expressions_blocked(self):
        """Test that unsafe expressions are blocked."""
        context = {"x": 5}

        # These should be blocked or fail safely
        assert not self.evaluator.evaluate("__import__('os')", context)
        assert not self.evaluator.evaluate("eval('1+1')", context)

        # Attribute access to __ should be blocked
        with pytest.raises(MCPSecurityError):
            self.evaluator.evaluate("context.__class__", context)

    def test_complex_expressions(self):
        """Test complex nested expressions."""
        ctx = SecurityContext(
            agent_id="test",
            agent_role="analyst",
            session_id="123",
            permissions={"read:data"},
            environment="production"
        )

        context = {
            "context": ctx,
            "tool_category": "database",
            "tool_risk_level": "high"
        }

        # Complex policy rule
        expr = (
            "context.environment == 'production' and "
            "tool_category == 'database' and "
            "tool_risk_level == 'high'"
        )

        assert self.evaluator.evaluate(expr, context)


class TestPolicyEngine:
    """Test PolicyEngine functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PolicyEngine()
        self.context = SecurityContext(
            agent_id="test-agent",
            agent_role="analyst",
            session_id="test-session",
            permissions={"read:data", "write:logs"},
            environment="development"
        )

    @pytest.mark.asyncio
    async def test_default_policies_loaded(self):
        """Test that default policies are loaded."""
        policies = self.engine.list_policies()
        assert len(policies) > 0
        assert "data_protection" in policies
        assert "rate_limiting" in policies

    @pytest.mark.asyncio
    async def test_allow_action(self):
        """Test policy evaluation resulting in ALLOW."""
        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="calculator",
            tool_category="computation",
            tool_permissions=[],
            tool_risk_level="low",
            arguments={"expression": "2 + 2"}
        )

        assert decision.action == PolicyAction.ALLOW

    @pytest.mark.asyncio
    async def test_deny_action(self):
        """Test policy evaluation resulting in DENY."""
        # Add sensitive data label
        self.context.add_data_label("sensitive")

        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="send_email",
            tool_category="network",
            tool_permissions=["send:email"],
            tool_risk_level="medium",
            arguments={"to": "user@example.com"}
        )

        # Should be denied due to data protection policy
        assert decision.action == PolicyAction.DENY
        assert "sensitive data" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_action(self):
        """Test rate limit policy."""
        # Exceed rate limit
        for i in range(150):
            self.context.increment_call_count("api")

        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="api_call",
            tool_category="api",
            tool_permissions=["read:api"],
            tool_risk_level="low",
            arguments={}
        )

        assert decision.action in [PolicyAction.RATE_LIMIT, PolicyAction.DENY]

    @pytest.mark.asyncio
    async def test_custom_policy(self):
        """Test adding and evaluating custom policy."""
        # Create custom policy
        custom_policy = SecurityPolicy(
            name="test_policy",
            description="Test policy",
            rules=[
                PolicyRule(
                    name="block_delete",
                    description="Block delete operations",
                    condition="'delete' in tool_name.lower()",
                    action=PolicyAction.DENY,
                    reason="Delete operations not allowed",
                    priority=95
                )
            ]
        )

        self.engine.add_policy(custom_policy)

        # Test evaluation
        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="delete_file",
            tool_category="files",
            tool_permissions=["write:files"],
            tool_risk_level="high",
            arguments={"path": "/tmp/test.txt"}
        )

        assert decision.action == PolicyAction.DENY
        assert "block_delete" in decision.matched_rules

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that rules are evaluated by priority."""
        policy = SecurityPolicy(
            name="priority_test",
            description="Test priority",
            rules=[
                PolicyRule(
                    name="low_priority_allow",
                    description="Low priority allow",
                    condition="True",
                    action=PolicyAction.ALLOW,
                    reason="Always allow",
                    priority=10
                ),
                PolicyRule(
                    name="high_priority_deny",
                    description="High priority deny",
                    condition="tool_category == 'test'",
                    action=PolicyAction.DENY,
                    reason="Test blocked",
                    priority=100
                )
            ]
        )

        self.engine.add_policy(policy)

        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="test_tool",
            tool_category="test",
            tool_permissions=[],
            tool_risk_level="low",
            arguments={}
        )

        # Higher priority DENY should win
        assert decision.action == PolicyAction.DENY
        assert "high_priority_deny" in decision.matched_rules

    @pytest.mark.asyncio
    async def test_policy_caching(self):
        """Test policy decision caching."""
        # First evaluation
        decision1 = await self.engine.evaluate(
            context=self.context,
            tool_name="calculator",
            tool_category="computation",
            tool_permissions=[],
            tool_risk_level="low",
            arguments={"expression": "2 + 2"},
            use_cache=True
        )

        # Second evaluation with same parameters (should hit cache)
        decision2 = await self.engine.evaluate(
            context=self.context,
            tool_name="calculator",
            tool_category="computation",
            tool_permissions=[],
            tool_risk_level="low",
            arguments={"expression": "2 + 2"},
            use_cache=True
        )

        assert decision1.action == decision2.action

    @pytest.mark.asyncio
    async def test_environment_specific_rules(self):
        """Test environment-specific policy rules."""
        prod_context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            environment="production"
        )

        decision = await self.engine.evaluate(
            context=prod_context,
            tool_name="database_write",
            tool_category="database",
            tool_permissions=["write:database"],
            tool_risk_level="high",
            arguments={}
        )

        # Production high-risk operations should require approval
        assert decision.action in [PolicyAction.REQUIRE_APPROVAL, PolicyAction.DENY]

    @pytest.mark.asyncio
    async def test_risk_score_calculation(self):
        """Test risk score calculation."""
        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="execute_code",
            tool_category="development",
            tool_permissions=["execute:code"],
            tool_risk_level="high",
            arguments={"code": "print('test')"}
        )

        # High risk tools should have elevated risk score
        assert decision.risk_score > 0.5

    def test_policy_enable_disable(self):
        """Test enabling/disabling policies."""
        # Disable a policy
        self.engine.disable_policy("rate_limiting")
        policy = self.engine.get_policy("rate_limiting")
        assert not policy.enabled

        # Re-enable
        self.engine.enable_policy("rate_limiting")
        policy = self.engine.get_policy("rate_limiting")
        assert policy.enabled

    @pytest.mark.asyncio
    async def test_audit_required_flag(self):
        """Test that high-risk operations set audit_required flag."""
        self.context.add_data_label("pii")

        decision = await self.engine.evaluate(
            context=self.context,
            tool_name="database_query",
            tool_category="data",
            tool_permissions=["read:database"],
            tool_risk_level="medium",
            arguments={}
        )

        # PII access should require audit
        assert decision.audit_required or decision.action == PolicyAction.AUDIT