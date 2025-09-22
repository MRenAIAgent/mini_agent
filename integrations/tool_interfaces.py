"""
External Tool Integration Interfaces

Standardized interfaces for integrating external tool providers
and services with the core agent tool system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ToolProviderType(Enum):
    """Types of external tool providers."""
    MCP_SERVER = "mcp_server"
    REST_API = "rest_api"
    GRPC_SERVICE = "grpc_service"
    WEBHOOK = "webhook"
    PLUGIN = "plugin"
    FUNCTION = "function"


@dataclass
class ToolConnection:
    """External tool provider connection configuration."""

    provider_type: ToolProviderType
    name: str
    endpoint: Optional[str] = None
    authentication: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    retry_attempts: int = 3
    rate_limit: Optional[Dict[str, Any]] = None
    ssl_verify: bool = True
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalToolDefinition:
    """Definition of an external tool."""

    name: str
    description: str
    provider: str
    endpoint: str
    method: str = "POST"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    authentication_required: bool = False
    rate_limit: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalToolCall:
    """External tool call specification."""

    tool_name: str
    provider: str
    arguments: Dict[str, Any]
    call_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None


@dataclass
class ExternalToolResult:
    """External tool execution result."""

    call_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    execution_time: float = 0.0
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ExternalToolProvider(ABC):
    """Abstract base class for external tool providers."""

    def __init__(self, connection: ToolConnection):
        self.connection = connection
        self.is_connected = False
        self.available_tools: Dict[str, ExternalToolDefinition] = {}
        self.call_count = 0
        self.success_count = 0
        self.total_execution_time = 0.0

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the external tool provider.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external tool provider."""
        pass

    @abstractmethod
    async def discover_tools(self) -> List[ExternalToolDefinition]:
        """
        Discover available tools from the provider.

        Returns:
            List of tool definitions
        """
        pass

    @abstractmethod
    async def execute_tool(self, tool_call: ExternalToolCall) -> ExternalToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call specification

        Returns:
            Tool execution result
        """
        pass

    @abstractmethod
    async def validate_tool_call(self, tool_call: ExternalToolCall) -> bool:
        """
        Validate a tool call without executing it.

        Args:
            tool_call: Tool call to validate

        Returns:
            True if valid
        """
        pass

    @abstractmethod
    async def get_tool_definition(self, tool_name: str) -> Optional[ExternalToolDefinition]:
        """
        Get definition for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool definition if found
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the provider.

        Returns:
            Health status dictionary
        """
        try:
            if not self.is_connected:
                await self.connect()

            # Test tool discovery
            import time
            start_time = time.time()
            tools = await self.discover_tools()
            discovery_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "connected": self.is_connected,
                "provider_type": self.connection.provider_type.value,
                "provider_name": self.connection.name,
                "tools_count": len(tools),
                "discovery_time_ms": discovery_time,
                "call_count": self.call_count,
                "success_rate": (
                    self.success_count / self.call_count * 100
                    if self.call_count > 0 else 0.0
                )
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "provider_type": self.connection.provider_type.value,
                "provider_name": self.connection.name
            }

    def get_provider_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        success_rate = (
            self.success_count / self.call_count * 100
            if self.call_count > 0 else 0.0
        )

        avg_execution_time = (
            self.total_execution_time / self.call_count
            if self.call_count > 0 else 0.0
        )

        return {
            "provider_name": self.connection.name,
            "provider_type": self.connection.provider_type.value,
            "is_connected": self.is_connected,
            "tools_count": len(self.available_tools),
            "call_count": self.call_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "average_execution_time_ms": avg_execution_time
        }

    def _update_stats(self, result: ExternalToolResult) -> None:
        """Update internal statistics."""
        self.call_count += 1
        if result.success:
            self.success_count += 1
        self.total_execution_time += result.execution_time


class RESTAPIProvider(ExternalToolProvider):
    """REST API tool provider implementation."""

    def __init__(self, connection: ToolConnection):
        super().__init__(connection)
        self.session = None

    async def connect(self) -> bool:
        """Connect to REST API provider."""
        try:
            import aiohttp

            # Create session with authentication and headers
            auth = None
            if self.connection.authentication:
                auth_type = self.connection.authentication.get("type")
                if auth_type == "basic":
                    auth = aiohttp.BasicAuth(
                        self.connection.authentication["username"],
                        self.connection.authentication["password"]
                    )

            connector = aiohttp.TCPConnector(
                ssl=self.connection.ssl_verify
            )

            self.session = aiohttp.ClientSession(
                headers=self.connection.headers,
                auth=auth,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.connection.timeout)
            )

            # Test connection
            if self.connection.endpoint:
                async with self.session.get(
                    f"{self.connection.endpoint}/health"
                ) as response:
                    if response.status < 400:
                        self.is_connected = True
                        return True

            return False

        except Exception:
            return False

    async def disconnect(self) -> None:
        """Disconnect from REST API provider."""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False

    async def discover_tools(self) -> List[ExternalToolDefinition]:
        """Discover tools from REST API."""
        if not self.session or not self.connection.endpoint:
            return []

        try:
            async with self.session.get(
                f"{self.connection.endpoint}/tools"
            ) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = []

                    for tool_data in tools_data:
                        tool = ExternalToolDefinition(
                            name=tool_data["name"],
                            description=tool_data.get("description", ""),
                            provider=self.connection.name,
                            endpoint=tool_data.get("endpoint", ""),
                            method=tool_data.get("method", "POST"),
                            input_schema=tool_data.get("input_schema", {}),
                            output_schema=tool_data.get("output_schema", {}),
                            authentication_required=tool_data.get("auth_required", False),
                            metadata=tool_data.get("metadata", {})
                        )
                        tools.append(tool)
                        self.available_tools[tool.name] = tool

                    return tools

        except Exception:
            pass

        return []

    async def execute_tool(self, tool_call: ExternalToolCall) -> ExternalToolResult:
        """Execute REST API tool call."""
        import time
        start_time = time.time()

        try:
            tool_def = self.available_tools.get(tool_call.tool_name)
            if not tool_def:
                return ExternalToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"Tool '{tool_call.tool_name}' not found"
                )

            # Build request
            url = f"{self.connection.endpoint}{tool_def.endpoint}"
            method = tool_def.method.upper()

            # Prepare request data
            if method in ["GET", "DELETE"]:
                params = tool_call.arguments
                json_data = None
            else:
                params = None
                json_data = tool_call.arguments

            # Execute request
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=tool_call.timeout or self.connection.timeout
            ) as response:
                execution_time = (time.time() - start_time) * 1000

                if response.status < 400:
                    result_data = await response.json() if response.content_type == "application/json" else await response.text()

                    result = ExternalToolResult(
                        call_id=tool_call.call_id,
                        success=True,
                        result=result_data,
                        status_code=response.status,
                        headers=dict(response.headers),
                        execution_time=execution_time
                    )
                else:
                    error_text = await response.text()
                    result = ExternalToolResult(
                        call_id=tool_call.call_id,
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        status_code=response.status,
                        headers=dict(response.headers),
                        execution_time=execution_time
                    )

                self._update_stats(result)
                return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            result = ExternalToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"Tool execution failed: {str(e)}",
                execution_time=execution_time
            )
            self._update_stats(result)
            return result

    async def validate_tool_call(self, tool_call: ExternalToolCall) -> bool:
        """Validate REST API tool call."""
        tool_def = self.available_tools.get(tool_call.tool_name)
        if not tool_def:
            return False

        # Basic validation against input schema
        input_schema = tool_def.input_schema
        if input_schema:
            required_fields = input_schema.get("required", [])
            for field in required_fields:
                if field not in tool_call.arguments:
                    return False

        return True

    async def get_tool_definition(self, tool_name: str) -> Optional[ExternalToolDefinition]:
        """Get tool definition."""
        return self.available_tools.get(tool_name)


class MockExternalProvider(ExternalToolProvider):
    """Mock external tool provider for testing."""

    def __init__(self, connection: Optional[ToolConnection] = None):
        if connection is None:
            connection = ToolConnection(
                provider_type=ToolProviderType.FUNCTION,
                name="mock_provider"
            )
        super().__init__(connection)

        # Pre-define some mock tools
        self.mock_tools = [
            ExternalToolDefinition(
                name="external_calculator",
                description="External calculator service",
                provider="mock_provider",
                endpoint="/calculate",
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    },
                    "required": ["expression"]
                }
            ),
            ExternalToolDefinition(
                name="data_processor",
                description="External data processing service",
                provider="mock_provider",
                endpoint="/process",
                input_schema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "array"},
                        "operation": {"type": "string"}
                    },
                    "required": ["data", "operation"]
                }
            )
        ]

    async def connect(self) -> bool:
        """Mock connection."""
        self.is_connected = True
        return True

    async def disconnect(self) -> None:
        """Mock disconnection."""
        self.is_connected = False

    async def discover_tools(self) -> List[ExternalToolDefinition]:
        """Return mock tools."""
        for tool in self.mock_tools:
            self.available_tools[tool.name] = tool
        return self.mock_tools

    async def execute_tool(self, tool_call: ExternalToolCall) -> ExternalToolResult:
        """Execute mock tool call."""
        import time
        start_time = time.time()

        try:
            if tool_call.tool_name == "external_calculator":
                expression = tool_call.arguments.get("expression", "")
                try:
                    # Simple calculation (unsafe - for demo only)
                    result = eval(expression) if expression else 0
                    execution_time = (time.time() - start_time) * 1000

                    return ExternalToolResult(
                        call_id=tool_call.call_id,
                        success=True,
                        result={"answer": str(result)},
                        execution_time=execution_time
                    )
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    return ExternalToolResult(
                        call_id=tool_call.call_id,
                        success=False,
                        error=f"Calculation error: {str(e)}",
                        execution_time=execution_time
                    )

            elif tool_call.tool_name == "data_processor":
                data = tool_call.arguments.get("data", [])
                operation = tool_call.arguments.get("operation", "count")

                if operation == "count":
                    result = {"count": len(data)}
                elif operation == "sum" and all(isinstance(x, (int, float)) for x in data):
                    result = {"sum": sum(data)}
                else:
                    result = {"processed": True, "operation": operation}

                execution_time = (time.time() - start_time) * 1000
                return ExternalToolResult(
                    call_id=tool_call.call_id,
                    success=True,
                    result=result,
                    execution_time=execution_time
                )

            else:
                execution_time = (time.time() - start_time) * 1000
                return ExternalToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"Unknown tool: {tool_call.tool_name}",
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ExternalToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"Execution error: {str(e)}",
                execution_time=execution_time
            )

    async def validate_tool_call(self, tool_call: ExternalToolCall) -> bool:
        """Validate mock tool call."""
        return tool_call.tool_name in [tool.name for tool in self.mock_tools]

    async def get_tool_definition(self, tool_name: str) -> Optional[ExternalToolDefinition]:
        """Get mock tool definition."""
        return self.available_tools.get(tool_name)


class ExternalToolProviderFactory:
    """Factory for creating external tool providers."""

    _providers = {
        ToolProviderType.REST_API: RESTAPIProvider,
        ToolProviderType.FUNCTION: MockExternalProvider
    }

    @classmethod
    def register_provider(cls, provider_type: ToolProviderType, provider_class: type) -> None:
        """Register a new tool provider."""
        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(cls, connection: ToolConnection) -> ExternalToolProvider:
        """Create a tool provider instance."""
        provider_class = cls._providers.get(connection.provider_type)

        if not provider_class:
            raise ValueError(f"Unknown tool provider type: {connection.provider_type}")

        return provider_class(connection)

    @classmethod
    def list_provider_types(cls) -> List[ToolProviderType]:
        """List available provider types."""
        return list(cls._providers.keys())