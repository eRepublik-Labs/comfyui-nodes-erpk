# ABOUTME: Tests for image_to_data_uri / images_to_data_uris helpers used by Seedance IMAGE inputs.
# ABOUTME: Verifies the base64 data URI format and the batch cap.

import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# These helpers depend on PIL + torch via wavespeed/wavespeed_api/utils.py.
# Skip the whole module if either is unavailable in the test env.
PIL = pytest.importorskip("PIL.Image")
torch = pytest.importorskip("torch")

from wavespeed.wavespeed_api.utils import image_to_data_uri, images_to_data_uris


def _solid_color_tensor(width=4, height=4, color=(255, 0, 0), batch=1):
    img = PIL.new("RGB", (width, height), color)
    arr = [
        [list(img.getpixel((x, y))) for x in range(width)]
        for y in range(height)
    ]
    t = torch.tensor(arr, dtype=torch.float32) / 255.0  # (H, W, C)
    return t.unsqueeze(0).expand(batch, -1, -1, -1).clone()


def test_image_to_data_uri_returns_jpeg_data_uri():
    pil = PIL.new("RGB", (4, 4), (0, 128, 255))
    uri = image_to_data_uri(pil)
    assert uri is not None
    assert uri.startswith("data:image/jpeg;base64,"), f"unexpected URI prefix: {uri[:40]}"


def test_image_to_data_uri_accepts_tensor():
    t = _solid_color_tensor()
    uri = image_to_data_uri(t)
    assert uri is not None and uri.startswith("data:image/jpeg;base64,")


def test_image_to_data_uri_returns_none_for_none():
    assert image_to_data_uri(None) is None


def test_images_to_data_uris_returns_list():
    t = _solid_color_tensor(batch=3)
    uris = images_to_data_uris(t)
    assert isinstance(uris, list) and len(uris) == 3
    assert all(u.startswith("data:image/jpeg;base64,") for u in uris)


def test_images_to_data_uris_caps_at_max_count():
    t = _solid_color_tensor(batch=6)
    uris = images_to_data_uris(t, max_count=4)
    assert len(uris) == 4


def test_images_to_data_uris_returns_none_for_none():
    assert images_to_data_uris(None) is None
