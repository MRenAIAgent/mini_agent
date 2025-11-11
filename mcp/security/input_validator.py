"""
Enhanced input validator with comprehensive security checks.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from urllib.parse import urlparse, quote
from ipaddress import ip_address, ip_network
import hashlib
from pathlib import Path

from ..core.exceptions import MCPValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation with detailed information."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_arguments: Optional[Dict[str, Any]] = None
    risk_indicators: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "risk_indicators": self.risk_indicators,
            "confidence_score": self.confidence_score,
            "has_sanitized": self.sanitized_arguments is not None,
            "metadata": self.metadata,
        }


class PatternDetector:
    """Detects malicious patterns in input."""

    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        # Classic SQL injection
        r"(\bOR\b|\bAND\b)\s+['\"]?\w*['\"]?\s*=\s*['\"]?\w*['\"]?",
        r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)\s+",
        r"UNION\s+(ALL\s+)?SELECT",
        r"--\s*$",  # SQL comment at end
        r"/\*[\s\S]*?\*/",  # Multi-line comment
        r"'\s*(OR|AND)\s+'[^']*'='",
        r'"\s*(OR|AND)\s+"[^"]*"="',
        # Advanced patterns
        r"EXEC(\s|\()",
        r"EXECUTE(\s|\()",
        r"sp_executesql",
        r"xp_cmdshell",
        r"WAITFOR\s+DELAY",
        r"BENCHMARK\s*\(",
        r"SLEEP\s*\(",
    ]

    # Command Injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|](?!&)",  # Command separators (not HTML entities)
        r"\$\([^)]+\)",  # Command substitution
        r"`[^`]+`",  # Backtick execution
        r">\s*/dev/",  # Redirect to /dev
        r"<\s*/dev/",
        r"\|\s*nc\s+",  # Netcat pipe
        r"\|\s*bash",  # Pipe to bash
        r"&&\s*[a-z]+",  # Command chaining
        r"\|\|\s*[a-z]+",
        # Process control
        r"(?:^|\s)kill\s+",
        r"(?:^|\s)pkill\s+",
        r"(?:^|\s)killall\s+",
    ]

    # Path Traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.[\\/]",  # ../
        r"\.\.%2[Ff]",  # URL encoded ../
        r"%2[Ee]%2[Ee][\\/]",  # URL encoded ../
        r"\.\.\\",  # Windows path traversal
        r"(?:^|[\\/])etc[\\/]passwd",  # /etc/passwd access
        r"(?:^|[\\/])windows[\\/]system32",  # Windows system access
        r"~[\\/]",  # Home directory access
        r"\$HOME",  # Environment variable
        r"%USERPROFILE%",  # Windows env var
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>[\s\S]*?</script>",
        r"javascript\s*:",
        r"on\w+\s*=",  # Event handlers
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
        r"vbscript\s*:",
        r"data:text/html",
    ]

    # LDAP Injection patterns
    LDAP_INJECTION_PATTERNS = [
        r"\*\s*\|\s*",
        r"\(\s*\|\s*",
        r"\)\s*\(\s*",
        r"[^\w]cn=",
        r"[^\w]ou=",
        r"[^\w]dc=",
    ]

    # XXE patterns
    XXE_PATTERNS = [
        r"<!DOCTYPE[^>]*>",
        r"<!ENTITY[^>]*>",
        r"SYSTEM\s+['\"]file:",
        r"SYSTEM\s+['\"]http:",
        r"&[a-zA-Z]+;",  # Entity references
    ]

    @classmethod
    def detect_sql_injection(cls, value: str) -> List[str]:
        """Detect SQL injection patterns."""
        detected = []
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
                detected.append(f"SQL injection pattern: {pattern[:30]}...")
        return detected

    @classmethod
    def detect_command_injection(cls, value: str) -> List[str]:
        """Detect command injection patterns."""
        detected = []
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                detected.append(f"Command injection pattern: {pattern[:30]}...")
        return detected

    @classmethod
    def detect_path_traversal(cls, value: str) -> List[str]:
        """Detect path traversal patterns."""
        detected = []
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                detected.append(f"Path traversal pattern: {pattern[:30]}...")
        return detected

    @classmethod
    def detect_xss(cls, value: str) -> List[str]:
        """Detect XSS patterns."""
        detected = []
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                detected.append(f"XSS pattern: {pattern[:30]}...")
        return detected

    @classmethod
    def detect_all(cls, value: str) -> List[str]:
        """Detect all malicious patterns."""
        all_detected = []
        all_detected.extend(cls.detect_sql_injection(value))
        all_detected.extend(cls.detect_command_injection(value))
        all_detected.extend(cls.detect_path_traversal(value))
        all_detected.extend(cls.detect_xss(value))
        return all_detected


class InputValidator:
    """
    Comprehensive input validator with multiple security layers.
    """

    def __init__(
        self,
        max_string_length: int = 10000,
        max_array_size: int = 1000,
        max_object_depth: int = 10,
    ):
        self.max_string_length = max_string_length
        self.max_array_size = max_array_size
        self.max_object_depth = max_object_depth
        self.pattern_detector = PatternDetector()

        # Whitelisted domains for URL validation
        self.whitelisted_domains: Set[str] = set()

        # Blacklisted file extensions
        self.blacklisted_extensions = {
            '.exe', '.dll', '.bat', '.cmd', '.sh',
            '.ps1', '.vbs', '.js', '.jar', '.app',
        }

    def validate_arguments(
        self,
        tool_schema: Dict[str, Any],
        arguments: Dict[str, Any],
        sanitize: bool = True,
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate arguments against schema with security checks.

        Args:
            tool_schema: JSON schema for validation
            arguments: Arguments to validate
            sanitize: Whether to sanitize inputs
            strict: Whether to use strict validation

        Returns:
            Validation result
        """
        errors = []
        warnings = []
        risk_indicators = []
        sanitized = {}

        # Get schema properties
        properties = tool_schema.get('properties', {})
        required = tool_schema.get('required', [])
        additional_properties = tool_schema.get('additionalProperties', not strict)

        # Check required fields
        for field in required:
            if field not in arguments:
                errors.append(f"Missing required field: {field}")

        # Check for unexpected fields
        if not additional_properties:
            for key in arguments:
                if key not in properties:
                    if strict:
                        errors.append(f"Unexpected field: {key}")
                    else:
                        warnings.append(f"Unknown field: {key}")

        # Validate each argument
        for key, value in arguments.items():
            if key not in properties and not additional_properties:
                continue

            field_schema = properties.get(key, {})

            # Type validation
            type_result = self._validate_type(key, value, field_schema)
            if not type_result.is_valid:
                errors.extend(type_result.errors)
                continue

            # Deep validation based on type
            if isinstance(value, str):
                str_result = self._validate_string(key, value, field_schema)
                errors.extend(str_result.errors)
                warnings.extend(str_result.warnings)
                risk_indicators.extend(str_result.risk_indicators)

                if sanitize and str_result.sanitized_arguments:
                    sanitized[key] = str_result.sanitized_arguments
                elif sanitize:
                    sanitized[key] = value

            elif isinstance(value, (list, tuple)):
                arr_result = self._validate_array(key, value, field_schema)
                errors.extend(arr_result.errors)
                warnings.extend(arr_result.warnings)
                sanitized[key] = arr_result.sanitized_arguments or value

            elif isinstance(value, dict):
                obj_result = self._validate_object(key, value, field_schema)
                errors.extend(obj_result.errors)
                warnings.extend(obj_result.warnings)
                sanitized[key] = obj_result.sanitized_arguments or value

            else:
                if sanitize:
                    sanitized[key] = value

        # Calculate confidence score
        confidence_score = 1.0
        if errors:
            confidence_score = 0.0
        elif warnings:
            confidence_score = max(0.5, 1.0 - (len(warnings) * 0.1))
        elif risk_indicators:
            confidence_score = max(0.3, 1.0 - (len(risk_indicators) * 0.2))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_arguments=sanitized if sanitize else None,
            risk_indicators=risk_indicators,
            confidence_score=confidence_score,
            metadata={
                "validated_fields": len(arguments),
                "required_fields": len(required),
            }
        )

    def _validate_type(
        self,
        field_name: str,
        value: Any,
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate value type against schema."""
        errors = []
        expected_type = schema.get('type')

        if not expected_type:
            return ValidationResult(is_valid=True)

        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': (list, tuple),
            'object': dict,
            'null': type(None),
        }

        # Handle union types
        if isinstance(expected_type, list):
            valid = any(
                isinstance(value, type_map.get(t, type(None)))
                for t in expected_type
            )
            if not valid:
                errors.append(
                    f"Field '{field_name}' type mismatch. "
                    f"Expected one of {expected_type}, got {type(value).__name__}"
                )
        else:
            expected_py_type = type_map.get(expected_type)
            if expected_py_type and not isinstance(value, expected_py_type):
                errors.append(
                    f"Field '{field_name}' type mismatch. "
                    f"Expected {expected_type}, got {type(value).__name__}"
                )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _validate_string(
        self,
        field_name: str,
        value: str,
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate string value with security checks."""
        errors = []
        warnings = []
        risk_indicators = []
        sanitized_value = value

        # Length validation
        if len(value) > self.max_string_length:
            errors.append(
                f"Field '{field_name}' exceeds maximum length "
                f"({len(value)} > {self.max_string_length})"
            )

        min_length = schema.get('minLength')
        max_length = schema.get('maxLength')

        if min_length and len(value) < min_length:
            errors.append(f"Field '{field_name}' too short (min: {min_length})")

        if max_length and len(value) > max_length:
            errors.append(f"Field '{field_name}' too long (max: {max_length})")

        # Pattern validation
        pattern = schema.get('pattern')
        if pattern:
            try:
                if not re.match(pattern, value):
                    errors.append(
                        f"Field '{field_name}' does not match required pattern"
                    )
            except re.error as e:
                warnings.append(f"Invalid regex pattern in schema: {e}")

        # Format validation
        format_type = schema.get('format')
        if format_type:
            format_result = self._validate_format(field_name, value, format_type)
            errors.extend(format_result.errors)
            warnings.extend(format_result.warnings)

        # Security pattern detection
        detected_patterns = self.pattern_detector.detect_all(value)
        if detected_patterns:
            risk_indicators.extend(detected_patterns)
            if schema.get('strict_validation', False):
                errors.extend([
                    f"Security risk in '{field_name}': {p}"
                    for p in detected_patterns
                ])
            else:
                warnings.extend([
                    f"Potential risk in '{field_name}': {p}"
                    for p in detected_patterns
                ])

        # Sanitization
        if schema.get('sanitize', True):
            sanitized_value = self._sanitize_string(value, schema)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            risk_indicators=risk_indicators,
            sanitized_arguments=sanitized_value if sanitized_value != value else None,
        )

    def _validate_array(
        self,
        field_name: str,
        value: List[Any],
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate array values."""
        errors = []
        warnings = []

        # Size validation
        if len(value) > self.max_array_size:
            errors.append(
                f"Array '{field_name}' exceeds maximum size "
                f"({len(value)} > {self.max_array_size})"
            )

        min_items = schema.get('minItems')
        max_items = schema.get('maxItems')

        if min_items and len(value) < min_items:
            errors.append(f"Array '{field_name}' too small (min: {min_items})")

        if max_items and len(value) > max_items:
            errors.append(f"Array '{field_name}' too large (max: {max_items})")

        # Item validation
        items_schema = schema.get('items', {})
        sanitized_items = []

        for i, item in enumerate(value):
            item_result = self._validate_value(
                f"{field_name}[{i}]",
                item,
                items_schema
            )
            errors.extend(item_result.errors)
            warnings.extend(item_result.warnings)
            sanitized_items.append(
                item_result.sanitized_arguments
                if item_result.sanitized_arguments is not None
                else item
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_arguments=sanitized_items,
        )

    def _validate_object(
        self,
        field_name: str,
        value: Dict[str, Any],
        schema: Dict[str, Any],
        depth: int = 0
    ) -> ValidationResult:
        """Validate object values with depth limit."""
        errors = []
        warnings = []

        # Depth validation
        if depth > self.max_object_depth:
            errors.append(
                f"Object '{field_name}' exceeds maximum depth "
                f"({depth} > {self.max_object_depth})"
            )
            return ValidationResult(is_valid=False, errors=errors)

        # Property validation
        properties = schema.get('properties', {})
        sanitized_obj = {}

        for key, val in value.items():
            prop_schema = properties.get(key, {})
            prop_result = self._validate_value(
                f"{field_name}.{key}",
                val,
                prop_schema,
                depth + 1
            )
            errors.extend(prop_result.errors)
            warnings.extend(prop_result.warnings)
            sanitized_obj[key] = (
                prop_result.sanitized_arguments
                if prop_result.sanitized_arguments is not None
                else val
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_arguments=sanitized_obj,
        )

    def _validate_value(
        self,
        field_name: str,
        value: Any,
        schema: Dict[str, Any],
        depth: int = 0
    ) -> ValidationResult:
        """Validate any value based on its type."""
        if isinstance(value, str):
            return self._validate_string(field_name, value, schema)
        elif isinstance(value, (list, tuple)):
            return self._validate_array(field_name, value, schema)
        elif isinstance(value, dict):
            return self._validate_object(field_name, value, schema, depth)
        else:
            return ValidationResult(is_valid=True, sanitized_arguments=value)

    def _validate_format(
        self,
        field_name: str,
        value: str,
        format_type: str
    ) -> ValidationResult:
        """Validate specific format types."""
        errors = []
        warnings = []

        validators = {
            'email': self._validate_email,
            'uri': self._validate_uri,
            'url': self._validate_url,
            'ipv4': self._validate_ipv4,
            'ipv6': self._validate_ipv6,
            'uuid': self._validate_uuid,
            'date': self._validate_date,
            'time': self._validate_time,
            'date-time': self._validate_datetime,
            'hostname': self._validate_hostname,
            'json': self._validate_json,
            'base64': self._validate_base64,
            'path': self._validate_path,
        }

        validator = validators.get(format_type)
        if validator:
            valid, error_msg = validator(value)
            if not valid:
                errors.append(f"Field '{field_name}': {error_msg}")
        else:
            warnings.append(f"Unknown format type: {format_type}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_email(self, value: str) -> tuple[bool, str]:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            return False, "Invalid email format"
        return True, ""

    def _validate_uri(self, value: str) -> tuple[bool, str]:
        """Validate URI format."""
        try:
            result = urlparse(value)
            if not result.scheme:
                return False, "Missing URI scheme"
            return True, ""
        except Exception:
            return False, "Invalid URI format"

    def _validate_url(self, value: str) -> tuple[bool, str]:
        """Validate URL format."""
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                return False, "Invalid URL format"
            if result.scheme not in ['http', 'https', 'ftp', 'ftps']:
                return False, f"Unsupported URL scheme: {result.scheme}"
            return True, ""
        except Exception:
            return False, "Invalid URL format"

    def _validate_ipv4(self, value: str) -> tuple[bool, str]:
        """Validate IPv4 address."""
        try:
            ip_address(value)
            return True, ""
        except ValueError:
            return False, "Invalid IPv4 address"

    def _validate_ipv6(self, value: str) -> tuple[bool, str]:
        """Validate IPv6 address."""
        try:
            addr = ip_address(value)
            if addr.version != 6:
                return False, "Not an IPv6 address"
            return True, ""
        except ValueError:
            return False, "Invalid IPv6 address"

    def _validate_uuid(self, value: str) -> tuple[bool, str]:
        """Validate UUID format."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        if not re.match(pattern, value, re.IGNORECASE):
            return False, "Invalid UUID format"
        return True, ""

    def _validate_date(self, value: str) -> tuple[bool, str]:
        """Validate date format (YYYY-MM-DD)."""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, value):
            return False, "Invalid date format (expected YYYY-MM-DD)"
        return True, ""

    def _validate_time(self, value: str) -> tuple[bool, str]:
        """Validate time format (HH:MM:SS)."""
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        if not re.match(pattern, value):
            return False, "Invalid time format (expected HH:MM:SS)"
        return True, ""

    def _validate_datetime(self, value: str) -> tuple[bool, str]:
        """Validate datetime format (ISO 8601)."""
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?$'
        if not re.match(pattern, value):
            return False, "Invalid datetime format (expected ISO 8601)"
        return True, ""

    def _validate_hostname(self, value: str) -> tuple[bool, str]:
        """Validate hostname format."""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(pattern, value):
            return False, "Invalid hostname format"
        return True, ""

    def _validate_json(self, value: str) -> tuple[bool, str]:
        """Validate JSON string."""
        try:
            json.loads(value)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"

    def _validate_base64(self, value: str) -> tuple[bool, str]:
        """Validate base64 encoding."""
        pattern = r'^[A-Za-z0-9+/]*={0,2}$'
        if not re.match(pattern, value):
            return False, "Invalid base64 format"
        if len(value) % 4 != 0:
            return False, "Invalid base64 padding"
        return True, ""

    def _validate_path(self, value: str) -> tuple[bool, str]:
        """Validate file path with security checks."""
        # Check for path traversal
        if '..' in value or '~' in value:
            return False, "Path traversal detected"

        # Check for absolute paths (configurable)
        if value.startswith('/') or (len(value) > 1 and value[1] == ':'):
            return False, "Absolute paths not allowed"

        # Check blacklisted extensions
        path = Path(value)
        if path.suffix.lower() in self.blacklisted_extensions:
            return False, f"Blacklisted file extension: {path.suffix}"

        return True, ""

    def _sanitize_string(self, value: str, schema: Dict[str, Any]) -> str:
        """Sanitize string value based on schema rules."""
        sanitized = value

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        # Apply format-specific sanitization
        format_type = schema.get('format')
        if format_type == 'sql':
            # Basic SQL escape
            sanitized = sanitized.replace("'", "''")
            sanitized = re.sub(r'--.*$', '', sanitized, flags=re.MULTILINE)

        elif format_type == 'html':
            # HTML entity encoding
            sanitized = (
                sanitized.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
            )

        elif format_type == 'shell':
            # Shell escape
            sanitized = quote(sanitized)

        elif format_type == 'path':
            # Path sanitization
            sanitized = re.sub(r'[^\w\-_\./]', '', sanitized)
            sanitized = sanitized.replace('..', '')

        return sanitized

    def validate_url_whitelist(
        self,
        url: str,
        whitelist: List[str]
    ) -> tuple[bool, str]:
        """
        Validate URL against domain whitelist.

        Args:
            url: URL to validate
            whitelist: List of allowed domains

        Returns:
            (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if not domain:
                return False, "Invalid URL: no domain"

            # Check against whitelist
            for allowed in whitelist:
                allowed = allowed.lower()
                # Exact match or subdomain
                if domain == allowed or domain.endswith(f'.{allowed}'):
                    return True, ""

            return False, f"Domain '{domain}' not in whitelist"

        except Exception as e:
            return False, f"URL validation error: {str(e)}"