# ABOUTME: TDD failing test driving ClaudeClient.send_request toward async execution.
# ABOUTME: Asserts two concurrent send_request calls overlap in-flight so ComfyUI can parallelize API nodes.

import asyncio
import time
from unittest.mock import MagicMock

from claude.claude_api.client import ClaudeClient


def test_send_request_runs_two_calls_concurrently():
    """Two send_request() calls under asyncio.gather must overlap, not serialize.

    Why this matters: ComfyUI's executor parallelizes API nodes by detecting that a
    node's execute() returned an unfinished asyncio.Task and moving on to the next
    ready node (execution.py:283-294, 544-552). That hinges on every layer below
    execute() being non-blocking. ClaudeClient is the shared HTTP layer; if its
    send_request blocks the event loop, parallel Claude nodes serialize instead of
    running concurrently.

    The fake transport (replacing self.client.messages.create) uses time.sleep to
    simulate real API latency while holding the in_flight counter elevated. Running
    both calls through asyncio.to_thread (the conversion) lets the thread pool
    overlap them — max in_flight becomes 2. With the original sync implementation,
    send_request returns a plain value (not a coroutine) so asyncio.gather raises
    TypeError before the assertion is ever reached (the expected red-phase failure).
    """
    counter = {"in_flight": 0, "max": 0}

    def slow_create(**kwargs):
        """Sync stand-in for self.client.messages.create with deliberate latency."""
        counter["in_flight"] += 1
        counter["max"] = max(counter["max"], counter["in_flight"])
        # Hold long enough that both threads overlap. A sync send_request would
        # run these serially, keeping max at 1 and failing the assertion.
        time.sleep(0.05)
        counter["in_flight"] -= 1
        resp = MagicMock()
        resp.model = "claude-sonnet-5-5"
        resp.usage.input_tokens = 0
        resp.usage.output_tokens = 0
        resp.usage.cache_read_input_tokens = 0
        resp.usage.cache_creation_input_tokens = 0
        return resp

    async def _drive():
        client = ClaudeClient(api_key="test-key")
        client.client.messages.create = slow_create

        await asyncio.gather(
            client.send_request(messages=[{"role": "user", "content": "a"}]),
            client.send_request(messages=[{"role": "user", "content": "b"}]),
        )

    asyncio.run(_drive())

    assert counter["max"] == 2, (
        f"Expected 2 concurrent calls in-flight at peak, observed max={counter['max']}. "
        "ClaudeClient.send_request must be async (via asyncio.to_thread) so "
        "ComfyUI's executor can interleave parallel Claude API nodes."
    )
