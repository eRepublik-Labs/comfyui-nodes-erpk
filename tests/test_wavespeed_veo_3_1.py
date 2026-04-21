# ABOUTME: Tests for WaveSpeed-billed Veo 3.1 text-to-video and image-to-video nodes.
# ABOUTME: Validates V3 compliance, request payloads/endpoints, and node schemas.

"""
Tests for WaveSpeed Veo 3.1 nodes (billed via WaveSpeed, NOT Google direct).

Validates:
- Request classes route to /api/v3/google/veo3.1/{text-to-video,image-to-video}
- Request payloads include all documented Veo 3.1 fields
- Node schemas comply with V3 API (IO.ComfyNode subclass, classmethod execute)
- Nodes appear in ERPK/WaveSpeedAI category and use WAVESPEED_AI_API_CLIENT type
- Node class names do NOT clash with gemini.veo_nodes.VeoTextToVideo/VeoImageToVideo
- Output type is string video_url
- fingerprint_inputs returns NaN when seed=-1
- not_idempotent is True
"""

import inspect
import math
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


class TestWaveSpeedVeo31TextToVideoRequest:
    """Veo 3.1 text-to-video request routes to /api/v3/google/veo3.1/text-to-video."""

    def test_api_path(self):
        cls = _import_request("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideo")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/google/veo3.1/text-to-video"

    def test_prompt_required(self):
        cls = _import_request("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideo")
        request = cls(prompt="hello")
        assert "prompt" in request.field_required()

    def test_payload_contains_core_fields(self):
        cls = _import_request("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideo")
        request = cls(
            prompt="a dog",
            duration=6,
            aspect_ratio="16:9",
            resolution="1080p",
            generate_audio=True,
            seed=42,
        )
        payload = request.build_payload()
        assert payload["prompt"] == "a dog"
        assert payload["duration"] == 6
        assert payload["aspect_ratio"] == "16:9"
        assert payload["resolution"] == "1080p"
        assert payload["generate_audio"] is True
        assert payload["seed"] == 42

    def test_payload_omits_empty_values(self):
        cls = _import_request("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideo")
        request = cls(prompt="test")
        payload = request.build_payload()
        # negative_prompt defaults to None/empty, should not appear
        assert "negative_prompt" not in payload or payload.get("negative_prompt")

    def test_payload_includes_negative_prompt_when_provided(self):
        cls = _import_request("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideo")
        request = cls(prompt="test", negative_prompt="bad stuff")
        payload = request.build_payload()
        assert payload["negative_prompt"] == "bad stuff"


