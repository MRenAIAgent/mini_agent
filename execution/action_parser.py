"""Parser for extracting actions from LLM responses."""

import re
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedAction:
    """Container for parsed action information."""

    action: str
    action_input: Dict[str, Any]
    raw_text: str
    confidence: float = 1.0  # Confidence in the parsing (0-1)


class ActionParser:
    """Parser for extracting actions and inputs from LLM responses."""

    def __init__(self):
        # Patterns for different action formats
        self.action_patterns = [
            # Standard ReAct format: Action: action_name
            r"Action:\s*([^\n]+)",
            # Alternative format: **Action:** action_name
            r"\*\*Action:\*\*\s*([^\n]+)",
            # Function call format: action_name(...)
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        ]

        self.input_patterns = [
            # Standard format: Action Input: {...}
            r"Action Input:\s*({.*?})",
            # Alternative format: **Action Input:** {...}
            r"\*\*Action Input:\*\*\s*({.*?})",
            # JSON format: {"key": "value"}
            r"({.*?})",
            # Simple key-value: key=value
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^\n,]+)",
        ]

    def parse_action(self, text: str) -> Optional[ParsedAction]:
        """
        Parse action from LLM response text.

        Args:
            text: Raw text from LLM response

        Returns:
            ParsedAction if successful, None if no action found
        """
        # Clean the text
        text = text.strip()

        # Try to find action
        action = self._extract_action(text)
        if not action:
            return None

        # Try to find action input
        action_input = self._extract_action_input(text, action)

        # Determine confidence based on format
        confidence = self._calculate_confidence(text, action, action_input)

        return ParsedAction(
            action=action,
            action_input=action_input,
            raw_text=text,
            confidence=confidence
        )

    def _extract_action(self, text: str) -> Optional[str]:
        """Extract action name from text."""
        for pattern in self.action_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                action = match.group(1).strip()
                # Clean up common artifacts
                action = action.replace("*", "").replace(":", "").strip()
                if action and not action.lower().startswith("final"):
                    return action

        return None

    def _extract_action_input(self, text: str, action: str) -> Dict[str, Any]:
        """Extract action input from text."""
        # Try JSON format first
        for pattern in self.input_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle key=value patterns
                    key, value = match
                    return {key: value.strip().strip('"\'').strip()}
                else:
                    # Try to parse as JSON
                    try:
                        input_dict = json.loads(match)
                        if isinstance(input_dict, dict):
                            return input_dict
                    except (json.JSONDecodeError, ValueError):
                        # Try to extract quoted strings
                        if match.startswith('"') and match.endswith('"'):
                            return {"input": match.strip('"')}

        # Fallback: look for common patterns
        return self._extract_fallback_input(text, action)

    def _extract_fallback_input(self, text: str, action: str) -> Dict[str, Any]:
        """Fallback extraction for action inputs."""
        # Look for quoted strings after the action
        quoted_pattern = r'["\']([^"\']+)["\']'
        quotes = re.findall(quoted_pattern, text)

        if quotes:
            # Use the last quoted string as input
            return {"input": quotes[-1]}

        # Look for text in parentheses
        paren_pattern = r'\(([^)]+)\)'
        parens = re.findall(paren_pattern, text)

        if parens:
            paren_text = parens[-1].strip()
            # Try to parse as JSON
            try:
                return json.loads(f'{{"{paren_text}"}}')
            except:
                return {"input": paren_text}

        # Look for text after colon
        colon_pattern = f"{re.escape(action)}:?\\s*([^\n]+)"
        colon_match = re.search(colon_pattern, text, re.IGNORECASE)
        if colon_match:
            colon_text = colon_match.group(1).strip()
            if colon_text and not colon_text.lower().startswith("action"):
                return {"input": colon_text}

        return {}

    def _calculate_confidence(self, text: str, action: str, action_input: Dict[str, Any]) -> float:
        """Calculate confidence in the parsing."""
        confidence = 0.5  # Base confidence

        # Boost confidence for standard formats
        if "Action:" in text:
            confidence += 0.3
        if "Action Input:" in text:
            confidence += 0.3

        # Boost confidence for valid JSON input
        if action_input and len(action_input) > 0:
            confidence += 0.2

        # Reduce confidence for unclear patterns
        if action.lower() in ["thought", "thinking", "consider"]:
            confidence -= 0.3

        return min(1.0, max(0.0, confidence))

    def is_final_answer(self, text: str) -> bool:
        """Check if the text contains a final answer."""
        final_patterns = [
            r"Final Answer:",
            r"Answer:",
            r"Final Response:",
            r"Conclusion:",
            r"Result:",
        ]

        for pattern in final_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def extract_final_answer(self, text: str) -> Optional[str]:
        """Extract final answer from text."""
        if not self.is_final_answer(text):
            return None

        # Patterns to extract final answer
        patterns = [
            r"Final Answer:\s*(.+?)(?:\n|$)",
            r"Answer:\s*(.+?)(?:\n|$)",
            r"Final Response:\s*(.+?)(?:\n|$)",
            r"Conclusion:\s*(.+?)(?:\n|$)",
            r"Result:\s*(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                # Clean up common artifacts
                answer = answer.replace("*", "").strip()
                if answer:
                    return answer

        # Fallback: return text after the last colon
        lines = text.split('\n')
        for line in reversed(lines):
            if ':' in line:
                answer = line.split(':', 1)[1].strip()
                if answer:
                    return answer

        return None

    def validate_action_format(self, text: str) -> bool:
        """Validate if text follows proper ReAct format."""
        # Should contain thought
        if not any(keyword in text.lower() for keyword in ["thought", "think", "reasoning"]):
            return False

        # Should contain action or final answer
        has_action = self._extract_action(text) is not None
        has_final = self.is_final_answer(text)

        return has_action or has_final