# ABOUTME: Behaviour tests for the Grok node options: what each widget offers and what reaches the SDK.
# ABOUTME: SDK-backed tests build real xai-sdk requests and skip when xai_sdk is not installed.

import pytest

from erpk.grok.grok_api.client import GrokClient


def _input(node_cls, input_id):
    matches = [i for i in node_cls.define_schema().inputs if i.id == input_id]
    assert matches, f"{node_cls.__name__} has no input {input_id!r}"
    return matches[0]


def _node(name):
    from erpk.grok import nodes
    return getattr(nodes, name)


def _video_node(name):
    from erpk.grok import video_nodes
    return getattr(video_nodes, name)


# ---------------------------------------------------------------------------
# Image aspect ratio "auto"
# ---------------------------------------------------------------------------

def test_auto_aspect_is_omitted_from_the_image_request():
    # The SDK has no "auto" literal (xai_sdk/types/image.py); omitting the
    # field gives the API default, which is auto (docs.x.ai images/generation).
    kwargs = GrokClient._image_request_kwargs(aspect_ratio="auto", resolution="1k")
    assert "aspect_ratio" not in kwargs
    assert kwargs["resolution"] == "1k"


def test_generation_auto_aspect_builds_a_valid_sdk_request():
    xai_image = pytest.importorskip("xai_sdk.image")
    kwargs = GrokClient._image_request_kwargs(aspect_ratio="auto", resolution="1k")
    xai_image._make_generate_request("a red cube", "grok-imagine-image-2.0", **kwargs)


def test_every_offered_generation_aspect_builds_a_valid_sdk_request():
    xai_image = pytest.importorskip("xai_sdk.image")
    for ratio in _input(_node("GrokImageGeneration"), "aspect_ratio").options:
        kwargs = GrokClient._image_request_kwargs(aspect_ratio=ratio, resolution="1k")
        xai_image._make_generate_request("a red cube", "grok-imagine-image-2.0", **kwargs)


def test_edit_aspect_options_have_no_duplicates():
    options = _input(_node("GrokImageEdit"), "aspect_ratio").options
    assert len(options) == len(set(options))
    assert options.count("auto") == 1


# ---------------------------------------------------------------------------
# Video edit / extend take a video input, which only grok-imagine-video has
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node", ["GrokVideoEdit", "GrokVideoExtend"])
def test_video_input_nodes_offer_only_grok_imagine_video(node):
    # docs.x.ai model page + /v1/video-generation-models list no video input
    # for grok-imagine-video-1.5.
    inp = _input(_video_node(node), "model")
    assert inp.options == ["grok-imagine-video"]
    assert inp.default == "grok-imagine-video"



# ---------------------------------------------------------------------------
# Text: reasoning_effort widget and per-model clamp
# Expected values come from live gRPC probes on xai-sdk 1.20 (2026-10-01):
#   grok-4.7: low/medium/high/xhigh -> 200, none -> 400 "does not support
#   reasoning_effort value none"; grok-4.20-0309-non-reasoning,
#   grok-4.20-multi-agent-0309, grok-build-0.1: low -> 400 "does not support
#   parameter reasoningEffort".
# ---------------------------------------------------------------------------

EFFORT_OPTIONS = ["(model default)", "none", "low", "medium", "high", "xhigh"]
NO_EFFORT_MODELS = [
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-multi-agent-0309",
    "grok-build-0.1",
]


@pytest.mark.parametrize("node", ["GrokTextGeneration", "GrokChat"])
def test_reasoning_effort_widget_is_appended_last(node):
    # widgets_values is positional: a new widget must be the last input.
    inputs = _node(node).define_schema().inputs
    assert inputs[-1].id == "reasoning_effort"
    assert inputs[-1].options == EFFORT_OPTIONS
    assert inputs[-1].default == "(model default)"
    assert inputs[-1].optional is True


@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh"])
def test_grok_47_sends_supported_effort_unchanged(effort):
    assert GrokClient.resolve_reasoning_effort("grok-4.7", effort) == effort


def test_grok_47_clamps_none_to_low():
    assert GrokClient.resolve_reasoning_effort("grok-4.7", "none") == "low"


def test_model_default_sends_nothing():
    assert GrokClient.resolve_reasoning_effort("grok-4.7", "(model default)") is None


@pytest.mark.parametrize("model", NO_EFFORT_MODELS)
@pytest.mark.parametrize("effort", EFFORT_OPTIONS)
def test_models_without_effort_never_receive_it(model, effort):
    assert GrokClient.resolve_reasoning_effort(model, effort) is None


def test_every_sent_effort_converts_in_the_sdk():
    # SDK 1.14 rejected "xhigh" locally; 1.18+ accepts it.
    xai_chat = pytest.importorskip("xai_sdk.chat")
    for effort in EFFORT_OPTIONS:
        sent = GrokClient.resolve_reasoning_effort("grok-4.7", effort)
        if sent is not None:
            xai_chat._reasoning_effort_to_proto(sent)


