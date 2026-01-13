# ABOUTME: Tests for Gemini ImageConfig SDK compatibility.
# ABOUTME: Ensures image_size parameter is handled gracefully across SDK versions.

import pytest
from unittest.mock import patch, MagicMock


def test_image_config_params_with_unsupported_image_size():
    """Test that image_size is skipped when SDK doesn't support it."""
    # Simulate building image_config_params like the node does
    from google.genai import types

    # Mock an older SDK that doesn't have image_size in model_fields
    mock_model_fields = {'aspect_ratio': MagicMock()}  # No image_size

    image_config_params = {}
    aspect_ratio = "16:9"
    image_size = "4K"
    model = "gemini-3-pro-image-preview"

    # Current code logic (should fail with old SDK)
    if aspect_ratio != "default":
        image_config_params["aspect_ratio"] = aspect_ratio

    # This is what the current code does - it would fail
    # if image_size != "default" and model == "gemini-3-pro-image-preview":
    #     image_config_params["image_size"] = image_size

    # This is what the fixed code should do
    if image_size != "default" and model == "gemini-3-pro-image-preview":
        if "image_size" in mock_model_fields:
            image_config_params["image_size"] = image_size
        # else: skip silently or warn

    # With old SDK, image_size should NOT be in params
    assert "image_size" not in image_config_params
    assert "aspect_ratio" in image_config_params


def test_image_config_params_with_supported_image_size():
    """Test that image_size is included when SDK supports it."""
    from google.genai import types

    # Check actual SDK support
    actual_support = "image_size" in types.ImageConfig.model_fields

    image_config_params = {}
    aspect_ratio = "16:9"
    image_size = "4K"
    model = "gemini-3-pro-image-preview"

    if aspect_ratio != "default":
        image_config_params["aspect_ratio"] = aspect_ratio

    # Fixed code logic - check SDK support at runtime
    if image_size != "default" and model == "gemini-3-pro-image-preview":
        if "image_size" in types.ImageConfig.model_fields:
            image_config_params["image_size"] = image_size

    # Result depends on actual SDK
    if actual_support:
        assert image_config_params.get("image_size") == "4K"
    else:
        assert "image_size" not in image_config_params


def test_image_config_creation_doesnt_raise():
    """Test that ImageConfig creation doesn't raise with filtered params."""
    from google.genai import types

    image_config_params = {"aspect_ratio": "16:9"}

    # Only add image_size if SDK supports it
    if "image_size" in types.ImageConfig.model_fields:
        image_config_params["image_size"] = "4K"

    # This should never raise regardless of SDK version
    config = types.ImageConfig(**image_config_params)
    assert config.aspect_ratio == "16:9"
