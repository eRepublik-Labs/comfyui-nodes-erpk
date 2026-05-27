# ABOUTME: Tests for Kling 3.0 and Kling O3 video generation nodes (WaveSpeed).
# ABOUTME: Covers 3 nodes, 6 endpoints across kling-v3.0 and kling-video-o3 namespaces.

"""
Tests for Kling video endpoints.

Validates:
- Request subclasses route to correct API paths in the two namespaces:
  * kling-v3.0-std/pro (image-to-video only)
  * kling-video-o3-std/pro (text-to-video, image-to-video)
- Request payload equality between std/pro variants
- Node schemas expose model combo + prompt + seed + duration + aspect_ratio
- Image-to-video nodes accept an 'image' string input
- not_idempotent=True on all nodes, fingerprint_inputs -> NaN on seed=-1
- Output is a single STRING video_url
"""

import asyncio
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


# ---------------------------------------------------------------------------
# Request class tests — Kling 3.0 image-to-video (kling-v3.0 namespace)
# ---------------------------------------------------------------------------

class TestKlingV3ImageToVideoRequest:
    """Kling 3.0 std + Pro image-to-video requests route to the correct endpoints."""

    def test_standard_api_path(self):
        cls = _import_request("kling_v3_image_to_video", "KlingV3ImageToVideo")
        request = cls(prompt="test", image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-v3.0-std/image-to-video"

    def test_pro_api_path(self):
        cls = _import_request("kling_v3_pro_image_to_video", "KlingV3ProImageToVideo")
        request = cls(prompt="test", image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-v3.0-pro/image-to-video"

    def test_pro_inherits_from_standard(self):
        base = _import_request("kling_v3_image_to_video", "KlingV3ImageToVideo")
        cls = _import_request("kling_v3_pro_image_to_video", "KlingV3ProImageToVideo")
        assert issubclass(cls, base)

    def test_pro_payload_matches_standard(self):
        base = _import_request("kling_v3_image_to_video", "KlingV3ImageToVideo")
        cls = _import_request("kling_v3_pro_image_to_video", "KlingV3ProImageToVideo")
        kwargs = dict(
            prompt="a running dog",
            image="http://example.com/dog.jpg",
            seed=42,
            duration=5,
            aspect_ratio="16:9",
        )
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()

    def test_payload_contains_prompt_and_image(self):
        cls = _import_request("kling_v3_image_to_video", "KlingV3ImageToVideo")
        req = cls(prompt="x", image="http://example.com/a.jpg")
        payload = req.build_payload()
        assert payload["prompt"] == "x"
        assert payload["image"] == "http://example.com/a.jpg"


# ---------------------------------------------------------------------------
# Request class tests — Kling O3 text-to-video (kling-video-o3 namespace)
# ---------------------------------------------------------------------------

class TestKlingO3TextToVideoRequest:
    """Kling O3 std + Pro text-to-video requests route to the correct endpoints."""

    def test_standard_api_path(self):
        cls = _import_request("kling_o3_text_to_video", "KlingO3TextToVideo")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-std/text-to-video"

    def test_pro_api_path(self):
        cls = _import_request("kling_o3_pro_text_to_video", "KlingO3ProTextToVideo")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-pro/text-to-video"

    def test_pro_inherits_from_standard(self):
        base = _import_request("kling_o3_text_to_video", "KlingO3TextToVideo")
        cls = _import_request("kling_o3_pro_text_to_video", "KlingO3ProTextToVideo")
        assert issubclass(cls, base)

    def test_pro_payload_matches_standard(self):
        base = _import_request("kling_o3_text_to_video", "KlingO3TextToVideo")
        cls = _import_request("kling_o3_pro_text_to_video", "KlingO3ProTextToVideo")
        kwargs = dict(
            prompt="a cat dancing",
            seed=7,
            duration=5,
            aspect_ratio="16:9",
        )
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


# ---------------------------------------------------------------------------
# Request class tests — Kling O3 image-to-video (kling-video-o3 namespace)
# ---------------------------------------------------------------------------

class TestKlingO3ImageToVideoRequest:
    """Kling O3 std + Pro image-to-video requests route to the correct endpoints."""

    def test_standard_api_path(self):
        cls = _import_request("kling_o3_image_to_video", "KlingO3ImageToVideo")
        request = cls(prompt="test", image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-std/image-to-video"

    def test_pro_api_path(self):
        cls = _import_request("kling_o3_pro_image_to_video", "KlingO3ProImageToVideo")
        request = cls(prompt="test", image="http://example.com/img.jpg")
        assert request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-pro/image-to-video"

    def test_pro_inherits_from_standard(self):
        base = _import_request("kling_o3_image_to_video", "KlingO3ImageToVideo")
        cls = _import_request("kling_o3_pro_image_to_video", "KlingO3ProImageToVideo")
        assert issubclass(cls, base)

    def test_pro_payload_matches_standard(self):
        base = _import_request("kling_o3_image_to_video", "KlingO3ImageToVideo")
        cls = _import_request("kling_o3_pro_image_to_video", "KlingO3ProImageToVideo")
        kwargs = dict(
            prompt="zoom on the subject",
            image="http://example.com/subject.jpg",
            seed=9,
            duration=10,
            aspect_ratio="9:16",
        )
        assert base(**kwargs).build_payload() == cls(**kwargs).build_payload()


# ---------------------------------------------------------------------------
# Namespace split sanity: v3 and o3 must NOT share the same path prefix
# ---------------------------------------------------------------------------

class TestKlingNamespaceSplit:
    """Kling v3 endpoints use kling-v3.0-*, O3 uses kling-video-o3-* under /kwaivgi/."""

    def test_v3_paths_use_kling_v3_0(self):
        std = _import_request("kling_v3_image_to_video", "KlingV3ImageToVideo")
        pro = _import_request("kling_v3_pro_image_to_video", "KlingV3ProImageToVideo")
        for cls in (std, pro):
            path = cls(prompt="x", image="http://example.com/i.jpg").get_api_path()
            assert "/kwaivgi/kling-v3.0-" in path
            assert "kling-video-o3" not in path

    def test_o3_paths_use_kling_video_o3(self):
        cases = [
            ("kling_o3_text_to_video", "KlingO3TextToVideo", {"prompt": "x"}),
            ("kling_o3_pro_text_to_video", "KlingO3ProTextToVideo", {"prompt": "x"}),
            ("kling_o3_image_to_video", "KlingO3ImageToVideo",
             {"prompt": "x", "image": "http://example.com/i.jpg"}),
            ("kling_o3_pro_image_to_video", "KlingO3ProImageToVideo",
             {"prompt": "x", "image": "http://example.com/i.jpg"}),
        ]
        for module, class_name, kwargs in cases:
            cls = _import_request(module, class_name)
            path = cls(**kwargs).get_api_path()
            assert "/kwaivgi/kling-video-o3-" in path
            assert "kling-v3.0" not in path


# ---------------------------------------------------------------------------
# Node tests — KlingV3ImageToVideoNode
# ---------------------------------------------------------------------------

class TestKlingV3ImageToVideoNode:
    """KlingV3ImageToVideoNode schema and behavior."""

    def _node(self):
        return _import_node("kling_v3_image_to_video", "KlingV3ImageToVideoNode")

    def test_inherits_comfy_node(self):
        assert issubclass(self._node(), IO.ComfyNode)

    def test_schema_basics(self):
        schema = self._node().define_schema()
        assert schema.node_id == "KlingV3ImageToVideoNode"
        assert schema.display_name == "Kling 3.0 Image-to-Video"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True
        assert schema.is_output_node is False

    def test_model_combo_options(self):
        schema = self._node().define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Kling 3.0" in model_input.options
        assert "Kling 3.0 Pro" in model_input.options
        assert model_input.default == "Kling 3.0"

    def test_required_inputs_present(self):
        schema = self._node().define_schema()
        ids = {i.id for i in schema.inputs}
        assert "prompt" in ids
        assert "image" in ids
        assert "seed" in ids
        assert "duration" in ids

    def test_client_optional(self):
        schema = self._node().define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_duration_bounds(self):
        schema = self._node().define_schema()
        duration = next(i for i in schema.inputs if i.id == "duration")
        assert duration.default == 5
        assert duration.min == 3
        assert duration.max == 15

    def test_output_is_string_video_url(self):
        schema = self._node().define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_fingerprint_nan_on_random_seed(self):
        result = self._node().fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result)

    def test_fingerprint_returns_seed_when_set(self):
        assert self._node().fingerprint_inputs(seed=12345) == 12345


# ---------------------------------------------------------------------------
# Node tests — KlingO3TextToVideoNode
# ---------------------------------------------------------------------------

class TestKlingO3TextToVideoNode:
    """KlingO3TextToVideoNode schema and behavior."""

    def _node(self):
        return _import_node("kling_o3_text_to_video", "KlingO3TextToVideoNode")

    def test_inherits_comfy_node(self):
        assert issubclass(self._node(), IO.ComfyNode)

    def test_schema_basics(self):
        schema = self._node().define_schema()
        assert schema.node_id == "KlingO3TextToVideoNode"
        assert schema.display_name == "Kling O3 Text-to-Video"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True
        assert schema.is_output_node is False

    def test_model_combo_options(self):
        schema = self._node().define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Kling O3" in model_input.options
        assert "Kling O3 Pro" in model_input.options
        assert model_input.default == "Kling O3"

    def test_required_inputs_present(self):
        schema = self._node().define_schema()
        ids = {i.id for i in schema.inputs}
        assert "prompt" in ids
        assert "seed" in ids
        assert "duration" in ids
        assert "aspect_ratio" in ids
        # text-to-video has no image input
        assert "image" not in ids

    def test_client_optional(self):
        schema = self._node().define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_output_is_string_video_url(self):
        schema = self._node().define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_fingerprint_nan_on_random_seed(self):
        result = self._node().fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result)

    def test_fingerprint_returns_seed_when_set(self):
        assert self._node().fingerprint_inputs(seed=42) == 42


# ---------------------------------------------------------------------------
# Node tests — KlingO3ImageToVideoNode
# ---------------------------------------------------------------------------

class TestKlingO3ImageToVideoNode:
    """KlingO3ImageToVideoNode schema and behavior."""

    def _node(self):
        return _import_node("kling_o3_image_to_video", "KlingO3ImageToVideoNode")

    def test_inherits_comfy_node(self):
        assert issubclass(self._node(), IO.ComfyNode)

    def test_schema_basics(self):
        schema = self._node().define_schema()
        assert schema.node_id == "KlingO3ImageToVideoNode"
        assert schema.display_name == "Kling O3 Image-to-Video"
        assert schema.category == "ERPK/WaveSpeedAI"
        assert schema.not_idempotent is True
        assert schema.is_output_node is False

    def test_model_combo_options(self):
        schema = self._node().define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Kling O3" in model_input.options
        assert "Kling O3 Pro" in model_input.options
        assert model_input.default == "Kling O3"

    def test_required_inputs_present(self):
        schema = self._node().define_schema()
        ids = {i.id for i in schema.inputs}
        assert "prompt" in ids
        assert "image" in ids
        assert "seed" in ids
        assert "duration" in ids

    def test_client_optional(self):
        schema = self._node().define_schema()
        client_inputs = [i for i in schema.inputs if i.id == "client"]
        assert len(client_inputs) == 1
        assert client_inputs[0].optional is True
        assert client_inputs[0].io_type == "WAVESPEED_AI_API_CLIENT"

    def test_output_is_string_video_url(self):
        schema = self._node().define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "STRING"
        assert out.id == "video_url"

    def test_fingerprint_nan_on_random_seed(self):
        result = self._node().fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result)

    def test_fingerprint_returns_seed_when_set(self):
        assert self._node().fingerprint_inputs(seed=999) == 999


