"""
Input Validator for MCP Security

Validates and sanitizes inputs to MCP tools to prevent injection attacks
and other security vulnerabilities.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_arguments: Optional[Dict[str, Any]] = None


class InputValidator:
    """
    Validates and sanitizes MCP tool inputs.

    Protections:
    - SQL injection
    - Command injection
    - Path traversal
    - XSS
    - Type validation
    - Schema validation
    - URL whitelist enforcement
    """

    def __init__(self):
        # Dangerous patterns to detect
        self.sql_injection_patterns = [
            r"(\bOR\b|\bAND\b).*=.*",
            r";\s*DROP\s+TABLE",
            r";\s*DELETE\s+FROM",
            r";\s*UPDATE\s+",
            r"UNION\s+SELECT",
            r"--",
            r"/\*.*\*/",
        ]

        self.command_injection_patterns = [
            r"[;&|`$]",
            r"\$\(",
            r">\s*/dev/",
            r"<\s*/dev/",
        ]

        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.",
            r"~\/",
        ]

        self.xss_patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onload=",
        ]

    def validate_arguments(
        self,
        tool_schema: Dict[str, Any],
        arguments: Dict[str, Any],
        sanitize: bool = True
    ) -> ValidationResult:
        """
        Validate arguments against JSON schema and security rules.

        Args:
            tool_schema: JSON schema for the tool
            arguments: Arguments to validate
            sanitize: Whether to sanitize inputs

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        sanitized = {} if sanitize else None

        # Get schema properties
        properties = tool_schema.get('properties', {})
        required = tool_schema.get('required', [])

        # Check required fields
        for field in required:
            if field not in arguments:
                errors.append(f"Missing required field: {field}")

        # Validate each argument
        for key, value in arguments.items():
            if key not in properties:
                warnings.append(f"Unknown field: {key}")
                continue

            field_schema = properties[key]

            # Type validation
            expected_type = field_schema.get('type')
            if expected_type:
                type_valid, type_error = self._validate_type(
                    key,
                    value,
                    expected_type
                )
                if not type_valid:
                    errors.append(type_error)
                    continue

            # String validation and sanitization
            if isinstance(value, str):
                string_result = self._validate_string(
                    key,
                    value,
                    field_schema
                )
                if not string_result.is_valid:
                    errors.extend(string_result.errors)
                    warnings.extend(string_result.warnings)

                if sanitize and string_result.is_valid:
                    sanitized[key] = self.sanitize_string(value)
            elif sanitize:
                sanitized[key] = value

            # Format validation
            format_type = field_schema.get('format')
            if format_type:
                format_valid, format_error = self._validate_format(
                    key,
                    value,
                    format_type
                )
                if not format_valid:
                    errors.append(format_error)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_arguments=sanitized if sanitize else None
        )

    def _validate_type(
        self,
        field_name: str,
        value: Any,
        expected_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate value type.

        Args:
            field_name: Name of field
            value: Value to check
            expected_type: Expected JSON schema type

        Returns:
            (is_valid, error_message)
        """
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
        }

        expected_py_type = type_map.get(expected_type)
        if not expected_py_type:
            return True, None

        if not isinstance(value, expected_py_type):
            return False, f"Field '{field_name}' must be {expected_type}, got {type(value).__name__}"

        return True, None

    def _validate_string(
        self,
        field_name: str,
        value: str,
        field_schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate string field for security issues.

        Args:
            field_name: Name of field
            value: String value
            field_schema: Schema for this field

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Check length constraints
        min_length = field_schema.get('minLength')
        max_length = field_schema.get('maxLength')

        if min_length and len(value) < min_length:
            errors.append(f"Field '{field_name}' too short (min: {min_length})")

        if max_length and len(value) > max_length:
            errors.append(f"Field '{field_name}' too long (max: {max_length})")

        # Check pattern if specified
        pattern = field_schema.get('pattern')
        if pattern and not re.match(pattern, value):
            errors.append(f"Field '{field_name}' does not match required pattern")

        # Security checks
        if self._contains_sql_injection(value):
            errors.append(f"Field '{field_name}' contains SQL injection pattern")

        if self._contains_command_injection(value):
            errors.append(f"Field '{field_name}' contains command injection pattern")

        if self._contains_path_traversal(value):
            errors.append(f"Field '{field_name}' contains path traversal pattern")

        if self._contains_xss(value):
            warnings.append(f"Field '{field_name}' contains potential XSS pattern")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_format(
        self,
        field_name: str,
        value: Any,
        format_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate specific formats (email, url, etc.).

        Args:
            field_name: Name of field
            value: Value to validate
            format_type: Format type (email, uri, etc.)

        Returns:
            (is_valid, error_message)
        """
        if format_type == 'email':
            return self._validate_email(field_name, value)
        elif format_type in ['uri', 'url']:
            return self._validate_url_format(field_name, value)
        elif format_type == 'ipv4':
            return self._validate_ipv4(field_name, value)

        return True, None

    def _validate_email(
        self,
        field_name: str,
        value: str
    ) -> tuple[bool, Optional[str]]:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return False, f"Field '{field_name}' is not a valid email"
        return True, None

    def _validate_url_format(
        self,
        field_name: str,
        value: str
    ) -> tuple[bool, Optional[str]]:
        """Validate URL format."""
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                return False, f"Field '{field_name}' is not a valid URL"
            return True, None
        except Exception:
            return False, f"Field '{field_name}' is not a valid URL"

    def _validate_ipv4(
        self,
        field_name: str,
        value: str
    ) -> tuple[bool, Optional[str]]:
        """Validate IPv4 address."""
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ipv4_pattern, value):
            return False, f"Field '{field_name}' is not a valid IPv4 address"

        # Check each octet is 0-255
        octets = value.split('.')
        for octet in octets:
            if int(octet) > 255:
                return False, f"Field '{field_name}' is not a valid IPv4 address"

        return True, None

    def sanitize_string(self, value: str) -> str:
        """
        Remove or escape dangerous characters.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        # Remove null bytes
        value = value.replace('\x00', '')

        # Escape SQL special characters
        value = value.replace("'", "''")
        value = value.replace(';', '')

        # Remove command injection characters
        value = re.sub(r'[;&|`$]', '', value)

        # Normalize path separators
        value = value.replace('\\', '/')

        return value

    def validate_url(
        self,
        url: str,
        whitelist: List[str]
    ) -> bool:
        """
        Ensure URL is in allowed domain whitelist.

        Args:
            url: URL to validate
            whitelist: List of allowed domains

        Returns:
            True if URL is allowed
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check against whitelist
            for allowed in whitelist:
                allowed = allowed.lower()
                # Exact match or subdomain
                if domain == allowed or domain.endswith(f'.{allowed}'):
                    return True

            logger.warning(f"URL domain {domain} not in whitelist")
            return False

        except Exception as e:
            logger.error(f"Error validating URL: {e}")
            return False

    def _contains_sql_injection(self, value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        value_upper = value.upper()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Detected SQL injection pattern: {pattern}")
                return True
        return False

    def _contains_command_injection(self, value: str) -> bool:
        """Check if string contains command injection patterns."""
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value):
                logger.warning(f"Detected command injection pattern: {pattern}")
                return True
        return False

    def _contains_path_traversal(self, value: str) -> bool:
        """Check if string contains path traversal patterns."""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value):
                logger.warning(f"Detected path traversal pattern: {pattern}")
                return True
        return False

    def _contains_xss(self, value: str) -> bool:
        """Check if string contains XSS patterns."""
        value_lower = value.lower()
        for pattern in self.xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Detected XSS pattern: {pattern}")
                return True
        return False

    def validate_json_schema(
        self,
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate that a schema is valid JSON Schema.

        Args:
            schema: Schema to validate

        Returns:
            True if valid
        """
        try:
            # Basic checks
            if not isinstance(schema, dict):
                return False

            # Should have type or properties
            if 'type' not in schema and 'properties' not in schema:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating JSON schema: {e}")
            return False
