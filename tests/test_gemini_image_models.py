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
        expected = ["gemini-3-pro-image-preview", "gemini-2.5-flash-image"]
        for model in expected:
            assert model in GeminiClient.IMAGE_MODELS

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
        assert model_input.default == "gemini-3-pro-image-preview"

    def test_edit_image_default(self):
        schema = GeminiImageEdit.define_schema()
        model_input = [i for i in schema.inputs if i.id == "model"][0]
        assert model_input.default == "gemini-3-pro-image-preview"
