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

    def test_offered_text_models_are_exactly_the_current_set(self):
        # Alex's 2026-10-01 ruling: the 2.5 family, 3 Flash Preview and
        # 3.1 Flash-Lite are withdrawn; these six remain.
        assert set(GeminiClient.MODELS) == {
            "gemini-3.1-pro-preview",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        }

    def test_withdrawn_models_removed(self):
        # gemini-2.5-pro 404s "no longer available to new users" (probed
        # 2026-10-01); the rest are superseded and withdrawn by Alex's ruling.
        for gone in ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
                     "gemini-3-flash-preview", "gemini-3.1-flash-lite"):
            assert gone not in GeminiClient.MODELS, f"{gone} was withdrawn; remove it"

    def test_dead_preview_models_removed(self):
        # Past their Google shutdown date; must not be selectable.
        for dead in ("gemini-3-pro-preview", "gemini-3.1-flash-lite-preview"):
            assert dead not in GeminiClient.MODELS, f"{dead} is past shutdown; remove it"