# ---------------------------------------------------------------------------
# Text: max_tokens cap
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node", ["GrokTextGeneration", "GrokChat"])
def test_max_tokens_reaches_api_default_ceiling(node):
    # docs.x.ai chat-completions reference: max_completion_tokens "Defaults to
    # 128,000 when unset". Live probe: 131072 and 262144 also return 200, so the
    # server enforces no lower ceiling.
    inp = _input(_node(node), "max_tokens")
    assert inp.max == 128000
    assert inp.default == 4096


# ---------------------------------------------------------------------------
# Image generation options for grok-imagine-image-2.0
# ---------------------------------------------------------------------------

# xai_sdk 1.20 types/image.py ImageAspectRatio literal. 21:9 and 5:2 (2.0 per
# docs.x.ai migration page) have no SDK literal or proto enum, so they are
# REST-only and not offered.
SDK_ASPECT_RATIOS = [
    "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2",
    "9:19.5", "19.5:9", "9:20", "20:9", "1:2", "2:1",
]


def test_generation_offers_every_sdk_aspect_plus_auto():
    options = _input(_node("GrokImageGeneration"), "aspect_ratio").options
    assert sorted(options) == sorted(SDK_ASPECT_RATIOS + ["auto"])
    assert "21:9" not in options and "5:2" not in options


def test_generation_aspect_default_unchanged():
    assert _input(_node("GrokImageGeneration"), "aspect_ratio").default == "1:1"


def test_generation_n_allows_up_to_ten():
    # docs.x.ai images/generation: n is 1-10.
    inp = _input(_node("GrokImageGeneration"), "n")
    assert (inp.min, inp.max, inp.default) == (1, 10, 1)


def test_quality_widget_is_appended_last():
    inputs = _node("GrokImageGeneration").define_schema().inputs
    assert inputs[-1].id == "quality"
    # SDK 1.20 ImageQuality literal is low/medium; "auto" leaves it unset.
    assert inputs[-1].options == ["auto", "low", "medium"]
    assert inputs[-1].default == "auto"
    assert inputs[-1].optional is True


def test_auto_quality_is_omitted_from_the_image_request():
    kwargs = GrokClient._image_request_kwargs(aspect_ratio="1:1", resolution="1k", quality="auto")
    assert "quality" not in kwargs
    kwargs = GrokClient._image_request_kwargs(aspect_ratio="1:1", resolution="1k", quality="low")
    assert kwargs["quality"] == "low"


def test_every_offered_quality_builds_a_valid_sdk_request():
    xai_image = pytest.importorskip("xai_sdk.image")
    for quality in _input(_node("GrokImageGeneration"), "quality").options:
        kwargs = GrokClient._image_request_kwargs(aspect_ratio="1:1", resolution="1k", quality=quality)
        xai_image._make_generate_request("a red cube", "grok-imagine-image-2.0", n=10, **kwargs)


def test_edit_output_widgets_are_appended_after_aspect_ratio():
    # Appended last so saved GrokImageEdit workflows keep their slots; "auto"
    # defaults keep the request unchanged for existing workflows.
    inputs = _node("GrokImageEdit").define_schema().inputs
    tail = [(i.id, i.default) for i in inputs[-4:]]
    assert tail == [("aspect_ratio", "auto"), ("resolution", "auto"), ("n", 1), ("quality", "auto")]
    n = inputs[-2]
    assert (n.min, n.max) == (1, 10)


def test_auto_resolution_is_omitted_from_the_image_request():
    kwargs = GrokClient._image_request_kwargs(aspect_ratio="auto", resolution="auto", quality="auto")
    assert kwargs == {}


def test_every_offered_edit_option_builds_a_valid_sdk_edit_request():
    xai_image = pytest.importorskip("xai_sdk.image")
    node = _node("GrokImageEdit")
    for resolution in _input(node, "resolution").options:
        for quality in _input(node, "quality").options:
            kwargs = GrokClient._image_request_kwargs(
                aspect_ratio="auto", resolution=resolution, quality=quality
            )
            xai_image._make_generate_request(
                "make it blue", "grok-imagine-image-2.0", n=10,
                image_urls=["https://example.com/a.png", "https://example.com/b.png"], **kwargs
            )


def test_image_edit_accepts_five_sources():
    # docs.x.ai multi-image editing: grok-imagine-image-2.0 takes up to 5 sources.
    assert GrokClient.MAX_EDIT_IMAGES == 5


def test_reference_to_video_keeps_three_reference_images():
    # The 5-source cap is image-edit only; the r2v reference cap is unchanged.
    assert GrokClient.MAX_REFERENCE_IMAGES == 3


def test_five_worst_case_edit_sources_fit_one_grpc_message():
    # xai_sdk 1.20 client.py sets grpc.max_send_message_length to 20 MiB. Random
    # noise is the worst case for JPEG; before the shared budget, five such
    # 2048px sources encoded to 21.95 MiB and the request could not be sent.
    torch = pytest.importorskip("torch")
    from erpk.grok.grok_api.utils import images_to_data_uris

    torch.manual_seed(0)
    uris = images_to_data_uris(torch.rand(5, 2048, 2048, 3), max_count=GrokClient.MAX_EDIT_IMAGES)
    assert len(uris) == 5
    headroom_for_prompt = 2**20
    assert sum(len(u) for u in uris) <= 20 * 2**20 - headroom_for_prompt
