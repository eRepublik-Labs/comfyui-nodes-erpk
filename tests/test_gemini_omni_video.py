# ABOUTME: Tests the Gemini Omni Flash video node's request shape and cache-control seed.
# ABOUTME: Omni Flash rejects temperature/system instructions and takes no API seed.

"""
Gemini Omni Flash is the first model in this package reached through the
Interactions API (client.interactions.create) rather than generate_content or
generate_videos, and it rejects most of the knobs the other Gemini nodes send:
system instructions, temperature, top_p, stop sequences and negative prompts
are all unsupported.

It also accepts no seed. Per the repo's caching invariant, a node that must be
able to re-run on demand needs a seed to gate fingerprint_inputs, so the node
carries a cache-control-only seed that is deliberately never sent to the API.
"""

import pytest

from gemini.omni_nodes import (
    OMNI_MODEL,
    GeminiOmniVideoGeneration,
    _build_omni_video_request,
    _generation_task,
)


def _config(aspect_ratio="16:9", has_image=False, resolution="720p"):
    return _build_omni_video_request(_generation_task(has_image), resolution,
                                     aspect_ratio=aspect_ratio)


def test_model_id_is_the_stable_omni_11_string():
    # gemini-omni-flash-preview shuts down 2026-09-30; the Gemini deprecations
    # page names gemini-omni-1.1-flash as its replacement.
    assert OMNI_MODEL == "gemini-omni-1.1-flash"


def test_text_only_request_uses_text_to_video_task():
    cfg = _config()
    assert cfg["generation_config"]["video_config"]["task"] == "text_to_video"


def test_image_input_switches_to_image_to_video_task():
    cfg = _config(has_image=True)
    assert cfg["generation_config"]["video_config"]["task"] == "image_to_video"


def test_aspect_ratio_is_passed_through():
    assert _config(aspect_ratio="9:16")["response_format"]["aspect_ratio"] == "9:16"


def test_response_format_requests_video():
    assert _config()["response_format"]["type"] == "video"


@pytest.mark.parametrize("resolution", ["360p", "720p"])
def test_synchronous_fast_path_is_requested(resolution):
    # The docs recommend background/store/stream all false for unary generation.
    cfg = _config(resolution=resolution)
    assert cfg["background"] is False
    assert cfg["store"] is False
    assert cfg["stream"] is False


@pytest.mark.parametrize("resolution", ["1080p", "4k"])
def test_uri_delivery_stores_the_interaction(resolution):
    # Measured 2026-10-14: 400 "store=true is required when response format has
    # video delivery set to URI."
    cfg = _config(resolution=resolution)
    assert cfg["response_format"]["delivery"] == "uri"
    assert cfg["store"] is True


def test_text_only_input_is_one_text_part():
    # Measured 2026-10-14 on google-genai 2.6.0: a bare string inside the input
    # list -> 400 "'input' must be a Content[], string, Turn[], Step[], or Content".
    from gemini.omni_nodes import _generation_contents
    assert _generation_contents("a red kite", None) == [{"type": "text", "text": "a red kite"}]


def test_start_image_precedes_the_prompt_as_an_inline_png_part():
    import base64
    from PIL import Image
    from gemini.omni_nodes import _generation_contents
    parts = _generation_contents("it flies away", Image.new("RGB", (4, 4), "blue"))
    assert [p["type"] for p in parts] == ["image", "text"]
    assert parts[0]["mime_type"] == "image/png"
    assert base64.b64decode(parts[0]["data"])[:8] == b"\x89PNG\r\n\x1a\n"
    assert parts[1] == {"type": "text", "text": "it flies away"}


@pytest.mark.parametrize("unsupported", ["temperature", "top_p", "system_instruction", "stop_sequences", "negative_prompt"])
def test_unsupported_parameters_are_never_sent(unsupported):
    assert unsupported not in _config()


# --- Node schema and caching ------------------------------------------------


def _schema():
    return GeminiOmniVideoGeneration.define_schema()


def _input(name):
    for spec in _schema().inputs:
        if getattr(spec, "id", None) == name:
            return spec
    raise AssertionError(f"no input named {name}")


def test_node_outputs_a_video_path():
    assert [o.id for o in _schema().outputs] == ["video_path"]


def test_aspect_ratio_offers_only_supported_values():
    assert list(_input("aspect_ratio").options) == ["16:9", "9:16"]


def test_node_has_a_seed_for_cache_control():
    assert _input("seed") is not None


def test_seed_defaults_to_randomize():
    # Matches every other seeded node: a fresh node generates on each queue
    # until the author fixes a seed (Alex's 2026-10-01 ruling).
    assert _input("seed").default == -1


def test_fingerprint_is_seed_gated():
    # A fixed seed reuses the paid result; -1 (randomize) re-runs every queue.
    import math
    assert math.isnan(GeminiOmniVideoGeneration.fingerprint_inputs(seed=-1))
    assert GeminiOmniVideoGeneration.fingerprint_inputs(seed=7) == 7


