# ABOUTME: Tests Grok model currency: retired and removed IDs are not offered, kept models are.
# ABOUTME: grok-4.7 is the text default; grok-imagine-image-2.0 is the only (and default) image model.

from erpk.grok.grok_api.client import GrokClient
from erpk.grok.nodes import TEXT_MODELS

# Removed from every Combo on 2026-10-01 (Alex's call). Saved workflows that
# picked one of these fail ComfyUI's Combo validation and must be re-pointed.
REMOVED_TEXT_MODELS = ["grok-4.6", "grok-4.5", "grok-4.3", "grok-4.20-0309-reasoning"]
REMOVED_IMAGE_MODELS = ["grok-imagine-image", "grok-imagine-image-quality"]

KEPT_TEXT_MODELS = [
    "grok-4.7",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-multi-agent-0309",
    "grok-build-0.1",
]


def test_grok_47_is_default_and_first():
    # docs.x.ai/docs/models: "For everything else, including code, use Grok 4.7."
    assert GrokClient.DEFAULT_TEXT_MODEL == "grok-4.7"
    assert TEXT_MODELS[0] == "grok-4.7"


def test_kept_text_models_offered():
    for model in KEPT_TEXT_MODELS:
        assert model in TEXT_MODELS


def test_removed_text_models_not_offered():
    for model in REMOVED_TEXT_MODELS:
        assert model not in TEXT_MODELS, f"{model} was removed and must not be selectable"


def test_retired_text_models_removed():
    # grok-3 retired (redirects to grok-4.3); grok-code-fast-1 retired (-> grok-build-0.1).
    assert "grok-3" not in TEXT_MODELS
    assert "grok-code-fast-1" not in TEXT_MODELS


def test_image_20_is_default_and_only_image_model():
    assert GrokClient.DEFAULT_IMAGE_MODEL == "grok-imagine-image-2.0"
    assert GrokClient.IMAGE_MODELS == ["grok-imagine-image-2.0"]


def test_removed_image_models_not_offered():
    # grok-imagine-image-pro retired earlier; grok-imagine-image (v1) and
    # grok-imagine-image-quality removed 2026-10-01 (quality retires 2026-11-02, D-mig).
    for model in REMOVED_IMAGE_MODELS + ["grok-imagine-image-pro"]:
        assert model not in GrokClient.IMAGE_MODELS


def test_both_video_models_kept():
    assert GrokClient.VIDEO_MODELS == ["grok-imagine-video", "grok-imagine-video-1.5"]
