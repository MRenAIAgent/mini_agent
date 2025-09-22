"""Tool registry for managing available tools."""

from typing import Dict, List, Optional, Set, Any
import asyncio

from .tool_interfaces import ToolInterface, ToolDefinition, ToolCall, ToolResult


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, ToolInterface] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._aliases: Dict[str, str] = {}

    def register_tool(
        self,
        tool: ToolInterface,
        aliases: Optional[List[str]] = None
    ) -> bool:
        """
        Register a tool in the registry.

        Args:
            tool: Tool implementation to register
            aliases: Optional list of aliases for the tool

        Returns:
            True if successful, False if name conflicts
        """
        definition = tool.get_definition()
        name = definition.name

        # Check for name conflicts
        if name in self._tools:
            return False

        # Register the tool
        self._tools[name] = tool

        # Add to category
        category = definition.category
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(name)

        # Register aliases
        if aliases:
            for alias in aliases:
                if alias not in self._aliases:
                    self._aliases[alias] = name

        return True

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            name: Name of the tool to unregister

        Returns:
            True if successful, False if not found
        """
        if name not in self._tools:
            return False

        tool = self._tools[name]
        definition = tool.get_definition()

        # Remove from tools
        del self._tools[name]

        # Remove from category
        category = definition.category
        if category in self._categories:
            self._categories[category].discard(name)
            if not self._categories[category]:
                del self._categories[category]

        # Remove aliases
        aliases_to_remove = [alias for alias, target in self._aliases.items() if target == name]
        for alias in aliases_to_remove:
            del self._aliases[alias]

        return True

    def get_tool(self, name: str) -> Optional[ToolInterface]:
        """
        Get a tool by name or alias.

        Args:
            name: Tool name or alias

        Returns:
            Tool interface if found, None otherwise
        """
        # Check direct name
        if name in self._tools:
            return self._tools[name]

        # Check aliases
        if name in self._aliases:
            actual_name = self._aliases[name]
            return self._tools.get(actual_name)

        return None

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List available tools.

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category is None:
            return list(self._tools.keys())

        if category in self._categories:
            return list(self._categories[category])

        return []

    def list_categories(self) -> List[str]:
        """List available tool categories."""
        return list(self._categories.keys())

    def get_tool_definitions(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get tool definitions.

        Args:
            category: Optional category filter

        Returns:
            List of tool definitions
        """
        tool_names = self.list_tools(category)
        definitions = []

        for name in tool_names:
            tool = self._tools[name]
            definitions.append(tool.get_definition())

        return definitions

    def get_openai_functions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tool definitions in OpenAI function format.

        Args:
            category: Optional category filter

        Returns:
            List of OpenAI function definitions
        """
        definitions = self.get_tool_definitions(category)
        return [definition.to_openai_function() for definition in definitions]

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call to execute

        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_call.name)

        if not tool:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Tool '{tool_call.name}' not found"
            )

        # Validate arguments
        if not tool.validate_arguments(tool_call.arguments):
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Invalid arguments for tool '{tool_call.name}'"
            )

        # Execute the tool
        try:
            return await tool.execute(tool_call)
        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    def search_tools(self, query: str) -> List[str]:
        """
        Search for tools by name or description.

        Args:
            query: Search query

        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        matches = []

        for name, tool in self._tools.items():
            definition = tool.get_definition()

            # Check name
            if query_lower in name.lower():
                matches.append(name)
                continue

            # Check description
            if query_lower in definition.description.lower():
                matches.append(name)
                continue

        return matches

    def validate_tool_call(self, tool_call: ToolCall) -> bool:
        """
        Validate a tool call without executing it.

        Args:
            tool_call: Tool call to validate

        Returns:
            True if valid, False otherwise
        """
        tool = self.get_tool(tool_call.name)
        if not tool:
            return False

        return tool.validate_arguments(tool_call.arguments)

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "categories": len(self._categories),
            "aliases": len(self._aliases),
            "tools_by_category": {
                category: len(tools)
                for category, tools in self._categories.items()
            }
        }

    def export_registry(self) -> Dict[str, Any]:
        """Export registry configuration."""
        return {
            "tools": [
                {
                    "definition": tool.get_definition().to_dict(),
                    "aliases": [
                        alias for alias, target in self._aliases.items()
                        if target == name
                    ]
                }
                for name, tool in self._tools.items()
            ],
            "stats": self.get_registry_stats()
        }

    def clear_registry(self) -> None:
        """Clear all tools from registry."""
        self._tools.clear()
        self._categories.clear()
        self._aliases.clear()

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return name in self._tools or name in self._aliases

    def get_tool_names(self) -> List[str]:
        """Get all tool names including aliases."""
        names = list(self._tools.keys())
        names.extend(self._aliases.keys())
        return names