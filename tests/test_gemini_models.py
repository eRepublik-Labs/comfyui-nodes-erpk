# ABOUTME: Tests that the MODELS dict contains expected model entries.
# ABOUTME: Verifies all Gemini model IDs are registered and DEFAULT_MODEL is unchanged.

import pytest

from gemini.gemini_api.client import GeminiClient


class TestModelsDict:
    """Tests for the GeminiClient.MODELS dictionary."""

    def test_gemini_31_pro_preview_in_models(self):
        assert "gemini-3.1-pro-preview" in GeminiClient.MODELS

    def test_gemini_31_pro_description_mentions_reasoning(self):
        desc = GeminiClient.MODELS["gemini-3.1-pro-preview"]
        assert "reasoning" in desc.lower() or "advanced" in desc.lower()

    def test_default_model_is_gemini_35_flash(self):
        assert GeminiClient.DEFAULT_MODEL == "gemini-3.5-flash"

    def test_gemini_35_flash_in_models(self):
        assert "gemini-3.5-flash" in GeminiClient.MODELS

    def test_gemini_35_flash_description_mentions_speed_or_intelligence(self):
        desc = GeminiClient.MODELS["gemini-3.5-flash"]
        assert "intelligence" in desc.lower() or "fast" in desc.lower() or "speed" in desc.lower()

    def test_gemini_31_flash_lite_preview_in_models(self):
        assert "gemini-3.1-flash-lite-preview" in GeminiClient.MODELS

    def test_gemini_31_flash_lite_description_mentions_speed_or_cost(self):
        desc = GeminiClient.MODELS["gemini-3.1-flash-lite-preview"]
        assert "fast" in desc.lower() or "cost" in desc.lower() or "efficient" in desc.lower()

    def test_all_existing_models_still_present(self):
        expected = [
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-3.1-flash-lite-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ]
        for model_id in expected:
            assert model_id in GeminiClient.MODELS, f"{model_id} missing from MODELS"
