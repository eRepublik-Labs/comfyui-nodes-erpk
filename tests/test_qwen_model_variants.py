# ABOUTME: Tests for Qwen Image model variant support (2512 text-to-image, 2511 edit).
# ABOUTME: Validates request API paths, node model combos, and payload compatibility.

"""
Tests for Qwen Image model variant endpoints.

Validates:
- Request subclasses override API paths correctly
- Request payload structure matches parent classes
- Node schemas expose model combo input with correct options
- Model combo defaults to the original model variant
"""

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


class TestQwenTextToImage2512Request:
    """QwenImageTextToImage2512 request routes to the 2512 endpoint."""

    def test_api_path(self):
        cls = _import_request("qwen_image_text_to_image_2512", "QwenImageTextToImage2512")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image/text-to-image-2512"

    def test_inherits_from_base(self):
        base = _import_request("qwen_image_text_to_image", "QwenImageTextToImage")
        cls = _import_request("qwen_image_text_to_image_2512", "QwenImageTextToImage2512")
        assert issubclass(cls, base)

    def test_payload_matches_parent(self):
        base = _import_request("qwen_image_text_to_image", "QwenImageTextToImage")
        cls = _import_request("qwen_image_text_to_image_2512", "QwenImageTextToImage2512")
        kwargs = dict(prompt="test prompt", size="512*512", seed=42)
        base_payload = base(**kwargs).build_payload()
        variant_payload = cls(**kwargs).build_payload()
        assert base_payload == variant_payload


class TestQwenEdit2511Request:
    """QwenImageEdit2511 request routes to the edit-2511 endpoint."""

    def test_api_path(self):
        cls = _import_request("qwen_image_edit_2511", "QwenImageEdit2511")
        request = cls(prompt="test", images=["http://example.com/img.jpg"])
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image/edit-2511"

    def test_inherits_from_edit_plus(self):
        base = _import_request("qwen_image_edit_plus", "QwenImageEditPlus")
        cls = _import_request("qwen_image_edit_2511", "QwenImageEdit2511")
        assert issubclass(cls, base)

    def test_payload_matches_parent(self):
        base = _import_request("qwen_image_edit_plus", "QwenImageEditPlus")
        cls = _import_request("qwen_image_edit_2511", "QwenImageEdit2511")
        kwargs = dict(prompt="edit this", images=["http://example.com/a.jpg"], seed=7)
        base_payload = base(**kwargs).build_payload()
        variant_payload = cls(**kwargs).build_payload()
        assert base_payload == variant_payload


