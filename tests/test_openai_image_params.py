# ABOUTME: Tests for OpenAI image generation API parameter construction
# ABOUTME: Ensures response_format is only sent for models that support it

import asyncio
import sys
from unittest.mock import MagicMock, patch

import pytest

from erpk.openai.openai_api.client import OpenAIClient
from tests.openai_sdk_signature import assert_binds, sdk_has


GPT_IMAGE_MODELS = [
    "gpt-image-2.6-sunburst", "gpt-image-2.6-flare",
    "gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2",
]
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
    mock_openai.post.return_value = mock_response
    client.client = mock_openai
    return client, mock_openai


class TestGenerateImageParams:
    """Verify generate_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="a cat", model=model, size="1024x1024"))
        params = mock.images.generate.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )

    @pytest.mark.parametrize("model", DALLE_MODELS)
    def test_dalle_models_include_response_format(self, model):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="a cat", model=model, size="1024x1024"))
        params = mock.images.generate.call_args[1]
        assert params.get("response_format") == "b64_json", (
            f"response_format must be b64_json for {model}"
        )


class TestGptImage2Background:
    """gpt-image-2 rejects transparent; the 2.5 models take it."""

    # Measured 2026-10-01: images.generate gpt-image-2 background=transparent ->
    # 400 "Transparent background is not supported for this model."; both 2.5
    # models returned RGBA PNGs with real alpha.
    def test_transparent_rejected_before_the_call_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.generate_image(
                prompt="a cat", model="gpt-image-2", background="transparent"
            ))
        assert str(exc.value) == (
            "gpt-image-2 does not support background='transparent'. Use gpt-image-2.5-flare, "
            "gpt-image-2.5-sunburst, gpt-image-2.6-flare, gpt-image-2.6-sunburst, "
            "or set background to auto or opaque."
        )
        mock.images.generate.assert_not_called()

    def test_edit_transparent_rejected_before_the_call_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError, match="gpt-image-2 does not support background='transparent'"):
            asyncio.run(client.edit_image(
                b"png-bytes", "add a hat", model="gpt-image-2", background="transparent"
            ))
        mock.images.edit.assert_not_called()

    def test_transparent_preserved_for_gpt_image_2_5(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="a cat", model="gpt-image-2.5-sunburst", background="transparent"
        ))
        params = mock.images.generate.call_args[1]
        assert params.get("background") == "transparent", (
            "gpt-image-2.5 supports transparent — must not be coerced"
        )

    def test_opaque_passes_through_unchanged_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="a cat", model="gpt-image-2", background="opaque"
        ))
        assert mock.images.generate.call_args[1].get("background") == "opaque"

    def test_auto_background_omitted_for_gpt_image_2(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="a cat", model="gpt-image-2", background="auto"
        ))
        # auto means "don't send the param" — matches existing behavior for other GPT image models
        assert "background" not in mock.images.generate.call_args[1]


class TestGptImage2ModelPresence:
    """gpt-image-2 must be exposed via the client's model catalog."""

    def test_gpt_image_2_in_image_models(self):
        assert "gpt-image-2" in OpenAIClient.IMAGE_MODELS

    def test_gpt_image_2_takes_custom_sizes_and_rejects_input_fidelity(self):
        caps = OpenAIClient.IMAGE_MODELS["gpt-image-2"]
        assert (caps.custom_size, caps.input_fidelity) == (True, False)


class TestModeration:
    """moderation parameter: pass-through for GPT Image models, skipped for others."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_moderation_low_sent_for_gpt_image_models(self, model):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model=model, size="1024x1024", moderation="low",
        ))
        params = mock.images.generate.call_args[1]
        assert params.get("moderation") == "low"

    def test_moderation_auto_not_sent(self):
        """'auto' is the API default — don't send it (matches our background pattern)."""
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model="gpt-image-2", size="1024x1024", moderation="auto",
        ))
        assert "moderation" not in mock.images.generate.call_args[1]

    def test_moderation_skipped_for_dalle_3(self):
        """dall-e-3 doesn't accept moderation — skip to avoid an API error."""
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model="dall-e-3", moderation="low",
        ))
        assert "moderation" not in mock.images.generate.call_args[1]

    def test_moderation_skipped_for_dalle_2(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model="dall-e-2", moderation="low",
        ))
        assert "moderation" not in mock.images.generate.call_args[1]

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_moderation_in_edit_reaches_the_server_through_extra_body(self, model):
        # Images.edit() has no `moderation` keyword in any SDK (2.15, 2.38,
        # 3.31), so passing it raises TypeError before the request. The server
        # does take the field: a bogus value via extra_body gets a 400 "Supported
        # values are: 'auto' and 'low'" naming moderation (measured 2026-10-14).
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=b"fakepng", prompt="edit", model=model, moderation="low",
        ))
        params = mock.images.edit.call_args[1]
        assert_binds(params, "openai.resources.images", "Images", "edit")
        assert params["extra_body"] == {"moderation": "low"}

    def test_moderation_auto_not_sent_in_edit(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=b"fakepng", prompt="edit", model="gpt-image-2", moderation="auto",
        ))
        params = mock.images.edit.call_args[1]
        assert "moderation" not in params
        assert "extra_body" not in params


