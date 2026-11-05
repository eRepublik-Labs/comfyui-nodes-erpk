# ABOUTME: ComfyUI V3 nodes for OpenAI image generation and editing
# ABOUTME: Provides image generation and editing with GPT Image models

import asyncio
from io import BytesIO

from comfy_api.latest import IO
from .openai_api.client import OpenAIClient
from ..utils.image_grid import (
    NO_GRID_IMAGE, grid_input, load_grid_images, model_grid_cap, register_grid_caps, validate_grid,
)

# Every GPT Image model takes images.generate, images.edit and the Responses
# image_generation tool, so the three nodes offer the same list.
IMAGE_MODELS = list(OpenAIClient.IMAGE_MODELS)
EDIT_MODELS = IMAGE_MODELS

# A saved workflow keeps its stored model; these reach only new nodes and
# prompts that omit the input.
GENERATION_DEFAULT_MODEL = "gpt-image-2.6-flare"
EDIT_DEFAULT_MODEL = "gpt-image-2.6-sunburst"

# One limit for every GPT Image model, "For GPT image models, you can provide up to 16 images":
# https://developers.openai.com/api/reference/resources/images/methods/edit
EDIT_GRID_CAPS = {"*": 16}
register_grid_caps("OpenAIImageEdit", EDIT_GRID_CAPS, model_widget="model")

# Mainline (text/reasoning) models for the Responses API call. Each returned
# 200 on responses.create with the image_generation tool attached (measured
# 2026-10-01, gpt-6.1-terra 2026-11-03; both gpt-image-2.6 tiers as the tool
# model 2026-11-05). The first entry is the node default.
RESPONSES_MAINLINE_MODELS = [
    "gpt-6.1-sol",
    "gpt-6.1-terra",
    "gpt-6-astra",
    "gpt-6-sol",
    "gpt-6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
]

RESPONSES_IMAGE_MODELS = IMAGE_MODELS

# max is Responses-only: 200 on all 8 mainlines here, 400 on chat.completions
# (measured 2026-10-14, gpt-6.1-terra 2026-11-03), so the text nodes stop at
# xhigh.
REASONING_EFFORT_LEVELS = ["default", "none", "minimal", "low", "medium", "high", "xhigh", "max"]

# Size presets shared by the generation and edit nodes, mirroring the official
# ComfyUI GPT Image node. "Custom" reads custom_width / custom_height.
SIZE_PRESETS = [
    "auto", "1024x1024", "1024x1536", "1536x1024",
    "2048x2048", "2048x1152", "1152x2048", "3840x2160", "2160x3840",
    "Custom",
]
CUSTOM_SIZE = "Custom"

COMPLEXITY_LEVELS = ["auto", "low", "medium", "high"]


def complexity_input():
    """The complexity Combo shared by the generation and edit nodes."""
    return IO.Combo.Input(
        "complexity",
        options=COMPLEXITY_LEVELS,
        default="auto",
        optional=True,
        tooltip=(
            "How much detail GPT Image 2.6 puts into the image: low, medium or high. "
            "'auto' sends nothing, which OpenAI documents as high. Other models reject "
            "the parameter, so there it is left out."
        ),
    )


def resolve_size(size, custom_width, custom_height):
    """Turn the size Combo plus the two custom Ints into the API size string."""
    if size == CUSTOM_SIZE:
        return f"{custom_width}x{custom_height}"
    return size


def size_inputs(model_hint):
    """The size Combo and its custom dimension Ints, in widget order."""
    return [
        IO.Combo.Input(
            "size",
            options=SIZE_PRESETS,
            default="1024x1024",
            optional=True,
            tooltip=(
                "Output image size. Select Custom to use custom_width and custom_height. "
                + model_hint
                + " Resolutions above 2560x1440 are experimental."
            ),
        ),
        IO.Int.Input(
            "custom_width",
            default=1024,
            min=256,
            max=3840,
            step=16,
            optional=True,
            tooltip="Width in pixels when size is Custom. Must be a multiple of 16.",
        ),
        IO.Int.Input(
            "custom_height",
            default=1024,
            min=256,
            max=3840,
            step=16,
            optional=True,
            tooltip="Height in pixels when size is Custom. Must be a multiple of 16.",
        ),
    ]

