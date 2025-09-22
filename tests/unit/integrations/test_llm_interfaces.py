"""Unit tests for LLM interfaces and configuration classes."""

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List, Optional
import pytest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from integrations.llm_interfaces import (
        LLMConfig, LLMMessage, LLMResponse,
        LLMProvider, ChatModel, FunctionCallModel
    )
except ImportError as e:
    pytest.skip(f"Integration imports not available: {e}", allow_module_level=True)


class TestLLMMessage:
    """Test the LLMMessage class."""

    def test_init_basic(self):
        """Test basic message initialization."""
        message = LLMMessage(role="user", content="Hello")

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.metadata == {}

    def test_init_with_metadata(self):
        """Test message initialization with metadata."""
        metadata = {"timestamp": "2024-01-01", "user_id": "123"}
        message = LLMMessage(
            role="assistant",
            content="Hi there!",
            metadata=metadata
        )

        assert message.role == "assistant"
        assert message.content == "Hi there!"
        assert message.metadata == metadata

    def test_to_dict(self):
        """Test message serialization."""
        message = LLMMessage(
            role="system",
            content="You are helpful",
            metadata={"type": "system"}
        )

        data = message.to_dict()

        assert data == {
            "role": "system",
            "content": "You are helpful",
            "metadata": {"type": "system"}
        }

    def test_from_dict(self):
        """Test message deserialization."""
        data = {
            "role": "user",
            "content": "What's the weather?",
            "metadata": {"location": "NYC"}
        }

        message = LLMMessage.from_dict(data)

        assert message.role == "user"
        assert message.content == "What's the weather?"
        assert message.metadata == {"location": "NYC"}

    def test_from_dict_minimal(self):
        """Test message deserialization with minimal data."""
        data = {
            "role": "user",
            "content": "Hello"
        }

        message = LLMMessage.from_dict(data)

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.metadata == {}

    def test_equality(self):
        """Test message equality comparison."""
        msg1 = LLMMessage("user", "Hello")
        msg2 = LLMMessage("user", "Hello")
        msg3 = LLMMessage("user", "Hi")

        assert msg1 == msg2
        assert msg1 != msg3

    def test_repr(self):
        """Test message string representation."""
        message = LLMMessage("user", "Hello world")
        repr_str = repr(message)

        assert "user" in repr_str
        assert "Hello world" in repr_str


class TestLLMResponse:
    """Test the LLMResponse class."""

    def test_init_basic(self):
        """Test basic response initialization."""
        response = LLMResponse(
            content="Generated text",
            model="gpt-3.5-turbo"
        )

        assert response.content == "Generated text"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage == {}
        assert response.metadata == {}
        assert isinstance(response.timestamp, datetime)

    def test_init_with_usage(self):
        """Test response initialization with usage data."""
        usage = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }

        response = LLMResponse(
            content="Text",
            model="gpt-4",
            usage=usage
        )

        assert response.usage == usage

    def test_init_with_metadata(self):
        """Test response initialization with metadata."""
        metadata = {"finish_reason": "stop", "latency": 1.5}

        response = LLMResponse(
            content="Response",
            model="claude-3",
            metadata=metadata
        )

        assert response.metadata == metadata

    def test_to_dict(self):
        """Test response serialization."""
        usage = {"prompt_tokens": 5, "completion_tokens": 3}
        metadata = {"finish_reason": "stop"}

        response = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            usage=usage,
            metadata=metadata
        )

        data = response.to_dict()

        assert data["content"] == "Test response"
        assert data["model"] == "gpt-3.5-turbo"
        assert data["usage"] == usage
        assert data["metadata"] == metadata
        assert "timestamp" in data

    def test_from_dict(self):
        """Test response deserialization."""
        timestamp = datetime.now()
        data = {
            "content": "Response text",
            "model": "gpt-4",
            "usage": {"total_tokens": 20},
            "metadata": {"type": "completion"},
            "timestamp": timestamp.isoformat()
        }

        response = LLMResponse.from_dict(data)

        assert response.content == "Response text"
        assert response.model == "gpt-4"
        assert response.usage == {"total_tokens": 20}
        assert response.metadata == {"type": "completion"}

    def test_token_count_properties(self):
        """Test token count convenience properties."""
        response = LLMResponse(
            content="Text",
            model="gpt-3.5-turbo",
            usage={
                "prompt_tokens": 15,
                "completion_tokens": 10,
                "total_tokens": 25
            }
        )

        assert response.prompt_tokens == 15
        assert response.completion_tokens == 10
        assert response.total_tokens == 25

    def test_token_count_properties_no_usage(self):
        """Test token count properties with no usage data."""
        response = LLMResponse(content="Text", model="gpt-3.5-turbo")

        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0


