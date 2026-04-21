# ABOUTME: Tests for Seedance 2.0 text-to-video and image-to-video nodes and request classes.
# ABOUTME: Validates API endpoints, model dispatch, payload structure, and node schemas.

"""
Tests for Seedance 2.0 video nodes and requests.

Validates:
- Request classes route to the correct text-to-video / image-to-video endpoints
- Fast/Turbo variants inherit base payload and override only the endpoint
- Node schemas expose model combo, prompt, duration, aspect_ratio, resolution, seed
- Execute dispatches to the correct request class based on model selection
- Video nodes output STRING (video_url) instead of IMAGE
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


# ---------- Request class tests ----------

class TestSeedance20TextToVideoRequest:
    """Seedance20TextToVideo request routes to the text-to-video endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/text-to-video"

    def test_prompt_is_required(self):
        cls = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        request = cls(prompt="a cat dancing")
        assert "prompt" in request.field_required()

    def test_payload_includes_video_params(self):
        cls = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        request = cls(
            prompt="a cat dancing",
            duration=5,
            aspect_ratio="16:9",
            resolution="720p",
            seed=42,
        )
        payload = request.build_payload()
        assert payload["prompt"] == "a cat dancing"
        assert payload["duration"] == 5
        assert payload["aspect_ratio"] == "16:9"
        assert payload["resolution"] == "720p"
        assert payload["seed"] == 42

    def test_empty_fields_removed_from_payload(self):
        cls = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        request = cls(prompt="x")
        payload = request.build_payload()
        assert "prompt" in payload
        # None defaults should be stripped
        assert all(v is not None for v in payload.values())


class TestSeedance20TextToVideoFastRequest:
    """Fast variant routes to the -fast endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_text_to_video_fast", "Seedance20TextToVideoFast")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/text-to-video-fast"

    def test_inherits_from_base(self):
        base = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        cls = _import_request("seedance_2_0_text_to_video_fast", "Seedance20TextToVideoFast")
        assert issubclass(cls, base)

    def test_payload_matches_base(self):
        base = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        cls = _import_request("seedance_2_0_text_to_video_fast", "Seedance20TextToVideoFast")
        kwargs = dict(prompt="hi", duration=5, aspect_ratio="9:16", resolution="480p", seed=7)
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


class TestSeedance20TextToVideoTurboRequest:
    """Turbo variant routes to the -turbo endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_text_to_video_turbo", "Seedance20TextToVideoTurbo")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/text-to-video-turbo"

    def test_inherits_from_base(self):
        base = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        cls = _import_request("seedance_2_0_text_to_video_turbo", "Seedance20TextToVideoTurbo")
        assert issubclass(cls, base)

    def test_payload_matches_base(self):
        base = _import_request("seedance_2_0_text_to_video", "Seedance20TextToVideo")
        cls = _import_request("seedance_2_0_text_to_video_turbo", "Seedance20TextToVideoTurbo")
        kwargs = dict(prompt="x", duration=6, aspect_ratio="1:1", resolution="1080p", seed=9)
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


class TestSeedance20ImageToVideoRequest:
    """Seedance20ImageToVideo request routes to the image-to-video endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        request = cls(prompt="test", image="http://example.com/a.jpg")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/image-to-video"

    def test_prompt_and_image_are_required(self):
        cls = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        request = cls(prompt="animate", image="http://example.com/a.jpg")
        required = request.field_required()
        assert "prompt" in required
        assert "image" in required

    def test_payload_includes_image_and_video_params(self):
        cls = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        request = cls(
            prompt="pan across",
            image="http://example.com/a.jpg",
            duration=5,
            aspect_ratio="16:9",
            resolution="720p",
            seed=11,
        )
        payload = request.build_payload()
        assert payload["prompt"] == "pan across"
        assert payload["image"] == "http://example.com/a.jpg"
        assert payload["duration"] == 5
        assert payload["aspect_ratio"] == "16:9"
        assert payload["resolution"] == "720p"


class TestSeedance20ImageToVideoFastRequest:
    """Fast variant routes to the -fast endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_image_to_video_fast", "Seedance20ImageToVideoFast")
        request = cls(prompt="x", image="http://example.com/a.jpg")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/image-to-video-fast"

    def test_inherits_from_base(self):
        base = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        cls = _import_request("seedance_2_0_image_to_video_fast", "Seedance20ImageToVideoFast")
        assert issubclass(cls, base)

    def test_payload_matches_base(self):
        base = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        cls = _import_request("seedance_2_0_image_to_video_fast", "Seedance20ImageToVideoFast")
        kwargs = dict(prompt="x", image="http://example.com/a.jpg", duration=4,
                      aspect_ratio="16:9", resolution="480p", seed=5)
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


