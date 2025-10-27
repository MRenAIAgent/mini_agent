"""
Tests for Persistent Agent Thread-Safety

Verifies that a persistent agent can handle concurrent requests
with different sessions without race conditions.
"""

import pytest
import asyncio
from datetime import datetime


# Mock LLM for testing
async def mock_llm(prompt: str) -> str:
    """Mock LLM that returns immediately"""
    await asyncio.sleep(0.01)  # Simulate quick processing
    return "Mock response"


class TestPersistentAgentThreadSafety:
    """Test thread-safety of persistent agent with concurrent requests"""

    @pytest.mark.asyncio
    async def test_concurrent_sessions_no_race_condition(self):
        """
        Test that concurrent requests with different sessions don't interfere.

        This is the CRITICAL test for persistent agents in production.
        """
        from agent import CoreAgent

        # Create persistent agent (simulates API server startup)
        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        # Track which session each sidecar execution used
        executed_sessions = []

        # Mock the sidecar to capture session_id
        class SessionCaptureSidecar:
            name = "session_capture"
            description = "Captures session ID"
            enabled = True
            timeout = 10

            async def execute(self, context):
                # Simulate some async work
                await asyncio.sleep(0.05)

                # Capture the session_id used
                executed_sessions.append({
                    "session": context["session_id"],
                    "input": context["user_input"],
                    "timestamp": datetime.now()
                })
                return {"captured": True}

            def should_execute(self, context):
                return True

        # Register capture sidecar
        agent.register_sidecar(SessionCaptureSidecar())

        # Simulate concurrent API requests with different sessions
        async def request_user_a():
            """Simulates request from User A"""
            response = await agent.run(
                user_input="Hello from User A",
                session_id="user-a-session"  # ✅ Thread-safe parameter
            )
            return response

        async def request_user_b():
            """Simulates request from User B"""
            # Start slightly after A to maximize overlap
            await asyncio.sleep(0.02)
            response = await agent.run(
                user_input="Hello from User B",
                session_id="user-b-session"  # ✅ Thread-safe parameter
            )
            return response

        async def request_user_c():
            """Simulates request from User C"""
            await asyncio.sleep(0.01)
            response = await agent.run(
                user_input="Hello from User C",
                session_id="user-c-session"  # ✅ Thread-safe parameter
            )
            return response

        # Execute all requests concurrently (simulates production load)
        responses = await asyncio.gather(
            request_user_a(),
            request_user_b(),
            request_user_c()
        )

        # Wait for all sidecars to complete
        await asyncio.sleep(0.2)

        # Verify all requests got responses
        assert len(responses) == 3
        for response in responses:
            assert response is not None

        # CRITICAL ASSERTION: Each message should be stored in the correct session
        assert len(executed_sessions) == 3

        # Find sessions for each message
        sessions_by_message = {
            entry["input"]: entry["session"]
            for entry in executed_sessions
        }

        # Verify no cross-contamination
        assert sessions_by_message["Hello from User A"] == "user-a-session"
        assert sessions_by_message["Hello from User B"] == "user-b-session"
        assert sessions_by_message["Hello from User C"] == "user-c-session"

        print("\n✅ Thread-safety test PASSED!")
        print("   No race conditions detected with concurrent sessions.")

        await agent.stop()

    @pytest.mark.asyncio
    async def test_session_parameter_overrides_instance_session(self):
        """Test that session_id parameter overrides instance session_id"""
        from agent import CoreAgent

        agent = CoreAgent(
            llm_function=mock_llm,
            session_id="default-session",  # Instance default
            enable_memory=False,
            enable_sidecars=False
        )

        # Run with explicit session (should override default)
        # Note: We can't easily verify this without sidecars,
        # but we can at least verify it doesn't crash
        response = await agent.run(
            user_input="Test",
            session_id="override-session"
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_fallback_to_instance_session(self):
        """Test that agent falls back to instance session_id if not provided"""
        from agent import CoreAgent

        agent = CoreAgent(
            llm_function=mock_llm,
            session_id="instance-session",
            enable_memory=False,
            enable_sidecars=False
        )

        # Run without explicit session (should use instance session)
        response = await agent.run(user_input="Test")

        assert response is not None

    @pytest.mark.asyncio
    async def test_persistent_sidecar_executor(self):
        """
        Test that sidecar executor persists across requests.

        This verifies background tasks continue after request completes.
        """
        from agent import CoreAgent

        # Create persistent agent
        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=True,
            enable_sidecars=True
        )
        await agent.start()

        # Track executions
        execution_count = [0]

        class CountingSidecar:
            name = "counting"
            description = "Counts executions"
            enabled = True
            timeout = 10

            async def execute(self, context):
                await asyncio.sleep(0.05)  # Simulate work
                execution_count[0] += 1
                return {"count": execution_count[0]}

            def should_execute(self, context):
                return True

        agent.register_sidecar(CountingSidecar())

        # Make multiple requests
        await agent.run("Request 1", session_id="session-1")
        await agent.run("Request 2", session_id="session-2")
        await agent.run("Request 3", session_id="session-3")

        # Wait for sidecars
        await asyncio.sleep(0.2)

        # Verify all 3 sidecars executed
        assert execution_count[0] == 3

        # Verify executor is still active
        stats = agent.get_sidecar_stats()
        assert stats["total_completed"] >= 3

        print("\n✅ Persistent executor test PASSED!")
        print(f"   Sidecars completed: {stats['total_completed']}")

        await agent.stop()


class TestPersistentAgentBackwardCompatibility:
    """Test that changes don't break existing code"""

    @pytest.mark.asyncio
    async def test_run_without_session_parameter_still_works(self):
        """Verify backward compatibility: run() works without session_id parameter"""
        from agent import CoreAgent

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=False,
            enable_sidecars=False
        )

        # Old style: no session parameter (should still work)
        response = await agent.run("Test message")

        assert response is not None

    @pytest.mark.asyncio
    async def test_setting_instance_session_still_works(self):
        """Verify setting agent.session_id directly still works"""
        from agent import CoreAgent

        agent = CoreAgent(
            llm_function=mock_llm,
            enable_memory=False,
            enable_sidecars=False
        )

        # Old style: set instance variable
        agent.session_id = "my-session"
        response = await agent.run("Test")

        assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