class TestNValidation:
    """GPT Image models accept n=1-10."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_models_accept_n_up_to_10(self, model):
        client, mock = _make_client_with_mock()
        # gpt-image-2 needs a valid size (n validation happens after size validation)
        asyncio.run(client.generate_image(prompt="x", model=model, size="1024x1024", n=10))
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
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="512x512"))

    def test_256_also_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least 655,360"):
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="256x256"))

    def test_valid_1024_passes(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="1024x1024"))
        assert mock.images.generate.called

    def test_above_max_edge_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="max edge"):
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="4000x2160"))

    def test_non_multiple_of_16_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="multiples of 16"):
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="1023x1024"))

    def test_aspect_ratio_over_3_1_raises(self):
        client, _ = _make_client_with_mock()
        # 3200x800 = 2.56M pixels (above min), edges multiples of 16, but 4:1 ratio
        with pytest.raises(ValueError, match="aspect ratio"):
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="3200x800"))

    def test_above_max_pixels_raises(self):
        client, _ = _make_client_with_mock()
        # 3840x3200 = 12.3M pixels (above 8.3M max); edges multiples of 16 and ratio 1.2:1
        with pytest.raises(ValueError, match=r"max is 8,294,400"):
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="3840x3200"))

    def test_auto_size_skips_validation(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="auto"))
        assert mock.images.generate.called

    @pytest.mark.parametrize("model", sorted(OpenAIClient.IMAGE_MODELS))
    def test_edit_rejects_sizes_below_pixel_budget_before_calling_api(self, model):
        # Measured live 2026-09-21: images.edit 400s 512x512 and 256x256 on
        # gpt-image-2 and both 2.5 models ("below the current minimum pixel budget").
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError, match=f"{model} requires at least 655,360"):
            asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model=model, size="512x512"))
        assert not mock.images.edit.called

    def test_edit_accepts_arbitrary_size_on_gpt_image_2(self):
        # Measured live 2026-09-21: 1536x864 is accepted by images.edit on gpt-image-2.
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model="gpt-image-2", size="1536x864"))
        assert mock.images.edit.call_args[1]["size"] == "1536x864"

    def test_edit_min_pixel_floor_matches_api(self):
        # Measured live 2026-09-21 on gpt-image-2 and gpt-image-2.5-flare:
        # 816x800 (652,800 px) 400s, 1024x640 (655,360 px) is accepted.
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least 655,360"):
            asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model="gpt-image-2", size="816x800"))
        asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model="gpt-image-2", size="1024x640"))
        assert mock.images.edit.call_args[1]["size"] == "1024x640"


class TestEditInputFidelity:
    """images.edit rejects input_fidelity on gpt-image-2 AND both 2.5 models
    (400 invalid_input_fidelity_model, measured live 2026-09-21). The OpenAI
    reference names only gpt-image-2 as ignoring it; the reference is wrong."""

    @pytest.mark.parametrize("model", sorted(OpenAIClient.IMAGE_MODELS))
    def test_dropped_for_gpt_image_2_family(self, model):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=b"fakepng", prompt="x", model=model, input_fidelity="high",
        ))
        assert "input_fidelity" not in mock.images.edit.call_args[1]

    def test_malformed_size_skips_validation(self):
        """Malformed strings fall through to the API, which returns its own
        error message. We don't try to second-guess the parser."""
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", size="notasize"))
        assert mock.images.generate.called

class TestEditImageParams:
    """Verify edit_image builds correct params per model."""

    @pytest.mark.parametrize("model", GPT_IMAGE_MODELS)
    def test_gpt_image_models_omit_response_format(self, model):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"fakepng", prompt="make it blue", model=model))
        params = mock.images.edit.call_args[1]
        assert "response_format" not in params, (
            f"response_format must not be sent for {model}"
        )


