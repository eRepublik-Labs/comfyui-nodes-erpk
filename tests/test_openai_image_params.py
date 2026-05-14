# ABOUTME: Tests for OpenAI image generation API parameter construction
# ABOUTME: Ensures response_format is only sent for models that support it

import sys
from unittest.mock import MagicMock, patch

import pytest

# In the test environment, our local openai/ package shadows the SDK's openai package.
# The client does `from openai import APIError` (lazy import inside methods), which
# resolves to our local package. Inject a mock APIError so the import succeeds.
import openai as _local_openai
if not hasattr(_local_openai, "APIError"):
    _local_openai.APIError = type("APIError", (Exception,), {})

from openai.openai_api.client import OpenAIClient


GPT_IMAGE_MODELS = ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]
DALLE_MODELS = ["dall-e-3", "dall-e-2"]


def _make_client_with_mock():
    """Create an OpenAIClient with a mocked SDK client."""
    client = OpenAIClient.__new__(OpenAIClient)
    mock_openai = MagicMock()
    mock_img = MagicMock()
    mock_img.b64_json = "fakebase64data"
    mock_img.revised_prompt = None
    mock_response = MagicMock()
    mock_response.data = [mock_img]
    mock_openai.images.generate.return_value = mock_response
    mock_openai.images.edit.return_value = mock_response
    client.client = mock_openai
    return client, mock_openai


class TestGenerateImageParams:
    """Verify generate_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="a cat", model=model, size="1024x1024")
        params = mock.images.generate.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )

    @pytest.mark.parametrize("model", DALLE_MODELS)
    def test_dalle_models_include_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="a cat", model=model, size="1024x1024")
        params = mock.images.generate.call_args[1]
        assert params.get("response_format") == "b64_json", (
            f"response_format must be b64_json for {model}"
        )


class TestGptImage2Background:
    """Background param passes through unchanged to gpt-image-2 (no client-side coercion)."""

    def test_transparent_passes_through_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="a cat", model="gpt-image-2", background="transparent"
        )
        params = mock.images.generate.call_args[1]
        assert params.get("background") == "transparent", (
            "background must be forwarded unchanged; OpenAI now controls model-specific support"
        )

    def test_transparent_preserved_for_gpt_image_1_5(self):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="a cat", model="gpt-image-1.5", background="transparent"
        )
        params = mock.images.generate.call_args[1]
        assert params.get("background") == "transparent", (
            "gpt-image-1.5 supports transparent — must not be coerced"
        )

    def test_opaque_passes_through_unchanged_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="a cat", model="gpt-image-2", background="opaque"
        )
        assert mock.images.generate.call_args[1].get("background") == "opaque"

    def test_auto_background_omitted_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="a cat", model="gpt-image-2", background="auto"
        )
        # auto means "don't send the param" — matches existing behavior for other GPT image models
        assert "background" not in mock.images.generate.call_args[1]


class TestGptImage2ModelPresence:
    """gpt-image-2 must be exposed via the client's model catalog."""

    def test_gpt_image_2_in_image_models(self):
        assert "gpt-image-2" in OpenAIClient.IMAGE_MODELS

    def test_gpt_image_2_in_gpt_image_models_set(self):
        assert "gpt-image-2" in OpenAIClient.GPT_IMAGE_MODELS

    def test_gpt_image_2_flagged_in_gpt_image_2_models_set(self):
        assert "gpt-image-2" in OpenAIClient.GPT_IMAGE_2_MODELS


class TestModeration:
    """moderation parameter: pass-through for GPT Image models, skipped for others."""

    @pytest.mark.parametrize("model", ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"])
    def test_moderation_low_sent_for_gpt_image_models(self, model):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="x", model=model, size="1024x1024", moderation="low",
        )
        params = mock.images.generate.call_args[1]
        assert params.get("moderation") == "low"

    def test_moderation_auto_not_sent(self):
        """'auto' is the API default — don't send it (matches our background pattern)."""
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="x", model="gpt-image-2", size="1024x1024", moderation="auto",
        )
        assert "moderation" not in mock.images.generate.call_args[1]

    def test_moderation_skipped_for_dalle_3(self):
        """dall-e-3 doesn't accept moderation — skip to avoid an API error."""
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="x", model="dall-e-3", moderation="low",
        )
        assert "moderation" not in mock.images.generate.call_args[1]

    def test_moderation_skipped_for_dalle_2(self):
        client, mock = _make_client_with_mock()
        client.generate_image(
            prompt="x", model="dall-e-2", moderation="low",
        )
        assert "moderation" not in mock.images.generate.call_args[1]

    def test_moderation_in_edit_for_gpt_image_models(self):
        client, mock = _make_client_with_mock()
        client.edit_image(
            image_data=b"fakepng", prompt="edit", model="gpt-image-2", moderation="low",
        )
        params = mock.images.edit.call_args[1]
        assert params.get("moderation") == "low"

    def test_moderation_auto_not_sent_in_edit(self):
        client, mock = _make_client_with_mock()
        client.edit_image(
            image_data=b"fakepng", prompt="edit", model="gpt-image-2", moderation="auto",
        )
        assert "moderation" not in mock.images.edit.call_args[1]


