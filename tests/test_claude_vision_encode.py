# ABOUTME: Verifies Claude vision images are PNG-encoded once and checked against the API's base64 size limit.
# ABOUTME: Measured 2026-11-03: 9.88 MB of base64 returned 200, 10.67 MB returned 400 "image exceeds 10 MB maximum".

import re

import numpy as np
import pytest
from PIL import Image

from erpk.claude.claude_api.utils import ImageConverter

BASE64_LIMIT = 10_485_760  # "image exceeds 10 MB maximum: 10670936 bytes > 10485760 bytes"


def _noise(side):
    # Incompressible, so the PNG is about side * side * 3 bytes.
    return Image.fromarray(np.random.default_rng(0).integers(0, 256, (side, side, 3), dtype=np.uint8))


def test_encode_matches_a_single_png_encode():
    img = Image.new("RGB", (32, 32), (10, 20, 30))
    assert ImageConverter.encode_and_validate_for_claude(img, format="PNG") == ImageConverter.pil_to_base64(img, format="PNG")


def test_encode_sends_an_image_between_5mb_and_the_base64_limit():
    b64 = ImageConverter.encode_and_validate_for_claude(_noise(1550), format="PNG")
    assert 7 * 1024 * 1024 < len(b64) < BASE64_LIMIT


def test_encode_refuses_an_image_over_the_base64_limit_with_its_size():
    with pytest.raises(ValueError) as raised:
        ImageConverter.encode_and_validate_for_claude(_noise(1700), format="PNG")
    match = re.fullmatch(r"Image is (\d+) bytes as base64; Claude accepts at most 10485760", str(raised.value))
    assert match is not None, str(raised.value)
    assert int(match.group(1)) > BASE64_LIMIT