class TestEditImageMultiImage:
    """edit_image accepts bytes or list[bytes] for multi-image editing."""

    def test_single_bytes_sends_singular_image_param(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"onepng", prompt="x", model="gpt-image-2"))
        image_param = mock.images.edit.call_args[1]["image"]
        # Singular: 3-tuple (filename, bytes, mime)
        assert isinstance(image_param, tuple)
        assert image_param[0] == "image.png"
        assert image_param[1] == b"onepng"
        assert image_param[2] == "image/png"

    def test_list_of_bytes_sends_array_image_param(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=[b"first", b"second", b"third"],
            prompt="compose these",
            model="gpt-image-2",
        ))
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
        asyncio.run(client.edit_image(
            image_data=[b"single_in_list"], prompt="x", model="gpt-image-2"
        ))
        image_param = mock.images.edit.call_args[1]["image"]
        # Len-1 list is collapsed to singular
        assert isinstance(image_param, tuple)
        assert image_param[1] == b"single_in_list"

    def test_empty_list_raises(self):
        client, _ = _make_client_with_mock()
        with pytest.raises(ValueError, match="at least one image"):
            asyncio.run(client.edit_image(image_data=[], prompt="x", model="gpt-image-2"))

    def test_mask_still_attaches_with_multi_image(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=[b"a", b"b"],
            mask_data=b"maskbytes",
            prompt="x",
            model="gpt-image-2",
        ))
        params = mock.images.edit.call_args[1]
        assert "mask" in params
        assert params["mask"][1] == b"maskbytes"
        # image is still the multi-image array
        assert isinstance(params["image"], list)
        assert len(params["image"]) == 2


class TestEditNodeMask:
    """The node turns a MASK into the first image's alpha: white (edit) becomes transparent."""

    # ComfyUI's MASK is [B, H, W]; a bare [H, W] also reaches the node.
    @pytest.mark.parametrize("mask_shape", [(1, 2, 3), (2, 3)])
    def test_mask_becomes_the_first_images_alpha(self, mask_shape):
        torch = pytest.importorskip("torch")
        from io import BytesIO
        from types import SimpleNamespace
        from PIL import Image
        from erpk.openai.image_nodes import OpenAIImageEdit

        seen = {}

        async def edit_image(**kwargs):
            seen.update(kwargs)
            return {"blocked": True, "error": "stop here"}

        mask = torch.zeros(mask_shape)
        mask[..., 0, 1] = 1.0
        with pytest.raises(ValueError, match="stop here"):
            asyncio.run(OpenAIImageEdit.execute(
                image=torch.zeros(1, 2, 3, 3), prompt="x",
                client=SimpleNamespace(edit_image=edit_image), mask=mask,
            ))
        sent = Image.open(BytesIO(seen["mask_data"]))
        assert (sent.mode, sent.size) == ("RGBA", (3, 2))
        assert list(sent.getchannel("A").getdata()) == [255, 0, 255, 255, 255, 255]


class TestMarkup:
    """images.edit takes a `markup` file of drawn marks, which SDK 2.15's
    Images.edit() has no keyword for and extra_body cannot carry (400 "Invalid
    type for 'markup': expected a file, but got an array instead", measured
    2026-11-05), so the client posts the multipart request itself."""

    @pytest.fixture(autouse=True)
    def images_response(self, monkeypatch):
        import types as pytypes
        stand_in = type("ImagesResponse", (), {})
        monkeypatch.setitem(sys.modules, "openai.types", pytypes.SimpleNamespace(ImagesResponse=stand_in))
        return stand_in

    def test_the_installed_sdk_has_what_the_post_uses(self):
        assert sdk_has("openai.types", "ImagesResponse")
        assert_binds({"cast_to": 1, "body": 1, "files": 1, "options": 1},
                     "openai._base_client", "SyncAPIClient", "post")

    def test_one_image_and_the_markup_go_out_as_files(self, images_response):
        client, mock = _make_client_with_mock()
        result = asyncio.run(client.edit_image(
            image_data=b"base", prompt="put an apple in the circle", model="gpt-image-2.6-flare",
            size="1024x1024", quality="low", markup_data=b"marks",
        ))
        mock.images.edit.assert_not_called()
        args, kwargs = mock.post.call_args
        assert args == ("/images/edits",)
        assert kwargs == {
            "cast_to": images_response,
            "body": {"model": "gpt-image-2.6-flare", "prompt": "put an apple in the circle",
                     "size": "1024x1024", "n": 1, "quality": "low"},
            "files": [("image", ("image.png", b"base", "image/png")),
                      ("markup", ("markup.png", b"marks", "image/png"))],
            "options": {"headers": {"Content-Type": "multipart/form-data"}},
        }
        assert result == {"images": ["fakebase64data"]}

    def test_several_images_go_out_as_an_array_with_the_body_extras(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=[b"first", b"second"], prompt="x", model="gpt-image-2.6-sunburst",
            moderation="low", complexity="medium", output_format="webp", output_compression=50,
            markup_data=b"marks",
        ))
        kwargs = mock.post.call_args[1]
        assert kwargs["body"] == {
            "model": "gpt-image-2.6-sunburst", "prompt": "x", "size": "1024x1024", "n": 1,
            "output_format": "webp", "output_compression": 50,
            "moderation": "low", "complexity": "medium",
        }
        assert kwargs["files"] == [
            ("image[]", ("image_0.png", b"first", "image/png")),
            ("image[]", ("image_1.png", b"second", "image/png")),
            ("markup", ("markup.png", b"marks", "image/png")),
        ]

    def test_a_mask_and_a_markup_are_refused_before_the_call(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.edit_image(
                image_data=b"base", prompt="x", model="gpt-image-2.6-flare",
                mask_data=b"mask", markup_data=b"marks",
            ))
        assert str(exc.value) == "A markup layer cannot be combined with a mask; send one or the other."
        mock.post.assert_not_called()
        mock.images.edit.assert_not_called()

    def test_a_model_outside_the_table_is_refused_before_the_call(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.edit_image(
                image_data=b"base", prompt="x", model="dall-e-2", markup_data=b"marks",
            ))
        assert str(exc.value) == (
            "dall-e-2 does not take a markup layer. Use gpt-image-2, gpt-image-2.5-flare, "
            "gpt-image-2.5-sunburst, gpt-image-2.6-flare, gpt-image-2.6-sunburst."
        )
        mock.post.assert_not_called()

    def test_without_a_markup_the_edit_still_goes_through_images_edit(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"base", prompt="x", model="gpt-image-2.6-flare"))
        mock.post.assert_not_called()
        assert mock.images.edit.called


