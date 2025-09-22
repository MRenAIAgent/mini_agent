"""Unit tests for LiteLLM provider integration."""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from integrations.litellm_provider import LiteLLMProvider
    from integrations.llm_interfaces import LLMConfig, LLMResponse, LLMMessage
except ImportError as e:
    pytest.skip(f"Integration imports not available: {e}", allow_module_level=True)


class TestLiteLLMProvider:
    """Test the LiteLLMProvider class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.7,
            max_tokens=100
        )

    def test_init(self):
        """Test provider initialization."""
        provider = LiteLLMProvider(self.config)

        assert provider.config == self.config
        assert provider.provider == "openai"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.api_key == "test-key"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 100

    def test_init_with_kwargs(self):
        """Test provider initialization with additional kwargs."""
        provider = LiteLLMProvider(
            self.config,
            custom_param="value",
            timeout=30
        )

        assert provider.config == self.config
        assert hasattr(provider, '_additional_kwargs')
        assert provider._additional_kwargs.get('custom_param') == 'value'
        assert provider._additional_kwargs.get('timeout') == 30

    @patch('integrations.litellm_provider.litellm')
    def test_validate_config_success(self, mock_litellm):
        """Test successful config validation."""
        mock_litellm.validate_environment.return_value = True
        mock_litellm.get_supported_openai_params.return_value = [
            'temperature', 'max_tokens', 'top_p'
        ]

        provider = LiteLLMProvider(self.config)
        result = provider.validate_config()

        assert result is True

    @patch('integrations.litellm_provider.litellm')
    def test_validate_config_failure(self, mock_litellm):
        """Test config validation failure."""
        mock_litellm.validate_environment.side_effect = Exception("Invalid API key")

        provider = LiteLLMProvider(self.config)
        result = provider.validate_config()

        assert result is False

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_litellm):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        provider = LiteLLMProvider(self.config)

        messages = [
            LLMMessage(role="user", content="Test prompt")
        ]

        response = await provider.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Generated text"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage['prompt_tokens'] == 10
        assert response.usage['completion_tokens'] == 5
        assert response.usage['total_tokens'] == 15

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_generate_with_system_message(self, mock_litellm):
        """Test generation with system message."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response with system"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 23

        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        provider = LiteLLMProvider(self.config)

        messages = [
            LLMMessage(role="system", content="You are a helpful assistant"),
            LLMMessage(role="user", content="Hello")
        ]

        response = await provider.generate(messages)

        assert response.content == "Response with system"

        # Verify correct message format was passed
        call_args = mock_litellm.acompletion.call_args
        passed_messages = call_args[1]['messages']
        assert len(passed_messages) == 2
        assert passed_messages[0]['role'] == 'system'
        assert passed_messages[1]['role'] == 'user'

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, mock_litellm):
        """Test error handling during generation."""
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("API Error"))

        provider = LiteLLMProvider(self.config)

        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(Exception) as exc_info:
            await provider.generate(messages)

        assert "API Error" in str(exc_info.value)

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_generate_stream_success(self, mock_litellm):
        """Test successful streaming generation."""
        # Mock streaming response
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].finish_reason = None

        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta.content = " world"
        mock_chunk2.choices[0].finish_reason = None

        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock()]
        mock_chunk3.choices[0].delta.content = None
        mock_chunk3.choices[0].finish_reason = "stop"

        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3

        mock_litellm.acompletion = AsyncMock(return_value=mock_stream())

        provider = LiteLLMProvider(self.config)

        messages = [LLMMessage(role="user", content="Test")]

        chunks = []
        async for chunk in provider.generate_stream(messages):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0] == "Hello"
        assert chunks[1] == " world"
        assert chunks[2] == ""  # Final chunk with finish_reason

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_generate_stream_error(self, mock_litellm):
        """Test error handling in streaming."""
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("Stream error"))

        provider = LiteLLMProvider(self.config)

        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(Exception) as exc_info:
            async for chunk in provider.generate_stream(messages):
                pass

        assert "Stream error" in str(exc_info.value)

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_batch_generate(self, mock_litellm):
        """Test batch generation."""
        # Mock responses for batch
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message.content = "Response 1"
        mock_response1.usage = Mock()
        mock_response1.usage.prompt_tokens = 5
        mock_response1.usage.completion_tokens = 3
        mock_response1.usage.total_tokens = 8

        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message.content = "Response 2"
        mock_response2.usage = Mock()
        mock_response2.usage.prompt_tokens = 7
        mock_response2.usage.completion_tokens = 4
        mock_response2.usage.total_tokens = 11

        mock_litellm.acompletion = AsyncMock(side_effect=[mock_response1, mock_response2])

        provider = LiteLLMProvider(self.config)

        batch_messages = [
            [LLMMessage(role="user", content="Prompt 1")],
            [LLMMessage(role="user", content="Prompt 2")]
        ]

        responses = await provider.batch_generate(batch_messages)

        assert len(responses) == 2
        assert responses[0].content == "Response 1"
        assert responses[1].content == "Response 2"
        assert responses[0].usage['total_tokens'] == 8
        assert responses[1].usage['total_tokens'] == 11

    @patch('integrations.litellm_provider.litellm')
    def test_get_supported_models(self, mock_litellm):
        """Test getting supported models."""
        mock_litellm.model_list = ["gpt-3.5-turbo", "gpt-4", "claude-3"]

        provider = LiteLLMProvider(self.config)
        models = provider.get_supported_models()

        assert "gpt-3.5-turbo" in models
        assert "gpt-4" in models
        assert "claude-3" in models

    @patch('integrations.litellm_provider.litellm')
    def test_estimate_cost(self, mock_litellm):
        """Test cost estimation."""
        mock_litellm.completion_cost = Mock(return_value=0.002)

        provider = LiteLLMProvider(self.config)

        usage = {
            'prompt_tokens': 100,
            'completion_tokens': 50,
            'total_tokens': 150
        }

        cost = provider.estimate_cost(usage)

        assert cost == 0.002
        mock_litellm.completion_cost.assert_called_once()

    def test_estimate_cost_no_usage(self):
        """Test cost estimation with no usage data."""
        provider = LiteLLMProvider(self.config)
        cost = provider.estimate_cost(None)

        assert cost == 0.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        provider = LiteLLMProvider(self.config)

        data = provider.to_dict()

        assert data['provider'] == 'openai'
        assert data['model'] == 'gpt-3.5-turbo'
        assert data['api_key'] == 'test-key'
        assert data['temperature'] == 0.7
        assert data['max_tokens'] == 100

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'provider': 'anthropic',
            'model': 'claude-3',
            'api_key': 'claude-key',
            'temperature': 0.5,
            'max_tokens': 200
        }

        provider = LiteLLMProvider.from_dict(data)

        assert provider.provider == 'anthropic'
        assert provider.model == 'claude-3'
        assert provider.api_key == 'claude-key'
        assert provider.temperature == 0.5
        assert provider.max_tokens == 200


