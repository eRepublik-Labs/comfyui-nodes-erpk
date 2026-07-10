# ABOUTME: Tests Grok model currency: retired IDs removed, current flagships present.
# ABOUTME: grok-4.5 default, grok-build-0.1 replaces grok-code-fast-1, quality de-aliased.

from erpk.grok.grok_api.client import GrokClient
from erpk.grok.nodes import TEXT_MODELS


def test_grok_45_is_default_and_present():
    assert GrokClient.DEFAULT_TEXT_MODEL == "grok-4.5"
    assert "grok-4.5" in TEXT_MODELS


def test_retired_text_models_removed():
    # grok-3 retired (redirects to grok-4.3); grok-code-fast-1 retired (-> grok-build-0.1).
    assert "grok-3" not in TEXT_MODELS
    assert "grok-code-fast-1" not in TEXT_MODELS


def test_grok_build_replaces_code_fast():
    assert "grok-build-0.1" in TEXT_MODELS


def test_retired_image_model_removed():
    # grok-imagine-image-pro retired; redirects to grok-imagine-image-quality.
    assert "grok-imagine-image-pro" not in GrokClient.IMAGE_MODELS


def test_image_quality_is_a_real_model_not_an_alias():
    # grok-imagine-image-quality is a distinct premium model (pro's successor),
    # not an alias of grok-imagine-image, so it must pass through unremapped.
    assert "grok-imagine-image-quality" in GrokClient.IMAGE_MODELS
    client = GrokClient.__new__(GrokClient)  # bypass __init__ key resolution
    assert client._resolve_image_model("grok-imagine-image-quality") == "grok-imagine-image-quality"


def test_video_15_available():
    assert "grok-imagine-video-1.5" in GrokClient.VIDEO_MODELS
