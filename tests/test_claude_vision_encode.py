# ABOUTME: Verifies Claude vision images are PNG-encoded once (size check folded in).
# ABOUTME: encode_and_validate_for_claude replaces the validate(encode)+pil_to_base64 pair.

import os

from PIL import Image

from erpk.claude.claude_api.utils import ImageConverter


def test_encode_and_validate_matches_single_encode_no_warning():
    img = Image.new("RGB", (32, 32), (10, 20, 30))
    b64, warning = ImageConverter.encode_and_validate_for_claude(img, format="PNG")
    assert warning is None
    # Must be byte-identical to a single pil_to_base64 encode (proves one encode).
    assert b64 == ImageConverter.pil_to_base64(img, format="PNG")


def test_encode_and_validate_flags_oversize():
    # Incompressible noise so the PNG comfortably exceeds Claude's 5MB limit.
    img = Image.frombytes("RGB", (2200, 2200), os.urandom(2200 * 2200 * 3))
    b64, warning = ImageConverter.encode_and_validate_for_claude(img, format="PNG")
    assert warning is not None and "5MB" in warning
    assert isinstance(b64, str) and len(b64) > 0