GEN_SIZES = [
    "auto",
    "1024x1024", "1024x1536", "1536x1024",
    "1792x1024", "1024x1792",
    # OpenAI marks resolutions above 2560x1440 as experimental
    "2048x2048", "2048x1152", "2560x1440", "3840x2160", "2160x3840",
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
                    default=GENERATION_DEFAULT_MODEL,
                    optional=True,
                    tooltip=(
                        "Image generation model. "
                        "gpt-image-2.6-sunburst / -flare: newest, add complexity control. "
                        "gpt-image-2.6 and 2.5 add xhigh/max quality and transparent background. "
                        "gpt-image-2: 4K output, multilingual text; no transparent background (the API rejects it)."
                    ),
                ),
                *size_inputs(
                    "gpt-image-2, 2.5 and 2.6 accept any size with both edges divisible by 16, "
                    "aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels and max edge 3840."
                ),
                IO.Combo.Input(
                    "quality",
                    options=["auto", "low", "medium", "high", "xhigh", "max"],
                    default="auto",
                    optional=True,
                    tooltip="Image quality. auto/low/medium/high on every model; xhigh/max only on GPT Image 2.6 and 2.5 (clamped to high on gpt-image-2).",
                ),
                IO.Combo.Input(
                    "background",
                    options=["auto", "transparent", "opaque"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Background type for the generated output (GPT Image models only). "
                        "'transparent' works on GPT Image 2.6 and 2.5 only (gpt-image-2 rejects it) and "
                        "needs png or webp output."
                    ),
                ),
                IO.Combo.Input(
                    "moderation",
                    options=["auto", "low"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Content moderation level (GPT Image models only). "
                        "'auto' uses OpenAI's default safety filters; 'low' asks for "
                        "less restrictive filtering. How much 'low' actually relaxes varies "
                        "by model and is not guaranteed; gpt-image-2 was observed to ignore it. "
                        "Neither level permits graphic or violent content."
                    ),
                ),
                IO.Int.Input(
                    "n",
                    default=1,
                    min=1,
                    max=10,
                    optional=True,
                    tooltip=(
                        "Number of images to generate per call (OpenAI supports 1-10)."
                    ),
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
                IO.Combo.Input(
                    "output_format",
                    options=["png", "jpeg", "webp", "gif"],
                    default="png",
                    optional=True,
                    tooltip=(
                        "Output file format. 'transparent' background needs png or webp. "
                        "'gif' (GPT Image 2.6 only) returns an animation, and the image output "
                        "holds every frame as a batch."
                    ),
                ),
                IO.Int.Input(
                    "output_compression",
                    default=100,
                    min=0,
                    max=100,
                    optional=True,
                    tooltip="Compression level 0-100 (100 = least compression). Applied only to jpeg and webp.",
                ),
                complexity_input(),
                IO.Int.Input(
                    "frame_count",
                    default=9,
                    min=2,
                    max=64,
                    optional=True,
                    tooltip=(
                        "Frames per GIF animation; used only when output_format is gif. The API tiles "
                        "the frames onto one sheet whose longest edge must stay within 3840 px, so "
                        "many frames need a smaller size or size auto."
                    ),
                ),
                IO.Int.Input(
                    "frame_duration_ms",
                    default=200,
                    min=20,
                    max=2000,
                    step=10,
                    optional=True,
                    tooltip="How long each GIF frame shows, in milliseconds; used only when output_format is gif.",
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
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        model = kwargs.get("model", GENERATION_DEFAULT_MODEL)
        size = resolve_size(
            kwargs.get("size", "1024x1024"),
            kwargs.get("custom_width", 1024),
            kwargs.get("custom_height", 1024),
        )
        quality = kwargs.get("quality", "auto")
        background = kwargs.get("background", "auto")
        moderation = kwargs.get("moderation", "auto")
        n = kwargs.get("n", 1)
        output_format = kwargs.get("output_format", "png")
        output_compression = kwargs.get("output_compression", 100)
        complexity = kwargs.get("complexity", "auto")
        frame_count = kwargs.get("frame_count", 9)
        frame_duration_ms = kwargs.get("frame_duration_ms", 200)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Use provided client or create new one
            if client is not None:
                image_client = client
            else:
                image_client = OpenAIClient(
                    api_key=None,
                    model=model
                )

            print(f"[OpenAI] Generating image with model: {model}")
            print(f"[OpenAI] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[OpenAI] Size: {size}, Quality: {quality}")

            # Generate image
            response = await image_client.generate_image(
                prompt=prompt.strip(),
                model=model,
                size=size,
                quality=quality,
                background=background,
                moderation=moderation,
                n=n,
                output_format=output_format,
                output_compression=output_compression,
                complexity=complexity,
                frame_count=frame_count,
                frame_duration_ms=frame_duration_ms,
            )

            if response.get("blocked", False):
                error_msg = f"Image blocked by content filters: {response.get('error', 'Unknown reason')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            images = response.get("images", [])
            if not images:
                raise ValueError("No image was generated")

            # Convert ALL returned images to a single batched tensor [N,H,W,C],
            # each GIF contributing every frame. Previously only images[0] was
            # kept, silently dropping N-1 images the user was billed for.
            tensors = [ImageConverter.base64_frames_to_tensor(img) for img in images]
            if len(tensors) == 1:
                image_tensor = tensors[0]
            else:
                import torch
                image_tensor = torch.cat(tensors, dim=0)
            print(f"[OpenAI] Generated {len(tensors)} image(s), batch shape: {image_tensor.shape}")

            # Get revised prompt if available
            revised_prompt = response.get("revised_prompt", "")
            if revised_prompt:
                print(f"[OpenAI] Revised prompt: {revised_prompt[:100]}...")

            return IO.NodeOutput(image_tensor, revised_prompt)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIImageResponses(IO.ComfyNode):
    """Generate images via OpenAI's Responses API with the image_generation
    hosted tool. Offers reasoning effort, web search integration, and
    mainline-model prompt revision — features not available on the direct
    /v1/images/generations endpoint.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIImageResponses",
            display_name="OpenAI Image Generation (Responses)",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Image description. The mainline model may auto-revise it before passing to the image model.",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node",
                ),
                IO.Combo.Input(
                    "mainline_model",
                    options=RESPONSES_MAINLINE_MODELS,
                    default=RESPONSES_MAINLINE_MODELS[0],
                    optional=True,
                    tooltip=(
                        "Text/reasoning model that drives the Responses API call. "
                        "Not the image model — this picks prompt interpretation, "
                        "reasoning, and (optionally) web search. gpt-6.1-sol is the "
                        "default; gpt-6.1-terra is the fast, efficient 6.1 tier at "
                        "half Sol's price; gpt-6-astra is the top tier; gpt-6-luna and "
                        "gpt-5.6-luna are the cheapest."
                    ),
                ),
                IO.Combo.Input(
                    "image_model",
                    options=RESPONSES_IMAGE_MODELS,
                    default=GENERATION_DEFAULT_MODEL,
                    optional=True,
                    tooltip="Underlying GPT Image model used for pixel generation inside the tool.",
                ),
                IO.Combo.Input(
                    "reasoning_effort",
                    options=REASONING_EFFORT_LEVELS,
                    default="default",
                    optional=True,
                    tooltip=(
                        "Mainline-model reasoning depth. 'default' sends nothing, so the model uses "
                        "its own default (medium). 'none' turns reasoning off on gpt-6.1-terra, "
                        "gpt-6-sol, gpt-6-luna and the gpt-5.6 tiers; gpt-6.1-sol and gpt-6-astra reject it, so "
                        "there 'none' acts like 'default'. "
                        "'low' to 'max' increase prompt-interpretation quality "
                        "at token cost. 'minimal' is rejected alongside the image tool and is sent "
                        "as 'low'. "
                        "Note: when enabled, reasoning_summary output contains the model's raw "
                        "chain-of-thought, which often includes orchestration-level thinking "
                        "(output channels, response format) rather than only creative rationale."
                    ),
                ),
                IO.Combo.Input(
                    "verbosity",
                    options=["default", "low", "medium", "high"],
                    default="default",
                    optional=True,
                    tooltip=(
                        "Mainline-model output verbosity. Shapes how chatty "
                        "the response is independent of max_tokens. 'default' lets the model "
                        "pick. Silently dropped for older mainlines."
                    ),
                ),
                IO.Combo.Input(
                    "size",
                    options=GEN_SIZES,
                    default="1024x1024",
                    optional=True,
                    tooltip="Image size. 'auto' lets the model choose. Same constraints as direct endpoint (gpt-image-2: min 655,360 pixels). 3840x2160 / 2160x3840 are experimental per OpenAI.",
                ),
                IO.Combo.Input(
                    "quality",
                    options=["auto", "low", "medium", "high", "xhigh", "max"],
                    default="auto",
                    optional=True,
                    tooltip="Image quality tier. xhigh/max only on GPT Image 2.6 and 2.5 (clamped to high on gpt-image-2).",
                ),
                IO.Combo.Input(
                    "background",
                    options=["auto", "transparent", "opaque"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Background type. 'transparent' works on GPT Image 2.6 and 2.5 only (gpt-image-2 "
                        "rejects it) and needs png or webp output."
                    ),
                ),
                IO.Combo.Input(
                    "output_format",
                    options=["png", "jpeg", "webp"],
                    default="png",
                    optional=True,
                    tooltip="Output image format. 'transparent' background needs png or webp.",
                ),
                IO.Combo.Input(
                    "moderation",
                    options=["auto", "low"],
                    default="auto",
                    optional=True,
                    tooltip="Content moderation level. 'low' asks for less restrictive filtering; how much it relaxes varies by model and is not guaranteed.",
                ),
                IO.Boolean.Input(
                    "enable_web_search",
                    default=False,
                    optional=True,
                    tooltip=(
                        "Add the web_search tool alongside image_generation. The mainline "
                        "model can decide to look up reference material before generating. "
                        "Adds $10/1000 calls when the model actually invokes it."
                    ),
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Cache-bust seed. Randomizes by default.",
                ),
                IO.Combo.Input(
                    "reasoning_mode",
                    options=["standard", "pro"],
                    default="standard",
                    optional=True,
                    tooltip=(
                        "Mainline-model reasoning mode. 'pro' spends more compute on the "
                        "prompt revision and adds about 2,000 to 4,000 input tokens per call, even "
                        "for a short prompt. Responses API only."
                    ),
                ),
                IO.Int.Input(
                    "output_compression",
                    default=100,
                    min=0,
                    max=100,
                    optional=True,
                    tooltip="Compression level 0-100 (100 = least compression). Applied only to jpeg and webp.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.String.Output("revised_prompt"),
                IO.String.Output("reasoning_summary"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        mainline_model = kwargs.get("mainline_model", RESPONSES_MAINLINE_MODELS[0])
        image_model = kwargs.get("image_model", GENERATION_DEFAULT_MODEL)
        reasoning_effort = kwargs.get("reasoning_effort", "default")
        verbosity = kwargs.get("verbosity", "default")
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "auto")
        background = kwargs.get("background", "auto")
        output_format = kwargs.get("output_format", "png")
        moderation = kwargs.get("moderation", "auto")
        enable_web_search = kwargs.get("enable_web_search", False)
        reasoning_mode = kwargs.get("reasoning_mode", "standard")
        output_compression = kwargs.get("output_compression", 100)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            if client is not None:
                image_client = client
            else:
                image_client = OpenAIClient(
                    api_key=None,
                    model=mainline_model,
                )

            print(f"[OpenAI Responses] mainline={mainline_model} image={image_model} reasoning={reasoning_effort}")
            print(f"[OpenAI Responses] prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

            response = await image_client.generate_image_via_responses(
                prompt=prompt.strip(),
                mainline_model=mainline_model,
                image_model=image_model,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                size=size,
                quality=quality,
                background=background,
                output_format=output_format,
                moderation=moderation,
                enable_web_search=enable_web_search,
                reasoning_mode=reasoning_mode,
                output_compression=output_compression,
            )

            if response.get("blocked", False):
                raise ValueError(f"Image blocked by content filters: {response.get('error', 'Unknown')}")

            images = response.get("images", [])
            if not images:
                raise ValueError("No image was generated")

            # Stack all returned images into a batched tensor (same pattern as
            # OpenAIImageGeneration — a single Responses call can emit multiple
            # image_generation_call items if the mainline model decides to).
            tensors = [ImageConverter.base64_to_tensor(img) for img in images]
            if len(tensors) == 1:
                image_tensor = tensors[0]
            else:
                import torch
                image_tensor = torch.cat(tensors, dim=0)
            print(f"[OpenAI Responses] Generated {len(tensors)} image(s), batch shape: {image_tensor.shape}")

            revised_prompt = response.get("revised_prompt", "")
            reasoning_summary = response.get("reasoning_summary", "")
            if revised_prompt:
                print(f"[OpenAI Responses] Revised prompt: {revised_prompt[:100]}...")
            if reasoning_summary:
                print(f"[OpenAI Responses] Reasoning summary ({len(reasoning_summary)} chars)")

            return IO.NodeOutput(image_tensor, revised_prompt, reasoning_summary)

        except Exception as e:
            error_msg = f"Failed to generate image via Responses API: {str(e)}"
            print(f"[OpenAI Responses] Error: {error_msg}")
            raise ValueError(error_msg)


def _grid_pngs(raw, model):
    """The grid's files as PNG bytes at their own size, in grid order.

    Re-encoded rather than sent as stored: the client labels every image image/png.
    """
    pictures = load_grid_images(raw, model_grid_cap("OpenAIImageEdit", model))
    if not pictures:
        raise ValueError(NO_GRID_IMAGE)
    pngs = []
    for picture in pictures:
        buffer = BytesIO()
        picture.save(buffer, format="PNG")
        pngs.append(buffer.getvalue())
    return pngs


def _markup_png(markup, markup_mask, first_size):
    """The markup layer as an RGBA PNG the size of image 1: marks opaque, the rest transparent.

    The colour comes from `markup`. The alpha comes from `markup_mask` read the way
    Load Image writes it (1 where the PNG was transparent), or, with no mask, is
    opaque wherever the markup pixel is not pure black.
    """
    import numpy as np
    from PIL import Image

    rgb = np.clip(markup[0, :, :, :3].cpu().numpy() * 255, 0, 255).astype(np.uint8)
    height, width = rgb.shape[:2]
    if (width, height) != first_size:
        raise ValueError(
            f"markup is {width}x{height} but image 1 is {first_size[0]}x{first_size[1]}; "
            f"draw the marks on a layer the size of image 1")
    if markup_mask is None:
        alpha = np.where(rgb.any(axis=2), 255, 0).astype(np.uint8)
    else:
        mask = markup_mask[0] if markup_mask.dim() == 3 else markup_mask
        mask_height, mask_width = mask.shape
        if (mask_width, mask_height) != (width, height):
            raise ValueError(
                f"markup_mask is {mask_width}x{mask_height} but markup is {width}x{height}; "
                f"connect the MASK of the Load Image that loads the markup")
        alpha = 255 - np.clip(mask.cpu().numpy() * 255, 0, 255).astype(np.uint8)
    buffer = BytesIO()
    Image.fromarray(np.dstack([rgb, alpha]), "RGBA").save(buffer, format="PNG")
    return buffer.getvalue()


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
                    optional=True,
                    tooltip=(
                        "Input image(s) to edit. A single image is the default. "
                        "If you pass a batched IMAGE (e.g. from an Image Batch / "
                        "Rebatch node), all N images are sent as reference images "
                        "— gpt-image-2 uses this for character/scene continuity "
                        "(up to 16 images). Mask (if provided) applies to the first. "
                        "When connected, the grid on the node is ignored."
                    ),
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
                IO.Image.Input(
                    "markup",
                    optional=True,
                    tooltip=(
                        "Optional markup layer: arrows, circles or text drawn on a transparent "
                        "layer the size of image 1, telling the model where and what to edit. "
                        "Load the PNG with Load Image and connect its IMAGE here and its MASK to "
                        "markup_mask. Cannot be combined with mask."
                    ),
                ),
                IO.Mask.Input(
                    "markup_mask",
                    optional=True,
                    tooltip=(
                        "The MASK output of the Load Image that loads the markup (white where the "
                        "layer is transparent). Without it, every pixel of markup that is not pure "
                        "black counts as a mark."
                    ),
                ),
                IO.Combo.Input(
                    "model",
                    options=EDIT_MODELS,
                    default=EDIT_DEFAULT_MODEL,
                    optional=True,
                    tooltip=(
                        "Image editing model. gpt-image-2.6-sunburst / -flare add complexity control; "
                        "gpt-image-2.6 and 2.5 add xhigh/max quality; "
                        "gpt-image-2 offers multilingual text and character continuity across edits."
                    ),
                ),
                *size_inputs(
                    "gpt-image-2, 2.5 and 2.6 accept any size with both edges divisible by 16, "
                    "aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels and max edge 3840."
                ),
                IO.Combo.Input(
                    "quality",
                    options=["auto", "low", "medium", "high", "xhigh", "max"],
                    default="auto",
                    optional=True,
                    tooltip="Image quality for GPT Image models; xhigh/max only on GPT Image 2.6 and 2.5 (clamped to high elsewhere).",
                ),
                IO.Combo.Input(
                    "moderation",
                    options=["auto", "low"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Content moderation level. 'auto' uses OpenAI's default "
                        "safety filters; 'low' relaxes them for permissive content."
                    ),
                ),
                IO.Int.Input(
                    "n",
                    default=1,
                    min=1,
                    max=10,
                    optional=True,
                    tooltip=(
                        "Number of edited image variants to return per call "
                        "(OpenAI supports 1-10 for all GPT Image models)."
                    ),
                ),
                IO.Combo.Input(
                    "background",
                    options=["auto", "transparent", "opaque"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Background type for the edited output (GPT Image models only). "
                        "'transparent' works on GPT Image 2.6 and 2.5 only (gpt-image-2 rejects it) and "
                        "needs png or webp output."
                    ),
                ),
                IO.Combo.Input(
                    "input_fidelity",
                    options=["auto", "high", "low"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Fidelity to the original input image(s). 'high' preserves details "
                        "more aggressively; 'low' gives the model more creative freedom. "
                        "Ignored by gpt-image-2, 2.5 and 2.6 (always high fidelity)."
                    ),
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
                IO.Combo.Input(
                    "output_format",
                    options=["png", "jpeg", "webp"],
                    default="png",
                    optional=True,
                    tooltip="Output file format. 'transparent' background needs png or webp.",
                ),
                IO.Int.Input(
                    "output_compression",
                    default=100,
                    min=0,
                    max=100,
                    optional=True,
                    tooltip="Compression level 0-100 (100 = least compression). Applied only to jpeg and webp.",
                ),
                grid_input(),
                # After grid_images, not before it: a save from before complexity
                # holds the grid list then the grid's DOM widget slot, so only that
                # slot's "" shifts here, and web/openai_dynamic_sizes.js resets it.
                complexity_input(),
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
    def validate_inputs(cls, grid_images="[]"):
        # Only `grid_images` is named: ComfyUI skips its own type and range checks for
        # every input named here.
        return validate_grid(grid_images)

    @classmethod
    async def execute(cls, prompt, image=None, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        mask = kwargs.get("mask")
        markup = kwargs.get("markup")
        markup_mask = kwargs.get("markup_mask")
        model = kwargs.get("model", EDIT_DEFAULT_MODEL)
        size = resolve_size(
            kwargs.get("size", "1024x1024"),
            kwargs.get("custom_width", 1024),
            kwargs.get("custom_height", 1024),
        )
        quality = kwargs.get("quality", "auto")
        moderation = kwargs.get("moderation", "auto")
        n = kwargs.get("n", 1)
        background = kwargs.get("background", "auto")
        input_fidelity = kwargs.get("input_fidelity", "auto")
        output_format = kwargs.get("output_format", "png")
        output_compression = kwargs.get("output_compression", 100)
        complexity = kwargs.get("complexity", "auto")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if markup_mask is not None and markup is None:
            raise ValueError("markup_mask is connected but markup is not; connect the markup IMAGE too")

        grid_pngs = None
        if image is None:
            grid_pngs = await asyncio.to_thread(
                _grid_pngs,
                kwargs.get("grid_images", "[]"),
                model,
            )

        try:
            # Use provided client or create new one
            if client is not None:
                image_client = client
            else:
                image_client = OpenAIClient(
                    api_key=None,
                    model=model
                )

            print(f"[OpenAI] Editing image with model: {model}")
            print(f"[OpenAI] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

            if image is None:
                image_bytes = grid_pngs
                print(f"[OpenAI] Grid edit: sending {len(grid_pngs)} image(s) at their own size")
            else:
                # Convert image tensor to PNG bytes. Handle batched input: if the
                # IMAGE tensor has N > 1 in its batch dimension, send all N as a
                # list of reference images (gpt-image-2 multi-image edit).
                batch_size = image.shape[0] if hasattr(image, "shape") and len(image.shape) == 4 else 1
                if batch_size > 1:
                    image_bytes = [
                        ImageConverter.tensor_to_bytes(image[i:i + 1], format="PNG")
                        for i in range(batch_size)
                    ]
                    print(f"[OpenAI] Multi-image edit: sending {batch_size} reference images")
                else:
                    image_bytes = ImageConverter.tensor_to_bytes(image, format="PNG")

            # Convert mask if provided
            mask_bytes = None
            if mask is not None:
                import numpy as np
                from PIL import Image

                try:
                    import torch
                except ImportError:
                    raise ImportError("torch is required for mask processing")

                # Handle mask tensor
                if len(mask.shape) == 4:
                    mask_tensor = mask[0]
                elif len(mask.shape) == 3:
                    mask_tensor = mask[0]
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
                pil_image = (ImageConverter.tensor_to_pil(image) if image is not None
                             else Image.open(BytesIO(image_bytes[0])))
                if pil_image.mode != 'RGBA':
                    pil_image = pil_image.convert('RGBA')

                # Apply mask as alpha channel (invert: white in mask = transparent = edit)
                alpha = 255 - mask_array
                pil_image.putalpha(Image.fromarray(alpha))

                buffer = BytesIO()
                pil_image.save(buffer, format="PNG")
                mask_bytes = buffer.getvalue()

                print(f"[OpenAI] Using mask for inpainting")

            markup_bytes = None
            if markup is not None:
                from PIL import Image
                first_size = ((image.shape[2], image.shape[1]) if image is not None
                              else Image.open(BytesIO(image_bytes[0])).size)
                markup_bytes = _markup_png(markup, markup_mask, first_size)
                print("[OpenAI] Using markup layer")

            # Edit image
            response = await image_client.edit_image(
                image_data=image_bytes,
                prompt=prompt.strip(),
                mask_data=mask_bytes,
                model=model,
                size=size,
                quality=quality,
                moderation=moderation,
                n=n,
                background=background,
                input_fidelity=input_fidelity,
                output_format=output_format,
                output_compression=output_compression,
                complexity=complexity,
                markup_data=markup_bytes,
            )

            if response.get("blocked", False):
                error_msg = f"Image blocked by content filters: {response.get('error', 'Unknown reason')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            images = response.get("images", [])
            if not images:
                raise ValueError("No image was generated")

            # Convert ALL returned images to a single batched tensor [N,H,W,C].
            tensors = [ImageConverter.base64_to_tensor(img) for img in images]
            if len(tensors) == 1:
                image_tensor = tensors[0]
            else:
                import torch
                image_tensor = torch.cat(tensors, dim=0)
            print(f"[OpenAI] Edited {len(tensors)} image(s), batch shape: {image_tensor.shape}")

            return IO.NodeOutput(image_tensor)

        except Exception as e:
            error_msg = f"Failed to edit image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)