class TestNValidation:
    """dall-e-3 only supports n=1; all other models accept n=1-10."""

    def test_dall_e_3_n_2_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="dall-e-3 supports n=1 only"):
            client.generate_image(prompt="x", model="dall-e-3", n=2)

    def test_dall_e_3_n_10_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="dall-e-3 supports n=1 only"):
            client.generate_image(prompt="x", model="dall-e-3", n=10)

    def test_dall_e_3_n_1_passes(self):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="x", model="dall-e-3", n=1)
        assert mock.images.generate.called

    @pytest.mark.parametrize("model", ["gpt-image-2", "gpt-image-1.5", "gpt-image-1",
                                       "gpt-image-1-mini", "dall-e-2"])
    def test_other_models_accept_n_up_to_10(self, model):
        client, mock = _make_client_with_mock()
        # gpt-image-2 needs a valid size (n validation happens after size validation)
        client.generate_image(prompt="x", model=model, size="1024x1024", n=10)
        assert mock.images.generate.called
        assert mock.images.generate.call_args[1].get("n") == 10


class TestGptImage2SizeValidation:
    """Preflight size validation before calling the OpenAI API.
    gpt-image-2 has stricter size rules than other models; validate at the
    client layer so users get a friendly error instead of a raw 400.
    """

    def test_below_min_pixels_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least 655,360"):
            client.generate_image(prompt="x", model="gpt-image-2", size="512x512")

    def test_256_also_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least 655,360"):
            client.generate_image(prompt="x", model="gpt-image-2", size="256x256")

    def test_valid_1024_passes(self):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="x", model="gpt-image-2", size="1024x1024")
        assert mock.images.generate.called

    def test_above_max_edge_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="max edge"):
            client.generate_image(prompt="x", model="gpt-image-2", size="4000x2160")

    def test_non_multiple_of_16_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="multiples of 16"):
            client.generate_image(prompt="x", model="gpt-image-2", size="1023x1024")

    def test_aspect_ratio_over_3_1_raises(self):
        client, _ = _make_client_with_mock()
        # 3200x800 = 2.56M pixels (above min), edges multiples of 16, but 4:1 ratio
        with pytest.raises(ValueError, match="aspect ratio"):
            client.generate_image(prompt="x", model="gpt-image-2", size="3200x800")

    def test_above_max_pixels_raises(self):
        client, _ = _make_client_with_mock()
        # 3840x3200 = 12.3M pixels (above 8.3M max); edges multiples of 16 and ratio 1.2:1
        with pytest.raises(ValueError, match=r"max is 8,294,400"):
            client.generate_image(prompt="x", model="gpt-image-2", size="3840x3200")

    def test_auto_size_skips_validation(self):
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="x", model="gpt-image-2", size="auto")
        assert mock.images.generate.called

    def test_malformed_size_skips_validation(self):
        """Malformed strings fall through to the API, which returns its own
        error message. We don't try to second-guess the parser."""
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="x", model="gpt-image-2", size="notasize")
        assert mock.images.generate.called

    def test_other_models_skip_validation(self):
        """Small sizes are fine on gpt-image-1 / gpt-image-1.5 / dall-e-2 — the
        gpt-image-2 validator must not reject them when a different model is chosen."""
        client, mock = _make_client_with_mock()
        client.generate_image(prompt="x", model="gpt-image-1", size="512x512")
        client.generate_image(prompt="x", model="gpt-image-1.5", size="512x512")
        client.generate_image(prompt="x", model="dall-e-2", size="512x512")
        # Three calls, no exceptions
        assert mock.images.generate.call_count == 3


class TestEditImageParams:
    """Verify edit_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        client.edit_image(image_data=b"fakepng", prompt="make it blue", model=model)
        params = mock.images.edit.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )


class TestEditImageMultiImage:
    """edit_image accepts bytes or list[bytes] for multi-image editing."""

    def test_single_bytes_sends_singular_image_param(self):
        client, mock = _make_client_with_mock()
        client.edit_image(image_data=b"onepng", prompt="x", model="gpt-image-2")
        image_param = mock.images.edit.call_args[1]["image"]
        # Singular: 3-tuple (filename, bytes, mime)
        assert isinstance(image_param, tuple)
        assert image_param[0] == "image.png"
        assert image_param[1] == b"onepng"
        assert image_param[2] == "image/png"

    def test_list_of_bytes_sends_array_image_param(self):
        client, mock = _make_client_with_mock()
        client.edit_image(
            image_data=[b"first", b"second", b"third"],
            prompt="compose these",
            model="gpt-image-2",
        )
        image_param = mock.images.edit.call_args[1]["image"]
        # Multi: list of 3-tuples
        assert isinstance(image_param, list)
        assert len(image_param) == 3
        for i, (fname, data, mime) in enumerate(image_param):
            assert fname == f"image_{i}.png"
            assert mime == "image/png"
        assert image_param[0][1] == b"first"
        assert image_param[1][1] == b"second"
        assert image_param[2][1] == b"third"

    def test_single_element_list_treated_as_singular(self):
        """A list with one image should behave the same as passing bytes directly."""
        client, mock = _make_client_with_mock()
        client.edit_image(
            image_data=[b"single_in_list"], prompt="x", model="gpt-image-2"
        )
        image_param = mock.images.edit.call_args[1]["image"]
        # Len-1 list is collapsed to singular
        assert isinstance(image_param, tuple)
        assert image_param[1] == b"single_in_list"

    def test_empty_list_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least one image"):
            client.edit_image(image_data=[], prompt="x", model="gpt-image-2")

    def test_mask_still_attaches_with_multi_image(self):
        client, mock = _make_client_with_mock()
        client.edit_image(
            image_data=[b"a", b"b"],
            mask_data=b"maskbytes",
            prompt="x",
            model="gpt-image-2",
        )
        params = mock.images.edit.call_args[1]
        assert "mask" in params
        assert params["mask"][1] == b"maskbytes"
        # image is still the multi-image array
        assert isinstance(params["image"], list)
        assert len(params["image"]) == 2
