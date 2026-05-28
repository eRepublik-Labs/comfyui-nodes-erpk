# ABOUTME: TDD parallelism test for GrokClient — two concurrent text calls overlap in-flight.
# ABOUTME: Mirrors tests/test_openai_async_parallel.py since both wrap sync SDKs via asyncio.to_thread.

import asyncio
import os
import sys
import threading

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)


def test_generate_text_runs_two_calls_concurrently():
    """Two GrokClient.generate_text() calls under asyncio.gather must overlap.

    The async public method wraps a sync helper via asyncio.to_thread. The
    patched layer (_generate_text_sync) runs in real OS threads, so the
    in_flight counter needs threading.Lock for correctness.
    """
    from erpk.grok.grok_api.client import GrokClient

    counter = {"in_flight": 0, "max": 0}
    lock = threading.Lock()

    def fake_sync(self, messages, model="grok-4.3", **kwargs):
        with lock:
            counter["in_flight"] += 1
            counter["max"] = max(counter["max"], counter["in_flight"])
        # Real network latency stand-in. The lock above doesn't span the sleep,
        # so two threads can both observe in_flight == 2 before either exits.
        import time
        time.sleep(0.05)
        with lock:
            counter["in_flight"] -= 1
        return {"text": "fake", "model": model}

    async def _drive():
        client = GrokClient(api_key="test")
        # Patch the sync helper on the instance.
        client._generate_text_sync = fake_sync.__get__(client, GrokClient)

        await asyncio.gather(
            client.generate_text([{"role": "user", "content": "a"}]),
            client.generate_text([{"role": "user", "content": "b"}]),
        )

    asyncio.run(_drive())

    assert counter["max"] == 2, (
        f"Expected 2 concurrent calls in-flight at peak, observed max={counter['max']}. "
        "GrokClient.generate_text must be async and must run its sync body off the event loop."
    )
