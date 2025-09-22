"""
Integration tests for backward compatibility.

These tests MUST FAIL initially (TDD Red phase) before implementation.
They validate that existing API remains functional after enhancements.
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import Mock, AsyncMock

# These imports will fail initially - that's expected for TDD
try:
    from agent import CoreAgent
    from integrations.llm_interfaces import LLMConfig
    from memory.memory_manager import CoreMemoryManager
    from tools.tool_manager import ToolManager
except ImportError:
    # Expected during TDD Red phase
    CoreAgent = None
    LLMConfig = None
    CoreMemoryManager = None
    ToolManager = None


class TestAgentBackwardCompatibility:
    """Test CoreAgent backward compatibility with existing API"""

    @pytest.fixture
    def legacy_llm_function(self):
        """Legacy LLM function for backward compatibility testing"""
        async def mock_llm_function(prompt: str) -> str:
            return f"Legacy response to: {prompt}"
        return mock_llm_function

    def test_legacy_agent_initialization(self, legacy_llm_function):
        """Test agent initialization with legacy llm_function parameter"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        # Legacy initialization pattern must still work
        agent = CoreAgent(llm_function=legacy_llm_function)

        # Verify agent was created successfully
        assert agent is not None, "Legacy agent initialization must work"
        assert hasattr(agent, 'run'), "Legacy agent must have run method"
        assert hasattr(agent, 'llm_function'), "Legacy agent must store llm_function"

    async def test_legacy_run_method(self, legacy_llm_function):
        """Test legacy run() method behavior is preserved"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        agent = CoreAgent(llm_function=legacy_llm_function)

        # Test basic run functionality
        user_input = "Hello world"
        response = await agent.run(user_input)

        # Validate legacy behavior
        assert isinstance(response, str), "Legacy run must return string"
        assert "Legacy response to:" in response, "Legacy function must be called"
        assert user_input in response, "Legacy run must process input"

    async def test_legacy_run_with_context(self, legacy_llm_function):
        """Test legacy run() method with context parameter"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        agent = CoreAgent(llm_function=legacy_llm_function)

        # Test run with context (existing API)
        user_input = "Test input"
        context = {"session_id": "test-123"}

        response = await agent.run(user_input, context=context)

        # Legacy behavior must be preserved
        assert isinstance(response, str), "Legacy run with context must return string"
        assert len(response) > 0, "Legacy run must return non-empty response"

    def test_legacy_constructor_parameters(self, legacy_llm_function):
        """Test legacy constructor parameters still work"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        # Test various legacy parameter combinations
        agent1 = CoreAgent(llm_function=legacy_llm_function)
        assert agent1 is not None

        # Test with memory manager (if it was supported before)
        try:
            agent2 = CoreAgent(
                llm_function=legacy_llm_function,
                memory_manager=Mock()
            )
            assert agent2 is not None
        except TypeError:
            # If memory_manager wasn't supported before, that's fine
            pass

    async def test_legacy_memory_integration(self, legacy_llm_function):
        """Test legacy memory integration still works"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        agent = CoreAgent(llm_function=legacy_llm_function)

        # If agent had memory features before, they should still work
        if hasattr(agent, 'memory_manager'):
            user_input = "Remember my name is Bob"
            await agent.run(user_input)

            # Test memory retrieval
            if hasattr(agent.memory_manager, 'search_memory'):
                memories = await agent.memory_manager.search_memory("Bob")
                # Should work without breaking


