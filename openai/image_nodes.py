# ABOUTME: ComfyUI nodes for OpenAI image generation and editing
# ABOUTME: Provides image generation with DALL-E and GPT-Image models

from .openai_api.client import OpenAIClient
from .openai_api.utils import ImageConverter


class OpenAIImageGeneration:
    """
    OpenAI Image Generation Node

    Generates images using OpenAI's image generation models.
    Can use a client from OpenAIAPIConfig or work standalone with an API key.
    """

    # Image generation models
    IMAGE_MODELS = ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini", "dall-e-3"]

    # Size options per model
    SIZES = [
        "1024x1024",
        "1024x1536",
        "1536x1024",
        "512x512",
        "256x256",
        "1792x1024",
        "1024x1792",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Description of the image to generate"
                    }
                ),
            },
            "optional": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client from OpenAI API Config node (uses API key from config)"}
                ),
                "model": (
                    cls.IMAGE_MODELS,
                    {
                        "default": "gpt-image-1.5",
                        "tooltip": "Image generation model"
                    }
                ),
                "size": (
                    cls.SIZES,
                    {
                        "default": "1024x1024",
                        "tooltip": "Image size (available sizes depend on model)"
                    }
                ),
                "quality": (
                    ["auto", "low", "medium", "high", "hd", "standard"],
                    {
                        "default": "auto",
                        "tooltip": "Image quality (gpt-image-1: low/medium/high/auto, dall-e-3: hd/standard)"
                    }
                ),
                "background": (
                    ["auto", "transparent", "opaque"],
                    {
                        "default": "auto",
                        "tooltip": "Background type (gpt-image-1 only)"
                    }
                ),
                "n": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 4,
                        "tooltip": "Number of images to generate (dall-e-3 only supports 1)"
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "OpenAI API key (only needed if not using client input)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "generate_image"
    CATEGORY = "ERPK/OpenAI"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for image generation
        return float("nan")

    def generate_image(
        self,
        prompt: str,
        client: OpenAIClient = None,
        model: str = "gpt-image-1.5",
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        n: int = 1,
        api_key: str = "",
    ):
        """
        Generate an image using OpenAI's image generation models.

        Args:
            prompt: Text description of image to generate
            client: Optional OpenAI API client from OpenAIAPIConfig
            model: Image generation model to use
            size: Image size
            quality: Image quality
            background: Background type (gpt-image-1 only)
            n: Number of images to generate
            api_key: Optional API key (fallback if no client)

        Returns:
            Tuple containing (image tensor, revised prompt)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Use provided client or create new one
            if client is not None:
                image_client = client
            else:
                # Standalone mode - use provided API key or env/config
                image_client = OpenAIClient(
                    api_key=api_key if api_key.strip() else None,
                    model=model
                )

            print(f"[OpenAI] Generating image with model: {model}")
            print(f"[OpenAI] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[OpenAI] Size: {size}, Quality: {quality}")

            # Generate image
            response = image_client.generate_image(
                prompt=prompt.strip(),
                model=model,
                size=size,
                quality=quality,
                background=background,
                n=n,
            )

            if response.get("blocked", False):
                error_msg = f"Image blocked by content filters: {response.get('error', 'Unknown reason')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            images = response.get("images", [])
            if not images:
                raise ValueError("No image was generated")

            # Convert first image from base64 to tensor
            image_tensor = ImageConverter.base64_to_tensor(images[0])
            print(f"[OpenAI] Image generated successfully: {image_tensor.shape}")

            # Get revised prompt if available
            revised_prompt = response.get("revised_prompt", "")
            if revised_prompt:
                print(f"[OpenAI] Revised prompt: {revised_prompt[:100]}...")

            return (image_tensor, revised_prompt)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIImageEdit:
    """
    OpenAI Image Editing Node

    Uses OpenAI's image editing API to modify existing images based on text prompts.
    Supports optional mask for inpainting.
    """

    # Image editing models (gpt-image-1.5 is recommended)
    IMAGE_MODELS = ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]

    # Size options
    SIZES = [
        "1024x1024",
        "1024x1536",
        "1536x1024",
        "512x512",
        "256x256",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    "IMAGE",
                    {"tooltip": "Input image to edit"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Description of how to modify the image"
                    }
                ),
            },
            "optional": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client from OpenAI API Config node"}
                ),
                "mask": (
                    "MASK",
                    {"tooltip": "Optional mask indicating areas to edit (white = edit, black = keep)"}
                ),
                "model": (
                    cls.IMAGE_MODELS,
                    {
                        "default": "gpt-image-1",
                        "tooltip": "Image editing model"
                    }
                ),
                "size": (
                    cls.SIZES,
                    {
                        "default": "1024x1024",
                        "tooltip": "Output image size"
                    }
                ),
                "quality": (
                    ["auto", "low", "medium", "high"],
                    {
                        "default": "auto",
                        "tooltip": "Image quality (gpt-image-1 only)"
                    }
                ),
                "n": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 4,
                        "tooltip": "Number of images to generate"
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "OpenAI API key (only needed if not using client input)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "edit_image"
    CATEGORY = "ERPK/OpenAI"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for image editing
        return float("nan")

    def edit_image(
        self,
        image,
        prompt: str,
        client: OpenAIClient = None,
        mask=None,
        model: str = "gpt-image-1.5",
        size: str = "1024x1024",
        quality: str = "auto",
        n: int = 1,
        api_key: str = "",
    ):
        """
        Edit an image using OpenAI's image editing API.

        Args:
            image: Input image as ComfyUI tensor
            prompt: Text description of how to modify the image
            client: Optional OpenAI API client
            mask: Optional mask tensor (white areas will be edited)
            model: Image editing model to use
            size: Output image size
            quality: Image quality (gpt-image-1 only)
            n: Number of images to generate
            api_key: Optional API key (fallback if no client)

        Returns:
            Tuple containing edited image tensor
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Use provided client or create new one
            if client is not None:
                image_client = client
            else:
                image_client = OpenAIClient(
                    api_key=api_key if api_key.strip() else None,
                    model=model
                )

            print(f"[OpenAI] Editing image with model: {model}")
            print(f"[OpenAI] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

            # Convert image tensor to PNG bytes
            image_bytes = ImageConverter.tensor_to_bytes(image, format="PNG")

            # Convert mask if provided
            mask_bytes = None
            if mask is not None:
                # Mask should be a grayscale image where white = edit area
                # Convert to RGBA with transparency in edit areas
                import numpy as np
                from PIL import Image
                from io import BytesIO

                try:
                    import torch
                except ImportError:
                    raise ImportError("torch is required for mask processing")

                # Handle mask tensor
                if len(mask.shape) == 4:
                    mask_tensor = mask[0]
                elif len(mask.shape) == 3:
                    mask_tensor = mask
                else:
                    mask_tensor = mask

                # Convert to numpy
                if len(mask_tensor.shape) == 3:
                    mask_array = mask_tensor.cpu().numpy()[:, :, 0]
                else:
                    mask_array = mask_tensor.cpu().numpy()

                # Normalize to 0-255
                mask_array = np.clip(mask_array * 255, 0, 255).astype(np.uint8)

                # Create RGBA image with transparency where mask is white
                # OpenAI expects transparent areas to be edited
                pil_image = ImageConverter.tensor_to_pil(image)
                if pil_image.mode != 'RGBA':
                    pil_image = pil_image.convert('RGBA')

                # Apply mask as alpha channel (invert: white in mask = transparent = edit)
                alpha = 255 - mask_array
                pil_image.putalpha(Image.fromarray(alpha))

                buffer = BytesIO()
                pil_image.save(buffer, format="PNG")
                mask_bytes = buffer.getvalue()

                print(f"[OpenAI] Using mask for inpainting")

            # Edit image
            response = image_client.edit_image(
                image_data=image_bytes,
                prompt=prompt.strip(),
                mask_data=mask_bytes,
                model=model,
                size=size,
                quality=quality,
                n=n,
            )

            if response.get("blocked", False):
                error_msg = f"Image blocked by content filters: {response.get('error', 'Unknown reason')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            images = response.get("images", [])
            if not images:
                raise ValueError("No image was generated")

            # Convert first image from base64 to tensor
            image_tensor = ImageConverter.base64_to_tensor(images[0])
            print(f"[OpenAI] Image edited successfully: {image_tensor.shape}")

            return (image_tensor,)

        except Exception as e:
            error_msg = f"Failed to edit image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


# Node registration
NODE_CLASS_MAPPINGS = {
    "OpenAIImageGeneration": OpenAIImageGeneration,
    "OpenAIImageEdit": OpenAIImageEdit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenAIImageGeneration": "OpenAI Image Generation",
    "OpenAIImageEdit": "OpenAI Image Edit",
}
