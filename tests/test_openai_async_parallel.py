# ABOUTME: TDD failing test driving OpenAIClient.generate_content toward async execution.
# ABOUTME: Asserts two concurrent calls overlap in-flight so ComfyUI can parallelize API nodes.

import asyncio
import os
import sys
import threading
import time

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# In the test environment our local openai/ package shadows the SDK's openai package.
# The client does `from openai import APIError, RateLimitError, APIConnectionError`
# (lazy import inside methods) — inject stubs so the import resolves.
import openai as _local_openai
for _name in ("APIError", "RateLimitError", "APIConnectionError"):
    if not hasattr(_local_openai, _name):
        setattr(_local_openai, _name, type(_name, (Exception,), {}))

from openai.openai_api.client import OpenAIClient


def test_generate_content_runs_two_calls_concurrently():
    """Two generate_content() calls under asyncio.gather must overlap, not serialize.

    Why this matters: ComfyUI's executor parallelizes API nodes by detecting
    that a node's execute() returned an unfinished asyncio.Task and moving on
    to the next ready node (execution.py:283-294, 544-552). That hinges on
    every layer below execute() being non-blocking. OpenAIClient.generate_content
    is the shared HTTP layer for all text/vision nodes; if it blocks the event
    loop, nodes that use it cannot run in parallel.

    The mocked _generate_content_sync increments an in_flight counter on entry
    (thread-safe via lock), sleeps in a worker thread so the event loop stays
    free for the second call, decrements on exit, and records the observed
    maximum. After gather, max must be 2 — meaning both calls were genuinely
    concurrent, not serialized one-after-the-other.
    """
    counter = {"in_flight": 0, "max": 0}
    lock = threading.Lock()

    async def _drive():
        def fake_sync(prompt, **kwargs):
            with lock:
                counter["in_flight"] += 1
                counter["max"] = max(counter["max"], counter["in_flight"])
            time.sleep(0.05)
            with lock:
                counter["in_flight"] -= 1
            return {
                "text": "fake",
                "blocked": False,
                "finish_reason": "stop",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }

        client = OpenAIClient.__new__(OpenAIClient)
        client.model_name = "gpt-4o"
        client.system_instruction = None
        client._generate_content_sync = fake_sync

        await asyncio.gather(
            client.generate_content("prompt a"),
            client.generate_content("prompt b"),
        )

    asyncio.run(_drive())

    assert counter["max"] == 2, (
        f"Expected 2 concurrent calls in-flight at peak, observed max={counter['max']}. "
        "OpenAIClient.generate_content must be async and must await "
        "asyncio.to_thread(self._generate_content_sync, ...) so ComfyUI's executor "
        "can interleave parallel API nodes."
    )
