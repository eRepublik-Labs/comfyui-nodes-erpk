# ABOUTME: Tests for WAN 2.7 video generation nodes (text-to-video, image-to-video, video-extend).
# ABOUTME: Validates request API paths, payload shape, and node schemas for all three WAN 2.7 video endpoints.

"""
Tests for Alibaba WAN 2.7 video generation nodes.

Validates:
- Request classes route to the correct /api/v3/alibaba/wan-2.7/* endpoints
- Payloads contain expected fields with correct defaults
- Node schemas expose prompt, client, seed, duration, resolution, aspect_ratio inputs
- Nodes declare not_idempotent=True and emit a video_url string output
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_request(module_name, class_name):
    """Import a request class from the wavespeed_api.requests package."""
    import importlib
    mod = importlib.import_module(f"wavespeed.wavespeed_api.requests.{module_name}")
    return getattr(mod, class_name)


def _import_node(module_name, class_name):
    """Import a node class from the wavespeed package."""
    import importlib
    mod = importlib.import_module(f"wavespeed.{module_name}")
    return getattr(mod, class_name)


# --- Request classes ---------------------------------------------------------


class TestWan27TextToVideoRequest:
    """Wan27TextToVideo request routes to the text-to-video endpoint."""

    def test_api_path(self):
        cls = _import_request("wan_2_7_text_to_video", "Wan27TextToVideo")
        request = cls(prompt="a cat")
        assert request.get_api_path() == "/api/v3/alibaba/wan-2.7/text-to-video"

    def test_prompt_required(self):
        cls = _import_request("wan_2_7_text_to_video", "Wan27TextToVideo")
        assert "prompt" in cls(prompt="hi").field_required()

    def test_defaults_included_in_payload(self):
        cls = _import_request("wan_2_7_text_to_video", "Wan27TextToVideo")
        payload = cls(prompt="a cat").build_payload()
        assert payload["prompt"] == "a cat"
        assert payload["duration"] == 5
        assert payload["aspect_ratio"] == "16:9"
        assert payload["resolution"] == "720p"
        assert payload["seed"] == -1

    def test_all_fields_propagate(self):
        cls = _import_request("wan_2_7_text_to_video", "Wan27TextToVideo")
        payload = cls(
            prompt="a cat",
            negative_prompt="blurry",
            audio="http://example.com/a.mp3",
            duration=10,
            aspect_ratio="9:16",
            resolution="1080p",
            enable_prompt_expansion=True,
            seed=42,
        ).build_payload()
        assert payload["negative_prompt"] == "blurry"
        assert payload["audio"] == "http://example.com/a.mp3"
        assert payload["duration"] == 10
        assert payload["aspect_ratio"] == "9:16"
        assert payload["resolution"] == "1080p"
        assert payload["enable_prompt_expansion"] is True
        assert payload["seed"] == 42


class TestWan27ImageToVideoRequest:
    """Wan27ImageToVideo request routes to the image-to-video endpoint."""

    def test_api_path(self):
        cls = _import_request("wan_2_7_image_to_video", "Wan27ImageToVideo")
        request = cls(prompt="a cat", image="http://example.com/cat.jpg")
        assert request.get_api_path() == "/api/v3/alibaba/wan-2.7/image-to-video"

    def test_required_fields(self):
        cls = _import_request("wan_2_7_image_to_video", "Wan27ImageToVideo")
        required = cls(prompt="a", image="http://example.com/x.jpg").field_required()
        assert "prompt" in required
        assert "image" in required

    def test_defaults_included_in_payload(self):
        cls = _import_request("wan_2_7_image_to_video", "Wan27ImageToVideo")
        payload = cls(prompt="a cat", image="http://example.com/cat.jpg").build_payload()
        assert payload["prompt"] == "a cat"
        assert payload["image"] == "http://example.com/cat.jpg"
        assert payload["duration"] == 5
        assert payload["resolution"] == "720p"
        assert payload["seed"] == -1

    def test_optional_last_image_propagates(self):
        cls = _import_request("wan_2_7_image_to_video", "Wan27ImageToVideo")
        payload = cls(
            prompt="a cat",
            image="http://example.com/cat.jpg",
            last_image="http://example.com/end.jpg",
        ).build_payload()
        assert payload["last_image"] == "http://example.com/end.jpg"


class TestWan27VideoExtendRequest:
    """Wan27VideoExtend request routes to the video-extend endpoint."""

    def test_api_path(self):
        cls = _import_request("wan_2_7_video_extend", "Wan27VideoExtend")
        request = cls(prompt="continue", video="http://example.com/clip.mp4")
        assert request.get_api_path() == "/api/v3/alibaba/wan-2.7/video-extend"

    def test_required_fields(self):
        cls = _import_request("wan_2_7_video_extend", "Wan27VideoExtend")
        required = cls(prompt="continue", video="http://example.com/x.mp4").field_required()
        assert "prompt" in required
        assert "video" in required

    def test_video_field_is_video_not_video_url(self):
        """WAN 2.7 video-extend uses the `video` field, not `video_url`."""
        cls = _import_request("wan_2_7_video_extend", "Wan27VideoExtend")
        payload = cls(
            prompt="continue",
            video="http://example.com/clip.mp4",
        ).build_payload()
        assert "video" in payload
        assert payload["video"] == "http://example.com/clip.mp4"
        assert "video_url" not in payload

    def test_defaults_included_in_payload(self):
        cls = _import_request("wan_2_7_video_extend", "Wan27VideoExtend")
        payload = cls(
            prompt="continue",
            video="http://example.com/clip.mp4",
        ).build_payload()
        assert payload["duration"] == 5
        assert payload["resolution"] == "720p"
        assert payload["seed"] == -1


# --- Node schemas ------------------------------------------------------------


class TestWan27TextToVideoNode:
    """Wan27TextToVideoNode schema exposes expected inputs and output."""

    def test_is_comfy_node(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_schema_metadata(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        assert schema.node_id == "Wan27TextToVideoNode"
        assert schema.display_name == "Alibaba WAN 2.7 Text-to-Video"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True

    def test_execute_is_classmethod(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_has_prompt_input(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "prompt" in ids

    def test_has_optional_client_input(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_has_seed_input(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        seed_inputs = [i for i in schema.inputs if i.id == "seed"]
        assert len(seed_inputs) == 1
        assert seed_inputs[0].default == -1

    def test_has_duration_input(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        duration = next(i for i in schema.inputs if i.id == "duration")
        assert duration.default == 5

    def test_has_aspect_ratio_combo(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        ar = next(i for i in schema.inputs if i.id == "aspect_ratio")
        assert "16:9" in ar.options
        assert "9:16" in ar.options
        assert "1:1" in ar.options

    def test_has_resolution_combo(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        res = next(i for i in schema.inputs if i.id == "resolution")
        assert "720p" in res.options
        assert "1080p" in res.options

    def test_outputs_video_url(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.id == "video_url"
        assert out.io_type == "STRING"

    def test_fingerprint_nan_for_random_seed(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        fp = cls.fingerprint_inputs(seed=-1)
        assert fp != fp  # NaN != NaN

    def test_fingerprint_value_for_fixed_seed(self):
        cls = _import_node("wan_2_7_text_to_video", "Wan27TextToVideoNode")
        assert cls.fingerprint_inputs(seed=42) == 42


class TestWan27ImageToVideoNode:
    """Wan27ImageToVideoNode schema exposes expected inputs and output."""

    def test_is_comfy_node(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_schema_metadata(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        schema = cls.define_schema()
        assert schema.node_id == "Wan27ImageToVideoNode"
        assert schema.display_name == "Alibaba WAN 2.7 Image-to-Video"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True

    def test_execute_is_classmethod(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_has_prompt_and_image_inputs(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "prompt" in ids
        assert "image" in ids

    def test_has_optional_client_input(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_has_duration_and_resolution(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "duration" in ids
        assert "resolution" in ids

    def test_outputs_video_url(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].id == "video_url"
        assert schema.outputs[0].io_type == "STRING"

    def test_fingerprint_nan_for_random_seed(self):
        cls = _import_node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
        fp = cls.fingerprint_inputs(seed=-1)
        assert fp != fp


class TestWan27VideoExtendNode:
    """Wan27VideoExtendNode schema exposes expected inputs and output."""

    def test_is_comfy_node(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_schema_metadata(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        schema = cls.define_schema()
        assert schema.node_id == "Wan27VideoExtendNode"
        assert schema.display_name == "Alibaba WAN 2.7 Video Extend"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True

    def test_execute_is_classmethod(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_has_prompt_and_video_url_inputs(self):
        """Node schema exposes a `video_url` input (per task spec) to accept the source clip."""
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        schema = cls.define_schema()
        ids = [i.id for i in schema.inputs]
        assert "prompt" in ids
        assert "video_url" in ids

    def test_has_extend_duration_input(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        schema = cls.define_schema()
        extend = next(i for i in schema.inputs if i.id == "extend_duration")
        assert extend.default == 5

    def test_has_optional_client_input(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_outputs_video_url(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].id == "video_url"
        assert schema.outputs[0].io_type == "STRING"

    def test_fingerprint_nan_for_random_seed(self):
        cls = _import_node("wan_2_7_video_extend", "Wan27VideoExtendNode")
        fp = cls.fingerprint_inputs(seed=-1)
        assert fp != fp