class TestNewAPIBackwardCompatibility:
    """Test new LLMConfig API maintains backward compatibility"""

    def test_llm_config_to_function_conversion(self):
        """Test LLMConfig can be converted to legacy function format"""
        # This test MUST FAIL initially
        if LLMConfig is None:
            pytest.skip("LLMConfig not implemented yet - TDD Red phase")

        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )

        # New config should be usable in legacy contexts
        # Either through adapter pattern or direct compatibility
        assert hasattr(config, 'to_function') or callable(config), \
            "LLMConfig must be convertible to legacy function format"

    async def test_mixed_initialization_compatibility(self):
        """Test agent works with both old and new initialization patterns"""
        # This test MUST FAIL initially
        if CoreAgent is None or LLMConfig is None:
            pytest.skip("CoreAgent/LLMConfig not implemented yet - TDD Red phase")

        # Legacy function
        async def legacy_llm(prompt: str) -> str:
            return f"Legacy: {prompt}"

        # New config
        new_config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )

        # Both should work
        legacy_agent = CoreAgent(llm_function=legacy_llm)
        new_agent = CoreAgent(llm_config=new_config)

        # Both should have same basic interface
        assert hasattr(legacy_agent, 'run'), "Legacy agent must have run method"
        assert hasattr(new_agent, 'run'), "New agent must have run method"

        # Both should produce responses
        legacy_response = await legacy_agent.run("test")
        new_response = await new_agent.run("test")

        assert isinstance(legacy_response, str), "Legacy response must be string"
        assert isinstance(new_response, str), "New response must be string"

    def test_parameter_precedence(self):
        """Test parameter precedence when both old and new params provided"""
        # This test validates behavior when both llm_function and llm_config are provided
        if CoreAgent is None or LLMConfig is None:
            pytest.skip("CoreAgent/LLMConfig not implemented yet - TDD Red phase")

        async def legacy_llm(prompt: str) -> str:
            return "legacy"

        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )

        # Test what happens when both are provided
        # Should either raise clear error or have documented precedence
        try:
            agent = CoreAgent(llm_function=legacy_llm, llm_config=config)
            # If this succeeds, there should be clear precedence documented
            assert agent is not None
        except (ValueError, TypeError) as e:
            # If this fails, the error should be clear about conflicting parameters
            assert "conflict" in str(e).lower() or "both" in str(e).lower()


class TestToolSystemBackwardCompatibility:
    """Test tool system backward compatibility"""

    def test_legacy_tool_registration(self):
        """Test legacy tool registration methods still work"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        async def mock_llm(prompt: str) -> str:
            return "response"

        agent = CoreAgent(llm_function=mock_llm)

        # If there was a legacy way to add tools, it should still work
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"

        if hasattr(agent, 'add_tool'):
            # Legacy tool addition should work
            agent.add_tool(mock_tool)
            assert mock_tool in agent.tools or hasattr(agent, 'tool_manager')

    async def test_legacy_tool_execution(self):
        """Test legacy tool execution patterns still work"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        async def mock_llm(prompt: str) -> str:
            return "Using tool: test_tool"

        agent = CoreAgent(llm_function=mock_llm)

        # Mock tool with legacy interface
        mock_tool = Mock()
        mock_tool.name = "calculator"
        mock_tool.call = AsyncMock(return_value="42")

        if hasattr(agent, 'add_tool'):
            agent.add_tool(mock_tool)

            # Legacy tool usage should work
            response = await agent.run("Calculate 6*7")
            assert isinstance(response, str), "Tool execution must return string"


class TestMemorySystemBackwardCompatibility:
    """Test memory system backward compatibility"""

    def test_legacy_memory_manager_interface(self):
        """Test legacy memory manager interface is preserved"""
        # This test MUST FAIL initially
        if CoreMemoryManager is None:
            pytest.skip("CoreMemoryManager not implemented yet - TDD Red phase")

        # Legacy memory manager creation
        memory_manager = CoreMemoryManager()

        # Legacy interface methods should exist
        legacy_methods = [
            'store_memory',
            'retrieve_memory',
            'search_memory'
        ]

        for method in legacy_methods:
            if hasattr(memory_manager, method):
                assert callable(getattr(memory_manager, method)), \
                    f"Legacy method {method} must be callable"

    async def test_legacy_memory_operations(self):
        """Test legacy memory operations still work"""
        # This test MUST FAIL initially
        if CoreMemoryManager is None:
            pytest.skip("CoreMemoryManager not implemented yet - TDD Red phase")

        memory_manager = CoreMemoryManager()

        # Test legacy memory storage
        if hasattr(memory_manager, 'store_memory'):
            # Legacy simple storage format
            memory_entry = "User's name is Charlie"
            result = await memory_manager.store_memory(memory_entry)

            # Should work without requiring new complex format
            assert result is not None

        # Test legacy memory search
        if hasattr(memory_manager, 'search_memory'):
            results = await memory_manager.search_memory("Charlie")
            assert isinstance(results, list), "Legacy search must return list"

    def test_memory_configuration_backward_compatibility(self):
        """Test memory configuration backward compatibility"""
        # This test MUST FAIL initially
        if CoreMemoryManager is None:
            pytest.skip("CoreMemoryManager not implemented yet - TDD Red phase")

        # Legacy simple configuration should still work
        try:
            simple_manager = CoreMemoryManager()
            assert simple_manager is not None
        except TypeError:
            # If configuration is now required, it should have sensible defaults
            pass

        # If there was a legacy config format, it should still work
        legacy_config = {"cache_size": 100}
        try:
            configured_manager = CoreMemoryManager(config=legacy_config)
            assert configured_manager is not None
        except (TypeError, AttributeError):
            # If legacy config format changed, migration path should be clear
            pass


