"""MCP (Model Context Protocol) adapter for tool integration."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json

from .tool_interfaces import ToolInterface, ToolDefinition, ToolCall, ToolResult, ToolParameter


@dataclass
class MCPConnection:
    """Represents a connection to an MCP server."""

    name: str
    url: str
    protocol: str = "stdio"
    status: str = "disconnected"  # disconnected, connecting, connected, error
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_ping: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "protocol": self.protocol,
            "status": self.status,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "metadata": self.metadata,
            "last_ping": self.last_ping.isoformat() if self.last_ping else None,
            "error_message": self.error_message
        }


class MCPProtocol(ABC):
    """Abstract MCP protocol interface."""

    @abstractmethod
    async def connect(self, connection_info: Dict[str, Any]) -> bool:
        """Connect to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Ping the MCP server."""
        pass


class MockMCPProtocol(MCPProtocol):
    """Mock MCP protocol for testing and demonstration."""

    def __init__(self):
        self.connected = False
        self.mock_tools = [
            {
                "name": "calculator",
                "description": "Perform basic arithmetic calculations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "weather",
                "description": "Get weather information for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]

    async def connect(self, connection_info: Dict[str, Any]) -> bool:
        """Mock connection."""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """Mock disconnection."""
        self.connected = False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Return mock tools."""
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        return self.mock_tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock tool call."""
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")

        await asyncio.sleep(0.05)  # Simulate execution delay

        if name == "calculator":
            expression = arguments.get("expression", "")
            try:
                # Simple expression evaluation (unsafe - for demo only)
                result = eval(expression) if expression else 0
                return {"result": str(result)}
            except Exception as e:
                return {"error": f"Calculation error: {str(e)}"}

        elif name == "weather":
            location = arguments.get("location", "Unknown")
            return {
                "result": f"Mock weather for {location}: 22°C, partly cloudy"
            }

        else:
            return {"error": f"Unknown tool: {name}"}

    async def ping(self) -> bool:
        """Mock ping."""
        return self.connected


class MCPTool(ToolInterface):
    """Tool that wraps an MCP server tool."""

    def __init__(self, mcp_adapter: 'MCPAdapter', tool_definition: ToolDefinition):
        self.mcp_adapter = mcp_adapter
        self.tool_definition = tool_definition

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition."""
        return self.tool_definition

    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate arguments using the tool definition."""
        try:
            # Basic validation - could be enhanced
            for param in self.tool_definition.parameters:
                if param.required and param.name not in arguments:
                    return False
            return True
        except Exception:
            return False

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute the tool via MCP adapter."""
        return await self.mcp_adapter.execute_mcp_tool(tool_call)


class MCPToolProxy(ToolInterface):
    """Proxy tool that forwards calls to MCP server."""

    def __init__(self, name: str, server_name: str, adapter: 'MCPAdapter', tool_info: Dict[str, Any]):
        self.name = name
        self.server_name = server_name
        self.adapter = adapter
        self.tool_info = tool_info

    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.tool_info.get("description", "MCP tool"),
            parameters=[
                ToolParameter(
                    name=param["name"],
                    param_type=param.get("type", "string"),
                    description=param.get("description", ""),
                    required=param.get("required", False)
                )
                for param in self.tool_info.get("parameters", [])
            ]
        )

    async def execute(self, call: ToolCall) -> ToolResult:
        """Execute tool call through MCP adapter."""
        try:
            result = await self.adapter.protocol.call_tool(call.name, call.arguments)
            return ToolResult(
                call_id=call.id,
                success=result.get("success", False),
                result=result.get("result"),
                error=result.get("error")
            )
        except Exception as e:
            return ToolResult(
                call_id=call.id,
                success=False,
                error=str(e)
            )


