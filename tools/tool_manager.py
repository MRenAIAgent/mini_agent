"""Core tool manager that orchestrates tool operations."""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime

from .tool_interfaces import ToolInterface, ToolCall, ToolResult, ToolDefinition
from .tool_registry import ToolRegistry
from .mcp_adapter import MCPAdapter, MCPTool


class ToolManager:
    """
    Core tool manager that orchestrates tool operations.

    This manager provides a unified interface for tool registration, discovery,
    and execution, supporting both local tools and MCP-connected tools.
    """

    def __init__(self):
        self.registry = ToolRegistry()
        self.mcp_adapter = MCPAdapter()

        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.total_executions = 0
        self.successful_executions = 0

        # Callbacks
        self._on_tool_executed: Optional[Callable[[ToolCall, ToolResult], Awaitable[None]]] = None

    async def register_tool(
        self,
        tool: ToolInterface,
        aliases: Optional[List[str]] = None
    ) -> bool:
        """
        Register a tool in the manager.

        Args:
            tool: Tool implementation to register
            aliases: Optional list of aliases for the tool

        Returns:
            True if successful, False if name conflicts
        """
        return self.registry.register_tool(tool, aliases)

    async def connect_mcp_server(
        self,
        name: str,
        connection_info: Dict[str, Any]
    ) -> bool:
        """
        Connect to an MCP server and register its tools.

        Args:
            name: Name for this MCP connection
            connection_info: Connection configuration

        Returns:
            True if successful, False otherwise
        """
        success = await self.mcp_adapter.connect_server(name, connection_info)

        if success:
            # Register MCP tools in the main registry
            await self._register_mcp_tools()

        return success

    async def _register_mcp_tools(self) -> None:
        """Register all available MCP tools in the main registry."""
        mcp_tools = self.mcp_adapter.get_available_tools()

        for tool_def in mcp_tools:
            # Create MCPTool wrapper
            mcp_tool = MCPTool(self.mcp_adapter, tool_def)

            # Register with mcp_ prefix to avoid conflicts
            prefixed_name = f"mcp_{tool_def.name}"
            tool_def.name = prefixed_name

            self.registry.register_tool(mcp_tool, aliases=[tool_def.name.replace("mcp_", "")])

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call to execute

        Returns:
            Tool execution result
        """
        start_time = datetime.now()
        self.total_executions += 1

        try:
            # Execute through registry
            result = await self.registry.execute_tool(tool_call)

            # Track success
            if result.success:
                self.successful_executions += 1

            # Add to history
            self.execution_history.append({
                "tool_call": tool_call.to_dict(),
                "result": result.to_dict(),
                "timestamp": start_time.isoformat()
            })

            # Limit history size
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

            # Trigger callback
            if self._on_tool_executed:
                await self._on_tool_executed(tool_call, result)

            return result

        except Exception as e:
            # Create error result
            result = ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Tool execution failed: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

            # Add to history
            self.execution_history.append({
                "tool_call": tool_call.to_dict(),
                "result": result.to_dict(),
                "timestamp": start_time.isoformat()
            })

            return result

    async def execute_tool_by_name(
        self,
        name: str,
        arguments: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute a tool by name and arguments.

        Args:
            name: Tool name
            arguments: Tool arguments
            metadata: Optional metadata

        Returns:
            Tool execution result
        """
        tool_call = ToolCall(
            name=name,
            arguments=arguments,
            metadata=metadata or {}
        )

        return await self.execute_tool(tool_call)

    def list_available_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """
        List all available tools.

        Args:
            category: Optional category filter

        Returns:
            List of tool definitions
        """
        return self.registry.get_tool_definitions(category)

    def get_tool_definitions_for_llm(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tool definitions in LLM-friendly format (OpenAI functions).

        Args:
            category: Optional category filter

        Returns:
            List of OpenAI function definitions
        """
        return self.registry.get_openai_functions(category)

    def search_tools(self, query: str) -> List[ToolDefinition]:
        """
        Search for tools by name or description.

        Args:
            query: Search query

        Returns:
            List of matching tool definitions
        """
        tool_names = self.registry.search_tools(query)
        definitions = []

        for name in tool_names:
            tool = self.registry.get_tool(name)
            if tool:
                definitions.append(tool.get_definition())

        return definitions

    def validate_tool_call(self, tool_call: ToolCall) -> bool:
        """
        Validate a tool call without executing it.

        Args:
            tool_call: Tool call to validate

        Returns:
            True if valid, False otherwise
        """
        return self.registry.validate_tool_call(tool_call)

    async def batch_execute_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Execute multiple tool calls concurrently.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results in the same order
        """
        tasks = [self.execute_tool(call) for call in tool_calls]
        return await asyncio.gather(*tasks)

    def get_tool_by_name(self, name: str) -> Optional[ToolInterface]:
        """
        Get a tool by name.

        Args:
            name: Tool name or alias

        Returns:
            Tool interface if found, None otherwise
        """
        return self.registry.get_tool(name)

    def has_tool(self, name: str) -> bool:
        """
        Check if a tool exists.

        Args:
            name: Tool name or alias

        Returns:
            True if tool exists, False otherwise
        """
        return self.registry.has_tool(name)

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        success_rate = (
            (self.successful_executions / self.total_executions * 100)
            if self.total_executions > 0 else 0
        )

        # Recent execution stats
        recent_history = self.execution_history[-100:] if self.execution_history else []
        recent_successes = sum(
            1 for entry in recent_history
            if entry["result"]["success"]
        )
        recent_success_rate = (
            (recent_successes / len(recent_history) * 100)
            if recent_history else 0
        )

        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "success_rate": success_rate,
            "recent_success_rate": recent_success_rate,
            "history_size": len(self.execution_history)
        }

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics."""
        registry_stats = self.registry.get_registry_stats()
        execution_stats = self.get_execution_stats()
        mcp_stats = self.mcp_adapter.get_adapter_stats()

        return {
            "registry": registry_stats,
            "execution": execution_stats,
            "mcp": mcp_stats
        }

    async def ping_mcp_connections(self) -> Dict[str, bool]:
        """Ping all MCP connections."""
        return await self.mcp_adapter.ping_connections()

    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tool executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of recent execution records
        """
        return self.execution_history[-limit:] if self.execution_history else []

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self.execution_history.clear()

    def set_execution_callback(
        self,
        callback: Callable[[ToolCall, ToolResult], Awaitable[None]]
    ) -> None:
        """Set callback for tool executions."""
        self._on_tool_executed = callback

    # Enhanced MCP support methods
    async def discover_mcp_capabilities(self, server_name: str) -> Dict[str, Any]:
        """
        Discover capabilities of connected MCP server.

        Args:
            server_name: Name of MCP server

        Returns:
            Server capabilities information
        """
        try:
            return await self.mcp_adapter.get_server_capabilities(server_name)
        except Exception as e:
            return {"error": str(e), "capabilities": []}

    async def auto_register_mcp_tools(self, server_name: str) -> int:
        """
        Automatically register all tools from MCP server.

        Args:
            server_name: Name of MCP server

        Returns:
            Number of tools registered
        """
        try:
            tools = await self.mcp_adapter.list_server_tools(server_name)
            registered_count = 0

            for tool_info in tools:
                # Convert MCP tool to our tool interface
                mcp_tool = MCPTool(
                    name=tool_info["name"],
                    description=tool_info.get("description", ""),
                    server_name=server_name,
                    tool_info=tool_info
                )

                if await self.register_tool(mcp_tool):
                    registered_count += 1

            return registered_count
        except Exception:
            return 0

    async def refresh_mcp_connections(self) -> Dict[str, bool]:
        """
        Refresh all MCP connections and re-register tools.

        Returns:
            Dictionary of server names and their refresh status
        """
        connections = self.mcp_adapter.get_connections()
        refresh_status = {}

        for connection in connections:
            try:
                # Refresh connection
                await self.mcp_adapter.reconnect_server(connection.name)

                # Re-register tools
                tool_count = await self.auto_register_mcp_tools(connection.name)
                refresh_status[connection.name] = True

            except Exception:
                refresh_status[connection.name] = False

        return refresh_status

    def get_mcp_server_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all MCP servers.

        Returns:
            List of server status information
        """
        connections = self.mcp_adapter.get_connections()
        return [
            {
                "name": conn.name,
                "status": conn.status,
                "url": conn.url,
                "tools_count": len([
                    tool for tool in self.list_available_tools()
                    if hasattr(tool, 'server_name') and tool.server_name == conn.name
                ]),
                "last_connected": conn.last_connected.isoformat() if conn.last_connected else None
            }
            for conn in connections
        ]

    async def validate_mcp_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Validate MCP tool availability and parameters.

        Args:
            tool_name: Name of tool to validate

        Returns:
            Validation results
        """
        try:
            tool = self.registry.get_tool(tool_name)
            if not tool or not hasattr(tool, 'server_name'):
                return {"valid": False, "error": "Tool not found or not MCP tool"}

            # Check server connection
            server_status = await self.mcp_adapter.check_server_status(tool.server_name)
            if not server_status.get("connected", False):
                return {"valid": False, "error": "MCP server not connected"}

            # Test tool call
            test_call = ToolCall(
                id="validation-test",
                name=tool_name,
                arguments={}
            )

            # Note: This is a dry run validation, not actual execution
            return {
                "valid": True,
                "server": tool.server_name,
                "server_status": server_status
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def shutdown(self) -> None:
        """Shutdown the tool manager and clean up resources."""
        # Disconnect all MCP connections
        connections = self.mcp_adapter.get_connections()
        for connection in connections:
            if connection.status == "connected":
                await self.mcp_adapter.disconnect_server(connection.name)

        # Clear registries
        self.registry.clear_registry()
        self.execution_history.clear()

    def export_configuration(self) -> Dict[str, Any]:
        """Export tool manager configuration."""
        return {
            "registry": self.registry.export_registry(),
            "mcp_connections": [
                conn.to_dict() for conn in self.mcp_adapter.get_connections()
            ],
            "stats": self.get_manager_stats()
        }