class TestSeedance20ImageToVideoTurboRequest:
    """Turbo variant routes to the -turbo endpoint."""

    def test_api_path(self):
        cls = _import_request("seedance_2_0_image_to_video_turbo", "Seedance20ImageToVideoTurbo")
        request = cls(prompt="x", image="http://example.com/a.jpg")
        assert request.get_api_path() == "/api/v3/bytedance/seedance-2.0/image-to-video-turbo"

    def test_inherits_from_base(self):
        base = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        cls = _import_request("seedance_2_0_image_to_video_turbo", "Seedance20ImageToVideoTurbo")
        assert issubclass(cls, base)

    def test_payload_matches_base(self):
        base = _import_request("seedance_2_0_image_to_video", "Seedance20ImageToVideo")
        cls = _import_request("seedance_2_0_image_to_video_turbo", "Seedance20ImageToVideoTurbo")
        kwargs = dict(prompt="x", image="http://example.com/a.jpg", duration=8,
                      aspect_ratio="9:16", resolution="1080p", seed=1)
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


# ---------- Node schema tests ----------

class TestSeedance20TextToVideoNodeSchema:
    """Seedance20TextToVideoNode exposes the expected schema."""

    def test_node_id(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert cls.define_schema().node_id == "Seedance20TextToVideoNode"

    def test_display_name(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert cls.define_schema().display_name == "Bytedance Seedance 2.0 Text-to-Video"

    def test_category(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert cls.define_schema().category == "ERPK/WaveSpeedAI"

    def test_not_idempotent(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert cls.define_schema().not_idempotent is True

    def test_inherits_comfy_node(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_execute_is_classmethod(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_model_input_options(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        model_input = next(i for i in cls.define_schema().inputs if i.id == "model")
        assert "Seedance 2.0" in model_input.options
        assert "Seedance 2.0 Fast" in model_input.options
        assert "Seedance 2.0 Turbo" in model_input.options

    def test_model_default(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        model_input = next(i for i in cls.define_schema().inputs if i.id == "model")
        assert model_input.default == "Seedance 2.0"

    def test_prompt_input_present(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        prompt = next(i for i in cls.define_schema().inputs if i.id == "prompt")
        assert prompt.multiline is True

    def test_duration_input(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        duration = next(i for i in cls.define_schema().inputs if i.id == "duration")
        assert duration.default == 5

    def test_aspect_ratio_input(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        aspect = next(i for i in cls.define_schema().inputs if i.id == "aspect_ratio")
        assert "16:9" in aspect.options
        assert "9:16" in aspect.options
        assert "1:1" in aspect.options
        assert aspect.default == "16:9"

    def test_resolution_input(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        res = next(i for i in cls.define_schema().inputs if i.id == "resolution")
        assert "480p" in res.options
        assert "720p" in res.options
        assert "1080p" in res.options
        assert res.default == "720p"

    def test_seed_input(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        seed = next(i for i in cls.define_schema().inputs if i.id == "seed")
        assert seed.default == -1
        assert seed.min == -1
        assert seed.max == 2147483647

    def test_client_input_optional(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        client = next(i for i in cls.define_schema().inputs if i.id == "client")
        assert client.optional is True
        assert client.io_type == "WAVESPEED_AI_API_CLIENT"

    def test_output_is_string_video_url(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        outputs = cls.define_schema().outputs
        assert len(outputs) == 1
        assert outputs[0].io_type == "STRING"
        assert outputs[0].id == "video_url"

    def test_fingerprint_nan_on_random_seed(self):
        import math
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert math.isnan(cls.fingerprint_inputs(seed=-1))

    def test_fingerprint_returns_seed_when_fixed(self):
        cls = _import_node("seedance_2_0_text_to_video", "Seedance20TextToVideoNode")
        assert cls.fingerprint_inputs(seed=42) == 42


class TestSeedance20ImageToVideoNodeSchema:
    """Seedance20ImageToVideoNode exposes the expected schema."""

    def test_node_id(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert cls.define_schema().node_id == "Seedance20ImageToVideoNode"

    def test_display_name(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert cls.define_schema().display_name == "Bytedance Seedance 2.0 Image-to-Video"

    def test_category(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert cls.define_schema().category == "ERPK/WaveSpeedAI"

    def test_not_idempotent(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert cls.define_schema().not_idempotent is True

    def test_inherits_comfy_node(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert issubclass(cls, IO.ComfyNode)

    def test_execute_is_classmethod(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod)

    def test_model_input_options(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        model_input = next(i for i in cls.define_schema().inputs if i.id == "model")
        assert "Seedance 2.0" in model_input.options
        assert "Seedance 2.0 Fast" in model_input.options
        assert "Seedance 2.0 Turbo" in model_input.options

    def test_image_input_present(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        image = next(i for i in cls.define_schema().inputs if i.id == "image")
        assert image.io_type == "STRING"

    def test_client_input_optional(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        client = next(i for i in cls.define_schema().inputs if i.id == "client")
        assert client.optional is True
        assert client.io_type == "WAVESPEED_AI_API_CLIENT"

    def test_output_is_string_video_url(self):
        cls = _import_node("seedance_2_0_image_to_video", "Seedance20ImageToVideoNode")
        outputs = cls.define_schema().outputs
        assert len(outputs) == 1
        assert outputs[0].io_type == "STRING"
        assert outputs[0].id == "video_url"


# ---------- Model dispatch tests ----------

class TestSeedance20TextToVideoDispatch:
    """Node execute() dispatches to the correct request class for each model tier."""

    def test_model_maps_to_request_class(self):
        """Verify the internal model_map returns correct class per tier."""
        from wavespeed.seedance_2_0_text_to_video import Seedance20TextToVideoNode
        from wavespeed.wavespeed_api.requests.seedance_2_0_text_to_video import Seedance20TextToVideo
        from wavespeed.wavespeed_api.requests.seedance_2_0_text_to_video_fast import Seedance20TextToVideoFast
        from wavespeed.wavespeed_api.requests.seedance_2_0_text_to_video_turbo import Seedance20TextToVideoTurbo

        mapping = Seedance20TextToVideoNode._request_class_for("Seedance 2.0")
        assert mapping is Seedance20TextToVideo
        assert Seedance20TextToVideoNode._request_class_for("Seedance 2.0 Fast") is Seedance20TextToVideoFast
        assert Seedance20TextToVideoNode._request_class_for("Seedance 2.0 Turbo") is Seedance20TextToVideoTurbo


class TestSeedance20ImageToVideoDispatch:
    """Node execute() dispatches to the correct request class for each model tier."""

    def test_model_maps_to_request_class(self):
        from wavespeed.seedance_2_0_image_to_video import Seedance20ImageToVideoNode
        from wavespeed.wavespeed_api.requests.seedance_2_0_image_to_video import Seedance20ImageToVideo
        from wavespeed.wavespeed_api.requests.seedance_2_0_image_to_video_fast import Seedance20ImageToVideoFast
        from wavespeed.wavespeed_api.requests.seedance_2_0_image_to_video_turbo import Seedance20ImageToVideoTurbo

        assert Seedance20ImageToVideoNode._request_class_for("Seedance 2.0") is Seedance20ImageToVideo
        assert Seedance20ImageToVideoNode._request_class_for("Seedance 2.0 Fast") is Seedance20ImageToVideoFast
        assert Seedance20ImageToVideoNode._request_class_for("Seedance 2.0 Turbo") is Seedance20ImageToVideoTurbo
