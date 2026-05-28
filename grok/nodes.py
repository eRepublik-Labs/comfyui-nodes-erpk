# ABOUTME: Grok (xAI) V3 nodes for ComfyUI — config, text generation, chat, and image nodes.
# ABOUTME: Pattern mirrors openai/nodes.py: shared GrokClient instance, optional api_key resolution.

import asyncio
import io as _io
import urllib.request
from typing import List

from comfy_api.latest import IO

from .grok_api.client import GrokClient

# Known Grok text models. GrokClient does not expose a list constant, so we
# maintain it here alongside the default so the Combo reflects real options.
TEXT_MODELS = [
    "grok-4.3",
    "grok-3",
    "grok-3-mini",
    "grok-2",
]


def _make_grok_client(client_dict) -> GrokClient:
    """Reconstruct a GrokClient from a client dict or create one via auto-resolution.

    GrokAPIClient.execute passes {"api_key": ...}. When the client input is not
    connected, client_dict is None and we fall through to the standard key
    resolution chain (Settings > env > config.ini).
    """
    if client_dict is not None:
        return GrokClient(api_key=client_dict.get("api_key"))
    return GrokClient()


def _url_to_tensor(url: str):
    """Download an image URL and return a ComfyUI tensor (1, H, W, C) float32 0-1."""
    try:
        from PIL import Image as PILImage
        import numpy as np
        import torch
    except ImportError as e:
        raise ImportError(f"PIL, numpy, and torch are required for image output: {e}")

    with urllib.request.urlopen(url, timeout=60) as resp:
        data = resp.read()
    pil = PILImage.open(_io.BytesIO(data)).convert("RGB")
    arr = np.array(pil).astype("float32") / 255.0
    return torch.from_numpy(arr).unsqueeze(0)  # (1, H, W, C)


def _urls_to_tensor(urls: List[str]):
    """Convert a list of image URLs to a batched tensor (N, H, W, C)."""
    import torch
    tensors = [_url_to_tensor(u) for u in urls]
    if len(tensors) == 1:
        return tensors[0]
    return torch.cat(tensors, dim=0)


def _download_urls_sync(urls: List[str]):
    """Sync wrapper for URL-to-tensor download, safe to run inside asyncio.to_thread."""
    return _urls_to_tensor(urls)


