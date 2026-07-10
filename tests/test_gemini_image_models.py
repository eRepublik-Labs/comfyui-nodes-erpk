# ABOUTME: Tests that IMAGE_MODELS is defined as a shared constant in GeminiClient.
# ABOUTME: Verifies image node COMBO options and defaults use the shared constant.

import pytest

from gemini.gemini_api.client import GeminiClient
from gemini.nodes import GeminiImageGeneration, GeminiImageEdit


class TestImageModelsConstant:
    """Verify IMAGE_MODELS is a shared constant on GeminiClient."""

    def test_image_models_exists_on_client(self):
        assert hasattr(GeminiClient, "IMAGE_MODELS")

    def test_image_models_contains_expected_models(self):
        expected = [
            "gemini-3.1-flash-image",
            "gemini-3-pro-image",
            "gemini-2.5-flash-image",
        ]
        for model in expected:
            assert model in GeminiClient.IMAGE_MODELS

    def test_dead_preview_image_models_removed(self):
        # Past their Google shutdown date (2026-06-25); must not be selectable.
        for dead in ("gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview"):
            assert dead not in GeminiClient.IMAGE_MODELS, f"{dead} is past shutdown; remove it"

    def test_image_models_order(self):
        """3.1 Flash (GA) should be first (the recommended default)."""
        assert GeminiClient.IMAGE_MODELS[0] == "gemini-3.1-flash-image"

    def test_image_gen_uses_client_image_models(self):
        schema = GeminiImageGeneration.define_schema()
        model_input = [i for i in schema.inputs if i.id == "model"][0]
        assert list(model_input.options) == list(GeminiClient.IMAGE_MODELS)

    def test_image_edit_uses_client_image_models(self):
        schema = GeminiImageEdit.define_schema()
        model_input = [i for i in schema.inputs if i.id == "model"][0]
        assert list(model_input.options) == list(GeminiClient.IMAGE_MODELS)


class TestImageModelDefaults:
    """Verify schema model COMBO defaults for image nodes."""

    def test_generate_image_default(self):
        schema = GeminiImageGeneration.define_schema()
        model_input = [i for i in schema.inputs if i.id == "model"][0]
        assert model_input.default == "gemini-3.1-flash-image"

    def test_edit_image_default(self):
        schema = GeminiImageEdit.define_schema()
        model_input = [i for i in schema.inputs if i.id == "model"][0]
        assert model_input.default == "gemini-3.1-flash-image"


class TestImageSchemaOptions:
    """Verify aspect_ratio and image_size COMBO options include all supported values."""

    EXPECTED_ASPECT_RATIOS = [
        "default", "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
        "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
    ]
    EXPECTED_IMAGE_SIZES = ["default", "1K", "2K", "4K"]

    def test_generate_image_aspect_ratios(self):
        schema = GeminiImageGeneration.define_schema()
        ar_input = [i for i in schema.inputs if i.id == "aspect_ratio"][0]
        assert list(ar_input.options) == self.EXPECTED_ASPECT_RATIOS

    def test_edit_image_aspect_ratios(self):
        schema = GeminiImageEdit.define_schema()
        ar_input = [i for i in schema.inputs if i.id == "aspect_ratio"][0]
        assert list(ar_input.options) == self.EXPECTED_ASPECT_RATIOS

    def test_generate_image_size_options(self):
        schema = GeminiImageGeneration.define_schema()
        size_input = [i for i in schema.inputs if i.id == "image_size"][0]
        assert list(size_input.options) == self.EXPECTED_IMAGE_SIZES

    def test_edit_image_size_options(self):
        schema = GeminiImageEdit.define_schema()
        size_input = [i for i in schema.inputs if i.id == "image_size"][0]
        assert list(size_input.options) == self.EXPECTED_IMAGE_SIZES