class TestEditNodeMarkup:
    """The node builds the markup PNG: colour from `markup`, alpha from
    `markup_mask` read as Load Image writes it (1 - alpha, ComfyUI nodes.py
    LoadImage), else opaque wherever the markup is not pure black."""

    @staticmethod
    def _refusal(**inputs):
        """The node's error message; the recording client answers every call with "stop here"."""
        from types import SimpleNamespace
        from erpk.openai.image_nodes import OpenAIImageEdit
        seen = inputs.pop("seen", {})

        async def edit_image(**kwargs):
            seen.update(kwargs)
            return {"blocked": True, "error": "stop here"}

        with pytest.raises(ValueError) as exc:
            asyncio.run(OpenAIImageEdit.execute(
                prompt="x", client=SimpleNamespace(edit_image=edit_image), **inputs,
            ))
        return str(exc.value)

    @classmethod
    def _run(cls, **inputs):
        seen = {}
        assert cls._refusal(seen=seen, **inputs).endswith("stop here")
        return seen

    @staticmethod
    def _markup(torch):
        # 2x3 layer: one red mark at (row 0, col 1), the rest black.
        markup = torch.zeros(1, 2, 3, 3)
        markup[0, 0, 1] = torch.tensor([1.0, 0.0, 0.0])
        return markup

    @staticmethod
    def _decode(payload):
        from io import BytesIO
        from PIL import Image
        with Image.open(BytesIO(payload)) as img:
            return img.mode, img.size, list(img.getdata())

    def test_without_a_mask_non_black_pixels_are_the_marks(self):
        torch = pytest.importorskip("torch")
        seen = self._run(image=torch.zeros(1, 2, 3, 3), markup=self._markup(torch))
        assert self._decode(seen["markup_data"]) == ("RGBA", (3, 2), [
            (0, 0, 0, 0), (255, 0, 0, 255), (0, 0, 0, 0),
            (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0),
        ])
        assert seen["mask_data"] is None

    def test_a_load_image_mask_sets_the_alpha(self):
        torch = pytest.importorskip("torch")
        # Load Image's MASK is 1 where the PNG is transparent; here the mark at
        # (row 1, col 2) is black but opaque, and the red pixel is transparent.
        mask = torch.ones(1, 2, 3)
        mask[0, 1, 2] = 0.0
        seen = self._run(image=torch.zeros(1, 2, 3, 3), markup=self._markup(torch), markup_mask=mask)
        assert self._decode(seen["markup_data"]) == ("RGBA", (3, 2), [
            (0, 0, 0, 0), (255, 0, 0, 0), (0, 0, 0, 0),
            (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 255),
        ])

    def test_a_markup_unlike_image_1_in_size_is_refused(self):
        torch = pytest.importorskip("torch")
        assert self._refusal(image=torch.zeros(1, 4, 5, 3), markup=self._markup(torch)) == (
            "Failed to edit image: markup is 3x2 but image 1 is 5x4; "
            "draw the marks on a layer the size of image 1"
        )

    def test_a_mask_unlike_the_markup_in_size_is_refused(self):
        torch = pytest.importorskip("torch")
        # Load Image gives a 64x64 zero MASK for a PNG with no alpha channel.
        assert self._refusal(image=torch.zeros(1, 2, 3, 3), markup=self._markup(torch),
                             markup_mask=torch.zeros(1, 64, 64)) == (
            "Failed to edit image: markup_mask is 64x64 but markup is 3x2; "
            "connect the MASK of the Load Image that loads the markup"
        )

    def test_a_markup_mask_alone_is_refused(self):
        torch = pytest.importorskip("torch")
        seen = {}
        assert self._refusal(seen=seen, image=torch.zeros(1, 2, 3, 3), markup_mask=torch.zeros(1, 2, 3)) == (
            "markup_mask is connected but markup is not; connect the markup IMAGE too")
        assert seen == {}

    def test_both_sockets_are_optional_and_sit_after_mask(self):
        from erpk.openai.image_nodes import OpenAIImageEdit
        inputs = OpenAIImageEdit.define_schema().inputs
        sockets = [(i.id, i.io_type, i.optional) for i in inputs if i.io_type in ("IMAGE", "MASK")]
        assert sockets == [("image", "IMAGE", True), ("mask", "MASK", True),
                           ("markup", "IMAGE", True), ("markup_mask", "MASK", True)]


