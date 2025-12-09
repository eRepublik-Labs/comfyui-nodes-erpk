from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_5_edit import SeedreamV4_5Edit
from .seedream_v4_5 import SEEDREAM_V4_5_SIZE_PRESETS
from .seedream_v4 import calculate_aspect_ratio


class SeedreamV4_5EditNode:
    """
    ByteDance Seedream V4.5 Edit Image Editor Node

    Enhanced typography and text rendering for editing images with text overlays.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description of the desired image modifications",
                    },
                ),
                "images": (
                    "STRING",
                    {
                        "tooltip": "The images to edit. A maximum of 10 reference images can be uploaded.",
                    },
                ),
                "size_preset": (
                    list(SEEDREAM_V4_5_SIZE_PRESETS.keys()),
                    {
                        "default": "Custom",
                        "tooltip": "Recommended resolution presets. Select 'Custom' to use manual width/height.",
                    },
                ),
            },
            "optional": {
                "width": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 1024,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom width (only used when size_preset is 'Custom')",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 1024,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom height (only used when size_preset is 'Custom')",
                    },
                ),
                "show_aspect_ratio": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Show aspect ratio in node title",
                    },
                ),
                "enable_sync_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Wait for result generation before returning response",
                    },
                ),
                "enable_base64_output": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Return BASE64 encoded output instead of URLs",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "aspect_ratio")

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def execute(
        self,
        client,
        prompt,
        images,
        size_preset,
        width=2048,
        height=2048,
        enable_sync_mode=False,
        enable_base64_output=False,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is None or images == "":
            raise ValueError("Images must be provided")

        # Ensure we have at most 10 image URLs
        images_param = images[:10]

        # Get dimensions from preset or use custom values
        preset_dims = SEEDREAM_V4_5_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV4_5Edit(
            prompt=prompt,
            images=images_param,
            size=f"{width}*{height}",
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        # Download and process images
        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        aspect_ratio = calculate_aspect_ratio(width, height)
        return (images, aspect_ratio)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4_5Edit": SeedreamV4_5EditNode}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4_5Edit": "Bytedance Seedream V4.5 Edit (Custom)"
}
