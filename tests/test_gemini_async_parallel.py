# ABOUTME: TDD failing test driving Gemini nodes toward async execute() methods.
# ABOUTME: Asserts the text-gen surface allows concurrent ComfyUI API node execution.

import asyncio
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# google.genai is a transitive dep; skip cleanly if absent.
pytest.importorskip("google.genai")

from erpk.gemini.nodes import GeminiTextGeneration


class _FakeGeminiClient:
    """Minimal GeminiClient stand-in: only exposes generate_content so that
    the node's execute() path works without touching the real SDK."""
    pass


def test_text_generation_runs_two_calls_concurrently():
    """Two GeminiTextGeneration.execute() calls under asyncio.gather must overlap.

    Why this matters: ComfyUI's executor parallelizes API nodes by detecting
    async execute() methods (execution.py:283). When execute() is async and
    awaits generate_content, two nodes can submit simultaneously instead of
    serializing. With sync execute(), asyncio.gather would receive plain return
    values (not coroutines) and raise TypeError — that is the intended RED failure.

    The mocked generate_content increments an in-flight counter on entry and
    decrements on exit. After gather, max must be 2 — both calls were genuinely
    concurrent, not one-after-the-other.
    """
    counter = {"in_flight": 0, "max": 0}

    async def _drive():
        async def fake_generate_content(prompt, **kwargs):
            counter["in_flight"] += 1
            counter["max"] = max(counter["max"], counter["in_flight"])
            # asyncio.sleep yields to the event loop, which is the whole point:
            # a sync time.sleep here would correctly fail (max would read 1).
            await asyncio.sleep(0.05)
            counter["in_flight"] -= 1
            return {"text": f"result for {prompt}", "blocked": False}

        client = _FakeGeminiClient()
        client.generate_content = fake_generate_content

        await asyncio.gather(
            GeminiTextGeneration.execute(prompt="hello", client=client, seed=-1),
            GeminiTextGeneration.execute(prompt="world", client=client, seed=-1),
        )

    asyncio.run(_drive())

    assert counter["max"] == 2, (
        f"Expected 2 concurrent calls in-flight at peak, observed max={counter['max']}. "
        "GeminiTextGeneration.execute must be async def and must await generate_content "
        "so ComfyUI's executor can interleave parallel Gemini API nodes."
    )
