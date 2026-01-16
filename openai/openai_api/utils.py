# ABOUTME: Utility classes for OpenAI API integration
# ABOUTME: Handles image conversion between ComfyUI tensors and OpenAI formats

import numpy as np
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, List, Optional


class ImageConverter:
    """
    Handles image conversion between ComfyUI tensors and OpenAI formats.

    ComfyUI images are torch.Tensor in format [B, H, W, C] with values in [0, 1].
    OpenAI API accepts base64-encoded images or URLs.
    """

    @staticmethod
    def tensor_to_pil(tensor) -> Image.Image:
        """
        Convert ComfyUI tensor to PIL Image.

        Args:
            tensor: ComfyUI image tensor [B, H, W, C] or [H, W, C]

        Returns:
            PIL Image
        """
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        # Handle batch dimension
        if len(tensor.shape) == 4:
            tensor = tensor[0]  # Take first image in batch

        # Convert to numpy and scale to [0, 255]
        array = np.clip(255.0 * tensor.cpu().numpy(), 0, 255).astype(np.uint8)

        # Convert to PIL
        return Image.fromarray(array)

    @staticmethod
    def tensor_to_base64(tensor, format: str = "PNG") -> str:
        """
        Convert ComfyUI tensor to base64-encoded string.

        Args:
            tensor: ComfyUI image tensor [B, H, W, C] or [H, W, C]
            format: Image format (PNG, JPEG, WEBP)

        Returns:
            Base64-encoded image string
        """
        pil_image = ImageConverter.tensor_to_pil(tensor)

        # Convert to RGB if needed (for JPEG)
        if format.upper() == "JPEG" and pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")

        # Encode to bytes
        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        buffer.seek(0)

        # Encode to base64
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def tensor_to_data_url(tensor, format: str = "PNG") -> str:
        """
        Convert ComfyUI tensor to data URL for OpenAI vision API.

        Args:
            tensor: ComfyUI image tensor [B, H, W, C] or [H, W, C]
            format: Image format (PNG, JPEG, WEBP)

        Returns:
            Data URL string (data:image/png;base64,...)
        """
        b64_str = ImageConverter.tensor_to_base64(tensor, format)
        mime_type = f"image/{format.lower()}"
        return f"data:{mime_type};base64,{b64_str}"

    @staticmethod
    def tensor_to_bytes(tensor, format: str = "PNG") -> bytes:
        """
        Convert ComfyUI tensor to image bytes.

        Args:
            tensor: ComfyUI image tensor [B, H, W, C] or [H, W, C]
            format: Image format (PNG, JPEG, WEBP)

        Returns:
            Image bytes
        """
        pil_image = ImageConverter.tensor_to_pil(tensor)

        # Convert to RGB if needed (for JPEG)
        if format.upper() == "JPEG" and pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")

        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        return buffer.getvalue()

    @staticmethod
    def tensors_to_pil_list(tensors) -> List[Image.Image]:
        """
        Convert multiple ComfyUI tensors to list of PIL Images.

        Args:
            tensors: ComfyUI image tensor [B, H, W, C]

        Returns:
            List of PIL Images
        """
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        images = []
        # If single tensor without batch dimension
        if len(tensors.shape) == 3:
            images.append(ImageConverter.tensor_to_pil(tensors))
        else:
            # Process each image in batch
            for i in range(tensors.shape[0]):
                tensor = tensors[i]
                array = np.clip(255.0 * tensor.cpu().numpy(), 0, 255).astype(np.uint8)
                images.append(Image.fromarray(array))

        return images

    @staticmethod
    def tensors_to_vision_content(tensors, detail: str = "auto") -> List[Dict]:
        """
        Convert ComfyUI tensors to OpenAI vision API content format.

        Args:
            tensors: ComfyUI image tensor [B, H, W, C]
            detail: Detail level (auto, low, high)

        Returns:
            List of image content dicts for OpenAI API
        """
        images = []

        # Handle batch dimension
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        if len(tensors.shape) == 3:
            # Single image
            data_url = ImageConverter.tensor_to_data_url(tensors)
            images.append({
                "url": data_url,
                "detail": detail
            })
        else:
            # Batch of images
            for i in range(tensors.shape[0]):
                data_url = ImageConverter.tensor_to_data_url(tensors[i])
                images.append({
                    "url": data_url,
                    "detail": detail
                })

        return images

    @staticmethod
    def pil_to_tensor(pil_image: Image.Image):
        """
        Convert PIL Image to ComfyUI tensor format.

        Args:
            pil_image: PIL Image

        Returns:
            ComfyUI tensor [1, H, W, C] with values in [0, 1]
        """
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for tensor conversion")

        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array and normalize to [0, 1]
        array = np.array(pil_image).astype(np.float32) / 255.0

        # Add batch dimension and convert to tensor [1, H, W, C]
        tensor = torch.from_numpy(array).unsqueeze(0)

        return tensor

    @staticmethod
    def base64_to_tensor(b64_string: str):
        """
        Convert base64-encoded image to ComfyUI tensor format.

        Args:
            b64_string: Base64-encoded image string

        Returns:
            ComfyUI tensor [1, H, W, C] with values in [0, 1]
        """
        # Decode base64
        image_bytes = base64.b64decode(b64_string)

        # Load as PIL Image
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert to tensor
        return ImageConverter.pil_to_tensor(pil_image)

    @staticmethod
    def bytes_to_tensor(image_bytes: bytes):
        """
        Convert image bytes to ComfyUI tensor format.

        Args:
            image_bytes: Raw image bytes

        Returns:
            ComfyUI tensor [1, H, W, C] with values in [0, 1]
        """
        # Load image from bytes
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert to tensor
        return ImageConverter.pil_to_tensor(pil_image)
