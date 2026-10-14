# ABOUTME: Tests that the MODELS dict contains expected model entries.
# ABOUTME: Verifies all Gemini model IDs are registered and DEFAULT_MODEL is the current Flash.

import pytest

from gemini.gemini_api.client import GeminiClient


class TestModelsDict:
    """Tests for the GeminiClient.MODELS dictionary."""

    def test_gemini_31_pro_preview_in_models(self):
        assert "gemini-3.1-pro-preview" in GeminiClient.MODELS

    def test_gemini_31_pro_description_mentions_reasoning(self):
        desc = GeminiClient.MODELS["gemini-3.1-pro-preview"]
        assert "reasoning" in desc.lower() or "advanced" in desc.lower()

    def test_default_model_is_gemini_38_flash(self):
        # gemini-3.5-flash was deprecated 2026-10-08 and is served by
        # gemini-3.6-flash (generate_content model_version, probed 2026-10-14);
        # Alex's 2026-10-14 ruling makes 3.8 Flash the default.
        assert GeminiClient.DEFAULT_MODEL == "gemini-3.8-flash"

    def test_gemini_35_flash_in_models(self):
        # Deprecated but still answering; removing a combo ID breaks saved workflows.
        assert "gemini-3.5-flash" in GeminiClient.MODELS

    @pytest.mark.parametrize("model, served_by", [
        ("gemini-3.5-flash", "3.6 Flash"),
        ("gemini-3.7-flash", "3.8 Flash"),
    ])
    def test_routed_models_are_labelled_deprecated(self, model, served_by):
        # Deprecations page: both deprecated 2026-10-08; model_version in the
        # response names the model that actually answers (probed 2026-10-14).
        desc = GeminiClient.MODELS[model]
        assert "deprecated 2026-10-08" in desc.lower()
        assert f"served by {served_by}" in desc

    def test_offered_text_models_are_exactly_the_current_set(self):
        # Alex's 2026-10-01 ruling: the 2.5 family, 3 Flash Preview and
        # 3.1 Flash-Lite are withdrawn; these six remain. gemini-4-argon went
        # GA on 2026-10-13 (Gemini API changelog).
        assert set(GeminiClient.MODELS) == {
            "gemini-4-argon",
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
