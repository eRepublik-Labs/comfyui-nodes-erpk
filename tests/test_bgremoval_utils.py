# ABOUTME: Tests for background removal utility functions.
# ABOUTME: Tests tensor/PIL conversions, mask extraction, and image processing.

"""
Tests for bgremoval/utils.py

These tests verify the utility functions work correctly without requiring
the heavy ML dependencies (rembg, transparent-background, transformers).
"""

import pytest
import numpy as np
from PIL import Image

# Import torch - skip all tests if not available
torch = pytest.importorskip("torch")

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bgremoval.utils import (
    tensor_to_pil,
    pil_to_tensor,
    pil_rgba_to_tensor,
    extract_mask_from_rgba,
    apply_mask_to_image,
    rgba_to_rgb_and_mask,
)


class TestTensorToPil:
    """Tests for tensor_to_pil conversion."""

    def test_single_image(self):
        """Convert single image tensor to PIL."""
        # Create a 3D tensor (H, W, C) representing a red image
        tensor = torch.zeros(64, 64, 3)
        tensor[:, :, 0] = 1.0  # Red channel

        images = tensor_to_pil(tensor)

        assert len(images) == 1
        assert images[0].mode == "RGB"
        assert images[0].size == (64, 64)
        # Check that the red channel is correct
        r, g, b = images[0].split()
        assert np.array(r).mean() == 255
        assert np.array(g).mean() == 0
        assert np.array(b).mean() == 0

    def test_batch_images(self):
        """Convert batch of image tensors to PIL list."""
        # Create a 4D tensor (B, H, W, C) with 3 images
        tensor = torch.rand(3, 32, 32, 3)

        images = tensor_to_pil(tensor)

        assert len(images) == 3
        for img in images:
            assert img.mode == "RGB"
            assert img.size == (32, 32)

    def test_value_range(self):
        """Verify values are correctly converted from [0,1] to [0,255]."""
        tensor = torch.full((1, 2, 2, 3), 0.5)

        images = tensor_to_pil(tensor)

        # 0.5 * 255 = 127.5 -> 127 (uint8)
        pixel = images[0].getpixel((0, 0))
        assert pixel == (127, 127, 127)


class TestPilToTensor:
    """Tests for pil_to_tensor conversion."""

    def test_rgb_image(self):
        """Convert RGB PIL image to tensor."""
        img = Image.new("RGB", (64, 64), color=(255, 0, 0))

        tensor = pil_to_tensor([img])

        assert tensor.shape == (1, 64, 64, 3)
        assert tensor.dtype == torch.float32
        # Red channel should be 1.0
        assert tensor[0, 0, 0, 0].item() == pytest.approx(1.0, abs=0.01)
        # Green and blue should be 0
        assert tensor[0, 0, 0, 1].item() == 0.0
        assert tensor[0, 0, 0, 2].item() == 0.0

    def test_rgba_to_rgb_conversion(self):
        """RGBA images should be converted to RGB (alpha dropped)."""
        img = Image.new("RGBA", (32, 32), color=(255, 0, 0, 128))

        tensor = pil_to_tensor([img])

        # Should have 3 channels, not 4
        assert tensor.shape == (1, 32, 32, 3)

    def test_batch_conversion(self):
        """Convert multiple PIL images to tensor batch."""
        images = [
            Image.new("RGB", (16, 16), color=(255, 0, 0)),
            Image.new("RGB", (16, 16), color=(0, 255, 0)),
            Image.new("RGB", (16, 16), color=(0, 0, 255)),
        ]

        tensor = pil_to_tensor(images)

        assert tensor.shape == (3, 16, 16, 3)


class TestPilRgbaToTensor:
    """Tests for pil_rgba_to_tensor conversion."""

    def test_rgba_preserved(self):
        """RGBA images should preserve alpha channel."""
        img = Image.new("RGBA", (32, 32), color=(255, 0, 0, 128))

        tensor = pil_rgba_to_tensor([img])

        assert tensor.shape == (1, 32, 32, 4)
        # Alpha should be 128/255 ≈ 0.502
        assert tensor[0, 0, 0, 3].item() == pytest.approx(128 / 255, abs=0.01)

    def test_rgb_converted_to_rgba(self):
        """RGB images should be converted to RGBA with full opacity."""
        img = Image.new("RGB", (32, 32), color=(255, 0, 0))

        tensor = pil_rgba_to_tensor([img])

        assert tensor.shape == (1, 32, 32, 4)
        # Alpha should be 1.0 (fully opaque)
        assert tensor[0, 0, 0, 3].item() == 1.0


