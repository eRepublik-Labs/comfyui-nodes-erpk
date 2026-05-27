# ABOUTME: TDD failing test driving ClaudeClient.send_request toward async execution.
# ABOUTME: Asserts two concurrent send_request calls overlap in-flight so ComfyUI can parallelize API nodes.

import asyncio
import importlib.util
import os
import pathlib
import sys
import time
from unittest.mock import MagicMock

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# Stub out the anthropic SDK so client.py can be imported without the real package.
# Only needs to satisfy the top-level `from anthropic import ...` in client.py;
# actual API calls are replaced by the test's slow_create transport fake.
if "anthropic" not in sys.modules:
    _stub = MagicMock()
    sys.modules["anthropic"] = _stub

# Load client.py directly, bypassing claude_api/__init__.py (which imports utils.py
# → numpy, not available in the test environment).
_client_py = pathlib.Path(_REPO) / "claude" / "claude_api" / "client.py"
_spec = importlib.util.spec_from_file_location("_claude_api_client", str(_client_py))
_client_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_client_mod)
ClaudeClient = _client_mod.ClaudeClient


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
