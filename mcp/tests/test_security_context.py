"""
Tests for SecurityContext.
"""

import pytest
from datetime import datetime, timedelta
from mcp.security.context import SecurityContext, SecurityLevel


class TestSecurityContext:
    """Test SecurityContext functionality."""

    def test_context_creation(self):
        """Test creating a security context."""
        context = SecurityContext(
            agent_id="test-agent",
            agent_role="analyst",
            session_id="session-123",
            permissions={"read:data", "write:logs"},
            environment="development"
        )

        assert context.agent_id == "test-agent"
        assert context.agent_role == "analyst"
        assert context.session_id == "session-123"
        assert "read:data" in context.permissions
        assert context.environment == "development"
        assert context.request_id is not None

    def test_permission_checking(self):
        """Test permission checking with wildcards."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            permissions={"read:*", "write:logs"}
        )

        # Test exact match
        assert context.has_permission("write:logs")

        # Test wildcard match
        assert context.has_permission("read:database")
        assert context.has_permission("read:files")

        # Test missing permission
        assert not context.has_permission("write:database")

        # Test denied permissions
        context.denied_permissions.add("read:sensitive")
        assert not context.has_permission("read:sensitive")

    def test_temporary_permissions(self):
        """Test temporary permission granting."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123"
        )

        # Grant temporary permission
        context.grant_temporary_permission("execute:code", duration_seconds=1)
        assert context.has_permission("execute:code")

        # Check expiry (would need to mock time for proper test)
        # In real test, we'd use freezegun or similar
        import time
        time.sleep(1.1)
        assert not context.has_permission("execute:code")

    def test_data_labels(self):
        """Test data label management."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123"
        )

        # Add labels
        context.add_data_label("sensitive")
        context.add_data_label("PII")

        assert context.has_data_label("sensitive")
        assert context.has_data_label("pii")  # Case insensitive
        assert not context.has_data_label("public")

        # Check risk score increases with sensitive data
        assert context.risk_score > 0

    def test_rate_limiting(self):
        """Test rate limit tracking."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123"
        )

        # Check rate limit before any calls
        assert context.check_rate_limit("api")

        # Increment calls
        for i in range(5):
            count = context.increment_call_count("api")
            assert count == i + 1

        # Check rate limit (depends on environment defaults)
        assert context.call_counts["api"] == 5

    def test_security_level_elevation(self):
        """Test security level elevation."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123"
        )

        assert context.security_level == SecurityLevel.MEDIUM

        # Elevate security
        context.elevate_security_level()
        assert context.security_level == SecurityLevel.HIGH
        assert context.audit_required

        # Elevate again
        context.elevate_security_level()
        assert context.security_level == SecurityLevel.CRITICAL

    def test_threat_indicators(self):
        """Test threat indicator tracking."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123"
        )

        initial_risk = context.risk_score

        # Add threat indicators
        context.add_threat_indicator("sql_injection_attempt")
        assert context.risk_score > initial_risk

        context.add_threat_indicator("path_traversal_detected")
        context.add_threat_indicator("repeated_auth_failures")

        # Should auto-elevate after 3 threats
        assert context.security_level != SecurityLevel.MEDIUM

    def test_context_serialization(self):
        """Test context serialization."""
        context = SecurityContext(
            agent_id="test",
            agent_role="analyst",
            session_id="123",
            permissions={"read:data"},
            data_labels={"sensitive"}
        )

        # Serialize to dict
        data = context.to_dict()
        assert data["agent_id"] == "test"
        assert "read:data" in data["permissions"]
        assert "sensitive" in data["data_labels"]

        # Deserialize from dict
        context2 = SecurityContext.from_dict(data)
        assert context2.agent_id == context.agent_id
        assert context2.has_permission("read:data")
        assert context2.has_data_label("sensitive")

    def test_permission_revocation(self):
        """Test permission revocation."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            permissions={"read:data", "write:logs"}
        )

        assert context.has_permission("read:data")

        # Revoke permission
        context.revoke_permission("read:data")
        assert not context.has_permission("read:data")
        assert "read:data" in context.denied_permissions

        # Permission stays denied even if tried to add again
        context.permissions.add("read:data")
        assert not context.has_permission("read:data")

    def test_environment_specific_limits(self):
        """Test environment-specific rate limits."""
        # Production context
        prod_context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            environment="production"
        )
        assert prod_context.rate_limits["api"] == 1000

        # Development context
        dev_context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            environment="development"
        )
        assert dev_context.rate_limits["api"] == 100

    def test_multiple_permission_checks(self):
        """Test multiple permission checking methods."""
        context = SecurityContext(
            agent_id="test",
            agent_role="user",
            session_id="123",
            permissions={"read:data", "write:logs", "execute:scripts"}
        )

        # Test has_any_permission
        assert context.has_any_permission(["read:data", "admin:all"])
        assert context.has_any_permission(["write:logs", "delete:data"])
        assert not context.has_any_permission(["admin:all", "delete:data"])

        # Test has_all_permissions
        assert context.has_all_permissions(["read:data", "write:logs"])
        assert not context.has_all_permissions(["read:data", "admin:all"])