class GrokAPIClient(IO.ComfyNode):
    """Initializes and provides a Grok (xAI) API client for downstream nodes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokAPIClient",
            display_name="Grok API Client",
            category="ERPK/Grok",
            description="Initialize an xAI Grok API client. Leave api_key empty to fall through to ComfyUI Settings, XAI_API_KEY env var, or config.ini.",
            inputs=[
                IO.String.Input(
                    "api_key",
                    optional=True,
                    default="",
                    tooltip="xAI API key. If empty, checks ComfyUI Settings, then XAI_API_KEY env var, then grok/config.ini.",
                ),
            ],
            outputs=[
                IO.Custom("GROK_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    def execute(cls, api_key: str = "", **kwargs) -> IO.NodeOutput:
        resolved_key = api_key.strip() if api_key else None
        try:
            client = GrokClient(api_key=resolved_key)
            return IO.NodeOutput({"api_key": client.api_key})
        except ValueError as e:
            raise ValueError(f"Grok API key resolution failed: {e}")


class GrokTextGeneration(IO.ComfyNode):
    """Sends a single prompt to Grok and returns the text response."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokTextGeneration",
            display_name="Grok Text Generation",
            category="ERPK/Grok",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text prompt to send to Grok.",
                ),
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Grok API client from Grok API Client node. If not connected, resolves from ComfyUI Settings or environment.",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GrokClient.DEFAULT_TEXT_MODEL,
                    optional=True,
                    tooltip="Grok model to use for generation.",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level (0.0 = focused, 2.0 = very creative).",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=16384,
                    step=128,
                    optional=True,
                    tooltip="Maximum number of tokens in the response.",
                ),
            ],
            outputs=[
                IO.String.Output("response"),
            ],
        )

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        model = kwargs.get("model") or GrokClient.DEFAULT_TEXT_MODEL
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        grok = _make_grok_client(client_dict)
        messages = [{"role": "user", "content": prompt.strip()}]

        try:
            result = await grok.generate_text(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = result.get("text", "")
            print(f"[Grok] Text generated ({len(text)} chars) via {model}")
            return IO.NodeOutput(text)
        except Exception as e:
            raise ValueError(f"Grok text generation failed: {e}")


class GrokChat(IO.ComfyNode):
    """Maintains a multi-turn Grok conversation by threading message history."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokChat",
            display_name="Grok Chat",
            category="ERPK/Grok",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Your message in the conversation.",
                ),
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Grok API client from Grok API Client node. If not connected, resolves from ComfyUI Settings or environment.",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GrokClient.DEFAULT_TEXT_MODEL,
                    optional=True,
                    tooltip="Grok model to use for chat.",
                ),
                IO.Custom("GROK_CHAT_SESSION").Input(
                    "chat_session",
                    optional=True,
                    tooltip="Previous chat session output from another Grok Chat node. Leave disconnected to start a new conversation.",
                ),
                IO.Boolean.Input(
                    "reset_conversation",
                    default=False,
                    optional=True,
                    tooltip="Discard existing history and start a new conversation.",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level.",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=16384,
                    step=128,
                    optional=True,
                    tooltip="Maximum number of tokens in the response.",
                ),
            ],
            outputs=[
                IO.String.Output("response"),
                IO.Custom("GROK_CHAT_SESSION").Output("chat_session"),
            ],
        )

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        model = kwargs.get("model") or GrokClient.DEFAULT_TEXT_MODEL
        chat_session = kwargs.get("chat_session")
        reset_conversation = kwargs.get("reset_conversation", False)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if reset_conversation or chat_session is None:
            messages = []
            print(f"[Grok] Started new conversation with {model}")
        else:
            messages = list(chat_session)
            print(f"[Grok] Continuing conversation ({len(messages)} messages)")

        messages.append({"role": "user", "content": prompt.strip()})

        grok = _make_grok_client(client_dict)
        try:
            result = await grok.generate_text(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = result.get("text", "")
            messages.append({"role": "assistant", "content": text})
            print(f"[Grok] Chat response ({len(text)} chars)")
            return IO.NodeOutput(text, messages)
        except Exception as e:
            raise ValueError(f"Grok chat failed: {e}")


class GrokImageGeneration(IO.ComfyNode):
    """Generates images from a text prompt using xAI's Grok image model."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokImageGeneration",
            display_name="Grok Image Generation",
            category="ERPK/Grok",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Description of the image to generate.",
                ),
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Grok API client from Grok API Client node. If not connected, resolves from ComfyUI Settings or environment.",
                ),
                IO.Combo.Input(
                    "model",
                    options=GrokClient.IMAGE_MODELS,
                    default=GrokClient.DEFAULT_IMAGE_MODEL,
                    optional=True,
                    tooltip="Grok image generation model.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=GrokClient.IMAGE_ASPECT_RATIOS,
                    default="1:1",
                    optional=True,
                    tooltip="Aspect ratio of the generated image.",
                ),
                IO.Combo.Input(
                    "resolution",
                    options=GrokClient.IMAGE_RESOLUTIONS,
                    default="1k",
                    optional=True,
                    tooltip="Output resolution: 1k (~1024px) or 2k (~2048px).",
                ),
                IO.Int.Input(
                    "n",
                    default=1,
                    min=1,
                    max=4,
                    optional=True,
                    tooltip="Number of images to generate.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
        )

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        model = kwargs.get("model") or GrokClient.DEFAULT_IMAGE_MODEL
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")
        resolution = kwargs.get("resolution", "1k")
        n = kwargs.get("n", 1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        grok = _make_grok_client(client_dict)
        print(f"[Grok] Generating {n} image(s) via {model} ({aspect_ratio}, {resolution})")
        print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        try:
            urls = await grok.generate_image(
                prompt.strip(),
                model=model,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n=n,
            )
            if not urls:
                raise ValueError("No image URLs returned from Grok.")
            image_tensor = await asyncio.to_thread(_download_urls_sync, urls)
            print(f"[Grok] Generated {len(urls)} image(s), shape: {image_tensor.shape}")
            return IO.NodeOutput(image_tensor)
        except Exception as e:
            raise ValueError(f"Grok image generation failed: {e}")


class GrokImageEdit(IO.ComfyNode):
    """Edits one or more input images using a text prompt via xAI's Grok image model."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokImageEdit",
            display_name="Grok Image Edit",
            category="ERPK/Grok",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip=(
                        "Source image(s) to edit. Pass a batched IMAGE tensor to send "
                        f"multiple reference images (xAI cap: {GrokClient.MAX_EDIT_IMAGES})."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Description of how to modify the image.",
                ),
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Grok API client from Grok API Client node. If not connected, resolves from ComfyUI Settings or environment.",
                ),
                IO.Combo.Input(
                    "model",
                    options=GrokClient.IMAGE_MODELS,
                    default=GrokClient.DEFAULT_IMAGE_MODEL,
                    optional=True,
                    tooltip="Grok image model for editing.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=["auto"] + GrokClient.IMAGE_ASPECT_RATIOS,
                    default="auto",
                    optional=True,
                    tooltip="Output aspect ratio. 'auto' preserves the source image ratio.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
        )

    @classmethod
    async def execute(cls, image, prompt, **kwargs) -> IO.NodeOutput:
        from .grok_api.utils import images_to_data_uris

        client_dict = kwargs.get("client")
        model = kwargs.get("model") or GrokClient.DEFAULT_IMAGE_MODEL
        aspect_ratio = kwargs.get("aspect_ratio", "auto")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        # Convert tensor(s) to data URIs — capped at MAX_EDIT_IMAGES.
        image_uris = await asyncio.to_thread(
            images_to_data_uris, image, GrokClient.MAX_EDIT_IMAGES
        )
        if not image_uris:
            raise ValueError("Could not convert input image to a data URI.")

        resolved_ratio = aspect_ratio if aspect_ratio != "auto" else None
        print(f"[Grok] Editing {len(image_uris)} image(s) via {model}")
        print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        grok = _make_grok_client(client_dict)
        try:
            urls = await grok.edit_image(
                prompt.strip(),
                image_urls=image_uris,
                model=model,
                aspect_ratio=resolved_ratio,
            )
            if not urls:
                raise ValueError("No image URLs returned from Grok.")
            image_tensor = await asyncio.to_thread(_download_urls_sync, urls)
            print(f"[Grok] Edited image shape: {image_tensor.shape}")
            return IO.NodeOutput(image_tensor)
        except Exception as e:
            raise ValueError(f"Grok image edit failed: {e}")
