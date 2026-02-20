# ABOUTME: Tests that IMAGE_MODELS is defined as a shared constant in GeminiClient
# ABOUTME: Verifies image node defaults match the dropdown and use the shared constant

import sys
import inspect
from unittest.mock import MagicMock

import pytest

for mod_name in ["numpy", "torch", "PIL", "PIL.Image"]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

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
        inputs = GeminiImageGeneration.INPUT_TYPES()
        dropdown_choices = inputs["optional"]["model"][0]
        assert list(dropdown_choices) == list(GeminiClient.IMAGE_MODELS)

    def test_image_edit_uses_client_image_models(self):
        inputs = GeminiImageEdit.INPUT_TYPES()
        dropdown_choices = inputs["optional"]["model"][0]
        assert list(dropdown_choices) == list(GeminiClient.IMAGE_MODELS)


class TestImageModelDefaults:
    """Verify method signature defaults match dropdown defaults."""

    def test_generate_image_default_matches_dropdown(self):
        inputs = GeminiImageGeneration.INPUT_TYPES()
        dropdown_default = inputs["optional"]["model"][1]["default"]
        sig = inspect.signature(GeminiImageGeneration.generate_image)
        param_default = sig.parameters["model"].default
        assert param_default == dropdown_default

    def test_edit_image_default_matches_dropdown(self):
        inputs = GeminiImageEdit.INPUT_TYPES()
        dropdown_default = inputs["optional"]["model"][1]["default"]
        sig = inspect.signature(GeminiImageEdit.edit_image)
        param_default = sig.parameters["model"].default
        assert param_default == dropdown_default
