"""
LLM-Based MCP Selector

Uses small language models to intelligently select MCPs based on user queries.
Provides better accuracy than regex matching by understanding context and intent.
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SelectionResult:
    """Result from LLM-based MCP selection."""

    reasoning: str
    required_capabilities: List[str]
    recommended_mcps: List[str]
    confidence: float
    fallback_used: bool = False
    latency_ms: int = 0


class LLMSelector:
    """
    Uses a small LLM to intelligently select MCPs based on user queries.

    Supports:
    - Local models: Phi-3, Llama 3.2, Gemma 2 (via Ollama)
    - API models: GPT-4o-mini, Claude Haiku, Gemini Flash
    - Automatic fallback to regex on errors
    """

    def __init__(
        self,
        model_type: str = "ollama",
        model_name: str = "phi3:mini",
        fallback_to_regex: bool = True,
        timeout_seconds: int = 5,
        use_few_shot: bool = True
    ):
        """
        Initialize LLM selector.

        Args:
            model_type: "ollama", "openai", "anthropic", "google"
            model_name: Specific model to use
            fallback_to_regex: Fall back to regex if LLM fails
            timeout_seconds: Max time for LLM inference
            use_few_shot: Use few-shot prompting for better accuracy
        """
        self.model_type = model_type
        self.model_name = model_name
        self.fallback_to_regex = fallback_to_regex
        self.timeout = timeout_seconds
        self.use_few_shot = use_few_shot

        # Initialize client
        self.client = self._initialize_client()

        # Regex fallback engine
        self.regex_fallback = None
        if fallback_to_regex:
            try:
                from .mcp_selection_engine import MCPSelectionEngine
                self.regex_fallback = MCPSelectionEngine(use_embeddings=False)
            except Exception as e:
                logger.warning(f"Could not initialize regex fallback: {e}")

    def _initialize_client(self) -> Optional[Any]:
        """Initialize LLM client based on model type."""
        try:
            if self.model_type == "ollama":
                import ollama
                client = ollama.Client()
                logger.info(f"Initialized Ollama client with model: {self.model_name}")
                return client

            elif self.model_type == "openai":
                from openai import OpenAI
                client = OpenAI()
                logger.info(f"Initialized OpenAI client with model: {self.model_name}")
                return client

            elif self.model_type == "anthropic":
                from anthropic import Anthropic
                client = Anthropic()
                logger.info(f"Initialized Anthropic client with model: {self.model_name}")
                return client

            elif self.model_type == "google":
                import google.generativeai as genai
                client = genai
                logger.info(f"Initialized Google AI client with model: {self.model_name}")
                return client

            else:
                logger.error(f"Unknown model type: {self.model_type}")
                return None

        except ImportError as e:
            logger.error(f"Failed to import {self.model_type} SDK: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize {self.model_type} client: {e}")
            return None

    async def select_mcps(
        self,
        user_query: str,
        available_mcps: Dict[str, Dict],
        agent_permissions: Set[str],
        max_mcps: int = 3
    ) -> SelectionResult:
        """
        Use LLM to select MCPs for a user query.

        Args:
            user_query: User's question or request
            available_mcps: Dict of {mcp_name: {description, capabilities, ...}}
            agent_permissions: Agent's permissions
            max_mcps: Maximum MCPs to select

        Returns:
            SelectionResult with recommended MCPs and reasoning
        """
        start_time = datetime.now()

        try:
            # Build prompt
            prompt = self._build_selection_prompt(
                user_query,
                available_mcps,
                max_mcps
            )

            # Call LLM with timeout
            response = await asyncio.wait_for(
                self._call_llm(prompt),
                timeout=self.timeout
            )

            # Parse structured output
            result = self._parse_llm_response(response)

            # Filter by permissions
            result.recommended_mcps = [
                mcp for mcp in result.recommended_mcps
                if mcp in available_mcps and self._check_permissions(
                    available_mcps[mcp],
                    agent_permissions
                )
            ]

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result.latency_ms = latency_ms

            logger.info(
                f"LLM selected {len(result.recommended_mcps)} MCPs "
                f"(confidence: {result.confidence:.2f}, latency: {latency_ms}ms)"
            )

            return result

        except asyncio.TimeoutError:
            logger.warning(f"LLM selection timed out after {self.timeout}s")
            return await self._fallback_selection(
                user_query,
                available_mcps,
                agent_permissions,
                max_mcps
            )

        except Exception as e:
            logger.warning(f"LLM selection failed: {e}")
            if self.fallback_to_regex:
                return await self._fallback_selection(
                    user_query,
                    available_mcps,
                    agent_permissions,
                    max_mcps
                )
            else:
                # Return empty result
                return SelectionResult(
                    reasoning=f"LLM error: {str(e)}",
                    required_capabilities=[],
                    recommended_mcps=[],
                    confidence=0.0,
                    fallback_used=False
                )

    def _build_selection_prompt(
        self,
        user_query: str,
        available_mcps: Dict[str, Dict],
        max_mcps: int
    ) -> str:
        """Build prompt for LLM to select MCPs."""

        # Format MCP descriptions
        mcp_descriptions = []
        for name, metadata in available_mcps.items():
            caps = metadata.get('capabilities', [])
            desc = metadata.get('description', '')
            mcp_descriptions.append(
                f"- **{name}**: {desc} (capabilities: {', '.join(caps)})"
            )

        mcp_list = "\n".join(mcp_descriptions)

        if self.use_few_shot:
            # Few-shot prompting for better accuracy
            prompt = f"""You are a tool selection assistant that helps choose the right tools (MCPs) to answer user queries.

**Available Tools:**
{mcp_list}

**Examples:**

