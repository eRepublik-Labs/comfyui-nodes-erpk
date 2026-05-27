# ABOUTME: TDD failing test driving WaveSpeedClient.send_request toward async execution.
# ABOUTME: Asserts two concurrent calls overlap in-flight so ComfyUI can parallelize API nodes.

import asyncio
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# requests is a transitive dep of the client module; skip cleanly if absent.
pytest.importorskip("requests")

from wavespeed.wavespeed_api.client import WaveSpeedClient


class _FakeRequest:
    """Minimal BaseRequest stand-in for client.send_request().

    Real BaseRequest subclasses live in wavespeed/wavespeed_api/utils.py and
    each carries model-specific payload shaping. For this test we only need
    the two surfaces send_request() actually invokes: build_payload() and
    get_api_path().
    """

    def __init__(self, prompt: str):
        self._prompt = prompt

    def build_payload(self):
        return {"prompt": self._prompt}

    def get_api_path(self):
        return "/api/v3/fake"


def test_send_request_runs_two_calls_concurrently():
    """Two send_request() calls under asyncio.gather must overlap, not serialize.

    Why this matters: ComfyUI's executor parallelizes API nodes by detecting
    that a node's execute() returned an unfinished asyncio.Task and moving on
    to the next ready node (execution.py:283-294, 544-552). That hinges on
    every layer below execute() being non-blocking. WaveSpeedClient is the
    shared HTTP layer for ~25 nodes; if its submission and polling block the
    event loop, none of the nodes that use it can run in parallel.

    The mocked transport increments an in_flight counter on entry, decrements
    on exit, and records the observed maximum. After gather, max must be 2 --
    meaning both submissions were genuinely concurrent, not interleaved
    by being scheduled one-after-the-other on a sync stack.
    """
    counter = {"in_flight": 0, "max": 0}

    async def _drive():
        async def fake_post(endpoint, payload, timeout=60):
            counter["in_flight"] += 1
            counter["max"] = max(counter["max"], counter["in_flight"])
            # Realistic submission latency. asyncio.sleep yields to the loop,
            # which is the whole point of this test -- a sync time.sleep here
            # would correctly fail the assertion (max would read 1).
            await asyncio.sleep(0.05)
            counter["in_flight"] -= 1
            return {"id": f"task-{payload['prompt']}"}

        async def fake_wait_for_task(request_id, polling_interval=5, timeout=None):
            # Polling-loop concurrency gets its own test once we convert
            # wait_for_task. Here we just want submission to overlap, so
            # return immediately.
            return {"status": "completed", "outputs": ["https://fake/out.png"]}

        client = WaveSpeedClient(api_key="test")
        client.post = fake_post
        client.wait_for_task = fake_wait_for_task

        await asyncio.gather(
            client.send_request(_FakeRequest("a")),
            client.send_request(_FakeRequest("b")),
        )

    asyncio.run(_drive())

    assert counter["max"] == 2, (
        f"Expected 2 concurrent calls in-flight at peak, observed max={counter['max']}. "
        "WaveSpeedClient.send_request must be async and must await its transport "
        "calls so ComfyUI's executor can interleave parallel API nodes."
    )
