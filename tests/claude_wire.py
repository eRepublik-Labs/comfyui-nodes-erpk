# ABOUTME: Test harness that runs ClaudeClient through the real Anthropic SDK against an in-process transport.
# ABOUTME: Captures the exact JSON the SDK would put on the wire and replays canned Messages API replies.

"""
MagicMock-ing `Anthropic` hides SDK signature changes: anthropic 1.x removed
`temperature` from `messages.create`, and a mocked `create` happily accepts it.
This harness keeps the real SDK in the loop and swaps only the HTTP transport,
so a kwarg the installed SDK rejects fails the test the same way it fails a
user, and assertions read the request body the API would receive.
"""

import json
from functools import partial

import anthropic
from anthropic import Anthropic, DefaultHttpxClient

# anthropic 1.x is built on httpx2 and refuses an httpx transport; 0.x is the reverse.
if int(anthropic.__version__.split(".")[0]) >= 1:
    import httpx2 as httpx_mod
else:
    import httpx as httpx_mod


def message_body(text="ok", model="claude-sonnet-5-5", stop_reason="end_turn", thinking="hmm", usage=None):
    content = []
    if thinking is not None:
        content.append({"type": "thinking", "thinking": thinking, "signature": "sig"})
    if text is not None:
        content.append({"type": "text", "text": text})
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": usage or {
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }


def _sse(body):
    """Render a Messages body as the SSE event sequence messages.stream() consumes."""
    start = dict(body, content=[], stop_reason=None)
    events = [("message_start", {"type": "message_start", "message": start})]
    for index, block in enumerate(body["content"]):
        if block["type"] == "text":
            events.append(("content_block_start", {"type": "content_block_start", "index": index,
                                                   "content_block": {"type": "text", "text": ""}}))
            events.append(("content_block_delta", {"type": "content_block_delta", "index": index,
                                                   "delta": {"type": "text_delta", "text": block["text"]}}))
        else:
            events.append(("content_block_start", {"type": "content_block_start", "index": index,
                                                   "content_block": {"type": "thinking", "thinking": "", "signature": ""}}))
            events.append(("content_block_delta", {"type": "content_block_delta", "index": index,
                                                   "delta": {"type": "thinking_delta", "thinking": block["thinking"]}}))
            events.append(("content_block_delta", {"type": "content_block_delta", "index": index,
                                                   "delta": {"type": "signature_delta", "signature": block["signature"]}}))
        events.append(("content_block_stop", {"type": "content_block_stop", "index": index}))
    events.append(("message_delta", {"type": "message_delta",
                                     "delta": {"stop_reason": body["stop_reason"], "stop_sequence": None},
                                     "usage": {"output_tokens": body["usage"]["output_tokens"]}}))
    events.append(("message_stop", {"type": "message_stop"}))
    return "".join(f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events)


class Wire:
    """In-process Anthropic API: records every request, answers with queued replies."""

    def __init__(self, *replies):
        self.requests = []
        self._replies = list(replies) or [(200, message_body())]

    @property
    def bodies(self):
        return [json.loads(r.content) for r in self.requests if r.content]

    def _handle(self, request):
        self.requests.append(request)
        reply = self._replies.pop(0) if len(self._replies) > 1 else self._replies[0]
        status, body = reply
        if request.url.path.endswith("/count_tokens"):
            return httpx_mod.Response(200, json=body if "input_tokens" in body else {"input_tokens": 42})
        if status == 200 and json.loads(request.content).get("stream"):
            return httpx_mod.Response(status, text=_sse(body), headers={"content-type": "text/event-stream"})
        return httpx_mod.Response(status, json=body)

    def install(self, monkeypatch):
        """Make every ClaudeClient built afterwards talk to this wire."""
        import claude.claude_api.client as client_module

        monkeypatch.setattr(
            client_module,
            "Anthropic",
            partial(
                Anthropic,
                max_retries=0,
                http_client=DefaultHttpxClient(transport=httpx_mod.MockTransport(self._handle)),
            ),
        )
        return self


def error_body(status, error_type, message):
    return status, {"type": "error", "error": {"type": error_type, "message": message}}