class TestOutputFormat:
    """images.generate and images.edit take output_format (png/jpeg/webp) and
    output_compression (0-100, jpeg/webp only) for GPT Image models, per the
    images API reference."""

    WIDGETS_BEFORE = {
        "OpenAIImageGeneration": [
            "prompt", "model", "size", "custom_width", "custom_height",
            "quality", "background", "moderation", "n", "seed",
        ],
        "OpenAIImageEdit": [
            "prompt", "model", "size", "custom_width", "custom_height",
            "quality", "moderation", "n", "background", "input_fidelity", "seed",
        ],
    }
    WIDGETS_AFTER = {
        "OpenAIImageGeneration": ["complexity", "frame_count", "frame_duration_ms"],
        "OpenAIImageEdit": ["grid_images", "complexity"],
    }
    FORMATS = {
        "OpenAIImageGeneration": ["png", "jpeg", "webp", "gif"],
        "OpenAIImageEdit": ["png", "jpeg", "webp"],
    }

    @pytest.mark.parametrize("class_name", sorted(WIDGETS_BEFORE))
    def test_new_widgets_are_appended_last(self, class_name):
        # widgets_values is positional: existing widgets keep their slots.
        import importlib
        cls = getattr(importlib.import_module("erpk.openai.image_nodes"), class_name)
        inputs = cls.define_schema().inputs
        widget_ids = [i.id for i in inputs
                      if i.io_type in ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")]
        assert widget_ids == (self.WIDGETS_BEFORE[class_name] + ["output_format", "output_compression"]
                              + self.WIDGETS_AFTER[class_name])
        fmt = next(i for i in inputs if i.id == "output_format")
        assert fmt.options == self.FORMATS[class_name] and fmt.default == "png"
        comp = next(i for i in inputs if i.id == "output_compression")
        assert (comp.min, comp.max, comp.default) == (0, 100, 100)

    @pytest.mark.parametrize("fmt", ["jpeg", "webp"])
    def test_lossy_format_sends_format_and_compression(self, fmt):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", output_format=fmt, output_compression=60))
        params = mock.images.generate.call_args[1]
        assert params["output_format"] == fmt
        assert params["output_compression"] == 60

    def test_png_sends_neither(self):
        # png is the API default and takes no compression.
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2", output_format="png", output_compression=60))
        params = mock.images.generate.call_args[1]
        assert "output_format" not in params
        assert "output_compression" not in params

    def test_edit_sends_format_and_compression(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model="gpt-image-2",
                                      output_format="webp", output_compression=40))
        params = mock.images.edit.call_args[1]
        assert params["output_format"] == "webp"
        assert params["output_compression"] == 40

    def test_edit_png_sends_neither(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(image_data=b"fakepng", prompt="x", model="gpt-image-2",
                                      output_format="png", output_compression=40))
        params = mock.images.edit.call_args[1]
        assert "output_format" not in params
        assert "output_compression" not in params

    def test_generation_node_forwards_widgets(self):
        from erpk.openai.image_nodes import OpenAIImageGeneration
        seen = {}

        class RecordingClient:
            async def generate_image(self, **kwargs):
                seen.update(kwargs)
                return {"blocked": True, "error": "stop here"}

        with pytest.raises(ValueError, match="stop here"):
            asyncio.run(OpenAIImageGeneration.execute(
                "a cat", client=RecordingClient(), output_format="jpeg", output_compression=70,
            ))
        assert (seen["output_format"], seen["output_compression"]) == ("jpeg", 70)


