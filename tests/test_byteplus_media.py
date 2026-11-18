# ABOUTME: BytePlus media conversion: ModelArk input-image limits, alpha from a ComfyUI MASK,
# ABOUTME: and Seedream responses (including layer decomposition) back to IMAGE plus alpha.

import base64
import io

import pytest

torch = pytest.importorskip("torch")
Image = pytest.importorskip("PIL.Image")

from erpk.byteplus.byteplus_api.media import (  # noqa: E402
    SEEDANCE_IMAGE_LIMITS, SEEDREAM_IMAGE_LIMITS, compose, decode_items, images_to_data_uris,
)


def response_to_images(data, layers):
    images, errors = decode_items(data)
    assert errors == []
    return compose(data, images, layers)


def _png_b64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_seedance_rejects_images_outside_its_documented_size_and_ratio():
    with pytest.raises(ValueError) as excinfo:
        images_to_data_uris(torch.zeros((1, 200, 400, 3)), SEEDANCE_IMAGE_LIMITS, "first_frame")
    assert str(excinfo.value) == "first_frame image 1 is 400x200; width and height must be 300-6000 px."
    with pytest.raises(ValueError) as excinfo:
        images_to_data_uris(torch.zeros((1, 300, 900, 3)), SEEDANCE_IMAGE_LIMITS, "first_frame")
    assert str(excinfo.value) == "first_frame image 1 is 900x300; the aspect ratio must be 0.4-2.5."
    uris = images_to_data_uris(torch.zeros((2, 300, 400, 3)), SEEDREAM_IMAGE_LIMITS, "images")
    assert len(uris) == 2 and all(u.startswith("data:image/jpeg;base64,") for u in uris)


def test_a_mask_becomes_the_png_alpha_channel_in_loadimage_convention():
    image = torch.ones((1, 300, 300, 3))
    mask = torch.zeros((1, 300, 300))
    mask[:, :, :150] = 1.0
    [uri] = images_to_data_uris(image, SEEDREAM_IMAGE_LIMITS, "images", mask=mask)
    assert uri.startswith("data:image/png;base64,")
    decoded = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))
    assert decoded.mode == "RGBA"
    assert decoded.getpixel((10, 10))[3] == 0 and decoded.getpixel((290, 10))[3] == 255


def test_layers_are_placed_on_the_base_canvas_at_their_bounding_box():
    base = Image.new("RGB", (8, 6), (0, 0, 255))
    layer = Image.new("RGBA", (2, 3), (255, 0, 0, 255))
    data = [
        {"b64_json": _png_b64(base), "z_index": 0},
        {"b64_json": _png_b64(layer), "z_index": 1,
         "bounding_box": {"absolute": [5, 2, 7, 5], "normalized": [0.625, 0.33, 0.875, 0.83]}},
    ]
    images, alpha = response_to_images(data, layers=True)
    assert tuple(images.shape) == (2, 6, 8, 3) and tuple(alpha.shape) == (2, 6, 8)
    assert images[0, 0, 0].tolist() == [0.0, 0.0, 1.0] and alpha[0].min().item() == 1.0
    assert images[1, 2, 5].tolist() == [1.0, 0.0, 0.0] and alpha[1, 2, 5].item() == 1.0
    assert alpha[1, 0, 0].item() == 0.0 and alpha[1, 5, 5].item() == 0.0
    assert alpha[1].sum().item() == 6.0


def test_mixed_output_sizes_are_letterboxed_onto_the_largest_with_transparent_bars():
    data = [{"b64_json": _png_b64(Image.new("RGB", (4, 4), (255, 255, 255)))},
            {"b64_json": _png_b64(Image.new("RGB", (4, 5), (0, 0, 0)))}]
    images, alpha = response_to_images(data, layers=False)
    assert tuple(images.shape) == (2, 5, 4, 3) and tuple(alpha.shape) == (2, 5, 4)
    assert images[0, 0, 0].tolist() == [1.0, 1.0, 1.0] and alpha[0, :4].min().item() == 1.0
    assert images[0, 4, 0].tolist() == pytest.approx([128 / 255] * 3) and alpha[0, 4].max().item() == 0.0
    assert alpha[1].min().item() == 1.0


def test_the_layer_base_is_the_item_with_z_index_0_wherever_it_sits():
    base = Image.new("RGB", (8, 6), (0, 0, 255))
    layer = Image.new("RGBA", (2, 3), (255, 0, 0, 255))
    data = [
        {"b64_json": _png_b64(layer), "z_index": 1, "bounding_box": {"absolute": [5, 2, 7, 5]}},
        {"b64_json": _png_b64(base), "z_index": 0},
    ]
    images, alpha = response_to_images(data, layers=True)
    assert images[0, 0, 0].tolist() == [0.0, 0.0, 1.0] and alpha[0].min().item() == 1.0
    assert images[1, 2, 5].tolist() == [1.0, 0.0, 0.0] and alpha[1].sum().item() == 6.0


@pytest.mark.parametrize("box, message", [
    (None, "A Seedream layer is 2x3 with no bounding box on a 8x6 base."),
    ({"absolute": [5, 2, 5, 5]}, "A Seedream layer has an empty bounding box [5, 2, 5, 5]."),
])
def test_a_layer_that_cannot_be_placed_raises(box, message):
    data = [{"b64_json": _png_b64(Image.new("RGB", (8, 6))), "z_index": 0},
            {"b64_json": _png_b64(Image.new("RGBA", (2, 3))), "z_index": 1, "bounding_box": box}]
    with pytest.raises(ValueError) as excinfo:
        response_to_images(data, layers=True)
    assert str(excinfo.value) == message


def test_decoding_keeps_every_image_that_decodes_and_names_the_rest():
    data = [{"b64_json": _png_b64(Image.new("RGB", (4, 4)))}, {"b64_json": "bm90IGFuIGltYWdl"}, {"size": "4x4"}]
    images, errors = decode_items(data)
    assert images[0].size == (4, 4) and images[1:] == [None, None]
    assert errors[0].startswith("image 2 of 3: ")
    assert errors[1] == "image 3 of 3: Seedream returned an image with neither url nor b64_json: ['size']"
