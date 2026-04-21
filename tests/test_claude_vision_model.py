# ABOUTME: Tests for Claude Vision per-node model override input.
# ABOUTME: Verifies the "(inherit from client)" default and explicit-model dispatch.

"""
ClaudeVisionAnalysis exposes an optional `model` Combo input. When set to
the default "(inherit from client)" sentinel, the client's configured model
is used. When set to an explicit model ID, that value is passed to
send_request and overrides the client's model for this call only.
"""

from unittest.mock import MagicMock, patch

import pytest


INHERIT_SENTINEL = "(inherit from client)"


def test_vision_has_model_input():
    from claude.vision_analysis import ClaudeVisionAnalysis
    schema = ClaudeVisionAnalysis.define_schema()
    model_input = next((i for i in schema.inputs if i.id == "model"), None)
    assert model_input is not None, "ClaudeVisionAnalysis must expose a model input"
    assert model_input.optional is True


def test_vision_model_defaults_to_inherit():
    from claude.vision_analysis import ClaudeVisionAnalysis
    schema = ClaudeVisionAnalysis.define_schema()
    model_input = next(i for i in schema.inputs if i.id == "model")
    assert model_input.default == INHERIT_SENTINEL


def test_vision_model_options_include_all_claude_models():
    from claude.vision_analysis import ClaudeVisionAnalysis
    schema = ClaudeVisionAnalysis.define_schema()
    model_input = next(i for i in schema.inputs if i.id == "model")
    assert INHERIT_SENTINEL in model_input.options
    assert "claude-opus-4-7" in model_input.options
    assert "claude-sonnet-4-6" in model_input.options
    assert "claude-opus-4-6" in model_input.options


def _mock_image_tensor():
    """Return a minimal tensor-like mock the vision node will accept."""
    import numpy as np
    try:
        import torch
        return torch.zeros((1, 8, 8, 3), dtype=torch.float32)
    except ImportError:
        return np.zeros((1, 8, 8, 3), dtype=np.float32)


def _patched_client():
    """Build a mocked ClaudeClient whose send_request records kwargs."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="mock analysis")]
    client.send_request.return_value = mock_response
    return client


def test_vision_inherit_does_not_pass_model_to_client():
    """With the inherit sentinel, send_request is called WITHOUT a model kwarg."""
    from claude.vision_analysis import ClaudeVisionAnalysis
    client = _patched_client()

    with patch("claude.claude_api.utils.ImageConverter") as mock_converter:
        mock_converter.tensor_to_pil.return_value = MagicMock()
        mock_converter.validate_image_for_claude.return_value = (True, None)
        mock_converter.pil_to_base64.return_value = "fake_base64"

        ClaudeVisionAnalysis.execute(
            image=_mock_image_tensor(),
            question="test",
            client=client,
            model=INHERIT_SENTINEL,
        )

    call_kwargs = client.send_request.call_args.kwargs
    assert "model" not in call_kwargs, \
        f"model must NOT be passed when inherit is selected, got: {call_kwargs.get('model')}"


def test_vision_explicit_model_is_passed_to_client():
    """With an explicit model string, send_request receives model=... kwarg."""
    from claude.vision_analysis import ClaudeVisionAnalysis
    client = _patched_client()

    with patch("claude.claude_api.utils.ImageConverter") as mock_converter:
        mock_converter.tensor_to_pil.return_value = MagicMock()
        mock_converter.validate_image_for_claude.return_value = (True, None)
        mock_converter.pil_to_base64.return_value = "fake_base64"

        ClaudeVisionAnalysis.execute(
            image=_mock_image_tensor(),
            question="test",
            client=client,
            model="claude-opus-4-7",
        )

    call_kwargs = client.send_request.call_args.kwargs
    assert call_kwargs.get("model") == "claude-opus-4-7"