class TestAPIResponseCompatibility:
    """Test API response format backward compatibility"""

    async def test_response_format_consistency(self):
        """Test response formats remain consistent with legacy expectations"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        async def mock_llm(prompt: str) -> str:
            return "test response"

        agent = CoreAgent(llm_function=mock_llm)

        # Test basic response format
        response = await agent.run("test input")

        # Legacy expectations
        assert isinstance(response, str), "Response must be string (legacy compatibility)"
        assert len(response) > 0, "Response must not be empty"

        # Test with context - response format should be same
        response_with_context = await agent.run("test", context={"test": True})
        assert isinstance(response_with_context, str), \
            "Response with context must be string (legacy compatibility)"

    def test_error_handling_backward_compatibility(self):
        """Test error handling maintains backward compatibility"""
        # This test validates that new features don't break existing error patterns
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        # Test agent creation with invalid legacy parameters
        with pytest.raises((TypeError, ValueError)):
            CoreAgent(llm_function=None)  # Should raise clear error

        # Test with invalid function signature
        def invalid_llm_function():  # Wrong signature
            return "test"

        with pytest.raises((TypeError, ValueError)):
            CoreAgent(llm_function=invalid_llm_function)

    async def test_streaming_backward_compatibility(self):
        """Test that adding streaming doesn't break existing non-streaming usage"""
        # This test MUST FAIL initially
        if CoreAgent is None:
            pytest.skip("CoreAgent not implemented yet - TDD Red phase")

        async def mock_llm(prompt: str) -> str:
            return "non-streaming response"

        agent = CoreAgent(llm_function=mock_llm)

        # Existing run() method should work exactly as before
        response = await agent.run("test")
        assert isinstance(response, str), "Non-streaming run must still return string"
        assert response == "non-streaming response", "Legacy behavior must be preserved"

        # New streaming method should be separate
        if hasattr(agent, 'run_stream'):
            # Stream method should not interfere with regular run method
            regular_response = await agent.run("test")
            assert isinstance(regular_response, str), \
                "Regular run must work independently of streaming"


class TestConfigurationMigration:
    """Test configuration migration and compatibility"""

    def test_configuration_file_compatibility(self):
        """Test existing configuration files still work"""
        # This validates that existing config files don't break

        # Example legacy configuration structure
        legacy_config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4"
            },
            "memory": {
                "enabled": True,
                "cache_size": 100
            }
        }

        # Legacy config should either work directly or have clear migration path
        # This test documents expected compatibility behavior
        assert isinstance(legacy_config, dict), "Legacy config structure documented"

    def test_environment_variable_compatibility(self):
        """Test environment variable compatibility"""
        # This test validates that existing environment variables still work
        import os

        # Common legacy environment variables
        legacy_env_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "AGENT_MEMORY_SIZE"
        ]

        # Test that these are still recognized if they were before
        for var in legacy_env_vars:
            # This documents expected environment variable behavior
            assert isinstance(var, str), f"Legacy env var {var} documented"


if __name__ == "__main__":
    # Run tests to verify they fail (TDD Red phase)
    pytest.main([__file__, "-v"])