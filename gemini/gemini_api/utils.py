# ABOUTME: Utility classes for Gemini API integration
# ABOUTME: Handles image conversion and safety settings configuration

import numpy as np
from PIL import Image
from typing import Dict, List
from google.genai import types


class ImageConverter:
    """
    Handles image conversion between ComfyUI tensors and PIL Images.

    ComfyUI images are torch.Tensor in format [B, H, W, C] with values in [0, 1].
    Gemini API accepts PIL Images directly.
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
    def bytes_to_tensor(image_bytes: bytes):
        """
        Convert image bytes to ComfyUI tensor format.

        Args:
            image_bytes: Raw image bytes

        Returns:
            ComfyUI tensor [1, H, W, C] with values in [0, 1]
        """
        from io import BytesIO

        # Load image from bytes
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert to tensor
        return ImageConverter.pil_to_tensor(pil_image)


class SafetySettings:
    """
    Helper class for configuring Gemini safety settings.

    Gemini has 4 harm categories with configurable thresholds.
    """

    # Harm categories (strings for new SDK)
    HARM_CATEGORIES = {
        "harassment": "HARM_CATEGORY_HARASSMENT",
        "hate_speech": "HARM_CATEGORY_HATE_SPEECH",
        "sexually_explicit": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "dangerous_content": "HARM_CATEGORY_DANGEROUS_CONTENT",
    }

    # Block thresholds (strings for new SDK)
    BLOCK_THRESHOLDS = {
        "none": "BLOCK_NONE",
        "low": "BLOCK_LOW_AND_ABOVE",
        "medium": "BLOCK_MEDIUM_AND_ABOVE",
        "high": "BLOCK_ONLY_HIGH",
    }

    @staticmethod
    def create_settings(
        harassment: str = "medium",
        hate_speech: str = "medium",
        sexually_explicit: str = "medium",
        dangerous_content: str = "medium"
    ) -> List[types.SafetySetting]:
        """
        Create safety settings configuration.

        Args:
            harassment: Threshold for harassment (none/low/medium/high)
            hate_speech: Threshold for hate speech (none/low/medium/high)
            sexually_explicit: Threshold for sexually explicit content (none/low/medium/high)
            dangerous_content: Threshold for dangerous content (none/low/medium/high)

        Returns:
            List of SafetySetting objects for Gemini API
        """
        settings = []

        # Map each category to its threshold
        category_thresholds = {
            "harassment": harassment,
            "hate_speech": hate_speech,
            "sexually_explicit": sexually_explicit,
            "dangerous_content": dangerous_content,
        }

        for category_name, threshold_name in category_thresholds.items():
            category = SafetySettings.HARM_CATEGORIES[category_name]
            threshold = SafetySettings.BLOCK_THRESHOLDS.get(
                threshold_name,
                SafetySettings.BLOCK_THRESHOLDS["medium"]
            )
            settings.append(
                types.SafetySetting(
                    category=category,
                    threshold=threshold
                )
            )

        return settings

    @staticmethod
    def get_preset(preset: str = "balanced") -> List[types.SafetySetting]:
        """
        Get preset safety settings.

        Args:
            preset: Preset name (strict/balanced/permissive)

        Returns:
            List of SafetySetting objects
        """
        presets = {
            "strict": {
                "harassment": "low",
                "hate_speech": "low",
                "sexually_explicit": "low",
                "dangerous_content": "low",
            },
            "balanced": {
                "harassment": "medium",
                "hate_speech": "medium",
                "sexually_explicit": "medium",
                "dangerous_content": "medium",
            },
            "permissive": {
                "harassment": "high",
                "hate_speech": "high",
                "sexually_explicit": "high",
                "dangerous_content": "high",
            },
        }

        config = presets.get(preset, presets["balanced"])
        return SafetySettings.create_settings(**config)
