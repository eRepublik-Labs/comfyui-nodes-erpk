# ABOUTME: Tests for GeminiImageEdit additional_images support.
# ABOUTME: Verifies the node accepts and merges additional image inputs.

import pytest
import torch
from unittest.mock import patch, MagicMock


def test_input_types_has_additional_images():
    """additional_images must be declared as an optional input."""
    from gemini.nodes import GeminiImageEdit

    input_types = GeminiImageEdit.INPUT_TYPES()
    assert "additional_images" in input_types["optional"], (
        "additional_images should be an optional input"
    )
    assert input_types["optional"]["additional_images"][0] == "IMAGE"


def test_edit_image_accepts_additional_images_kwarg():
    """edit_image() must accept additional_images without TypeError."""
    import inspect
    from gemini.nodes import GeminiImageEdit

    sig = inspect.signature(GeminiImageEdit.edit_image)
    assert "additional_images" in sig.parameters, (
        "edit_image() must accept additional_images parameter"
    )


@patch("gemini.nodes.GeminiClient")
def test_additional_images_merged_into_contents(mock_client_cls):
    """When additional_images is provided, all images appear in the API call."""
    from gemini.nodes import GeminiImageEdit

    node = GeminiImageEdit()

    # Create fake image tensors (B, H, W, C) — 1 primary + 2 additional
    primary = torch.rand(1, 64, 64, 3)
    additional = torch.rand(2, 64, 64, 3)

    # Mock the Gemini client and its response
    mock_client = MagicMock()
    mock_client.api_key = "test-key"
    mock_client.safety_settings = None
    mock_client.system_instruction = None

    # Build a fake response with an image part
    fake_image_bytes = _make_tiny_png()
    mock_part = MagicMock()
    mock_part.text = None
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = fake_image_bytes

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]

    mock_instance = MagicMock()
    mock_instance.api_key = "test-key"
    mock_instance.model_name = "gemini-3-pro-image-preview"
    mock_instance.client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_instance

    result = node.edit_image(
        image=primary,
        prompt="test prompt",
        client=mock_client,
        additional_images=additional,
    )

    # Verify generate_content was called
    call_args = mock_instance.client.models.generate_content.call_args
    contents = call_args.kwargs.get("contents") or call_args[1].get("contents")

    # Should have 3 images (1 primary + 2 additional) + 1 prompt string
    assert len(contents) == 4, (
        f"Expected 4 content parts (3 images + prompt), got {len(contents)}"
    )
    assert contents[-1] == "test prompt"


def _make_tiny_png() -> bytes:
    """Create a minimal valid PNG for testing."""
    from PIL import Image
    import io
    img = Image.new("RGB", (8, 8), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
