# ABOUTME: Tests for the Grok provider — schema presence, custom type, async execute.
# ABOUTME: Covers GrokAPIClient (config node) and the four video generation nodes.

import asyncio
import os
import sys
import inspect

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# Skip the whole module cleanly if comfy_api stub isn't loaded.
IO = pytest.importorskip("comfy_api.latest").IO


def _get_node(name):
    """Import a Grok node class by name from the grok package."""
    from erpk.grok import nodes
    return getattr(nodes, name)


class TestGrokAPIClient:
    """The config node that emits a GROK_API_CLIENT typed dict for downstream nodes."""

    def test_node_id_is_registered(self):
        cls = _get_node("GrokAPIClient")
        schema = cls.define_schema()
        assert schema.node_id == "GrokAPIClient"

    def test_emits_grok_api_client_output(self):
        cls = _get_node("GrokAPIClient")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "GROK_API_CLIENT"
        assert out.id == "client"

    def test_api_key_input_is_optional(self):
        """Optional Client Pattern per MEMORY.md — config nodes work when key is in Settings."""
        cls = _get_node("GrokAPIClient")
        schema = cls.define_schema()
        api_key_inputs = [i for i in schema.inputs if i.id == "api_key"]
        assert len(api_key_inputs) == 1
        assert api_key_inputs[0].optional is True

    def test_execute_is_sync(self):
        """Config nodes stay sync — no HTTP call, just key resolution + dict construction."""
        cls = _get_node("GrokAPIClient")
        assert not inspect.iscoroutinefunction(cls.execute), (
            "GrokAPIClient.execute does no HTTP work and must remain sync to avoid "
            "forcing every model node that consumes its output to also be async."
        )


class TestGrokClientSurface:
    """The GrokClient class that all model nodes will call into."""

    def test_async_public_methods_exist(self):
        """Each xAI capability has a corresponding async client method.

        Teammates in Phase 2 will await these methods; if any are missing
        or sync, propagation breaks.
        """
        from erpk.grok.grok_api.client import GrokClient
        required = [
            "generate_text",     # chat.create
            "continue_response", # responses.create with previous_response_id
            "generate_image",    # image.sample
            "edit_image",        # image.sample with image_url(s)
            "generate_video",    # video.generate (also handles reference-to-video)
            "edit_video",        # video.generate with video_url
            "extend_video",      # /v1/videos/extensions
        ]
        for name in required:
            method = getattr(GrokClient, name, None)
            assert method is not None, f"GrokClient is missing public method: {name}"
            assert inspect.iscoroutinefunction(method), (
                f"GrokClient.{name} must be async so ComfyUI's executor can "
                f"parallelize the model nodes that call it."
            )

    def test_sync_helpers_exist(self):
        """Each public async method should have a _<name>_sync counterpart for to_thread wrapping."""
        from erpk.grok.grok_api.client import GrokClient
        for name in ["generate_text", "generate_image", "edit_image", "generate_video", "extend_video"]:
            helper = getattr(GrokClient, f"_{name}_sync", None)
            assert helper is not None, (
                f"GrokClient is missing _{name}_sync. Pattern: public async method "
                f"wraps the sync helper via asyncio.to_thread, so retries/error handling "
                f"in the SDK stay in the worker thread."
            )
            assert not inspect.iscoroutinefunction(helper), (
                f"_{name}_sync must stay sync — it's the body that runs inside to_thread."
            )

    def test_init_accepts_optional_api_key(self):
        """Multi-tier key resolution: explicit > Settings > env > config.ini."""
        from erpk.grok.grok_api.client import GrokClient
        sig = inspect.signature(GrokClient.__init__)
        api_key_param = sig.parameters.get("api_key")
        assert api_key_param is not None
        assert api_key_param.default is None, "api_key must default to None to trigger resolution chain"


# ---------------------------------------------------------------------------
# Phase 2: Video nodes
# ---------------------------------------------------------------------------

def _get_video_node(name):
    """Import a Grok video node class by name from grok.video_nodes."""
    from erpk.grok import video_nodes
    return getattr(video_nodes, name)


def _schema_input(schema, input_id):
    """Return the first input with the given id, or None."""
    matches = [i for i in schema.inputs if i.id == input_id]
    return matches[0] if matches else None


