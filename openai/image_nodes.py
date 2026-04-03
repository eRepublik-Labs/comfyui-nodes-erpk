# ABOUTME: ComfyUI V3 nodes for OpenAI image generation and editing
# ABOUTME: Provides image generation with DALL-E and GPT-Image models

from comfy_api.latest import IO
from .openai_api.client import OpenAIClient

IMAGE_MODELS = list(OpenAIClient.IMAGE_MODELS.keys())
EDIT_MODELS = ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]

GEN_SIZES = [
    "1024x1024", "1024x1536", "1536x1024",
    "512x512", "256x256", "1792x1024", "1024x1792",
]

EDIT_SIZES = [
    "1024x1024", "1024x1536", "1536x1024",
    "512x512", "256x256",
]


class OpenAIImageGeneration(IO.ComfyNode):
    """Generates images using OpenAI's image generation models."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIImageGeneration",
            display_name="OpenAI Image Generation",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Description of the image to generate",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node (uses API key from config)",
                ),
                IO.Combo.Input(
                    "model",
                    options=IMAGE_MODELS,
                    default="gpt-image-1.5",
                    optional=True,
                    tooltip="Image generation model",
                ),
                IO.Combo.Input(
                    "size",
                    options=GEN_SIZES,
                    default="1024x1024",
                    optional=True,
                    tooltip="Image size (available sizes depend on model)",
                ),
                IO.Combo.Input(
                    "quality",
                    options=["auto", "low", "medium", "high", "hd", "standard"],
                    default="auto",
                    optional=True,
                    tooltip="Image quality (gpt-image-1: low/medium/high/auto, dall-e-3: hd/standard)",
                ),
                IO.Combo.Input(
                    "background",
                    options=["auto", "transparent", "opaque"],
                    default="auto",
                    optional=True,
                    tooltip="Background type (gpt-image-1 only)",
                ),
                IO.Int.Input(
                    "n",
                    default=1,
                    min=1,
                    max=4,
                    optional=True,
                    tooltip="Number of images to generate (dall-e-3 only supports 1)",
                ),
                IO.String.Input(
                    "api_key",
                    default="",
                    optional=True,
                    tooltip="OpenAI API key (only needed if not using client input)",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.String.Output("revised_prompt"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        model = kwargs.get("model", "gpt-image-1.5")
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "auto")
        background = kwargs.get("background", "auto")
        n = kwargs.get("n", 1)
        api_key = kwargs.get("api_key", "")

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

            return IO.NodeOutput(image_tensor, revised_prompt)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIImageEdit(IO.ComfyNode):
    """Uses OpenAI's image editing API to modify existing images based on text prompts."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIImageEdit",
            display_name="OpenAI Image Edit",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip="Input image to edit",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Description of how to modify the image",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node",
                ),
                IO.Mask.Input(
                    "mask",
                    optional=True,
                    tooltip="Optional mask indicating areas to edit (white = edit, black = keep)",
                ),
                IO.Combo.Input(
                    "model",
                    options=EDIT_MODELS,
                    default="gpt-image-1",
                    optional=True,
                    tooltip="Image editing model",
                ),
                IO.Combo.Input(
                    "size",
                    options=EDIT_SIZES,
                    default="1024x1024",
                    optional=True,
                    tooltip="Output image size",
                ),
                IO.Combo.Input(
                    "quality",
                    options=["auto", "low", "medium", "high"],
                    default="auto",
                    optional=True,
                    tooltip="Image quality (gpt-image-1 only)",
                ),
                IO.Int.Input(
                    "n",
                    default=1,
                    min=1,
                    max=4,
                    optional=True,
                    tooltip="Number of images to generate",
                ),
                IO.String.Input(
                    "api_key",
                    default="",
                    optional=True,
                    tooltip="OpenAI API key (only needed if not using client input)",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    def execute(cls, image, prompt, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        mask = kwargs.get("mask")
        model = kwargs.get("model", "gpt-image-1.5")
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "auto")
        n = kwargs.get("n", 1)
        api_key = kwargs.get("api_key", "")

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

            return IO.NodeOutput(image_tensor)

        except Exception as e:
            error_msg = f"Failed to edit image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)
