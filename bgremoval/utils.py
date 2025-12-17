# ABOUTME: Shared utilities for background removal nodes.
# ABOUTME: Provides tensor/PIL conversion and image processing helpers.

"""
Utility functions for background removal nodes.

Provides common functionality shared across all backends:
- Tensor to PIL image conversion
- PIL image to tensor conversion
- Mask extraction and conversion
- Batch processing helpers
"""

from typing import List, Tuple
import numpy as np
from PIL import Image

try:
    import torch
except ImportError:
    torch = None


def tensor_to_pil(tensor) -> List[Image.Image]:
    """
    Convert a ComfyUI image tensor to a list of PIL Images.

    Args:
        tensor: ComfyUI IMAGE tensor with shape (B, H, W, C) where C is 3 (RGB)
                Values are floats in range [0, 1]

    Returns:
        List of PIL Images in RGB mode
    """
    if torch is None:
        raise ImportError("PyTorch is required for tensor conversion")

    # Handle single image (H, W, C) by adding batch dimension
    if tensor.dim() == 3:
        tensor = tensor.unsqueeze(0)

    images = []
    for i in range(tensor.shape[0]):
        # Convert from (H, W, C) float [0,1] to uint8 [0,255]
        img_np = (tensor[i].cpu().numpy() * 255).astype(np.uint8)
        images.append(Image.fromarray(img_np, mode="RGB"))

    return images


def pil_to_tensor(images: List[Image.Image]) -> "torch.Tensor":
    """
    Convert a list of PIL Images to a ComfyUI image tensor.

    For RGBA images, composites onto black background to show transparency effect.

    Args:
        images: List of PIL Images (RGB or RGBA mode)

    Returns:
        ComfyUI IMAGE tensor with shape (B, H, W, C) where C is 3 (RGB)
        Values are floats in range [0, 1]
    """
    if torch is None:
        raise ImportError("PyTorch is required for tensor conversion")

    tensors = []
    for img in images:
        if img.mode == "RGBA":
            # Composite RGBA onto black background to show cutout effect
            background = Image.new("RGB", img.size, (0, 0, 0))
            background.paste(img, mask=img.split()[3])  # Use alpha as mask
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Convert to float tensor [0, 1]
        img_np = np.array(img).astype(np.float32) / 255.0
        tensors.append(torch.from_numpy(img_np))

    return torch.stack(tensors)


def pil_rgba_to_tensor(images: List[Image.Image]) -> "torch.Tensor":
    """
    Convert a list of RGBA PIL Images to a ComfyUI image tensor.

    Args:
        images: List of PIL Images in RGBA mode

    Returns:
        ComfyUI IMAGE tensor with shape (B, H, W, 4) for RGBA
        Values are floats in range [0, 1]
    """
    if torch is None:
        raise ImportError("PyTorch is required for tensor conversion")

    tensors = []
    for img in images:
        # Ensure RGBA mode
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Convert to float tensor [0, 1]
        img_np = np.array(img).astype(np.float32) / 255.0
        tensors.append(torch.from_numpy(img_np))

    return torch.stack(tensors)


def extract_mask_from_rgba(images: List[Image.Image]) -> "torch.Tensor":
    """
    Extract alpha channel from RGBA images as a mask tensor.

    Args:
        images: List of PIL Images in RGBA mode

    Returns:
        ComfyUI MASK tensor with shape (B, H, W)
        Values are floats in range [0, 1] where 1 = foreground
    """
    if torch is None:
        raise ImportError("PyTorch is required for tensor conversion")

    masks = []
    for img in images:
        # Ensure RGBA mode
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Extract alpha channel
        alpha = np.array(img.split()[3]).astype(np.float32) / 255.0
        masks.append(torch.from_numpy(alpha))

    return torch.stack(masks)


def apply_mask_to_image(
    images: List[Image.Image], masks: List[Image.Image]
) -> List[Image.Image]:
    """
    Apply grayscale masks to images to create RGBA images with transparency.

    Args:
        images: List of PIL Images (RGB mode)
        masks: List of PIL Images (L/grayscale mode) where white = foreground

    Returns:
        List of PIL Images in RGBA mode with transparency applied
    """
    results = []
    for img, mask in zip(images, masks):
        # Ensure correct modes
        if img.mode != "RGB":
            img = img.convert("RGB")
        if mask.mode != "L":
            mask = mask.convert("L")

        # Resize mask to match image if needed
        if mask.size != img.size:
            mask = mask.resize(img.size, Image.Resampling.LANCZOS)

        # Create RGBA image with mask as alpha
        rgba = img.copy()
        rgba.putalpha(mask)
        results.append(rgba)

    return results


def rgba_to_rgb_and_mask(
    images: List[Image.Image],
) -> Tuple[List[Image.Image], List[Image.Image]]:
    """
    Split RGBA images into RGB images and grayscale masks.

    Args:
        images: List of PIL Images in RGBA mode

    Returns:
        Tuple of (rgb_images, mask_images) where:
        - rgb_images: List of PIL Images in RGB mode
        - mask_images: List of PIL Images in L mode (grayscale)
    """
    rgb_images = []
    mask_images = []

    for img in images:
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Split into RGB and Alpha
        r, g, b, a = img.split()
        rgb_images.append(Image.merge("RGB", (r, g, b)))
        mask_images.append(a)

    return rgb_images, mask_images
