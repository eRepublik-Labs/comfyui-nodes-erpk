"""
Utility functions for WaveSpeed API integration
"""

import base64
import io
import requests
from typing import List, Optional, Union
from collections.abc import Iterable
from pydantic import BaseModel


def imageurl2tensor(image_urls: List[str]):
    """
    Download images from URLs and convert them to ComfyUI tensors.

    Args:
        image_urls: List of image URLs

    Returns:
        torch.Tensor: Batch of images as tensors (B, H, W, C)
    """
    import torch
    import PIL.Image

    images = []
    if not image_urls:
        return torch.zeros((1, 1, 1, 3))

    for url in image_urls:
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            image_data = response.content

            with io.BytesIO(image_data) as bytes_io:
                img = PIL.Image.open(bytes_io)
                img = img.convert('RGB')
                images.append(img)
        except Exception as e:
            print(f"[WaveSpeed] Error downloading/processing image from {url}: {e}")
            continue

    if not images:
        return torch.zeros((1, 1, 1, 3))

    return images2tensor(images)


def images2tensor(images):
    """
    Convert PIL images to ComfyUI tensor format.

    Args:
        images: Single PIL image or list of PIL images

    Returns:
        torch.Tensor: Images as tensor (B, H, W, C) normalized to [0, 1]
    """
    import numpy
    import torch
    import PIL.Image

    if isinstance(images, PIL.Image.Image):
        images = [images]

    if not isinstance(images, Iterable):
        raise ValueError("images must be a PIL Image or iterable of PIL Images")

    tensors = []
    for img in images:
        np_img = numpy.array(img, dtype=numpy.float32)
        np_img = np_img / 255.0
        tensor = torch.from_numpy(np_img)
        tensors.append(tensor)

    return torch.stack(tensors)


def tensor2images(tensor):
    """
    Convert ComfyUI tensor to PIL images.

    Args:
        tensor: ComfyUI image tensor (B, H, W, C)

    Returns:
        list: List of PIL images
    """
    import numpy
    import PIL.Image

    # Handle both (B, H, W, C) and (H, W, C) formats
    if len(tensor.shape) == 3:
        tensor = tensor.unsqueeze(0)

    np_imgs = numpy.clip(tensor.cpu().numpy() * 255.0, 0.0, 255.0).astype(numpy.uint8)

    return [PIL.Image.fromarray(np_img) for np_img in np_imgs]


def encode_image(img, mask=None) -> bytes:
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


def image_to_base64(image) -> Optional[str]:
    """
    Convert image to base64 string.

    Args:
        image: Image as tensor or PIL Image

    Returns:
        str: Base64 encoded image string
    """
    import torch
    import PIL.Image

    if image is None:
        return None

    if isinstance(image, torch.Tensor):
        pil_images = tensor2images(image)
        if not pil_images:
            return None
        pil_image = pil_images[0]
    elif not isinstance(image, PIL.Image.Image):
        raise ValueError(f"Cannot process image of type {type(image)}")
    else:
        pil_image = image

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