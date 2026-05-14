# ABOUTME: Tests for GeminiImageEdit additional_images support.
# ABOUTME: Verifies the V3 schema declares additional_images and merging works.

import pytest
import torch
from unittest.mock import patch, MagicMock


def test_schema_has_additional_images():
    """additional_images must be declared as an optional IMAGE input in the V3 schema."""
    from gemini.nodes import GeminiImageEdit

    schema = GeminiImageEdit.define_schema()
    addl = [i for i in schema.inputs if i.id == "additional_images"]
    assert len(addl) == 1, "additional_images should appear once in the schema inputs"
    assert addl[0].optional is True
    assert addl[0].io_type == "IMAGE"


def test_execute_is_classmethod_accepting_kwargs():
    """V3 nodes expose execute() (not edit_image()) and pass through kwargs.
    The schema is the contract for which kwargs are accepted; this test just
    pins the V3 callable shape so V2-style refactors don't silently regress."""
    import inspect
    from gemini.nodes import GeminiImageEdit

    assert hasattr(GeminiImageEdit, "execute"), "V3 nodes must expose execute()"
    sig = inspect.signature(GeminiImageEdit.execute)
    has_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )
    assert has_var_kw, "execute() must accept **kwargs so the schema can drive inputs"


@patch("gemini.nodes.GeminiClient")
def test_additional_images_merged_into_contents(mock_client_cls):
    """When additional_images is provided, all images appear in the API call."""
    from gemini.nodes import GeminiImageEdit

    # Create fake image tensors (B, H, W, C) — 1 primary + 2 additional
    primary = torch.rand(1, 64, 64, 3)
    additional = torch.rand(2, 64, 64, 3)

    # Mock the Gemini client and its response
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
    mock_instance.safety_settings = None
    mock_instance.system_instruction = None
    mock_instance.client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_instance

    # V3 uses execute() (classmethod) instead of V1's edit_image()
    GeminiImageEdit.execute(
        image=primary,
        prompt="test prompt",
        client=mock_instance,
        additional_images=additional,
    )

    # Verify generate_content was called with all images merged into contents
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