1. User Query: "What's the weather in New York?"
   Response: {{"reasoning": "User needs current weather data for NYC", "required_capabilities": ["weather", "forecast"], "recommended_mcps": ["weather"], "confidence": 0.95}}

2. User Query: "Calculate the average sales from the database"
   Response: {{"reasoning": "Needs to query database and perform calculation", "required_capabilities": ["data", "computation"], "recommended_mcps": ["database", "calculator"], "confidence": 0.9}}

3. User Query: "Hello, how are you today?"
   Response: {{"reasoning": "Just a greeting, no tools needed", "required_capabilities": [], "recommended_mcps": [], "confidence": 1.0}}

4. User Query: "Don't send me email notifications"
   Response: {{"reasoning": "User declining service, no action needed", "required_capabilities": [], "recommended_mcps": [], "confidence": 0.95}}

5. User Query: "Will I need an umbrella tomorrow?"
   Response: {{"reasoning": "Implicit request for rain forecast", "required_capabilities": ["weather", "forecast"], "recommended_mcps": ["weather"], "confidence": 0.9}}

**Now analyze this query:**

User Query: "{user_query}"

**Instructions:**
1. Select at most {max_mcps} tools
2. Only select tools that are DIRECTLY needed
3. Handle implicit requests (e.g., "umbrella" implies weather)
4. Handle negation (e.g., "don't send" means NO email tool)
5. Confidence: 0.0-1.0 based on certainty

**Response (JSON only, no markdown):**"""

        else:
            # Zero-shot prompting
            prompt = f"""You are a tool selection assistant.

**Available Tools:**
{mcp_list}

**User Query:**
"{user_query}"

**Task:**
Analyze the query and select which tools (if any) are needed to answer it.
Select at most {max_mcps} tools.

**Output Format (JSON only, no markdown):**
{{
  "reasoning": "Brief explanation",
  "required_capabilities": ["capability1", "capability2"],
  "recommended_mcps": ["tool1", "tool2"],
  "confidence": 0.95
}}

**Response:**"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM and return response."""
        if not self.client:
            raise RuntimeError("LLM client not initialized")

        if self.model_type == "ollama":
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistency
                    "num_predict": 500,
                    "stop": ["\n\n"]  # Stop at double newline
                }
            )
            return response['response']

        elif self.model_type == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a tool selection expert. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content

        elif self.model_type == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        elif self.model_type == "google":
            model = self.client.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 500
                }
            )
            return response.text

        raise ValueError(f"Unsupported model type: {self.model_type}")

    def _parse_llm_response(self, response: str) -> SelectionResult:
        """Parse LLM JSON response into SelectionResult."""
        # Clean response (remove markdown code blocks if present)
        response = response.strip()

        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            # Try to extract JSON between any code blocks
            parts = response.split("```")
            if len(parts) >= 2:
                response = parts[1].strip()

        # Remove leading/trailing whitespace
        response = response.strip()

        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response}")
            # Try to extract JSON object from text
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise

        return SelectionResult(
            reasoning=data.get("reasoning", ""),
            required_capabilities=data.get("required_capabilities", []),
            recommended_mcps=data.get("recommended_mcps", []),
            confidence=float(data.get("confidence", 0.5)),
            fallback_used=False
        )

    def _check_permissions(
        self,
        mcp_metadata: Dict,
        agent_permissions: Set[str]
    ) -> bool:
        """Check if agent has required permissions for MCP."""
        if "*" in agent_permissions:
            return True

        required = mcp_metadata.get("required_permissions", [])
        for perm in required:
            if perm in agent_permissions:
                continue

            # Check category wildcard (e.g., "read:*")
            category = perm.split(":")[0] if ":" in perm else perm
            if f"{category}:*" in agent_permissions:
                continue

            # Missing permission
            return False

        return True

    async def _fallback_selection(
        self,
        user_query: str,
        available_mcps: Dict,
        agent_permissions: Set[str],
        max_mcps: int
    ) -> SelectionResult:
        """Fallback to regex-based selection when LLM fails."""
        if not self.regex_fallback:
            logger.error("Regex fallback not available")
            return SelectionResult(
                reasoning="No fallback available (LLM failed)",
                required_capabilities=[],
                recommended_mcps=[],
                confidence=0.0,
                fallback_used=True
            )

        logger.info("Using regex fallback for MCP selection")

        # Load available MCPs into regex engine
        for name, metadata in available_mcps.items():
            from .mcp_selection_engine import MCPMetadata
            mcp_meta = MCPMetadata(
                name=name,
                description=metadata.get('description', ''),
                categories=metadata.get('categories', []),
                capabilities=metadata.get('capabilities', []),
                required_permissions=metadata.get('required_permissions', []),
                risk_level=metadata.get('risk_level', 'medium'),
                connection=metadata.get('connection', {})
            )
            self.regex_fallback.register_mcp(mcp_meta)

        # Create temporary session for regex selection
        session_id = f"fallback-{datetime.now().timestamp()}"
        self.regex_fallback.create_session(
            agent_id="fallback",
            session_id=session_id,
            baseline_mcps=[]
        )

        # Use regex selection
        regex_selected = await self.regex_fallback.select_mcps_for_query(
            user_query=user_query,
            session_id=session_id,
            agent_permissions=agent_permissions,
            max_new_mcps=max_mcps,
            confidence_threshold=0.3
        )

        # Clean up session
        self.regex_fallback.close_session(session_id)

        return SelectionResult(
            reasoning="Regex fallback (LLM unavailable)",
            required_capabilities=[],
            recommended_mcps=regex_selected,
            confidence=0.6,  # Lower confidence for regex
            fallback_used=True
        )
