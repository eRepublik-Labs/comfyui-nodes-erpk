# ABOUTME: Runs Grok nodes through the real xai-sdk with its gRPC stubs swapped for an in-process wire.
# ABOUTME: Asserts what each node sends to xAI, and that cut-off replies and oversized edit batches raise.

"""
Replacing GrokClient methods with fakes would hide an SDK rename: the finish
reason string, the request proto fields and the polling loop all live in
xai-sdk. This harness keeps xai_sdk.Client, Chat, Response and the request
builders real and swaps only the three gRPC stubs, so assertions read the
request proto xAI would receive and replies are parsed by the SDK itself.
"""

import asyncio
import re

import pytest

xai_sdk = pytest.importorskip("xai_sdk")
from xai_sdk.proto import chat_pb2, deferred_pb2, image_pb2, sample_pb2, video_pb2  # noqa: E402

from erpk.grok import nodes, video_nodes  # noqa: E402
from erpk.grok.grok_api.client import GrokClient  # noqa: E402

CLIENT = {"api_key": "test-key"}
SOURCE = "data:image/jpeg;base64,AAAA"
IMAGE_URL = "https://example.com/out.jpg"
VIDEO_URL = "https://example.com/out.mp4"


class Wire:
    """Stands in for the chat, image and video gRPC stubs and records every request."""

    def __init__(self):
        self.requests = []
        self.finish_reason = sample_pb2.REASON_STOP
        self.content = "Rivers carve valleys."

    def GetCompletion(self, request):
        self.requests.append(request)
        return chat_pb2.GetChatCompletionResponse(
            id="resp-test",
            outputs=[chat_pb2.CompletionOutput(
                index=0,
                finish_reason=self.finish_reason,
                message=chat_pb2.CompletionMessage(
                    content=self.content, role=chat_pb2.MessageRole.ROLE_ASSISTANT
                ),
            )],
        )

    def GenerateImage(self, request):
        self.requests.append(request)
        return image_pb2.ImageResponse(images=[image_pb2.GeneratedImage(url=IMAGE_URL)])

    def GenerateVideo(self, request):
        self.requests.append(request)
        return deferred_pb2.StartDeferredResponse(request_id="video-test")

    def GetDeferredVideo(self, request):
        return video_pb2.GetDeferredVideoResponse(
            status=deferred_pb2.DeferredStatus.DONE,
            response=video_pb2.VideoResponse(video=video_pb2.GeneratedVideo(url=VIDEO_URL)),
        )


@pytest.fixture
def wire(monkeypatch):
    wire = Wire()
    sdk_client = xai_sdk.Client

    def wired_client(**kwargs):
        client = sdk_client(**kwargs)
        client.chat._stub = wire
        client.image._stub = wire
        client.video._stub = wire
        return client

    monkeypatch.setattr(xai_sdk, "Client", wired_client)
    return wire


# ---------------------------------------------------------------------------
# A reply cut off at max_tokens is an error, never partial output.
# Live probe 2026-11-03: max_tokens=1 on grok-4.7, grok-4.20-0309-non-reasoning
# and grok-build-0.1 returned status 200 with finish reason REASON_MAX_LEN.
# ---------------------------------------------------------------------------

TEXT_NODES = ["GrokTextGeneration", "GrokChat"]


def _run_text(node, **kwargs):
    return asyncio.run(getattr(nodes, node).execute(prompt="Write about rivers.", client=CLIENT, **kwargs))


@pytest.mark.parametrize("node", TEXT_NODES)
def test_reply_cut_off_at_max_tokens_raises(wire, node):
    wire.finish_reason = sample_pb2.REASON_MAX_LEN
    wire.content = "Rivers carve"
    with pytest.raises(ValueError, match=re.escape("Grok's reply was cut off at max_tokens=256; raise max_tokens")):
        _run_text(node, max_tokens=256)
    assert wire.requests[0].max_tokens == 256


@pytest.mark.parametrize("node", TEXT_NODES)
def test_reply_that_stops_on_its_own_is_returned(wire, node):
    assert _run_text(node, max_tokens=256).args[0] == "Rivers carve valleys."


# ---------------------------------------------------------------------------
# System prompt. Live probe 2026-11-18: grok-4.7 accepts a system message
# (13 more prompt tokens than the same call without it).
# ---------------------------------------------------------------------------

def _sent_messages(request):
    return [(chat_pb2.MessageRole.Name(m.role), m.content[0].text) for m in request.messages]


@pytest.mark.parametrize("node", TEXT_NODES)
def test_system_prompt_is_sent_before_the_user_turn(wire, node):
    _run_text(node, system_prompt="  Answer in French.  ")
    assert _sent_messages(wire.requests[0]) == [
        ("ROLE_SYSTEM", "Answer in French."),
        ("ROLE_USER", "Write about rivers."),
    ]


@pytest.mark.parametrize("node", TEXT_NODES)
@pytest.mark.parametrize("blank", ["", "   \n"])
def test_blank_system_prompt_sends_no_system_message(wire, node, blank):
    _run_text(node, system_prompt=blank)
    assert _sent_messages(wire.requests[0]) == [("ROLE_USER", "Write about rivers.")]


