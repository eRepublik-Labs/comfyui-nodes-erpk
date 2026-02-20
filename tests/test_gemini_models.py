# ABOUTME: Tests that the MODELS dict contains expected model entries
# ABOUTME: Verifies gemini-3.1-pro-preview is registered and DEFAULT_MODEL is unchanged

import sys
from unittest.mock import MagicMock

import pytest

for mod_name in ["numpy", "torch", "PIL", "PIL.Image"]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from gemini.gemini_api.client import GeminiClient


class TestModelsDict:
    """Tests for the GeminiClient.MODELS dictionary."""

    def test_gemini_31_pro_preview_in_models(self):
        assert "gemini-3.1-pro-preview" in GeminiClient.MODELS

    def test_gemini_31_pro_description_mentions_reasoning(self):
        desc = GeminiClient.MODELS["gemini-3.1-pro-preview"]
        assert "reasoning" in desc.lower() or "advanced" in desc.lower()

    def test_default_model_unchanged(self):
        assert GeminiClient.DEFAULT_MODEL == "gemini-3-flash-preview"

    def test_all_existing_models_still_present(self):
        expected = [
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ]
        for model_id in expected:
            assert model_id in GeminiClient.MODELS, f"{model_id} missing from MODELS"