class TestComplexity:
    """complexity low/medium/high returns 200 on GPT Image 2.6 for images.generate
    and images.edit; 2.5 answers 400 "Complexity 'low' is not supported for this
    image model." (measured 2026-11-05). SDK 2.15 has no complexity keyword."""

    def test_generate_sends_it_in_the_body_on_26(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model="gpt-image-2.6-flare", complexity="low"))
        params = mock.images.generate.call_args[1]
        assert_binds(params, "openai.resources.images", "Images", "generate")
        assert params["extra_body"] == {"complexity": "low"}

    @pytest.mark.parametrize("model,complexity", [
        ("gpt-image-2.6-flare", "auto"),
        ("gpt-image-2.5-flare", "high"),
        ("gpt-image-2", "low"),
    ])
    def test_generate_leaves_it_out_for_auto_and_older_models(self, model, complexity):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(prompt="x", model=model, complexity=complexity))
        assert "extra_body" not in mock.images.generate.call_args[1]

    def test_edit_merges_it_with_moderation(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=b"fakepng", prompt="x", model="gpt-image-2.6-sunburst",
            moderation="low", complexity="high",
        ))
        params = mock.images.edit.call_args[1]
        assert_binds(params, "openai.resources.images", "Images", "edit")
        assert params["extra_body"] == {"moderation": "low", "complexity": "high"}

    def test_edit_on_25_keeps_moderation_alone(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.edit_image(
            image_data=b"fakepng", prompt="x", model="gpt-image-2.5-sunburst",
            moderation="low", complexity="high",
        ))
        assert mock.images.edit.call_args[1]["extra_body"] == {"moderation": "low"}

    @pytest.mark.parametrize("class_name", ["OpenAIImageGeneration", "OpenAIImageEdit"])
    def test_combo_offers_auto_and_the_three_levels(self, class_name):
        import importlib
        cls = getattr(importlib.import_module("erpk.openai.image_nodes"), class_name)
        combo = next(i for i in cls.define_schema().inputs if i.id == "complexity")
        assert (combo.options, combo.default, combo.optional) == (["auto", "low", "medium", "high"], "auto", True)

    def test_generation_node_forwards_it(self):
        from erpk.openai.image_nodes import OpenAIImageGeneration
        seen = {}

        class RecordingClient:
            async def generate_image(self, **kwargs):
                seen.update(kwargs)
                return {"blocked": True, "error": "stop here"}

        with pytest.raises(ValueError, match="stop here"):
            asyncio.run(OpenAIImageGeneration.execute("a cat", client=RecordingClient(), complexity="medium"))
        assert seen["complexity"] == "medium"

    def test_edit_node_forwards_it(self):
        torch = pytest.importorskip("torch")
        from types import SimpleNamespace
        from erpk.openai.image_nodes import OpenAIImageEdit
        seen = {}

        async def edit_image(**kwargs):
            seen.update(kwargs)
            return {"blocked": True, "error": "stop here"}

        with pytest.raises(ValueError, match="stop here"):
            asyncio.run(OpenAIImageEdit.execute(
                image=torch.zeros(1, 8, 8, 3), prompt="x",
                client=SimpleNamespace(edit_image=edit_image), complexity="low",
            ))
        assert seen["complexity"] == "low"


def _gif_base64(colours, size=(4, 3)):
    """An animated GIF, one solid frame per colour, as the API's b64_json."""
    import base64
    from io import BytesIO
    from PIL import Image
    frames = [Image.new("RGB", size, colour) for colour in colours]
    buffer = BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=200, loop=0)
    return base64.b64encode(buffer.getvalue()).decode()