class TestGrokTextToVideo:
    """text-to-video: prompt → video_url string."""

    def test_node_id(self):
        cls = _get_video_node("GrokTextToVideo")
        assert cls.define_schema().node_id == "GrokTextToVideo"

    def test_execute_is_async(self):
        cls = _get_video_node("GrokTextToVideo")
        assert inspect.iscoroutinefunction(cls.execute)

    def test_output_is_string_video_url(self):
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_prompt_is_required(self):
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "prompt")
        assert inp is not None
        assert not inp.optional

    def test_client_is_optional(self):
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None
        assert inp.optional

    def test_model_default_matches_client_constant(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "model")
        assert inp is not None
        assert inp.default == GrokClient.DEFAULT_VIDEO_MODEL

    def test_aspect_ratio_options_match_client_constants(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "aspect_ratio")
        assert inp is not None
        assert set(inp.options) == set(GrokClient.VIDEO_ASPECT_RATIOS)

    def test_resolution_options_match_client_constants(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "resolution")
        assert inp is not None
        assert set(inp.options) == set(GrokClient.VIDEO_RESOLUTIONS)

    def test_duration_bounds(self):
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "duration")
        assert inp is not None
        assert inp.min == 1
        assert inp.max == 15

    def test_seed_is_optional(self):
        cls = _get_video_node("GrokTextToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "seed")
        assert inp is not None
        assert inp.optional


class TestGrokRefToVideo:
    """reference-to-video: prompt + reference images → video_url string."""

    def test_node_id(self):
        cls = _get_video_node("GrokRefToVideo")
        assert cls.define_schema().node_id == "GrokRefToVideo"

    def test_execute_is_async(self):
        cls = _get_video_node("GrokRefToVideo")
        assert inspect.iscoroutinefunction(cls.execute)

    def test_output_is_string_video_url(self):
        cls = _get_video_node("GrokRefToVideo")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_prompt_is_required(self):
        cls = _get_video_node("GrokRefToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "prompt")
        assert inp is not None
        assert not inp.optional

    def test_reference_images_input_exists(self):
        cls = _get_video_node("GrokRefToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "reference_images")
        assert inp is not None
        assert inp.io_type == "IMAGE"

    def test_client_is_optional(self):
        cls = _get_video_node("GrokRefToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None
        assert inp.optional

    def test_model_default_matches_client_constant(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokRefToVideo")
        schema = cls.define_schema()
        inp = _schema_input(schema, "model")
        assert inp.default == GrokClient.DEFAULT_VIDEO_MODEL


class TestGrokVideoEdit:
    """video-edit: prompt + source video_url → edited video_url string."""

    def test_node_id(self):
        cls = _get_video_node("GrokVideoEdit")
        assert cls.define_schema().node_id == "GrokVideoEdit"

    def test_execute_is_async(self):
        cls = _get_video_node("GrokVideoEdit")
        assert inspect.iscoroutinefunction(cls.execute)

    def test_output_is_string_video_url(self):
        cls = _get_video_node("GrokVideoEdit")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_prompt_is_required(self):
        cls = _get_video_node("GrokVideoEdit")
        schema = cls.define_schema()
        inp = _schema_input(schema, "prompt")
        assert inp is not None
        assert not inp.optional

    def test_video_url_input_is_required(self):
        cls = _get_video_node("GrokVideoEdit")
        schema = cls.define_schema()
        inp = _schema_input(schema, "video_url")
        assert inp is not None
        assert not inp.optional

    def test_client_is_optional(self):
        cls = _get_video_node("GrokVideoEdit")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None
        assert inp.optional

    def test_model_default_matches_client_constant(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokVideoEdit")
        schema = cls.define_schema()
        inp = _schema_input(schema, "model")
        assert inp.default == GrokClient.DEFAULT_VIDEO_MODEL


class TestGrokVideoExtend:
    """video-extend: source video_url + duration → extended video_url string."""

    def test_node_id(self):
        cls = _get_video_node("GrokVideoExtend")
        assert cls.define_schema().node_id == "GrokVideoExtend"

    def test_execute_is_async(self):
        cls = _get_video_node("GrokVideoExtend")
        assert inspect.iscoroutinefunction(cls.execute)

    def test_output_is_string_video_url(self):
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_video_url_input_is_required(self):
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        inp = _schema_input(schema, "video_url")
        assert inp is not None
        assert not inp.optional

    def test_prompt_is_optional(self):
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        inp = _schema_input(schema, "prompt")
        assert inp is not None
        assert inp.optional

    def test_client_is_optional(self):
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None
        assert inp.optional

    def test_duration_bounds(self):
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        inp = _schema_input(schema, "duration")
        assert inp is not None
        assert inp.min == 1
        assert inp.max == 15

    def test_model_default_matches_client_constant(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_video_node("GrokVideoExtend")
        schema = cls.define_schema()
        inp = _schema_input(schema, "model")
        assert inp.default == GrokClient.DEFAULT_VIDEO_MODEL

# ---------------------------------------------------------------------------
# Phase 2: Text and image nodes (grok-text-image-converter)
# ---------------------------------------------------------------------------

def _get_text_image_node(name):
    """Import a Grok text/image node class by name from grok.nodes."""
    from erpk.grok import nodes
    return getattr(nodes, name)


class TestGrokTextGeneration:
    """One-shot prompt-to-response node using GrokClient.generate_text."""

    def test_node_id_is_registered(self):
        cls = _get_text_image_node("GrokTextGeneration")
        assert cls.define_schema().node_id == "GrokTextGeneration"

    def test_has_prompt_input(self):
        cls = _get_text_image_node("GrokTextGeneration")
        schema = cls.define_schema()
        assert _schema_input(schema, "prompt") is not None

    def test_client_input_is_optional(self):
        cls = _get_text_image_node("GrokTextGeneration")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None and inp.optional is True

    def test_model_input_is_optional(self):
        cls = _get_text_image_node("GrokTextGeneration")
        schema = cls.define_schema()
        inp = _schema_input(schema, "model")
        assert inp is not None and inp.optional is True

    def test_emits_string_response(self):
        cls = _get_text_image_node("GrokTextGeneration")
        schema = cls.define_schema()
        assert len(schema.outputs) >= 1
        assert schema.outputs[0].id == "response"

    def test_execute_is_async(self):
        cls = _get_text_image_node("GrokTextGeneration")
        assert inspect.iscoroutinefunction(cls.execute)


class TestGrokChat:
    """Multi-turn conversation node — maintains history via GROK_CHAT_SESSION."""

    def test_node_id_is_registered(self):
        cls = _get_text_image_node("GrokChat")
        assert cls.define_schema().node_id == "GrokChat"

    def test_has_prompt_input(self):
        cls = _get_text_image_node("GrokChat")
        schema = cls.define_schema()
        assert _schema_input(schema, "prompt") is not None

    def test_client_input_is_optional(self):
        cls = _get_text_image_node("GrokChat")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None and inp.optional is True

    def test_chat_session_input_is_optional_and_typed(self):
        cls = _get_text_image_node("GrokChat")
        schema = cls.define_schema()
        inp = _schema_input(schema, "chat_session")
        assert inp is not None
        assert inp.optional is True
        assert inp.io_type == "GROK_CHAT_SESSION"

    def test_emits_response_and_session(self):
        cls = _get_text_image_node("GrokChat")
        schema = cls.define_schema()
        output_ids = [o.id for o in schema.outputs]
        assert "response" in output_ids
        assert "chat_session" in output_ids

    def test_emits_grok_chat_session_type(self):
        cls = _get_text_image_node("GrokChat")
        schema = cls.define_schema()
        session_out = [o for o in schema.outputs if o.id == "chat_session"]
        assert len(session_out) == 1
        assert session_out[0].io_type == "GROK_CHAT_SESSION"

    def test_execute_is_async(self):
        cls = _get_text_image_node("GrokChat")
        assert inspect.iscoroutinefunction(cls.execute)


class TestGrokImageGeneration:
    """Text-to-image node via GrokClient.generate_image."""

    def test_node_id_is_registered(self):
        cls = _get_text_image_node("GrokImageGeneration")
        assert cls.define_schema().node_id == "GrokImageGeneration"

    def test_has_prompt_input(self):
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        assert _schema_input(schema, "prompt") is not None

    def test_client_input_is_optional(self):
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None and inp.optional is True

    def test_has_aspect_ratio_and_resolution_inputs(self):
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        assert _schema_input(schema, "aspect_ratio") is not None
        assert _schema_input(schema, "resolution") is not None

    def test_aspect_ratio_options_match_client_constants(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        inp = _schema_input(schema, "aspect_ratio")
        assert set(inp.options) == set(GrokClient.IMAGE_ASPECT_RATIOS)

    def test_resolution_options_match_client_constants(self):
        from erpk.grok.grok_api.client import GrokClient
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        inp = _schema_input(schema, "resolution")
        assert set(inp.options) == set(GrokClient.IMAGE_RESOLUTIONS)

    def test_emits_image_output(self):
        cls = _get_text_image_node("GrokImageGeneration")
        schema = cls.define_schema()
        assert len(schema.outputs) >= 1
        assert schema.outputs[0].id == "image"

    def test_execute_is_async(self):
        cls = _get_text_image_node("GrokImageGeneration")
        assert inspect.iscoroutinefunction(cls.execute)


class TestGrokImageEdit:
    """Image editing node via GrokClient.edit_image — takes IMAGE tensor + prompt."""

    def test_node_id_is_registered(self):
        cls = _get_text_image_node("GrokImageEdit")
        assert cls.define_schema().node_id == "GrokImageEdit"

    def test_has_image_and_prompt_inputs(self):
        cls = _get_text_image_node("GrokImageEdit")
        schema = cls.define_schema()
        assert _schema_input(schema, "image") is not None
        assert _schema_input(schema, "prompt") is not None

    def test_client_input_is_optional(self):
        cls = _get_text_image_node("GrokImageEdit")
        schema = cls.define_schema()
        inp = _schema_input(schema, "client")
        assert inp is not None and inp.optional is True

    def test_emits_image_output(self):
        cls = _get_text_image_node("GrokImageEdit")
        schema = cls.define_schema()
        assert len(schema.outputs) >= 1
        assert schema.outputs[0].id == "image"

    def test_execute_is_async(self):
        cls = _get_text_image_node("GrokImageEdit")
        assert inspect.iscoroutinefunction(cls.execute)