def test_node_exposes_async_execute():
    import inspect
    assert inspect.iscoroutinefunction(GeminiOmniVideoGeneration.execute.__func__)


def test_node_is_registered():
    from gemini import NODES
    assert GeminiOmniVideoGeneration in NODES


# --- Output resolution (docs/omni "Output resolution"; the API's validation
# error lists '360p', '720p', '1080p', '4k', probed 2026-10-14) ---------------

def test_resolution_is_sent_in_response_format():
    for resolution in ("360p", "720p", "1080p", "4k"):
        assert _config(resolution=resolution)["response_format"]["resolution"] == resolution


def test_large_resolutions_use_uri_delivery():
    # Omni docs: "For videos larger than 4MB (>720p when available), use
    # delivery="uri" in response_format to avoid payload size limits."
    assert _config(resolution="1080p")["response_format"]["delivery"] == "uri"
    assert _config(resolution="4k")["response_format"]["delivery"] == "uri"


def test_small_resolutions_keep_inline_delivery():
    assert "delivery" not in _config(resolution="360p")["response_format"]
    assert "delivery" not in _config(resolution="720p")["response_format"]


def test_resolution_widget_offers_the_api_values_and_defaults_to_720p():
    spec = _input("resolution")
    assert list(spec.options) == ["360p", "720p", "1080p", "4k"]
    assert spec.default == "720p"


def test_resolution_widget_is_appended_last():
    # widgets_values is positional: saved workflows only stay aligned when a
    # new widget goes after every existing one.
    assert [i.id for i in _schema().inputs][-1] == "resolution"


# --- Fetching the output video ----------------------------------------------

import asyncio
import base64
from types import SimpleNamespace

from gemini import omni_nodes

_URI = "https://generativelanguage.googleapis.com/v1beta/files/abc123:download?alt=media"


class _FilesAPI:
    """Files API double: reports the given states in order, then serves bytes."""

    def __init__(self, states):
        self.states = list(states)
        self.got = []
        self.downloaded = None

    def get(self, name):
        self.got.append(name)
        return SimpleNamespace(state=SimpleNamespace(name=self.states.pop(0)))

    def download(self, file):
        self.downloaded = file
        return b"mp4-bytes"

    def delete(self, name):
        self.deleted = name


def _fetch(interaction, files, monkeypatch):
    monkeypatch.setattr(omni_nodes, "_FILE_POLL_INTERVAL_S", 0)
    return asyncio.run(omni_nodes._output_video_bytes(SimpleNamespace(files=files), interaction))


def test_inline_video_is_decoded(monkeypatch):
    interaction = SimpleNamespace(output_video=SimpleNamespace(data=base64.b64encode(b"clip").decode()))
    assert _fetch(interaction, _FilesAPI([]), monkeypatch) == b"clip"


def test_uri_video_is_downloaded_once_active(monkeypatch):
    files = _FilesAPI(["PROCESSING", "ACTIVE"])
    interaction = SimpleNamespace(output_video=SimpleNamespace(data=None, uri=_URI))
    assert _fetch(interaction, files, monkeypatch) == b"mp4-bytes"
    assert files.got == ["files/abc123", "files/abc123"]
    assert files.downloaded == _URI
    # The stored copy is removed once downloaded instead of waiting 48 hours.
    assert files.deleted == "files/abc123"


def test_failed_uri_video_raises_with_the_file_name(monkeypatch):
    files = _FilesAPI(["FAILED"])
    interaction = SimpleNamespace(output_video=SimpleNamespace(data=None, uri=_URI))
    with pytest.raises(ValueError, match=r"generated video \(files/abc123\) as FAILED"):
        _fetch(interaction, files, monkeypatch)
    assert files.downloaded is None


def test_missing_video_raises(monkeypatch):
    with pytest.raises(ValueError, match="Omni Flash returned no video"):
        _fetch(SimpleNamespace(output_video=None), _FilesAPI([]), monkeypatch)


# A 1080p/4k Omni job can outlast the 5-minute default and still be billed, so
# Omni gets the same 15-minute floor as Gemini 4 Argon (Alex, 2026-10-14).
FIFTEEN_MINUTES_MS = 15 * 60 * 1000


def test_omni_gets_a_fifteen_minute_timeout():
    from gemini.gemini_api.cooperative_call import resolve_timeout_ms
    assert resolve_timeout_ms(OMNI_MODEL) == FIFTEEN_MINUTES_MS


def test_omni_interaction_is_sent_with_the_fifteen_minute_timeout(tmp_path):
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        return SimpleNamespace(output_video=SimpleNamespace(data=base64.b64encode(b"clip").decode()))

    client = SimpleNamespace(client=SimpleNamespace(interactions=SimpleNamespace(create=create)))
    asyncio.run(omni_nodes._generate_and_save(client, [], {}, str(tmp_path)))
    assert sent["timeout"] == FIFTEEN_MINUTES_MS / 1000