class TestGif:
    """output_format gif returns a GIF89a on GPT Image 2.6; 2.5 and gpt-image-2
    answer 400 "GIF output is not enabled for the model '<id>'." frame_count
    (2-64) and frame_duration_ms (20-2000) ride in the body (measured 2026-11-05)."""

    def test_26_sends_the_format_and_the_frame_fields(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="a bouncing ball", model="gpt-image-2.6-flare", size="auto", output_format="gif",
            output_compression=40, complexity="low", frame_count=2, frame_duration_ms=150,
        ))
        params = mock.images.generate.call_args[1]
        assert_binds(params, "openai.resources.images", "Images", "generate")
        assert params["output_format"] == "gif"
        assert "output_compression" not in params
        assert params["extra_body"] == {"complexity": "low", "frame_count": 2, "frame_duration_ms": 150}

    @pytest.mark.parametrize("model", ["gpt-image-2.5-flare", "gpt-image-2.5-sunburst", "gpt-image-2"])
    def test_older_models_are_refused_before_the_call(self, model):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.generate_image(prompt="x", model=model, output_format="gif", frame_count=2))
        assert str(exc.value) == (
            f"{model} does not support output_format='gif'. "
            "Use gpt-image-2.6-flare, gpt-image-2.6-sunburst, or pick png, jpeg or webp."
        )
        mock.images.generate.assert_not_called()

    def test_frame_fields_stay_out_of_a_still_image(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model="gpt-image-2.6-flare", output_format="png", frame_count=2, frame_duration_ms=150,
        ))
        assert "extra_body" not in mock.images.generate.call_args[1]

    @staticmethod
    def _node_output(images, **inputs):
        from erpk.openai.image_nodes import OpenAIImageGeneration

        class Client:
            async def generate_image(self, **kwargs):
                return {"images": images, "revised_prompt": None}

        return asyncio.run(OpenAIImageGeneration.execute("a ball", client=Client(), output_format="gif", **inputs))

    def test_the_node_returns_every_frame_of_every_animation(self):
        pytest.importorskip("torch")
        output = self._node_output([_gif_base64([(255, 0, 0), (0, 0, 255)]),
                                    _gif_base64([(0, 255, 0), (255, 255, 255)])])
        image = output.args[0]
        assert tuple(image.shape) == (4, 3, 4, 3)
        corners = [tuple(round(float(v) * 255) for v in image[i, 0, 0]) for i in range(4)]
        assert corners == [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 255)]

    def test_the_node_forwards_the_frame_widgets(self):
        from erpk.openai.image_nodes import OpenAIImageGeneration
        seen = {}

        class RecordingClient:
            async def generate_image(self, **kwargs):
                seen.update(kwargs)
                return {"blocked": True, "error": "stop here"}

        with pytest.raises(ValueError, match="stop here"):
            asyncio.run(OpenAIImageGeneration.execute(
                "a ball", client=RecordingClient(), output_format="gif", frame_count=4, frame_duration_ms=90,
            ))
        assert (seen["output_format"], seen["frame_count"], seen["frame_duration_ms"]) == ("gif", 4, 90)

    def test_the_api_sheet_message_reaches_the_user_whole(self):
        from erpk.openai.image_nodes import OpenAIImageGeneration
        api_message = ("No supported sheet fits 2 GIF frames at size '1024x1024'. Invalid size "
                       "'4096x2048'. The longest edge must be less than or equal to 3840.")

        class RefusingClient:
            async def generate_image(self, **kwargs):
                raise RuntimeError(api_message)

        with pytest.raises(ValueError) as exc:
            asyncio.run(OpenAIImageGeneration.execute("a ball", client=RefusingClient(), output_format="gif"))
        assert str(exc.value) == f"Failed to generate image: {api_message}"

    def test_frame_widgets_cover_the_documented_ranges(self):
        from erpk.openai.image_nodes import OpenAIImageGeneration
        inputs = {i.id: i for i in OpenAIImageGeneration.define_schema().inputs}
        count, duration = inputs["frame_count"], inputs["frame_duration_ms"]
        assert (count.min, count.max, count.default, count.optional) == (2, 64, 9, True)
        assert (duration.min, duration.max, duration.step, duration.default, duration.optional) == (20, 2000, 10, 200, True)


class TestSvg:
    """output_format svg on GPT Image 2.6 returns base64 SVG markup written by
    svg.model; without svg.model the API answers 400 "SVG generation requires
    'svg.model'", and 2.5 and gpt-image-2 answer 400 "SVG output is not
    supported for this model." (measured 2026-11-05)."""

    def test_26_sends_the_format_and_the_text_model(self):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="a red circle", model="gpt-image-2.6-sunburst", output_format="svg", n=1,
            complexity="medium", svg_model="gpt-6.1-sol",
        ))
        params = mock.images.generate.call_args[1]
        assert_binds(params, "openai.resources.images", "Images", "generate")
        assert (params["output_format"], params["n"]) == ("svg", 1)
        assert params["extra_body"] == {"complexity": "medium", "svg": {"model": "gpt-6.1-sol"}}

    @pytest.mark.parametrize("model", ["gpt-image-2.5-flare", "gpt-image-2.5-sunburst", "gpt-image-2"])
    def test_older_models_are_refused_before_the_call(self, model):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.generate_image(prompt="x", model=model, output_format="svg", svg_model="gpt-6.1-sol"))
        assert str(exc.value) == (
            f"{model} does not support output_format='svg'. Use gpt-image-2.6-flare, gpt-image-2.6-sunburst."
        )
        mock.images.generate.assert_not_called()

    def test_a_missing_text_model_is_refused_before_the_call(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError) as exc:
            asyncio.run(client.generate_image(prompt="x", model="gpt-image-2.6-flare", output_format="svg"))
        assert str(exc.value) == "output_format='svg' needs svg_model, the text model that writes the SVG markup."
        mock.images.generate.assert_not_called()


