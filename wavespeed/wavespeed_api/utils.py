"""
Utility functions for WaveSpeed API integration
"""

import base64
import io
import requests
import numpy
from typing import List, Optional, Union
from collections.abc import Iterable
from pydantic import BaseModel

# Import torch with proper error handling for ComfyUI
try:
    import torch
except ImportError:
    # This might happen during module discovery or outside ComfyUI
    # We'll try to import it later when actually needed
    torch = None
    import sys
    print("[WaveSpeed] Warning: torch not found during initial import. This is normal if not running in ComfyUI.", file=sys.stderr)

try:
    import PIL.Image
except ImportError:
    from PIL import Image as PIL


def imageurl2tensor(image_urls: List[str]):
    """
    Download images from URLs and convert them to ComfyUI tensors.

    Args:
        image_urls: List of image URLs

    Returns:
        torch.Tensor: Batch of images as tensors (B, H, W, C)
    """
    # Late import of torch if not already imported
    global torch
    if torch is None:
        import torch

    images = []
    if not image_urls:
        # Return a minimal valid tensor if no images
        return torch.zeros((1, 1, 1, 3))

    for url in image_urls:
        try:
            # Download image
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            image_data = response.content

            # Decode image
            with io.BytesIO(image_data) as bytes_io:
                img = PIL.Image.open(bytes_io)
                img = img.convert('RGB')
                images.append(img)
        except Exception as e:
            print(f"[WaveSpeed] Error downloading/processing image from {url}: {e}")
            continue

    if not images:
        # Return minimal tensor if all downloads failed
        return torch.zeros((1, 1, 1, 3))

    # Convert images to tensor
    return images2tensor(images)


def images2tensor(images: Union[List[PIL.Image.Image], PIL.Image.Image]):
    """
    Convert PIL images to ComfyUI tensor format.

    Args:
        images: Single PIL image or list of PIL images

    Returns:
        torch.Tensor: Images as tensor (B, H, W, C) normalized to [0, 1]
    """
    # Late import of torch if not already imported
    global torch
    if torch is None:
        import torch

    if isinstance(images, PIL.Image.Image):
        images = [images]

    if not isinstance(images, Iterable):
        raise ValueError("images must be a PIL Image or iterable of PIL Images")

    # Convert each image to tensor
    tensors = []
    for img in images:
        # Convert to numpy array
        np_img = numpy.array(img, dtype=numpy.float32)
        # Normalize to [0, 1]
        np_img = np_img / 255.0
        # Convert to tensor
        tensor = torch.from_numpy(np_img)
        tensors.append(tensor)

    # Stack into batch
    return torch.stack(tensors)


def tensor2images(tensor) -> List[PIL.Image.Image]:
    """
    Convert ComfyUI tensor to PIL images.

    Args:
        tensor: ComfyUI image tensor (B, H, W, C)

    Returns:
        List[PIL.Image.Image]: List of PIL images
    """
    # Late import of torch if not already imported
    global torch
    if torch is None:
        import torch

    # Handle both (B, H, W, C) and (H, W, C) formats
    if len(tensor.shape) == 3:
        tensor = tensor.unsqueeze(0)

    # Convert to numpy and denormalize
    np_imgs = numpy.clip(tensor.cpu().numpy() * 255.0, 0.0, 255.0).astype(numpy.uint8)

    # Convert each image to PIL
    return [PIL.Image.fromarray(np_img) for np_img in np_imgs]


def encode_image(img: PIL.Image.Image, mask: Optional[PIL.Image.Image] = None) -> bytes:
    """
    Encode PIL image to bytes.

    Args:
        img: PIL image to encode
        mask: Optional alpha mask

    Returns:
        bytes: Encoded image data
    """
    if mask is not None:
        img = img.copy()
        img.putalpha(mask)

    with io.BytesIO() as bytes_io:
        if mask is not None:
            img.save(bytes_io, format='PNG')
        else:
            img.save(bytes_io, format='JPEG', quality=95)
        data_bytes = bytes_io.getvalue()

    return data_bytes


def image_to_base64(image: Union[PIL.Image.Image, object]) -> Optional[str]:
    """
    Convert image to base64 string.

    Args:
        image: Image as tensor or PIL Image

    Returns:
        str: Base64 encoded image string
    """
    # Late import of torch if not already imported
    global torch
    if torch is None:
        try:
            import torch
        except ImportError:
            # If we can't import torch and the image is a tensor, we can't process it
            if not isinstance(image, PIL.Image.Image):
                raise ImportError("torch is required to process tensor images")

    if image is None:
        return None

    # Convert tensor to PIL if needed
    if torch and isinstance(image, torch.Tensor):
        pil_images = tensor2images(image)
        if not pil_images:
            return None
        pil_image = pil_images[0]
    elif not isinstance(image, PIL.Image.Image):
        # If torch isn't available and this isn't a PIL image, we can't process it
        raise ValueError(f"Cannot process image of type {type(image)} without torch")
    else:
        pil_image = image

    # Encode to base64
    image_bytes = encode_image(pil_image)
    return base64.b64encode(image_bytes).decode("utf-8")


def image_to_base64s(tensor) -> Optional[List[str]]:
    """
    Convert batch of images to base64 strings.

    Args:
        tensor: Batch of images as tensor

    Returns:
        List[str]: List of base64 encoded image strings
    """
    if tensor is None:
        return None

    images = tensor2images(tensor)
    return [base64.b64encode(encode_image(image)).decode("utf-8") for image in images]


class BaseRequest(BaseModel):
    """
    Base class for all WaveSpeed API request objects.

    All API request classes should inherit from this and implement:
    - build_payload(): Build the API request payload
    - get_api_path(): Return the API endpoint path
    - field_required(): Return list of required fields
    - field_order(): Return field ordering for serialization
    """

    def build_payload(self) -> dict:
        """
        Build the request payload dictionary.

        Returns:
            dict: API request payload
        """
        raise NotImplementedError("Subclasses must implement build_payload")

    def get_api_path(self) -> str:
        """
        Get the API endpoint path.

        Returns:
            str: API endpoint path (e.g., "/api/v3/bytedance/seedream-v4")
        """
        raise NotImplementedError("Subclasses must implement get_api_path")

    def field_required(self) -> List[str]:
        """
        Get list of required fields for validation.

        Returns:
            List[str]: List of required field names
        """
        return []

    def field_order(self) -> List[str]:
        """
        Get field order for serialization.

        Returns:
            List[str]: Ordered list of field names
        """
        return []

    def _remove_empty_fields(self, payload: dict) -> dict:
        """
        Remove None, empty string, and empty dict values from payload.

        Args:
            payload: Raw payload dictionary

        Returns:
            dict: Cleaned payload with empty values removed
        """
        return {
            k: v for k, v in payload.items()
            if v is not None and v != "" and v != {}
        }