class TestQwenTextToImageNodeModelCombo:
    """QwenImageTextToImageNode exposes a model selector."""

    def test_schema_has_model_input(self):
        cls = _import_node("qwen_image_text_to_image", "QwenImageTextToImageNode")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1, "Should have a 'model' input"

    def test_model_options(self):
        cls = _import_node("qwen_image_text_to_image", "QwenImageTextToImageNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Qwen Image" in model_input.options
        assert "Qwen Image 2512" in model_input.options

    def test_model_defaults_to_original(self):
        cls = _import_node("qwen_image_text_to_image", "QwenImageTextToImageNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert model_input.default == "Qwen Image"


class TestQwenEditPlusNodeModelCombo:
    """QwenImageEditPlusNode exposes a model selector."""

    def test_schema_has_model_input(self):
        cls = _import_node("qwen_image_edit_plus", "QwenImageEditPlusNode")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1, "Should have a 'model' input"

    def test_model_options(self):
        cls = _import_node("qwen_image_edit_plus", "QwenImageEditPlusNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Qwen Edit Plus" in model_input.options
        assert "Qwen Edit 2511" in model_input.options

    def test_model_defaults_to_original(self):
        cls = _import_node("qwen_image_edit_plus", "QwenImageEditPlusNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert model_input.default == "Qwen Edit Plus"


class TestQwenImage20TextToImageRequest:
    """QwenImage20TextToImage and Pro variants route to the correct endpoints."""

    def test_standard_api_path(self):
        cls = _import_request("qwen_image_2_0_text_to_image", "QwenImage20TextToImage")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image-2.0/text-to-image"

    def test_pro_api_path(self):
        cls = _import_request("qwen_image_2_0_pro_text_to_image", "QwenImage20ProTextToImage")
        request = cls(prompt="test")
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image-2.0-pro/text-to-image"

    def test_pro_inherits_from_standard(self):
        base = _import_request("qwen_image_2_0_text_to_image", "QwenImage20TextToImage")
        cls = _import_request("qwen_image_2_0_pro_text_to_image", "QwenImage20ProTextToImage")
        assert issubclass(cls, base)

    def test_pro_payload_matches_standard(self):
        base = _import_request("qwen_image_2_0_text_to_image", "QwenImage20TextToImage")
        cls = _import_request("qwen_image_2_0_pro_text_to_image", "QwenImage20ProTextToImage")
        kwargs = dict(prompt="test prompt", size="512*512", seed=42)
        base_payload = base(**kwargs).build_payload()
        variant_payload = cls(**kwargs).build_payload()
        assert base_payload == variant_payload


class TestQwenImage20EditRequest:
    """QwenImage20Edit and Pro variants route to the correct endpoints."""

    def test_standard_api_path(self):
        cls = _import_request("qwen_image_2_0_edit", "QwenImage20Edit")
        request = cls(prompt="test", images=["http://example.com/img.jpg"])
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image-2.0/edit"

    def test_pro_api_path(self):
        cls = _import_request("qwen_image_2_0_pro_edit", "QwenImage20ProEdit")
        request = cls(prompt="test", images=["http://example.com/img.jpg"])
        assert request.get_api_path() == "/api/v3/wavespeed-ai/qwen-image-2.0-pro/edit"

    def test_pro_inherits_from_standard(self):
        base = _import_request("qwen_image_2_0_edit", "QwenImage20Edit")
        cls = _import_request("qwen_image_2_0_pro_edit", "QwenImage20ProEdit")
        assert issubclass(cls, base)

    def test_pro_payload_matches_standard(self):
        base = _import_request("qwen_image_2_0_edit", "QwenImage20Edit")
        cls = _import_request("qwen_image_2_0_pro_edit", "QwenImage20ProEdit")
        kwargs = dict(prompt="edit this", images=["http://example.com/a.jpg"], seed=7)
        base_payload = base(**kwargs).build_payload()
        variant_payload = cls(**kwargs).build_payload()
        assert base_payload == variant_payload


class TestQwenImage20TextToImageNodeModelCombo:
    """QwenImage20TextToImageNode exposes a model selector."""

    def test_schema_has_model_input(self):
        cls = _import_node("qwen_image_2_0_text_to_image", "QwenImage20TextToImageNode")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1, "Should have a 'model' input"

    def test_model_options(self):
        cls = _import_node("qwen_image_2_0_text_to_image", "QwenImage20TextToImageNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Qwen Image 2.0" in model_input.options
        assert "Qwen Image 2.0 Pro" in model_input.options

    def test_model_defaults_to_standard(self):
        cls = _import_node("qwen_image_2_0_text_to_image", "QwenImage20TextToImageNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert model_input.default == "Qwen Image 2.0"


class TestQwenImage20EditNodeModelCombo:
    """QwenImage20EditNode exposes a model selector."""

    def test_schema_has_model_input(self):
        cls = _import_node("qwen_image_2_0_edit", "QwenImage20EditNode")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1, "Should have a 'model' input"

    def test_model_options(self):
        cls = _import_node("qwen_image_2_0_edit", "QwenImage20EditNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert "Qwen Image 2.0" in model_input.options
        assert "Qwen Image 2.0 Pro" in model_input.options

    def test_model_defaults_to_standard(self):
        cls = _import_node("qwen_image_2_0_edit", "QwenImage20EditNode")
        schema = cls.define_schema()
        model_input = next(i for i in schema.inputs if i.id == "model")
        assert model_input.default == "Qwen Image 2.0"