def test_chat_session_carries_the_system_prompt_to_the_next_turn(wire):
    first = _run_text("GrokChat", system_prompt="Answer in French.")
    asyncio.run(nodes.GrokChat.execute(prompt="And lakes?", client=CLIENT, chat_session=first.args[1]))
    assert _sent_messages(wire.requests[1]) == [
        ("ROLE_SYSTEM", "Answer in French."),
        ("ROLE_USER", "Write about rivers."),
        ("ROLE_ASSISTANT", "Rivers carve valleys."),
        ("ROLE_USER", "And lakes?"),
    ]


def test_chat_system_prompt_replaces_the_one_in_the_session(wire):
    first = _run_text("GrokChat", system_prompt="Answer in French.")
    asyncio.run(nodes.GrokChat.execute(
        prompt="And lakes?", client=CLIENT, chat_session=first.args[1], system_prompt="Answer in German.",
    ))
    assert _sent_messages(wire.requests[1]) == [
        ("ROLE_SYSTEM", "Answer in German."),
        ("ROLE_USER", "Write about rivers."),
        ("ROLE_ASSISTANT", "Rivers carve valleys."),
        ("ROLE_USER", "And lakes?"),
    ]


def test_chat_system_prompt_starts_a_session_that_had_none(wire):
    first = _run_text("GrokChat")
    asyncio.run(nodes.GrokChat.execute(
        prompt="And lakes?", client=CLIENT, chat_session=first.args[1], system_prompt="Answer in German.",
    ))
    assert _sent_messages(wire.requests[1])[0] == ("ROLE_SYSTEM", "Answer in German.")
    assert [role for role, _ in _sent_messages(wire.requests[1])].count("ROLE_SYSTEM") == 1


def test_chat_does_not_alter_the_upstream_session(wire):
    first = _run_text("GrokChat")
    upstream = first.args[1]
    before = [dict(m) for m in upstream]
    asyncio.run(nodes.GrokChat.execute(
        prompt="And lakes?", client=CLIENT, chat_session=upstream, system_prompt="Answer in German.",
    ))
    assert upstream == before


# ---------------------------------------------------------------------------
# Image edit sources. docs.x.ai multi-image editing: grok-imagine-image-2.0
# takes up to 5 source images.
# ---------------------------------------------------------------------------

def test_image_edit_rejects_more_than_five_sources_before_any_api_call(wire):
    with pytest.raises(ValueError) as exc:
        asyncio.run(nodes.GrokImageEdit.execute(image=[SOURCE] * 7, prompt="make it blue", client=CLIENT))
    assert str(exc.value) == "Grok Image Edit takes at most 5 source images; got 7. Trim the batch before this node."
    assert wire.requests == []


def test_image_edit_client_rejects_six_sources_before_any_api_call(wire):
    with pytest.raises(ValueError, match="takes at most 5 source images; got 6"):
        asyncio.run(GrokClient(api_key="test-key").edit_image("make it blue", [SOURCE] * 6))
    assert wire.requests == []


def test_image_edit_sends_all_five_sources(wire):
    urls = asyncio.run(GrokClient(api_key="test-key").edit_image("make it blue", [SOURCE] * 5))
    assert urls == [IMAGE_URL]
    assert [i.image_url for i in wire.requests[0].images] == [SOURCE] * 5


# ---------------------------------------------------------------------------
# Text to video. docs.x.ai video overview recommends grok-imagine-video-1.5-lite
# for simple videos ($0.02/s). Lite rejects reference images (live probe
# 2026-10-14: "reference_images is not supported for this model."), so
# Text to Video must never send any.
# ---------------------------------------------------------------------------

def test_text_to_video_defaults_to_lite(wire):
    out = asyncio.run(video_nodes.GrokTextToVideo.execute(prompt="a red cube", client=CLIENT))
    assert out.args[0] == VIDEO_URL
    assert wire.requests[0].model == "grok-imagine-video-1.5-lite"


@pytest.mark.parametrize("model", ["grok-imagine-video", "grok-imagine-video-1.5", "grok-imagine-video-1.5-lite"])
def test_text_to_video_sends_no_reference_images(wire, model):
    asyncio.run(video_nodes.GrokTextToVideo.execute(prompt="a red cube", client=CLIENT, model=model))
    assert wire.requests[0].model == model
    assert len(wire.requests[0].reference_images) == 0


def test_reference_to_video_defaults_to_grok_imagine_video_1_5_and_sends_its_images(wire):
    asyncio.run(video_nodes.GrokRefToVideo.execute(
        prompt="<IMAGE_0> walks past <IMAGE_1>", reference_images=[SOURCE] * 2, client=CLIENT,
    ))
    assert wire.requests[0].model == "grok-imagine-video-1.5"
    assert [r.image_url for r in wire.requests[0].reference_images] == [SOURCE] * 2