class TestWaveSpeedVeo31ImageToVideoRequest:
    """Veo 3.1 image-to-video request routes to /api/v3/google/veo3.1/image-to-video."""

    def test_api_path(self):
        cls = _import_request("wavespeed_veo_3_1_image_to_video",
                              "WaveSpeedVeo31ImageToVideo")
        request = cls(prompt="test", image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/google/veo3.1/image-to-video"

    def test_prompt_and_image_required(self):
        cls = _import_request("wavespeed_veo_3_1_image_to_video",
                              "WaveSpeedVeo31ImageToVideo")
        request = cls(prompt="hello", image="http://example.com/img.jpg")
        required = request.field_required()
        assert "prompt" in required
        assert "image" in required

    def test_payload_contains_image_url(self):
        cls = _import_request("wavespeed_veo_3_1_image_to_video",
                              "WaveSpeedVeo31ImageToVideo")
        request = cls(
            prompt="make it move",
            image="http://example.com/cat.png",
            duration=4,
            aspect_ratio="9:16",
            resolution="720p",
            generate_audio=False,
        )
        payload = request.build_payload()
        assert payload["image"] == "http://example.com/cat.png"
        assert payload["prompt"] == "make it move"
        assert payload["duration"] == 4
        assert payload["aspect_ratio"] == "9:16"
        assert payload["resolution"] == "720p"
        assert payload["generate_audio"] is False


class TestWaveSpeedVeo31TextToVideoNode:
    """WaveSpeedVeo31TextToVideoNode schema and execute compliance."""

    def test_inherits_comfy_node(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_execute_is_classmethod(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_schema_node_id(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        assert schema.node_id == "WaveSpeedVeo31TextToVideoNode"

    def test_schema_category(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        assert schema.category == "ERPK/WaveSpeedAI"

    def test_schema_not_idempotent(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        assert schema.not_idempotent is True

    def test_schema_has_prompt(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        prompt_inputs = [i for i in schema.inputs if i.id == "prompt"]
        assert len(prompt_inputs) == 1

    def test_schema_client_optional(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_schema_has_duration_int(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        duration_inputs = [i for i in schema.inputs if i.id == "duration"]
        assert len(duration_inputs) == 1
        assert duration_inputs[0].io_type == "INT"
        assert duration_inputs[0].min == 4
        assert duration_inputs[0].max == 8

    def test_schema_has_aspect_ratio_combo(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        ar_inputs = [i for i in schema.inputs if i.id == "aspect_ratio"]
        assert len(ar_inputs) == 1
        assert ar_inputs[0].io_type == "COMBO"
        assert "16:9" in ar_inputs[0].options
        assert "9:16" in ar_inputs[0].options

    def test_schema_has_resolution_combo(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        res_inputs = [i for i in schema.inputs if i.id == "resolution"]
        assert len(res_inputs) == 1
        assert res_inputs[0].io_type == "COMBO"
        assert "720p" in res_inputs[0].options
        assert "1080p" in res_inputs[0].options

    def test_schema_has_audio_enabled(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        audio_inputs = [i for i in schema.inputs if i.id == "audio_enabled"]
        assert len(audio_inputs) == 1
        assert audio_inputs[0].io_type == "BOOLEAN"
        assert audio_inputs[0].default is True

    def test_schema_has_seed_int(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        seed_inputs = [i for i in schema.inputs if i.id == "seed"]
        assert len(seed_inputs) == 1
        assert seed_inputs[0].io_type == "INT"

    def test_output_is_video_url_string(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].id == "video_url"
        assert schema.outputs[0].io_type == "STRING"

    def test_fingerprint_nan_when_seed_negative_one(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        result = cls.fingerprint_inputs(seed=-1)
        assert math.isnan(result)

    def test_fingerprint_returns_seed_when_set(self):
        cls = _import_node("wavespeed_veo_3_1_text_to_video",
                           "WaveSpeedVeo31TextToVideoNode")
        result = cls.fingerprint_inputs(seed=42)
        assert result == 42


class TestWaveSpeedVeo31ImageToVideoNode:
    """WaveSpeedVeo31ImageToVideoNode schema and execute compliance."""

    def test_inherits_comfy_node(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_execute_is_classmethod(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_schema_node_id(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        assert schema.node_id == "WaveSpeedVeo31ImageToVideoNode"

    def test_schema_category(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        assert schema.category == "ERPK/WaveSpeedAI"

    def test_schema_not_idempotent(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        assert schema.not_idempotent is True

    def test_schema_has_image_string(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        image_inputs = [i for i in schema.inputs if i.id == "image"]
        assert len(image_inputs) == 1
        assert image_inputs[0].io_type == "STRING"

    def test_schema_has_prompt(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        prompt_inputs = [i for i in schema.inputs if i.id == "prompt"]
        assert len(prompt_inputs) == 1

    def test_schema_client_optional(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_schema_has_duration_int(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        duration_inputs = [i for i in schema.inputs if i.id == "duration"]
        assert len(duration_inputs) == 1
        assert duration_inputs[0].io_type == "INT"
        assert duration_inputs[0].min == 4
        assert duration_inputs[0].max == 8

    def test_schema_has_aspect_ratio_combo(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        ar_inputs = [i for i in schema.inputs if i.id == "aspect_ratio"]
        assert len(ar_inputs) == 1
        assert ar_inputs[0].io_type == "COMBO"
        assert "16:9" in ar_inputs[0].options
        assert "9:16" in ar_inputs[0].options

    def test_schema_has_resolution_combo(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        res_inputs = [i for i in schema.inputs if i.id == "resolution"]
        assert len(res_inputs) == 1
        assert res_inputs[0].io_type == "COMBO"
        assert "720p" in res_inputs[0].options
        assert "1080p" in res_inputs[0].options

    def test_schema_has_audio_enabled(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        audio_inputs = [i for i in schema.inputs if i.id == "audio_enabled"]
        assert len(audio_inputs) == 1
        assert audio_inputs[0].io_type == "BOOLEAN"
        assert audio_inputs[0].default is True

    def test_output_is_video_url_string(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        schema = cls.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].id == "video_url"
        assert schema.outputs[0].io_type == "STRING"

    def test_fingerprint_nan_when_seed_negative_one(self):
        cls = _import_node("wavespeed_veo_3_1_image_to_video",
                           "WaveSpeedVeo31ImageToVideoNode")
        result = cls.fingerprint_inputs(seed=-1)
        assert math.isnan(result)


class TestNoClashWithGeminiVeoNodes:
    """The WaveSpeed Veo 3.1 node names must not collide with the Gemini Veo nodes."""

    def test_wavespeed_node_ids_differ_from_gemini(self):
        ws_t2v = _import_node("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideoNode")
        ws_i2v = _import_node("wavespeed_veo_3_1_image_to_video",
                              "WaveSpeedVeo31ImageToVideoNode")
        # Gemini ones use node_id "VeoTextToVideo" / "VeoImageToVideo"
        assert ws_t2v.define_schema().node_id != "VeoTextToVideo"
        assert ws_i2v.define_schema().node_id != "VeoImageToVideo"

    def test_wavespeed_category_differs_from_gemini(self):
        ws_t2v = _import_node("wavespeed_veo_3_1_text_to_video",
                              "WaveSpeedVeo31TextToVideoNode")
        assert ws_t2v.define_schema().category == "ERPK/WaveSpeedAI"
        # Gemini version uses ERPK/Gemini/Veo
        assert ws_t2v.define_schema().category != "ERPK/Gemini/Veo"
