"""
LLM Provider Integration Interfaces

Standardized interfaces for integrating different LLM providers
(OpenAI, Anthropic, local models, etc.) with the core agent.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator, Union, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime

# Type aliases for backward compatibility
LLMFunction = Callable[[str], Awaitable[str]]


@dataclass
class LLMResponse:
    """Standard LLM response format."""

    content: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LLMConfig:
    """LLM provider configuration with LiteLLM support."""

    provider: str  # "openai", "anthropic", "local", etc.
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 30.0
    retry_attempts: int = 3
    streaming: bool = False
    stream: bool = False  # Alias for streaming (LiteLLM compatibility)
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}

        # Sync streaming and stream fields for backward compatibility
        if self.stream and not self.streaming:
            self.streaming = self.stream
        elif self.streaming and not self.stream:
            self.stream = self.streaming

        # Validate configuration
        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ValueError("temperature must be between 0.0 and 1.0")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LiteLLM."""
        config_dict = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "stream": self.stream
        }

        if self.api_key:
            config_dict["api_key"] = self.api_key

        if self.base_url:
            config_dict["api_base"] = self.base_url

        if self.max_tokens:
            config_dict["max_tokens"] = self.max_tokens

        # Add extra parameters
        config_dict.update(self.extra_params)

        return config_dict

    def to_litellm_config(self) -> Dict[str, Any]:
        """Convert to LiteLLM-specific configuration format."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LLMConfig':
        """Create LLMConfig from dictionary."""
        # Extract known fields
        known_fields = {
            'provider', 'model', 'api_key', 'base_url', 'temperature',
            'max_tokens', 'timeout', 'retry_attempts', 'streaming', 'stream'
        }

        config_args = {}
        extra_params = {}

        for key, value in config_dict.items():
            if key in known_fields:
                # Handle field name aliases
                if key == 'api_base':
                    config_args['base_url'] = value
                else:
                    config_args[key] = value
            else:
                extra_params[key] = value

        if extra_params:
            config_args['extra_params'] = extra_params

        return cls(**config_args)

    def to_function(self) -> 'LLMFunction':
        """
        Convert LLMConfig to callable function for backward compatibility.
        Returns a function that can be used like the legacy llm_function parameter.
        """
        try:
            from .litellm_provider import LiteLLMProvider
        except ImportError:
            raise ImportError("LiteLLM provider not available")

        provider = LiteLLMProvider(self.to_dict())

        async def llm_function(prompt: str) -> str:
            """Backward-compatible LLM function."""
            return await provider.call(prompt)

        return llm_function

    def __call__(self, prompt: str):
        """
        Make LLMConfig directly callable for backward compatibility.
        """
        return self.to_function()(prompt)

    def get_supported_providers(self) -> List[str]:
        """Get list of supported providers."""
        return [
            "openai", "anthropic", "cohere", "ollama", "azure", "vertex_ai",
            "bedrock", "palm", "replicate", "huggingface", "together_ai"
        ]

    def validate_provider(self) -> bool:
        """Validate that the provider is supported."""
        return self.provider in self.get_supported_providers()

    def estimate_cost(self, input_text: str, output_text: str) -> float:
        """
        Estimate cost for the API call.
        Simple approximation based on token counts.
        """
        input_tokens = len(input_text) // 4  # Rough approximation
        output_tokens = len(output_text) // 4

        # Basic cost estimates (these change frequently)
        cost_per_1k = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.001,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
        }

        rate = cost_per_1k.get(self.model, 0.001)
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * rate


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.call_count = 0
        self.total_tokens = 0
        self.total_latency = 0.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            Response chunks
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate the connection to the LLM provider.

        Returns:
            True if connection is valid
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Model information dictionary
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get provider usage statistics."""
        avg_latency = (
            self.total_latency / self.call_count
            if self.call_count > 0 else 0.0
        )

        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "average_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency
        }

    def _update_stats(self, response: LLMResponse) -> None:
        """Update internal statistics."""
        self.call_count += 1
        self.total_tokens += response.tokens_used
        self.total_latency += response.latency_ms


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and development."""

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                provider="mock",
                model="mock-model"
            )
        super().__init__(config)
        self.responses = []
        self.default_response = "I'm a mock LLM response."

    def set_responses(self, responses: List[str]) -> None:
        """Set predetermined responses."""
        self.responses = responses

    def set_default_response(self, response: str) -> None:
        """Set default response when no predetermined responses."""
        self.default_response = response

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate mock response."""
        import time
        start_time = time.time()

        # Use predetermined response if available
        if self.responses:
            content = self.responses.pop(0)
        else:
            content = self._generate_contextual_response(prompt, system_prompt)

        response = LLMResponse(
            content=content,
            model=self.config.model,
            tokens_used=len(content.split()),
            latency_ms=(time.time() - start_time) * 1000,
            finish_reason="stop"
        )

        self._update_stats(response)
        return response

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate mock streaming response."""
        response = await self.generate(prompt, system_prompt, **kwargs)

        # Split response into chunks
        words = response.content.split()
        for word in words:
            yield word + " "

    async def validate_connection(self) -> bool:
        """Mock connection is always valid."""
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            "name": self.config.model,
            "provider": "mock",
            "context_length": 4096,
            "capabilities": ["text_generation", "streaming"]
        }

    def _generate_contextual_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate contextual mock response based on prompt."""
        prompt_lower = prompt.lower()

        # Math calculations
        if any(op in prompt_lower for op in ['+', '-', '*', '/', 'calculate', 'what is']):
            return self._handle_math_prompt(prompt)

        # ReAct patterns
        if 'action:' in prompt_lower or 'thought:' in prompt_lower:
            return self._handle_react_prompt(prompt)

        # Tool usage
        if 'tool' in prompt_lower:
            return "I can help you use tools. What tool would you like me to use?"

        # Default conversational response
        return self.default_response

    def _handle_math_prompt(self, prompt: str) -> str:
        """Handle mathematical prompts."""
        import re

        # Extract simple math expressions
        math_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
        match = re.search(math_pattern, prompt)

        if match:
            num1, operator, num2 = match.groups()
            num1, num2 = float(num1), float(num2)

            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                result = num1 / num2 if num2 != 0 else "undefined"

            return f"The answer is {result}."

        return "I can help with mathematical calculations."

    def _handle_react_prompt(self, prompt: str) -> str:
        """Handle ReAct-style prompts."""
        if 'calculator' in prompt.lower():
            return """Thought: I need to use the calculator tool.

Action: calculator
Action Input: {"expression": "2 + 3"}"""

        return """Thought: I need to think about this step by step.

Final Answer: I understand you're using ReAct format. How can I help?"""


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    _providers = {
        "mock": MockLLMProvider
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """Register a new LLM provider."""
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(cls, config: LLMConfig) -> LLMProvider:
        """Create an LLM provider instance."""
        provider_class = cls._providers.get(config.provider)

        if not provider_class:
            raise ValueError(f"Unknown LLM provider: {config.provider}")

        return provider_class(config)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List available providers."""
        return list(cls._providers.keys())


# Utility function for easy LLM integration
async def create_llm_function(config: LLMConfig) -> callable:
    """
    Create an LLM function compatible with CoreAgent.

    Args:
        config: LLM provider configuration

    Returns:
        Async function that takes a prompt and returns a response
    """
    provider = LLMProviderFactory.create_provider(config)

    async def llm_function(prompt: str) -> str:
        response = await provider.generate(prompt)
        return response.content

    return llm_function