class TestExtractMaskFromRgba:
    """Tests for extract_mask_from_rgba."""

    def test_extracts_alpha_channel(self):
        """Alpha channel should be extracted as mask."""
        # Create RGBA image with gradient alpha
        img = Image.new("RGBA", (32, 32), color=(255, 255, 255, 0))
        # Set some pixels to full opacity
        for x in range(16):
            for y in range(32):
                img.putpixel((x, y), (255, 255, 255, 255))

        mask = extract_mask_from_rgba([img])

        assert mask.shape == (1, 32, 32)
        # Left half should be 1.0 (foreground)
        assert mask[0, 0, 0].item() == 1.0
        # Right half should be 0.0 (background)
        assert mask[0, 0, 31].item() == 0.0

    def test_batch_extraction(self):
        """Extract masks from multiple images."""
        images = [
            Image.new("RGBA", (16, 16), color=(255, 0, 0, 255)),
            Image.new("RGBA", (16, 16), color=(0, 255, 0, 128)),
        ]

        masks = extract_mask_from_rgba(images)

        assert masks.shape == (2, 16, 16)
        assert masks[0, 0, 0].item() == 1.0  # Full opacity
        assert masks[1, 0, 0].item() == pytest.approx(128 / 255, abs=0.01)


class TestApplyMaskToImage:
    """Tests for apply_mask_to_image."""

    def test_creates_rgba_with_mask(self):
        """Mask should be applied as alpha channel."""
        img = Image.new("RGB", (32, 32), color=(255, 0, 0))
        mask = Image.new("L", (32, 32), color=128)

        result = apply_mask_to_image([img], [mask])

        assert len(result) == 1
        assert result[0].mode == "RGBA"
        # Alpha should match mask value
        r, g, b, a = result[0].split()
        assert np.array(a).mean() == 128

    def test_resizes_mask_to_match_image(self):
        """Mask should be resized if dimensions don't match."""
        img = Image.new("RGB", (64, 64), color=(255, 0, 0))
        mask = Image.new("L", (32, 32), color=255)

        result = apply_mask_to_image([img], [mask])

        assert result[0].size == (64, 64)


class TestRgbaToRgbAndMask:
    """Tests for rgba_to_rgb_and_mask."""

    def test_splits_correctly(self):
        """RGBA should be split into RGB and mask."""
        img = Image.new("RGBA", (32, 32), color=(255, 128, 64, 200))

        rgb_images, mask_images = rgba_to_rgb_and_mask([img])

        assert len(rgb_images) == 1
        assert len(mask_images) == 1
        assert rgb_images[0].mode == "RGB"
        assert mask_images[0].mode == "L"
        # Check RGB values preserved
        assert rgb_images[0].getpixel((0, 0)) == (255, 128, 64)
        # Check alpha extracted correctly
        assert mask_images[0].getpixel((0, 0)) == 200


class TestRoundTrip:
    """Test roundtrip conversions maintain data integrity."""

    def test_tensor_pil_tensor(self):
        """tensor -> PIL -> tensor should preserve values."""
        original = torch.rand(2, 32, 32, 3)

        pil_images = tensor_to_pil(original)
        result = pil_to_tensor(pil_images)

        # Allow for uint8 quantization error
        assert torch.allclose(original, result, atol=1 / 255 + 0.01)

    def test_pil_tensor_pil(self):
        """PIL -> tensor -> PIL should preserve values."""
        original = Image.new("RGB", (32, 32), color=(100, 150, 200))

        tensor = pil_to_tensor([original])
        result = tensor_to_pil(tensor)[0]

        assert result.getpixel((0, 0)) == (100, 150, 200)
