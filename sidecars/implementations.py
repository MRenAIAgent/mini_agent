"""
Example Sidecar Implementations

Concrete implementations of common sidecar patterns:
- Memory storage
- Analytics tracking
- Logging
- Metrics
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .base import Sidecar

logger = logging.getLogger(__name__)


class MemoryStoreSidecar(Sidecar):
    """
    Store conversation in memory after execution completes.

    This runs in background, allowing the agent to return response
    immediately without waiting for memory storage to complete.

    Typical storage time: 50-150ms (saved per response!)
    """

    name = "memory_store"
    description = "Store conversation in memory (non-blocking)"
    timeout = 30  # Memory storage should be fast

    def __init__(self, memory_manager):
        """
        Initialize memory storage sidecar.

        Args:
            memory_manager: CoreMemoryManager instance
        """
        self.memory_manager = memory_manager

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store conversation in memory.

        This runs in background after agent returns response.
        """
        if not self.memory_manager:
            logger.warning("Memory manager not available, skipping storage")
            return {"status": "skipped", "reason": "no_memory_manager"}

        # Store conversation turn
        await self.memory_manager.add_conversation_turn(
            session_id=context["session_id"],
            user_input=context["user_input"],
            agent_response=context["response"],
            execution_result=context["execution_result"]
        )

        return {
            "status": "stored",
            "session_id": context["session_id"],
            "timestamp": datetime.now().isoformat()
        }

    async def on_success(self, result: Any):
        """Log successful storage"""
        logger.debug(
            f"Memory stored for session {result.get('session_id')}"
        )

    async def on_error(self, error: Exception):
        """Log storage failure"""
        logger.error(
            f"Failed to store memory: {error}",
            exc_info=True
        )


class AnalyticsSidecar(Sidecar):
    """
    Track analytics events after execution completes.

    Records metrics like:
    - Response time
    - Iterations used
    - Tools called
    - Success/failure
    """

    name = "analytics"
    description = "Track agent execution analytics"
    timeout = 15

    def __init__(self, analytics_service: Optional[Any] = None):
        """
        Initialize analytics sidecar.

        Args:
            analytics_service: Optional analytics service (e.g., Mixpanel, Amplitude)
        """
        self.analytics_service = analytics_service

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track analytics event.

        This runs in background, doesn't delay response.
        """
        execution_result = context.get("execution_result", {})

        event_data = {
            "event": "agent_response",
            "session_id": context["session_id"],
            "timestamp": context["timestamp"],
            "metrics": {
                "response_length": len(context["response"]),
                "input_length": len(context["user_input"]),
                "iterations": execution_result.get("iterations_used", 0),
                "success": execution_result.get("success", False),
                "tools_used": len(execution_result.get("execution_steps", [])),
            }
        }

        # Send to analytics service if available
        if self.analytics_service:
            await self._send_to_service(event_data)
        else:
            # Just log locally
            logger.info(f"Analytics: {event_data}")

        return event_data

    async def _send_to_service(self, event_data: Dict[str, Any]):
        """
        Send to external analytics service.

        Override this to integrate with your analytics platform.
        """
        # Example: await self.analytics_service.track(event_data)
        logger.debug(f"Would send to analytics: {event_data}")


class LoggingSidecar(Sidecar):
    """
    Log conversation for debugging and auditing.

    Writes detailed logs in background without blocking response.
    Useful for:
    - Debugging
    - Auditing
    - Training data collection
    """

    name = "logging"
    description = "Log conversation details"
    timeout = 10

    def __init__(self, log_file: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize logging sidecar.

        Args:
            log_file: Optional file to write logs to
            log_level: Minimum log level
        """
        self.log_file = log_file
        self.log_level = log_level

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log conversation details.

        This runs in background after response is sent.
        """
        log_entry = {
            "timestamp": context["timestamp"],
            "session_id": context["session_id"],
            "input": context["user_input"],
            "response": context["response"],
            "execution": {
                "success": context["execution_result"].get("success", False),
                "iterations": context["execution_result"].get("iterations_used", 0),
            }
        }

        # Write to file if specified
        if self.log_file:
            await self._write_to_file(log_entry)
        else:
            # Just log to stdout
            logger.info(f"Conversation log: {log_entry}")

        return log_entry

    async def _write_to_file(self, entry: Dict[str, Any]):
        """
        Write log entry to file.

        Uses async file I/O to avoid blocking.
        """
        import json
        import aiofiles

        try:
            async with aiofiles.open(self.log_file, mode='a') as f:
                await f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log file: {e}")


class MetricsSidecar(Sidecar):
    """
    Collect performance metrics.

    Tracks:
    - Execution time
    - Resource usage
    - Success rates
    - Error patterns
    """

    name = "metrics"
    description = "Collect performance metrics"
    timeout = 5

    def __init__(self):
        self.metrics = {
            "total_executions": 0,
            "total_success": 0,
            "total_failures": 0,
            "total_time": 0.0,
            "by_session": {}
        }

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect and update metrics.

        This runs in background.
        """
        execution_result = context.get("execution_result", {})
        session_id = context["session_id"]

        # Update global metrics
        self.metrics["total_executions"] += 1

        if execution_result.get("success", False):
            self.metrics["total_success"] += 1
        else:
            self.metrics["total_failures"] += 1

        # Update session metrics
        if session_id not in self.metrics["by_session"]:
            self.metrics["by_session"][session_id] = {
                "executions": 0,
                "success": 0,
                "failures": 0
            }

        session_metrics = self.metrics["by_session"][session_id]
        session_metrics["executions"] += 1

        if execution_result.get("success", False):
            session_metrics["success"] += 1
        else:
            session_metrics["failures"] += 1

        return {
            "metrics_updated": True,
            "total_executions": self.metrics["total_executions"]
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return dict(self.metrics)

    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_executions": 0,
            "total_success": 0,
            "total_failures": 0,
            "total_time": 0.0,
            "by_session": {}
        }


class NotificationSidecar(Sidecar):
    """
    Send notifications after execution.

    Example use cases:
    - Email notifications when task completes
    - Slack messages for important events
    - Webhook calls to external services
    """

    name = "notification"
    description = "Send notifications"
    timeout = 30

    def __init__(self, notification_service: Optional[Any] = None):
        """
        Initialize notification sidecar.

        Args:
            notification_service: Service for sending notifications
        """
        self.notification_service = notification_service

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification if conditions are met.

        This runs in background.
        """
        # Example: notify on failures
        execution_result = context.get("execution_result", {})

        if not execution_result.get("success", False):
            await self._send_notification(
                title="Agent Execution Failed",
                message=f"Session: {context['session_id']}\n"
                        f"Error: {execution_result.get('error_message', 'Unknown')}"
            )

        return {"notification_sent": True}

    async def _send_notification(self, title: str, message: str):
        """
        Send notification via configured service.

        Override to integrate with your notification system.
        """
        if self.notification_service:
            # Example: await self.notification_service.send(title, message)
            logger.info(f"Notification: {title} - {message}")
        else:
            logger.info(f"Would send notification: {title} - {message}")

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """
        Only execute if there's a failure or specific condition.

        Override to customize when notifications are sent.
        """
        if not self.enabled:
            return False

        # Example: only notify on failures
        execution_result = context.get("execution_result", {})
        return not execution_result.get("success", True)


class EpisodeMemorySidecar(Sidecar):
    """
    Generate and store episode memories from conversations.

    Episode memories are extracted from user inputs and agent interactions,
    capturing important facts, preferences, events, and context that should
    be remembered long-term.

    This sidecar analyzes conversations to extract:
    - User preferences and likes/dislikes
    - Important facts mentioned by the user
    - Significant events or experiences shared
    - Goals, plans, or intentions
    - Personal information worth remembering

    Example:
        User: "I'm planning a trip to Japan next month. I love sushi!"

        Generated episode memories:
        - "User is planning a trip to Japan"
        - "User loves sushi"
        - Memory metadata includes: type=preference, type=plan
    """

    name = "episode_memory"
    description = "Extract and store episode memories from conversations"
    timeout = 60  # May need more time for LLM analysis

    def __init__(
        self,
        memory_manager,
        llm_function=None,
        extraction_strategy: str = "simple"
    ):
        """
        Initialize episode memory sidecar.

        Args:
            memory_manager: CoreMemoryManager instance for storing memories
            llm_function: Optional LLM function for intelligent extraction
            extraction_strategy: "simple" (rule-based) or "llm" (LLM-powered)
        """
        self.memory_manager = memory_manager
        self.llm_function = llm_function
        self.extraction_strategy = extraction_strategy

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze conversation and extract episode memories.

        This runs in background after agent returns response.
        """
        if not self.memory_manager:
            logger.warning("Memory manager not available, skipping episode extraction")
            return {"status": "skipped", "reason": "no_memory_manager"}

        user_input = context.get("user_input", "")
        agent_response = context.get("response", "")
        session_id = context.get("session_id")

        # Extract episode memories based on strategy
        if self.extraction_strategy == "llm" and self.llm_function:
            episodes = await self._extract_episodes_with_llm(
                user_input, agent_response, context
            )
        else:
            episodes = await self._extract_episodes_simple(
                user_input, agent_response, context
            )

        # Store each episode memory
        stored_count = 0
        for episode in episodes:
            try:
                success = await self.memory_manager.store_memory(
                    content=episode["content"],
                    importance=episode.get("importance", 0.7),
                    session_id=session_id,
                    memory_type="episode",
                    episode_type=episode.get("type", "general"),
                    source="conversation_analysis",
                    extracted_from={
                        "user_input": user_input[:100],  # First 100 chars
                        "timestamp": context.get("timestamp")
                    }
                )

                if success:
                    stored_count += 1
                    logger.debug(f"Stored episode memory: {episode['content'][:50]}...")

            except Exception as e:
                logger.error(f"Failed to store episode memory: {e}")

        return {
            "status": "completed",
            "episodes_extracted": len(episodes),
            "episodes_stored": stored_count,
            "session_id": session_id
        }

    async def _extract_episodes_simple(
        self,
        user_input: str,
        agent_response: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Simple rule-based episode extraction.

        Looks for patterns that indicate important information:
        - "I am...", "I like...", "I prefer..."  (preferences)
        - "I'm planning...", "I will..." (plans/goals)
        - "My name is...", "I live in..." (personal info)
        - "I work as...", "I studied..." (background)
        """
        episodes = []

        # Pattern matching for common episode types
        preference_patterns = [
            "I like", "I love", "I prefer", "I enjoy", "I hate", "I dislike",
            "my favorite", "I'm a fan of"
        ]

        plan_patterns = [
            "I'm planning", "I will", "I'm going to", "I want to",
            "next week", "next month", "soon", "planning to"
        ]

        personal_info_patterns = [
            "My name is", "I am", "I'm a", "I live in", "I work as",
            "I studied", "my job", "my role"
        ]

        # Extract preferences
        for pattern in preference_patterns:
            if pattern.lower() in user_input.lower():
                # Extract the sentence containing the pattern
                sentences = user_input.split('.')
                for sentence in sentences:
                    if pattern.lower() in sentence.lower():
                        episodes.append({
                            "content": sentence.strip(),
                            "type": "preference",
                            "importance": 0.8
                        })
                        break

        # Extract plans
        for pattern in plan_patterns:
            if pattern.lower() in user_input.lower():
                sentences = user_input.split('.')
                for sentence in sentences:
                    if pattern.lower() in sentence.lower():
                        episodes.append({
                            "content": sentence.strip(),
                            "type": "plan",
                            "importance": 0.7
                        })
                        break

        # Extract personal information
        for pattern in personal_info_patterns:
            if pattern.lower() in user_input.lower():
                sentences = user_input.split('.')
                for sentence in sentences:
                    if pattern.lower() in sentence.lower():
                        episodes.append({
                            "content": sentence.strip(),
                            "type": "personal_info",
                            "importance": 0.9
                        })
                        break

        # Deduplicate episodes
        unique_episodes = []
        seen_content = set()
        for episode in episodes:
            if episode["content"] not in seen_content:
                seen_content.add(episode["content"])
                unique_episodes.append(episode)

        return unique_episodes

    async def _extract_episodes_with_llm(
        self,
        user_input: str,
        agent_response: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to intelligently extract episode memories.

        This provides more accurate and nuanced extraction than simple patterns.
        """
        if not self.llm_function:
            logger.warning("LLM function not available, falling back to simple extraction")
            return await self._extract_episodes_simple(user_input, agent_response, context)

        # Create prompt for episode extraction
        extraction_prompt = f"""Analyze the following conversation and extract important episode memories.

Episode memories are facts, preferences, plans, or context worth remembering long-term.

User: {user_input}
Assistant: {agent_response}

Extract episode memories in the following JSON format:
[
    {{
        "content": "Brief description of what to remember",
        "type": "preference|plan|fact|personal_info|event",
        "importance": 0.0-1.0 (how important is this to remember)
    }}
]

Only extract meaningful information. If there's nothing worth remembering, return an empty array [].

Examples:
User: "I love pizza and hate mushrooms"
[
    {{"content": "User loves pizza", "type": "preference", "importance": 0.8}},
    {{"content": "User hates mushrooms", "type": "preference", "importance": 0.8}}
]

User: "What's the weather?"
[]

Extracted memories:"""

        try:
            # Call LLM to extract memories
            llm_response = await self.llm_function(extraction_prompt)

            # Parse JSON response
            import json
            import re

            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                episodes = json.loads(json_match.group(0))

                # Validate and clean episodes
                validated_episodes = []
                for episode in episodes:
                    if isinstance(episode, dict) and "content" in episode:
                        validated_episodes.append({
                            "content": episode.get("content", ""),
                            "type": episode.get("type", "general"),
                            "importance": float(episode.get("importance", 0.7))
                        })

                return validated_episodes
            else:
                logger.warning("No JSON found in LLM response, using simple extraction")
                return await self._extract_episodes_simple(user_input, agent_response, context)

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, falling back to simple extraction")
            return await self._extract_episodes_simple(user_input, agent_response, context)

    async def on_success(self, result: Any):
        """Log successful episode extraction"""
        logger.info(
            f"Episode memory extraction completed: "
            f"{result.get('episodes_stored', 0)} episodes stored "
            f"for session {result.get('session_id')}"
        )

    async def on_error(self, error: Exception):
        """Log extraction failure"""
        logger.error(
            f"Failed to extract episode memories: {error}",
            exc_info=True
        )