# ---------------------------------------------------------------------------
# Execute behavior — dispatch to std vs pro request class per model combo
# ---------------------------------------------------------------------------

class _FakeClient:
    """Captures the BaseRequest passed to send_request; returns a fake video URL."""

    def __init__(self):
        self.requests = []

    async def send_request(self, request, *args, **kwargs):
        self.requests.append((request, args, kwargs))
        return {"outputs": ["http://cdn.example.com/out.mp4"]}


def _patch_client(monkeypatch, fake):
    """Make WaveSpeedClient(api_key) return our fake instance."""
    import wavespeed.wavespeed_api.client as client_mod
    monkeypatch.setattr(client_mod, "WaveSpeedClient", lambda api_key: fake)


class TestKlingV3ImageToVideoExecute:
    """execute() dispatches to std/pro request and returns video_url string."""

    def test_standard_model_uses_std_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_v3_image_to_video", "KlingV3ImageToVideoNode")

        output = asyncio.run(cls.execute(
            model="Kling 3.0",
            prompt="a running dog",
            image="http://example.com/dog.jpg",
            client={"api_key": "fake"},
            seed=123,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-v3.0-std/image-to-video"
        assert output.result[0] == "http://cdn.example.com/out.mp4"

    def test_pro_model_uses_pro_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_v3_image_to_video", "KlingV3ImageToVideoNode")

        asyncio.run(cls.execute(
            model="Kling 3.0 Pro",
            prompt="a running dog",
            image="http://example.com/dog.jpg",
            client={"api_key": "fake"},
            seed=123,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-v3.0-pro/image-to-video"

    def test_requires_prompt(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_v3_image_to_video", "KlingV3ImageToVideoNode")
        with pytest.raises(ValueError, match="[Pp]rompt"):
            asyncio.run(cls.execute(
                model="Kling 3.0",
                prompt="",
                image="http://example.com/x.jpg",
                client={"api_key": "fake"},
            ))

    def test_requires_image(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_v3_image_to_video", "KlingV3ImageToVideoNode")
        with pytest.raises(ValueError, match="[Ii]mage"):
            asyncio.run(cls.execute(
                model="Kling 3.0",
                prompt="test",
                image="",
                client={"api_key": "fake"},
            ))


class TestKlingO3TextToVideoExecute:
    def test_standard_model_uses_std_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_o3_text_to_video", "KlingO3TextToVideoNode")

        output = asyncio.run(cls.execute(
            model="Kling O3",
            prompt="a dancing cat",
            client={"api_key": "fake"},
            seed=1,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-std/text-to-video"
        assert output.result[0] == "http://cdn.example.com/out.mp4"

    def test_pro_model_uses_pro_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_o3_text_to_video", "KlingO3TextToVideoNode")

        asyncio.run(cls.execute(
            model="Kling O3 Pro",
            prompt="a dancing cat",
            client={"api_key": "fake"},
            seed=1,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-pro/text-to-video"


class TestKlingO3ImageToVideoExecute:
    def test_standard_model_uses_std_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_o3_image_to_video", "KlingO3ImageToVideoNode")

        output = asyncio.run(cls.execute(
            model="Kling O3",
            prompt="zoom in",
            image="http://example.com/x.jpg",
            client={"api_key": "fake"},
            seed=1,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-std/image-to-video"
        assert output.result[0] == "http://cdn.example.com/out.mp4"

    def test_pro_model_uses_pro_endpoint(self, monkeypatch):
        fake = _FakeClient()
        _patch_client(monkeypatch, fake)
        cls = _import_node("kling_o3_image_to_video", "KlingO3ImageToVideoNode")

        asyncio.run(cls.execute(
            model="Kling O3 Pro",
            prompt="zoom in",
            image="http://example.com/x.jpg",
            client={"api_key": "fake"},
            seed=1,
            duration=5,
            aspect_ratio="16:9",
        ))

        sent_request = fake.requests[0][0]
        assert sent_request.get_api_path() == "/api/v3/kwaivgi/kling-video-o3-pro/image-to-video"
