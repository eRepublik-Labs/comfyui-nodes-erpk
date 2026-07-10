# ABOUTME: Verifies the Claude streaming path runs off the event-loop thread.
# ABOUTME: _generate_streaming iterates a blocking SDK generator; it must be offloaded.

import asyncio
import threading


class _FakeStreamingClient:
    """Minimal stand-in for ClaudeClient that records the thread streaming runs on."""

    def __init__(self):
        self.enable_streaming = True
        self.stream_thread = None

    def send_request_streaming(self, messages, system, temperature, max_tokens):
        self.stream_thread = threading.current_thread()
        yield "hello"


def test_text_generation_streaming_runs_off_event_loop_thread():
    from erpk.claude.text_generation import ClaudeTextGeneration
    client = _FakeStreamingClient()
    main = threading.current_thread()
    result = asyncio.run(ClaudeTextGeneration.execute(
        prompt="hi", client=client, use_streaming=True,
    ))
    assert result is not None
    assert client.stream_thread is not None, "streaming generator was never consumed"
    assert client.stream_thread is not main, (
        "streaming iterated on the event-loop thread; must be offloaded via asyncio.to_thread"
    )
