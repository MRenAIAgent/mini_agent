"""
LiteLLM provider for unified LLM access.

This module provides a unified interface to 100+ LLM providers through LiteLLM,
including OpenAI, Anthropic, Cohere, Ollama, and many others.
Constitutional compliance: simple interface wrapping LiteLLM.
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncIterator, Union
from datetime import datetime
import json

try:
    import litellm
    from litellm import acompletion, ModelResponse
except ImportError:
    litellm = None
    acompletion = None
    ModelResponse = None


class LiteLLMProvider:
    """
    Unified LLM provider using LiteLLM.

    Provides access to 100+ LLM providers through a single interface.
    Constitutional compliance: simple wrapper around LiteLLM.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LiteLLM provider.

        Args:
            config: Configuration dict with provider, model, api_key, etc.
        """
        if litellm is None:
            raise ImportError("litellm package not installed. Run: pip install litellm")

        self.config = config
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.stream = config.get("stream", False)

        # Set up LiteLLM configuration
        self._setup_litellm()

    def _setup_litellm(self) -> None:
        """Set up LiteLLM configuration and API keys."""
        # Set API key based on provider
        if self.api_key:
            if self.provider == "openai":
                import os
                os.environ["OPENAI_API_KEY"] = self.api_key
            elif self.provider == "anthropic":
                import os
                os.environ["ANTHROPIC_API_KEY"] = self.api_key
            elif self.provider == "cohere":
                import os
                os.environ["COHERE_API_KEY"] = self.api_key
            # Add more providers as needed

        # Set custom API base if provided
        if self.api_base:
            litellm.api_base = self.api_base

        # Configure LiteLLM settings
        litellm.set_verbose = False  # Reduce logging unless debugging

    async def call(self, prompt: str, **kwargs) -> str:
        """
        Make a completion call to the LLM.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            LLM response text
        """
        try:
            # Prepare messages format
            messages = [{"role": "user", "content": prompt}]

            # Override config with kwargs
            call_config = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False  # Non-streaming call
            }

            # Add provider-specific configuration
            if self.provider == "anthropic":
                call_config["model"] = f"anthropic/{self.model}"
            elif self.provider == "cohere":
                call_config["model"] = f"cohere/{self.model}"
            elif self.provider == "ollama":
                call_config["model"] = f"ollama/{self.model}"

            # Make the call
            response = await acompletion(**call_config)

            # Extract content from response
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content or ""
            else:
                return str(response)

        except Exception as e:
            raise RuntimeError(f"LiteLLM call failed: {e}")

    async def stream_call(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Make a streaming completion call to the LLM.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Chunks of the response
        """
        try:
            # Prepare messages format
            messages = [{"role": "user", "content": prompt}]

            # Override config with kwargs
            call_config = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": True  # Enable streaming
            }

            # Add provider-specific configuration
            if self.provider == "anthropic":
                call_config["model"] = f"anthropic/{self.model}"
            elif self.provider == "cohere":
                call_config["model"] = f"cohere/{self.model}"
            elif self.provider == "ollama":
                call_config["model"] = f"ollama/{self.model}"

            # Make the streaming call
            response = await acompletion(**call_config)

            # Stream the response
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content

        except Exception as e:
            # Fallback to non-streaming if streaming fails
            response = await self.call(prompt, **kwargs)
            words = response.split()
            for word in words:
                yield word + " "

    async def call_with_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Make a completion call with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters

        Returns:
            LLM response text
        """
        try:
            # Override config with kwargs
            call_config = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }

            # Add provider-specific configuration
            if self.provider == "anthropic":
                call_config["model"] = f"anthropic/{self.model}"
            elif self.provider == "cohere":
                call_config["model"] = f"cohere/{self.model}"
            elif self.provider == "ollama":
                call_config["model"] = f"ollama/{self.model}"

            # Make the call
            response = await acompletion(**call_config)

            # Extract content from response
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content or ""
            else:
                return str(response)

        except Exception as e:
            raise RuntimeError(f"LiteLLM conversation call failed: {e}")

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for the provider.

        Returns:
            List of model names
        """
        # This would ideally query LiteLLM for supported models
        # For now, return common models by provider
        model_map = {
            "openai": [
                "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo",
                "gpt-4-32k", "gpt-3.5-turbo-16k"
            ],
            "anthropic": [
                "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
                "claude-2", "claude-instant-1"
            ],
            "cohere": [
                "command", "command-nightly", "command-light",
                "command-light-nightly"
            ],
            "ollama": [
                "llama2", "codellama", "mistral", "neural-chat"
            ]
        }

        return model_map.get(self.provider, [self.model])

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current provider configuration.

        Returns:
            Provider information dict
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream_enabled": self.stream,
            "api_base": self.api_base,
            "has_api_key": bool(self.api_key)
        }

    async def validate_connection(self) -> bool:
        """
        Validate that the provider connection is working.

        Returns:
            True if connection is valid
        """
        try:
            # Make a simple test call
            test_response = await self.call("Test connection", max_tokens=5)
            return len(test_response) > 0
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Simple approximation: ~4 characters per token for English.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate estimated cost for the API call.
        Note: This is a rough approximation and may not be accurate.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Rough cost estimates (prices change frequently)
        cost_per_1k_tokens = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }

        model_costs = cost_per_1k_tokens.get(self.model, {"input": 0.001, "output": 0.002})

        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]

        return input_cost + output_cost

    async def batch_call(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Make multiple calls in parallel (simple batching).

        Args:
            prompts: List of prompts to process
            **kwargs: Additional parameters

        Returns:
            List of responses
        """
        try:
            # Simple parallel processing
            tasks = [self.call(prompt, **kwargs) for prompt in prompts]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error messages
            results = []
            for response in responses:
                if isinstance(response, Exception):
                    results.append(f"Error: {response}")
                else:
                    results.append(response)

            return results
        except Exception as e:
            raise RuntimeError(f"Batch call failed: {e}")


# Utility functions for LiteLLM configuration
def create_provider_from_config(config: Dict[str, Any]) -> LiteLLMProvider:
    """
    Create LiteLLM provider from configuration.

    Args:
        config: Provider configuration

    Returns:
        Configured LiteLLM provider
    """
    return LiteLLMProvider(config)


def list_supported_providers() -> List[str]:
    """
    List all providers supported by LiteLLM.

    Returns:
        List of provider names
    """
    return [
        "openai", "anthropic", "cohere", "ollama", "azure", "vertex_ai",
        "bedrock", "palm", "replicate", "huggingface", "together_ai"
    ]


def get_provider_template(provider: str) -> Dict[str, Any]:
    """
    Get configuration template for a provider.

    Args:
        provider: Provider name

    Returns:
        Configuration template
    """
    templates = {
        "openai": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "your-openai-api-key",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "anthropic": {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "api_key": "your-anthropic-api-key",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "ollama": {
            "provider": "ollama",
            "model": "llama2",
            "api_base": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }

    return templates.get(provider, {
        "provider": provider,
        "model": "default-model",
        "api_key": "your-api-key",
        "temperature": 0.7,
        "max_tokens": 1000
    })