class TestLiteLLMProviderIntegration:
    """Integration tests for LiteLLMProvider."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key"
        )

    @patch('integrations.litellm_provider.litellm')
    def test_provider_lifecycle(self, mock_litellm):
        """Test complete provider lifecycle."""
        # Setup mocks
        mock_litellm.validate_environment.return_value = True
        mock_litellm.get_supported_openai_params.return_value = ['temperature']
        mock_litellm.model_list = ["gpt-3.5-turbo"]

        # Create provider
        provider = LiteLLMProvider(self.config)

        # Validate
        assert provider.validate_config() is True

        # Get models
        models = provider.get_supported_models()
        assert "gpt-3.5-turbo" in models

        # Serialize/deserialize
        data = provider.to_dict()
        new_provider = LiteLLMProvider.from_dict(data)

        assert new_provider.model == provider.model
        assert new_provider.provider == provider.provider

    @patch('integrations.litellm_provider.litellm')
    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_litellm):
        """Test error recovery scenarios."""
        provider = LiteLLMProvider(self.config)

        # Test retry on temporary failure
        mock_litellm.acompletion = AsyncMock(side_effect=[
            Exception("Temporary failure"),
            Mock(choices=[Mock(message=Mock(content="Success"))])
        ])

        messages = [LLMMessage(role="user", content="Test")]

        # First call should fail
        with pytest.raises(Exception):
            await provider.generate(messages)

        # Reset mock for second call
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_response.usage.total_tokens = 8

        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        # Second call should succeed
        response = await provider.generate(messages)
        assert response.content == "Success"


class TestLiteLLMProviderEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_config(self):
        """Test handling of invalid configuration."""
        # Missing required fields
        with pytest.raises((ValueError, TypeError)):
            LiteLLMProvider(None)

    def test_empty_messages(self):
        """Test handling of empty message list."""
        config = LLMConfig(provider="openai", model="gpt-3.5-turbo")
        provider = LiteLLMProvider(config)

        # Should handle empty messages gracefully
        with patch('integrations.litellm_provider.litellm') as mock_litellm:
            mock_litellm.acompletion = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=""))],
                usage=Mock(prompt_tokens=0, completion_tokens=0, total_tokens=0)
            ))

            async def test_empty():
                response = await provider.generate([])
                assert response.content == ""

            asyncio.run(test_empty())

    def test_malformed_response(self):
        """Test handling of malformed API responses."""
        config = LLMConfig(provider="openai", model="gpt-3.5-turbo")
        provider = LiteLLMProvider(config)

        with patch('integrations.litellm_provider.litellm') as mock_litellm:
            # Mock malformed response
            mock_response = Mock()
            mock_response.choices = []  # Empty choices
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            async def test_malformed():
                messages = [LLMMessage(role="user", content="Test")]
                with pytest.raises((IndexError, AttributeError)):
                    await provider.generate(messages)

            asyncio.run(test_malformed())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])