class TestLLMConfig:
    """Test the LLMConfig class."""

    def test_init_basic(self):
        """Test basic config initialization."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo"
        )

        assert config.provider == "openai"
        assert config.model == "gpt-3.5-turbo"
        assert config.api_key is None
        assert config.api_base is None
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0

    def test_init_with_params(self):
        """Test config initialization with parameters."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test-key",
            api_base="https://api.test.com",
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.2
        )

        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.api_key == "test-key"
        assert config.api_base == "https://api.test.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.1
        assert config.presence_penalty == 0.2

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )

        assert config.validate() is True

    def test_validate_invalid_temperature(self):
        """Test validation with invalid temperature."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=2.5  # Invalid: > 2.0
        )

        assert config.validate() is False

    def test_validate_invalid_max_tokens(self):
        """Test validation with invalid max_tokens."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            max_tokens=0  # Invalid: <= 0
        )

        assert config.validate() is False

    def test_validate_invalid_top_p(self):
        """Test validation with invalid top_p."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            top_p=1.5  # Invalid: > 1.0
        )

        assert config.validate() is False

    def test_to_dict(self):
        """Test config serialization."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="secret",
            temperature=0.8
        )

        data = config.to_dict()

        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["api_key"] == "secret"
        assert data["temperature"] == 0.8

    def test_from_dict(self):
        """Test config deserialization."""
        data = {
            "provider": "anthropic",
            "model": "claude-3",
            "api_key": "claude-key",
            "temperature": 0.6,
            "max_tokens": 500
        }

        config = LLMConfig.from_dict(data)

        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.api_key == "claude-key"
        assert config.temperature == 0.6
        assert config.max_tokens == 500

    def test_get_litellm_params(self):
        """Test getting LiteLLM-compatible parameters."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="key",
            temperature=0.5,
            max_tokens=200
        )

        params = config.get_litellm_params()

        assert params["model"] == "gpt-3.5-turbo"
        assert params["api_key"] == "key"
        assert params["temperature"] == 0.5
        assert params["max_tokens"] == 200

    def test_get_litellm_params_with_base(self):
        """Test getting LiteLLM params with custom base URL."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_base="https://custom.api.com"
        )

        params = config.get_litellm_params()

        assert params["api_base"] == "https://custom.api.com"

    def test_update_method(self):
        """Test config update method."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        config.update(temperature=0.9, max_tokens=500)

        assert config.temperature == 0.9
        assert config.max_tokens == 500
        assert config.provider == "openai"  # Unchanged

    def test_copy_method(self):
        """Test config copy method."""
        original = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="secret"
        )

        copy = original.copy()

        assert copy.provider == original.provider
        assert copy.model == original.model
        assert copy.api_key == original.api_key
        assert copy is not original  # Different objects


class TestLLMProvider:
    """Test the abstract LLMProvider class."""

    def test_abstract_methods(self):
        """Test that LLMProvider is properly abstract."""
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            LLMProvider()

    def test_subclass_implementation(self):
        """Test that subclasses must implement abstract methods."""
        class IncompleteProvider(LLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_concrete_subclass(self):
        """Test a concrete implementation of LLMProvider."""
        class TestProvider(LLMProvider):
            def __init__(self, config):
                self.config = config

            async def generate(self, messages):
                return LLMResponse("test", "test-model")

            async def generate_stream(self, messages):
                yield "test"

            def validate_config(self):
                return True

            def get_supported_models(self):
                return ["test-model"]

        config = LLMConfig(provider="test", model="test-model")
        provider = TestProvider(config)

        assert provider.config == config
        assert provider.validate_config() is True
        assert "test-model" in provider.get_supported_models()


class TestChatModel:
    """Test the ChatModel interface."""

    def test_concrete_implementation(self):
        """Test a concrete ChatModel implementation."""
        class TestChatModel(ChatModel):
            async def chat(self, messages, **kwargs):
                return LLMResponse("chat response", "test-model")

            async def chat_stream(self, messages, **kwargs):
                yield "streaming"
                yield " response"

        model = TestChatModel()

        # Test methods exist and are callable
        assert hasattr(model, 'chat')
        assert hasattr(model, 'chat_stream')


class TestFunctionCallModel:
    """Test the FunctionCallModel interface."""

    def test_concrete_implementation(self):
        """Test a concrete FunctionCallModel implementation."""
        class TestFunctionModel(FunctionCallModel):
            async def call_function(self, messages, functions, **kwargs):
                return {
                    "function_call": {
                        "name": "test_function",
                        "arguments": "{\"param\": \"value\"}"
                    }
                }

            def validate_functions(self, functions):
                return True

        model = TestFunctionModel()

        # Test methods exist and are callable
        assert hasattr(model, 'call_function')
        assert hasattr(model, 'validate_functions')


class TestIntegrationScenarios:
    """Test integration scenarios between classes."""

    def test_message_response_workflow(self):
        """Test complete message to response workflow."""
        # Create messages
        messages = [
            LLMMessage("system", "You are helpful"),
            LLMMessage("user", "Hello", {"user_id": "123"})
        ]

        # Create config
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7
        )

        # Create response
        response = LLMResponse(
            content="Hi there! How can I help?",
            model=config.model,
            usage={"prompt_tokens": 15, "completion_tokens": 10},
            metadata={"finish_reason": "stop"}
        )

        # Verify workflow
        assert len(messages) == 2
        assert config.validate() is True
        assert response.total_tokens == 25

    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        # Original objects
        message = LLMMessage("user", "Test", {"id": "123"})
        config = LLMConfig("openai", "gpt-3.5-turbo", temperature=0.8)
        response = LLMResponse("Result", "gpt-3.5-turbo", {"tokens": 10})

        # Serialize
        message_data = message.to_dict()
        config_data = config.to_dict()
        response_data = response.to_dict()

        # Deserialize
        new_message = LLMMessage.from_dict(message_data)
        new_config = LLMConfig.from_dict(config_data)
        new_response = LLMResponse.from_dict(response_data)

        # Verify roundtrip
        assert new_message.role == message.role
        assert new_message.content == message.content
        assert new_message.metadata == message.metadata

        assert new_config.provider == config.provider
        assert new_config.model == config.model
        assert new_config.temperature == config.temperature

        assert new_response.content == response.content
        assert new_response.model == response.model
        assert new_response.metadata == response.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])