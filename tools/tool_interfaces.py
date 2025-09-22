"""Core tool interfaces and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid


@dataclass
class ToolCall:
    """Represents a call to a tool."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCall':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            arguments=data.get("arguments", {}),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        )


@dataclass
class ToolResult:
    """Represents the result of a tool call."""

    call_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolResult':
        """Create from dictionary."""
        return cls(
            call_id=data["call_id"],
            success=data["success"],
            result=data.get("result"),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        )


@dataclass
class ToolParameter:
    """Defines a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "enum": self.enum
        }


@dataclass
class ToolDefinition:
    """Defines a tool's interface and metadata."""

    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    return_type: str = "any"
    category: str = "general"
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "category": self.category,
            "version": self.version,
            "metadata": self.metadata
        }

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function call format."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                properties[param.name]["enum"] = param.enum

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolDefinition':
        """Create from dictionary."""
        parameters = [
            ToolParameter(
                name=p["name"],
                type=p["type"],
                description=p["description"],
                required=p.get("required", True),
                default=p.get("default"),
                enum=p.get("enum")
            )
            for p in data.get("parameters", [])
        ]

        return cls(
            name=data["name"],
            description=data["description"],
            parameters=parameters,
            return_type=data.get("return_type", "any"),
            category=data.get("category", "general"),
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {})
        )


class ToolInterface(ABC):
    """Abstract interface for tools."""

    @abstractmethod
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return result."""
        pass

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get the tool's definition."""
        pass

    @abstractmethod
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments."""
        pass

    def get_name(self) -> str:
        """Get the tool name."""
        return self.get_definition().name

    def get_description(self) -> str:
        """Get the tool description."""
        return self.get_definition().description


class BaseTool(ToolInterface):
    """Base implementation of ToolInterface."""

    def __init__(self, definition: ToolDefinition):
        self.definition = definition

    def get_definition(self) -> ToolDefinition:
        """Get the tool's definition."""
        return self.definition

    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments against definition."""
        try:
            # Check required parameters
            for param in self.definition.parameters:
                if param.required and param.name not in arguments:
                    return False

            # Check parameter types (basic validation)
            for param in self.definition.parameters:
                if param.name in arguments:
                    value = arguments[param.name]
                    if not self._validate_type(value, param.type):
                        return False

                    # Check enum constraints
                    if param.enum and value not in param.enum:
                        return False

            return True

        except Exception:
            return False

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Basic type validation."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }

        if expected_type == "any":
            return True

        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Unknown type, assume valid

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Default implementation that should be overridden."""
        return ToolResult(
            call_id=tool_call.id,
            success=False,
            error="Tool execution not implemented"
        )


class MockTool(BaseTool):
    """Mock tool for testing and demonstration."""

    def __init__(self, name: str, description: str = "Mock tool"):
        definition = ToolDefinition(
            name=name,
            description=description,
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input to the mock tool"
                )
            ]
        )
        super().__init__(definition)

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute mock tool."""
        import time
        start_time = time.time()

        try:
            input_text = tool_call.arguments.get("input", "")
            result = f"Mock result for '{input_text}' from {self.definition.name}"

            return ToolResult(
                call_id=tool_call.id,
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )