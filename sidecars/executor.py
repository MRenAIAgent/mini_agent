"""
Sidecar Executor

Manages the execution of sidecars in the background without blocking
the agent's response to the user.

Key features:
- Non-blocking execution via asyncio.create_task()
- Timeout protection
- Error isolation (sidecar failures don't crash agent)
- Concurrent execution of multiple sidecars
- Task lifecycle management
"""

import asyncio
from typing import Dict, Any, Set, Optional
from datetime import datetime
import logging

from .base import Sidecar, SidecarContext

logger = logging.getLogger(__name__)


class SidecarExecutor:
    """
    Executor for running sidecars in the background.

    Handles:
    - Non-blocking execution (fire-and-forget)
    - Timeout enforcement
    - Error handling and isolation
    - Task lifecycle management
    - Concurrent execution limits
    """

    def __init__(
        self,
        max_concurrent: int = 50,
        default_timeout: int = 60,
        track_tasks: bool = True
    ):
        """
        Initialize sidecar executor.

        Args:
            max_concurrent: Maximum number of concurrent sidecar tasks
            default_timeout: Default timeout in seconds if sidecar doesn't specify
            track_tasks: Whether to track tasks (needed for graceful shutdown)
        """
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.track_tasks = track_tasks

        # Active tasks
        self._active_tasks: Set[asyncio.Task] = set()
        self._task_count = 0

        # Statistics
        self._stats = {
            "total_started": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_timeout": 0,
            "by_sidecar": {}
        }

    def execute_all(
        self,
        sidecars: list[Sidecar],
        context: Dict[str, Any]
    ) -> int:
        """
        Execute all sidecars in background (non-blocking).

        This method returns immediately after starting all sidecars.
        The agent does NOT wait for sidecars to complete.

        Args:
            sidecars: List of sidecar instances to execute
            context: Execution context to pass to sidecars

        Returns:
            Number of sidecars started
        """
        if not sidecars:
            return 0

        # Convert dict context to SidecarContext if needed
        if isinstance(context, dict):
            ctx = SidecarContext.from_dict(context)
        else:
            ctx = context

        started_count = 0

        for sidecar in sidecars:
            # Check if sidecar should execute
            if not sidecar.should_execute(ctx.to_dict()):
                logger.debug(f"Skipping sidecar {sidecar.name} (should_execute returned False)")
                continue

            # Start sidecar in background
            self.execute_one(sidecar, ctx.to_dict())
            started_count += 1

        logger.info(f"Started {started_count} sidecars in background")
        return started_count

    def execute_one(
        self,
        sidecar: Sidecar,
        context: Dict[str, Any]
    ) -> Optional[asyncio.Task]:
        """
        Execute a single sidecar in background (non-blocking).

        Args:
            sidecar: Sidecar instance to execute
            context: Execution context

        Returns:
            The asyncio Task if started, None if skipped
        """
        # Check concurrent limit
        if len(self._active_tasks) >= self.max_concurrent:
            logger.warning(
                f"Max concurrent sidecars reached ({self.max_concurrent}), "
                f"skipping {sidecar.name}"
            )
            return None

        # Create background task (DOES NOT BLOCK!)
        task = asyncio.create_task(
            self._execute_sidecar_safe(sidecar, context)
        )

        # Track task if enabled
        if self.track_tasks:
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)

        # Update stats
        self._task_count += 1
        self._stats["total_started"] += 1

        logger.debug(f"Started sidecar {sidecar.name} in background (task #{self._task_count})")

        return task

    async def _execute_sidecar_safe(
        self,
        sidecar: Sidecar,
        context: Dict[str, Any]
    ):
        """
        Execute sidecar with timeout and error handling.

        This runs in the background. Errors are caught and logged,
        but don't propagate to the agent.
        """
        sidecar_name = sidecar.name
        timeout = sidecar.timeout or self.default_timeout

        # Initialize stats for this sidecar
        if sidecar_name not in self._stats["by_sidecar"]:
            self._stats["by_sidecar"][sidecar_name] = {
                "started": 0,
                "completed": 0,
                "failed": 0,
                "timeout": 0,
                "total_time": 0.0
            }

        sidecar_stats = self._stats["by_sidecar"][sidecar_name]
        sidecar_stats["started"] += 1

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                sidecar.execute(context),
                timeout=timeout
            )

            # Success callback
            await sidecar.on_success(result)

            # Update stats
            elapsed = asyncio.get_event_loop().time() - start_time
            self._stats["total_completed"] += 1
            sidecar_stats["completed"] += 1
            sidecar_stats["total_time"] += elapsed

            logger.debug(
                f"Sidecar {sidecar_name} completed successfully in {elapsed:.2f}s"
            )

        except asyncio.TimeoutError:
            # Timeout callback
            await sidecar.on_timeout()

            # Update stats
            self._stats["total_timeout"] += 1
            sidecar_stats["timeout"] += 1

            logger.warning(
                f"Sidecar {sidecar_name} timed out after {timeout}s"
            )

        except Exception as e:
            # Error callback
            await sidecar.on_error(e)

            # Update stats
            self._stats["total_failed"] += 1
            sidecar_stats["failed"] += 1

            logger.error(
                f"Sidecar {sidecar_name} failed: {e}",
                exc_info=True
            )

    async def wait_all(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all active sidecar tasks to complete.

        Useful for graceful shutdown.

        Args:
            timeout: Maximum time to wait (seconds), None = wait forever

        Returns:
            True if all completed, False if timeout
        """
        if not self._active_tasks:
            return True

        logger.info(f"Waiting for {len(self._active_tasks)} sidecars to complete...")

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._active_tasks, return_exceptions=True),
                timeout=timeout
            )
            logger.info("All sidecars completed")
            return True

        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for sidecars, "
                f"{len(self._active_tasks)} still running"
            )
            return False

    def cancel_all(self):
        """
        Cancel all active sidecar tasks.

        Useful for immediate shutdown.
        """
        if not self._active_tasks:
            return

        logger.info(f"Cancelling {len(self._active_tasks)} active sidecars...")

        for task in self._active_tasks:
            if not task.done():
                task.cancel()

        self._active_tasks.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get executor statistics.

        Returns:
            Dictionary with execution statistics
        """
        return {
            "active_tasks": len(self._active_tasks),
            "total_started": self._stats["total_started"],
            "total_completed": self._stats["total_completed"],
            "total_failed": self._stats["total_failed"],
            "total_timeout": self._stats["total_timeout"],
            "by_sidecar": dict(self._stats["by_sidecar"])
        }

    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "total_started": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_timeout": 0,
            "by_sidecar": {}
        }

    @property
    def active_count(self) -> int:
        """Number of currently active sidecar tasks"""
        return len(self._active_tasks)

    @property
    def has_capacity(self) -> bool:
        """Whether executor has capacity for more sidecars"""
        return len(self._active_tasks) < self.max_concurrent


# Global singleton executor (can be replaced with custom instance)
_default_executor: Optional[SidecarExecutor] = None


def get_default_executor() -> SidecarExecutor:
    """
    Get the default global sidecar executor.

    Creates one if it doesn't exist.
    """
    global _default_executor
    if _default_executor is None:
        _default_executor = SidecarExecutor()
    return _default_executor


def set_default_executor(executor: SidecarExecutor):
    """
    Set a custom default executor.

    Args:
        executor: Custom executor instance
    """
    global _default_executor
    _default_executor = executor