class TestSvgNode:
    """OpenAI SVG Generation returns the markup as one STRING."""

    SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="red"/></svg>'

    def _recording_client(self, seen, answer=None):
        import base64

        class Client:
            async def generate_image(self, **kwargs):
                seen.update(kwargs)
                return answer or {"images": [base64.b64encode(TestSvgNode.SVG.encode()).decode()]}

        return Client()

    def test_returns_the_decoded_markup(self):
        from erpk.openai.image_nodes import OpenAISVGGeneration
        seen = {}
        output = asyncio.run(OpenAISVGGeneration.execute("a red circle", client=self._recording_client(seen)))
        assert output.args == (self.SVG,)

    def test_sends_one_svg_from_the_defaults(self):
        from erpk.openai.image_nodes import OpenAISVGGeneration
        seen = {}
        asyncio.run(OpenAISVGGeneration.execute("a red circle", client=self._recording_client(seen)))
        assert seen == {
            "prompt": "a red circle", "model": "gpt-image-2.6-flare", "size": "1024x1024",
            "quality": "auto", "background": "auto", "n": 1, "output_format": "svg",
            "complexity": "auto", "svg_model": "gpt-6.1-sol",
        }

    def test_forwards_the_widgets(self):
        from erpk.openai.image_nodes import OpenAISVGGeneration
        seen = {}
        asyncio.run(OpenAISVGGeneration.execute(
            "a logo", client=self._recording_client(seen), model="gpt-image-2.6-sunburst",
            svg_model="gpt-6-luna", size="Custom", custom_width=1040, custom_height=1040,
            quality="low", complexity="low", background="transparent",
        ))
        assert {k: seen[k] for k in ("model", "svg_model", "size", "quality", "complexity", "background")} == {
            "model": "gpt-image-2.6-sunburst", "svg_model": "gpt-6-luna", "size": "1040x1040",
            "quality": "low", "complexity": "low", "background": "transparent",
        }

    def test_a_refusal_names_the_reason(self):
        from erpk.openai.image_nodes import OpenAISVGGeneration
        client = self._recording_client({}, answer={"images": [], "blocked": True, "error": "The prompt was refused."})
        with pytest.raises(ValueError) as exc:
            asyncio.run(OpenAISVGGeneration.execute("x", client=client))
        assert str(exc.value) == "Failed to generate SVG: Image blocked by content filters: The prompt was refused."

    def test_schema(self):
        from erpk.openai.image_nodes import OpenAISVGGeneration
        schema = OpenAISVGGeneration.define_schema()
        inputs = {i.id: i for i in schema.inputs}
        assert [(o.io_type, o.id) for o in schema.outputs] == [("STRING", "svg")]
        assert (inputs["model"].options, inputs["model"].default) == (
            ["gpt-image-2.6-sunburst", "gpt-image-2.6-flare"], "gpt-image-2.6-flare")
        assert inputs["svg_model"].default == "gpt-6.1-sol"
        assert "output_format" not in inputs and "n" not in inputs


class TestTransparentNeedsAlphaFormat:
    """background=transparent with output_format=jpeg returns 400 "Transparent
    background is not supported for JPEG output format" (measured on
    gpt-image-2.5-flare 2026-10-14), so all three paths refuse it before the
    call, naming both values."""

    MESSAGE = r"background='transparent'.*output_format='jpeg'"

    def test_generate_refuses_transparent_jpeg(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError, match=self.MESSAGE):
            asyncio.run(client.generate_image(
                prompt="x", model="gpt-image-2.5-flare", size="1024x1024",
                background="transparent", output_format="jpeg",
            ))
        mock.images.generate.assert_not_called()

    def test_edit_refuses_transparent_jpeg(self):
        client, mock = _make_client_with_mock()
        with pytest.raises(ValueError, match=self.MESSAGE):
            asyncio.run(client.edit_image(
                image_data=b"fakepng", prompt="x", model="gpt-image-2.5-flare",
                background="transparent", output_format="jpeg",
            ))
        mock.images.edit.assert_not_called()

    def test_responses_refuses_transparent_jpeg(self):
        client, mock = _make_client_with_mock()
        client.system_instruction = None
        with pytest.raises(ValueError, match=self.MESSAGE):
            asyncio.run(client.generate_image_via_responses(
                prompt="x", image_model="gpt-image-2.5-flare", size="1024x1024",
                background="transparent", output_format="jpeg",
            ))
        mock.responses.create.assert_not_called()

    @pytest.mark.parametrize("output_format", ["png", "webp"])
    def test_transparent_png_and_webp_still_sent(self, output_format):
        client, mock = _make_client_with_mock()
        asyncio.run(client.generate_image(
            prompt="x", model="gpt-image-2.5-flare", size="1024x1024",
            background="transparent", output_format=output_format,
        ))
        assert mock.images.generate.call_args[1]["background"] == "transparent"