class MCPAdapter:
    """Adapter for integrating MCP servers as tools."""

    def __init__(self, protocol: Optional[MCPProtocol] = None):
        self.protocol = protocol or MockMCPProtocol()
        self.connections: Dict[str, MCPConnection] = {}
        self.tools_cache: Dict[str, ToolDefinition] = {}

    async def connect_server(
        self,
        name: str,
        connection_info: Dict[str, Any]
    ) -> bool:
        """
        Connect to an MCP server.

        Args:
            name: Name for this connection
            connection_info: Connection configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create connection object
            connection = MCPConnection(
                name=name,
                url=connection_info.get("url", ""),
                protocol=connection_info.get("protocol", "stdio"),
                status="connecting"
            )

            self.connections[name] = connection

            # Attempt connection
            success = await self.protocol.connect(connection_info)

            if success:
                connection.status = "connected"
                connection.last_ping = datetime.now()

                # Discover tools
                await self._discover_tools(name)

                return True
            else:
                connection.status = "error"
                connection.error_message = "Connection failed"
                return False

        except Exception as e:
            if name in self.connections:
                self.connections[name].status = "error"
                self.connections[name].error_message = str(e)
            return False

    async def disconnect_server(self, name: str) -> bool:
        """
        Disconnect from an MCP server.

        Args:
            name: Name of the connection

        Returns:
            True if successful, False otherwise
        """
        if name not in self.connections:
            return False

        try:
            await self.protocol.disconnect()
            self.connections[name].status = "disconnected"

            # Clear cached tools for this connection
            tools_to_remove = [
                tool_name for tool_name, tool_def in self.tools_cache.items()
                if tool_def.metadata.get("mcp_connection") == name
            ]
            for tool_name in tools_to_remove:
                del self.tools_cache[tool_name]

            return True

        except Exception as e:
            self.connections[name].status = "error"
            self.connections[name].error_message = str(e)
            return False

    async def _discover_tools(self, connection_name: str) -> None:
        """Discover tools from the connected MCP server."""
        try:
            mcp_tools = await self.protocol.list_tools()

            for mcp_tool in mcp_tools:
                tool_def = self._convert_mcp_tool_to_definition(mcp_tool, connection_name)
                self.tools_cache[tool_def.name] = tool_def

                # Update connection tool list
                if connection_name in self.connections:
                    self.connections[connection_name].tools.append(tool_def.name)

        except Exception as e:
            if connection_name in self.connections:
                self.connections[connection_name].error_message = f"Tool discovery failed: {str(e)}"

    def _convert_mcp_tool_to_definition(
        self,
        mcp_tool: Dict[str, Any],
        connection_name: str
    ) -> ToolDefinition:
        """Convert MCP tool format to ToolDefinition."""
        name = mcp_tool["name"]
        description = mcp_tool.get("description", "")

        # Parse input schema
        parameters = []
        input_schema = mcp_tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for prop_name, prop_def in properties.items():
            parameter = ToolParameter(
                name=prop_name,
                type=prop_def.get("type", "string"),
                description=prop_def.get("description", ""),
                required=prop_name in required,
                default=prop_def.get("default"),
                enum=prop_def.get("enum")
            )
            parameters.append(parameter)

        return ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            category="mcp",
            metadata={
                "mcp_connection": connection_name,
                "mcp_tool": mcp_tool
            }
        )

    async def execute_mcp_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute an MCP tool call."""
        import time
        start_time = time.time()

        try:
            # Find the connection for this tool
            tool_def = self.tools_cache.get(tool_call.name)
            if not tool_def:
                return ToolResult(
                    call_id=tool_call.id,
                    success=False,
                    error=f"Tool '{tool_call.name}' not found"
                )

            connection_name = tool_def.metadata.get("mcp_connection")
            if not connection_name or connection_name not in self.connections:
                return ToolResult(
                    call_id=tool_call.id,
                    success=False,
                    error=f"MCP connection not found for tool '{tool_call.name}'"
                )

            connection = self.connections[connection_name]
            if connection.status != "connected":
                return ToolResult(
                    call_id=tool_call.id,
                    success=False,
                    error=f"MCP server '{connection_name}' not connected"
                )

            # Execute via MCP protocol
            mcp_result = await self.protocol.call_tool(tool_call.name, tool_call.arguments)

            # Convert result
            if "error" in mcp_result:
                return ToolResult(
                    call_id=tool_call.id,
                    success=False,
                    error=mcp_result["error"],
                    execution_time=time.time() - start_time
                )
            else:
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    result=mcp_result.get("result"),
                    execution_time=time.time() - start_time,
                    metadata={"mcp_connection": connection_name}
                )

        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"MCP execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def get_available_tools(self) -> List[ToolDefinition]:
        """Get all available MCP tools."""
        return list(self.tools_cache.values())

    def get_connections(self) -> List[MCPConnection]:
        """Get all MCP connections."""
        return list(self.connections.values())

    async def ping_connections(self) -> Dict[str, bool]:
        """Ping all connections to check status."""
        results = {}

        for name, connection in self.connections.items():
            if connection.status == "connected":
                try:
                    success = await self.protocol.ping()
                    results[name] = success
                    if success:
                        connection.last_ping = datetime.now()
                    else:
                        connection.status = "error"
                        connection.error_message = "Ping failed"
                except Exception as e:
                    results[name] = False
                    connection.status = "error"
                    connection.error_message = f"Ping error: {str(e)}"
            else:
                results[name] = False

        return results

    # Enhanced extensibility methods
    async def register_custom_protocol(self, protocol_name: str, protocol_class: type) -> bool:
        """
        Register a custom MCP protocol implementation.

        Args:
            protocol_name: Name of the protocol
            protocol_class: Protocol implementation class

        Returns:
            True if registered successfully
        """
        try:
            if not issubclass(protocol_class, MCPProtocol):
                return False

            # Store protocol for future use
            if not hasattr(self, '_custom_protocols'):
                self._custom_protocols = {}

            self._custom_protocols[protocol_name] = protocol_class
            return True
        except Exception:
            return False

    async def create_tool_proxy(self, tool_name: str, server_name: str) -> Optional[ToolInterface]:
        """
        Create a proxy tool that forwards calls to MCP server.

        Args:
            tool_name: Name of the tool
            server_name: Name of MCP server

        Returns:
            Tool proxy instance or None if failed
        """
        try:
            if server_name not in self.connections:
                return None

            connection = self.connections[server_name]
            if connection.status != "connected":
                return None

            # Get tool info from cache
            tool_info = self.tools_cache.get(f"{server_name}:{tool_name}")
            if not tool_info:
                return None

            # Create proxy tool
            proxy_tool = MCPToolProxy(
                name=tool_name,
                server_name=server_name,
                adapter=self,
                tool_info=tool_info
            )

            return proxy_tool
        except Exception:
            return None

    async def batch_tool_execution(self, server_name: str, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Execute multiple tools on the same server in batch.

        Args:
            server_name: Name of MCP server
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results
        """
        if server_name not in self.connections:
            return [ToolResult(call_id=call.id, success=False, error="Server not found")
                   for call in tool_calls]

        try:
            # Execute calls sequentially (simple implementation)
            results = []
            for call in tool_calls:
                result = await self.protocol.call_tool(call.name, call.arguments)
                results.append(ToolResult(
                    call_id=call.id,
                    success=result.get("success", False),
                    result=result.get("result"),
                    error=result.get("error")
                ))

            return results
        except Exception as e:
            return [ToolResult(call_id=call.id, success=False, error=str(e))
                   for call in tool_calls]

    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """
        Get detailed capabilities of MCP server.

        Args:
            server_name: Name of MCP server

        Returns:
            Server capabilities information
        """
        if server_name not in self.connections:
            return {"error": "Server not found"}

        connection = self.connections[server_name]
        if connection.status != "connected":
            return {"error": "Server not connected"}

        try:
            # Get capabilities through protocol
            capabilities = await self.protocol.get_capabilities()
            return {
                "server_name": server_name,
                "capabilities": capabilities,
                "tools": connection.tools,
                "metadata": connection.metadata
            }
        except Exception as e:
            return {"error": str(e)}

    async def check_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Check detailed status of MCP server.

        Args:
            server_name: Name of MCP server

        Returns:
            Server status information
        """
        if server_name not in self.connections:
            return {"connected": False, "error": "Server not found"}

        connection = self.connections[server_name]

        try:
            # Ping server to check connectivity
            if connection.status == "connected":
                ping_success = await self.protocol.ping()
                return {
                    "connected": ping_success,
                    "status": connection.status,
                    "last_ping": connection.last_ping.isoformat() if connection.last_ping else None,
                    "tools_available": len(connection.tools),
                    "capabilities": connection.capabilities
                }
            else:
                return {
                    "connected": False,
                    "status": connection.status,
                    "error": connection.error_message
                }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def reconnect_server(self, server_name: str) -> bool:
        """
        Reconnect to MCP server.

        Args:
            server_name: Name of MCP server

        Returns:
            True if reconnection successful
        """
        if server_name not in self.connections:
            return False

        connection = self.connections[server_name]

        try:
            # Disconnect first if connected
            if connection.status == "connected":
                await self.disconnect_server(server_name)

            # Reconnect
            return await self.connect_server(server_name, {
                "url": connection.url,
                "protocol": connection.protocol
            })
        except Exception:
            return False

    def get_adapter_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        total_connections = len(self.connections)
        active_connections = sum(
            1 for conn in self.connections.values()
            if conn.status == "connected"
        )

        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_tools": len(self.tools_cache),
            "connections": [conn.to_dict() for conn in self.connections.values()]
        }