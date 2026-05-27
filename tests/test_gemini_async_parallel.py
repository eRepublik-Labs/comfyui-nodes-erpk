# ABOUTME: TDD failing test driving Gemini nodes toward async execute() methods.
# ABOUTME: Asserts text-gen and Veo polling surfaces allow concurrent ComfyUI API node execution.

import asyncio
import inspect
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# google.genai is a transitive dep; skip cleanly if absent.
pytest.importorskip("google.genai")

from gemini.nodes import GeminiTextGeneration
from gemini.veo_nodes import VeoTextToVideo, VeoImageToVideo, _poll_until_done


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


def test_veo_text_to_video_execute_is_async():
    """VeoTextToVideo.execute must be async def for ComfyUI parallelism.

    Video generation takes minutes; serializing two Veo nodes means the second
    waits for the first to finish. With async execute(), both start together.
    """
    assert inspect.iscoroutinefunction(VeoTextToVideo.execute), (
        "VeoTextToVideo.execute must be async def so ComfyUI's executor can "
        "parallelize multiple Veo video generation jobs."
    )


def test_veo_image_to_video_execute_is_async():
    """VeoImageToVideo.execute must be async def for ComfyUI parallelism."""
    assert inspect.iscoroutinefunction(VeoImageToVideo.execute), (
        "VeoImageToVideo.execute must be async def so ComfyUI's executor can "
        "parallelize multiple Veo video generation jobs."
    )


def test_veo_poll_until_done_is_async():
    """_poll_until_done must be an async def that uses asyncio.sleep.

    The polling loop's time.sleep(20) blocks the entire event loop for 20 seconds
    per iteration, freezing every other pending API node. Converting to
    await asyncio.sleep(20) releases the loop so other jobs advance in parallel.
    """
    assert inspect.iscoroutinefunction(_poll_until_done), (
        "_poll_until_done must be async def with 'await asyncio.sleep' so the "
        "event loop is free for other Veo/Gemini nodes between status checks."
    )


def test_veo_two_jobs_share_loop_during_polling():
    """Two _poll_until_done coroutines under asyncio.gather must both complete.

    With time.sleep(20) the first poll blocks for 20s before the second can
    run. With await asyncio.sleep(20) both polls share the event loop between
    iterations. This test mocks operations.get to complete immediately and
    patches asyncio.sleep to be instant so the suite stays fast.

    In RED phase, _poll_until_done is sync — asyncio.gather receives a plain
    return value and raises TypeError, which is the intended failure.
    """
    completed = []

    _real_sleep = asyncio.sleep

    class _FakeOp:
        """Operation that is already done — avoids real 20s sleep in RED/GREEN."""
        done = True
        error = None
        response = None

    class _FakeInnerClient:
        class operations:
            @staticmethod
            def get(op):
                return op

    class _FakeVeoClient:
        def __init__(self):
            self.client = _FakeInnerClient()

    async def _drive():
        vc = _FakeVeoClient()

        async def fast_sleep(n):
            await _real_sleep(0)  # yield without actually sleeping

        # Patch asyncio.sleep so the poll loop doesn't actually wait 20 s.
        asyncio.sleep = fast_sleep
        try:
            op1 = _FakeOp()
            op2 = _FakeOp()
            results = await asyncio.gather(
                _poll_until_done(op1, vc),
                _poll_until_done(op2, vc),
            )
            completed.extend(results)
        finally:
            asyncio.sleep = _real_sleep

    asyncio.run(_drive())

    assert len(completed) == 2, (
        f"Expected both Veo poll coroutines to complete, got {len(completed)}. "
        "_poll_until_done must be async def so asyncio.gather can run it."
    )
