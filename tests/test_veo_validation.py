# ABOUTME: Tests for Veo per-model validation rules (duration / resolution gating).
# ABOUTME: Pure-Python tests for _validate_veo_config; no torch / comfy required.

import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)


def _import_validator():
    """Import _validate_veo_config without dragging in the comfy_api dependency."""
    import importlib.util
    path = os.path.join(_REPO, "gemini", "veo_nodes.py")
    spec = importlib.util.spec_from_file_location("_veo_nodes_for_test", path)
    mod = importlib.util.module_from_spec(spec)
    # The module imports `comfy_api.latest.IO` at top level. Stub it before exec.
    import types as _types
    fake_comfy = _types.ModuleType("comfy_api")
    fake_latest = _types.ModuleType("comfy_api.latest")
    fake_latest.IO = _types.SimpleNamespace()
    fake_comfy.latest = fake_latest
    sys.modules.setdefault("comfy_api", fake_comfy)
    sys.modules.setdefault("comfy_api.latest", fake_latest)
    spec.loader.exec_module(mod)
    return mod


veo = _import_validator()


def test_default_3_1_8s_1080p_passes_through():
    dur, res, warnings = veo._validate_veo_config("veo-3.1-generate-preview", 8, "1080p")
    assert dur == 8
    assert res == "1080p"
    assert warnings == []


def test_lite_4k_clamps_to_1080p():
    dur, res, warnings = veo._validate_veo_config("veo-3.1-lite-generate-preview", 8, "4k")
    assert res == "1080p"
    assert any("4k" in w and "1080p" in w for w in warnings)


def test_6s_at_1080p_does_not_bump_duration():
    # 1080p does not require 8s; the constraint runs the other way.
    dur, res, warnings = veo._validate_veo_config("veo-3.1-generate-preview", 6, "1080p")
    assert dur == 6
    assert res == "1080p"
    assert warnings == []


def test_8s_at_720p_no_refs_bumps_resolution_to_1080p():
    # 8s on Veo 3.1 family requires resolution >= 1080p OR reference_images.
    dur, res, warnings = veo._validate_veo_config(
        "veo-3.1-generate-preview", 8, "720p", has_reference_images=False
    )
    assert dur == 8
    assert res == "1080p"
    assert any("1080p" in w and "720p" in w for w in warnings)


def test_8s_at_720p_with_refs_stays_at_720p():
    # Reference images unlock 8s at 720p — no resolution bump.
    dur, res, warnings = veo._validate_veo_config(
        "veo-3.1-generate-preview", 8, "720p", has_reference_images=True
    )
    assert dur == 8
    assert res == "720p"
    assert warnings == []


def test_lite_8s_at_720p_bumps_resolution():
    # Lite has no 4k path, so the gate uplifts to 1080p only.
    dur, res, warnings = veo._validate_veo_config(
        "veo-3.1-lite-generate-preview", 8, "720p", has_reference_images=False
    )
    assert dur == 8
    assert res == "1080p"


def test_veo_3_x_rejects_5s_clamps_to_nearest():
    # 5s is invalid on Veo 3.x; both 4 and 6 are tied for nearest valid value.
    dur, res, warnings = veo._validate_veo_config("veo-3.1-generate-preview", 5, "720p")
    assert dur in (4, 6)
    assert any("duration" in w for w in warnings)


def test_veo_3_x_rejects_7s_clamps_to_6_or_8():
    dur, res, warnings = veo._validate_veo_config("veo-3.1-generate-preview", 7, "720p")
    assert dur in (6, 8)
    assert any("duration" in w for w in warnings)


def test_lite_model_in_models_list():
    assert "veo-3.1-lite-generate-preview" in veo.VEO_MODELS


def test_dead_veo_models_removed():
    # Veo 3.0 / 2.0 shut down 2026-06-30; only the 3.1 family remains selectable.
    for dead in ("veo-3.0-generate-001", "veo-3.0-fast-generate-001", "veo-2.0-generate-001"):
        assert dead not in veo.VEO_MODELS, f"{dead} is past shutdown; remove it"


def test_reference_image_capable_models():
    assert "veo-3.1-generate-preview" in veo._MODELS_WITH_REFERENCE_IMAGES
    assert "veo-3.1-fast-generate-preview" in veo._MODELS_WITH_REFERENCE_IMAGES
    assert "veo-3.1-lite-generate-preview" not in veo._MODELS_WITH_REFERENCE_IMAGES


def test_veo_3x_i2v_rejects_allow_all():
    import pytest
    for model in ("veo-3.1-generate-preview", "veo-3.1-fast-generate-preview",
                  "veo-3.1-lite-generate-preview"):
        with pytest.raises(ValueError, match="allow_all"):
            veo._validate_person_generation(model, "allow_all", is_image_to_video=True)


def test_veo_3x_i2v_accepts_allow_adult_and_dont_allow():
    for model in ("veo-3.1-generate-preview", "veo-3.1-lite-generate-preview"):
        veo._validate_person_generation(model, "allow_adult", is_image_to_video=True)
        veo._validate_person_generation(model, "dont_allow", is_image_to_video=True)


def test_veo_3x_t2v_accepts_allow_all():
    veo._validate_person_generation(
        "veo-3.1-generate-preview", "allow_all", is_image_to_video=False
    )


def test_last_frame_requires_8s_duration():
    import pytest
    for bad_duration in (4, 6):
        with pytest.raises(ValueError, match="duration_seconds=8"):
            veo._validate_interpolation_constraints(
                has_last_frame=True, has_reference_images=False,
                duration=bad_duration, aspect_ratio="16:9",
            )


def test_last_frame_accepts_8s_duration():
    veo._validate_interpolation_constraints(
        has_last_frame=True, has_reference_images=False,
        duration=8, aspect_ratio="16:9",
    )


def test_no_constraints_when_neither_feature_used():
    for d in (4, 6, 8):
        for ar in ("16:9", "9:16"):
            veo._validate_interpolation_constraints(
                has_last_frame=False, has_reference_images=False,
                duration=d, aspect_ratio=ar,
            )


def test_reference_images_requires_8s_duration():
    import pytest
    with pytest.raises(ValueError, match="duration_seconds=8"):
        veo._validate_interpolation_constraints(
            has_last_frame=False, has_reference_images=True,
            duration=4, aspect_ratio="16:9",
        )


def test_reference_images_requires_16_9_aspect():
    import pytest
    with pytest.raises(ValueError, match="aspect_ratio='16:9'"):
        veo._validate_interpolation_constraints(
            has_last_frame=False, has_reference_images=True,
            duration=8, aspect_ratio="9:16",
        )


def test_reference_images_mutually_exclusive_with_last_frame():
    import pytest
    with pytest.raises(ValueError, match="mutually exclusive"):
        veo._validate_interpolation_constraints(
            has_last_frame=True, has_reference_images=True,
            duration=8, aspect_ratio="16:9",
        )


def test_reference_images_happy_path():
    veo._validate_interpolation_constraints(
        has_last_frame=False, has_reference_images=True,
        duration=8, aspect_ratio="16:9",
    )
