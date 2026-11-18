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


def _data_uri_image(uri):
    """(the part before the comma, the decoded image) of a base64 data URI."""
    header, payload = uri.split(",", 1)
    return header, Image.open(io.BytesIO(base64.b64decode(payload)))


def test_seedance_rejects_images_outside_its_documented_size_and_ratio():
    with pytest.raises(ValueError) as excinfo:
        images_to_data_uris(torch.zeros((1, 200, 400, 3)), SEEDANCE_IMAGE_LIMITS, "first_frame")
    assert str(excinfo.value) == "first_frame image 1 is 400x200; width and height must be 300-6000 px."
    with pytest.raises(ValueError) as excinfo:
        images_to_data_uris(torch.zeros((1, 300, 900, 3)), SEEDANCE_IMAGE_LIMITS, "first_frame")
    assert str(excinfo.value) == "first_frame image 1 is 900x300; the aspect ratio must be 0.4-2.5."
    uris = images_to_data_uris(torch.zeros((2, 300, 400, 3)), SEEDREAM_IMAGE_LIMITS, "images")
    decoded = [_data_uri_image(uri) for uri in uris]
    assert [(header, image.format, image.size) for header, image in decoded] == [
        ("data:image/jpeg;base64", "JPEG", (400, 300))] * 2


def test_a_mask_becomes_the_png_alpha_channel_in_loadimage_convention():
    image = torch.ones((1, 300, 300, 3))
    mask = torch.zeros((1, 300, 300))
    mask[:, :, :150] = 1.0
    [uri] = images_to_data_uris(image, SEEDREAM_IMAGE_LIMITS, "images", mask=mask)
    header, decoded = _data_uri_image(uri)
    assert (header, decoded.format, decoded.mode) == ("data:image/png;base64", "PNG", "RGBA")
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
    assert errors[0] == "image 2 of 3: the data is not an image PIL can read"
    assert errors[1] == "image 3 of 3: Seedream returned an image with neither url nor b64_json: ['size']"


@pytest.fixture
def resolver(monkeypatch):
    """Answers the real fetch_remote_bytes' host lookups from a script and counts them.
    No test resolves to a public address, so no request ever leaves the machine."""
    import socket

    from erpk.byteplus.byteplus_api import media

    script, lookups = [], []

    def getaddrinfo(host, *_, **__):
        lookups.append(host)
        outcome = script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (outcome, 443))]

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(media, "DOWNLOAD_RETRY_DELAYS", (0, 0))
    return script, lookups


def test_a_result_host_that_does_not_resolve_is_retried_like_a_connection_error(resolver):
    import socket

    script, lookups = resolver
    script += [socket.gaierror(8, "nodename nor servname provided, or not known")] * 3
    images, errors = decode_items([{"url": "https://cdn.example.com/a.png"}])
    assert images == [None]
    assert errors == ["image 1 of 1: Downloading https://cdn.example.com/a.png failed after 3 attempts: "
                      "Cannot resolve host: cdn.example.com"]
    assert lookups == ["cdn.example.com"] * 3


@pytest.mark.parametrize("url, script, error, lookup_count", [
    ("https://cdn.example.com/a.png", ["127.0.0.1"],
     "Host cdn.example.com resolves to blocked address 127.0.0.1", 1),
    ("ftp://cdn.example.com/a.png", [], "Disallowed scheme: 'ftp'", 0),
])
def test_a_result_url_that_fails_validation_is_not_retried(resolver, url, script, error, lookup_count):
    queued, lookups = resolver
    queued += script
    images, errors = decode_items([{"url": url}])
    assert images == [None]
    assert errors == [f"image 1 of 1: Downloading {url} failed: {error}"]
    assert len(lookups) == lookup_count
