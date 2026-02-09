from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4_5 import SeedreamV4_5


# Recommended resolutions from WaveSpeed API docs for V4.5
SEEDREAM_V4_5_SIZE_PRESETS = {
    "Custom": None,
    "1:1 (2048x2048)": (2048, 2048),
    "1:1 4K (4096x4096)": (4096, 4096),
    "4:3 (2688x2016)": (2688, 2016),
    "3:4 (2016x2688)": (2016, 2688),
    "3:2 (2688x1792)": (2688, 1792),
    "2:3 (1792x2688)": (1792, 2688),
    "16:9 (2560x1440)": (2560, 1440),
    "9:16 (1440x2560)": (1440, 2560),
}


class SeedreamV4_5Node:
    """
    ByteDance Seedream-V4.5 Image Generator Node

    Enhanced typography and text rendering for posters, logos, UI, and marketing layouts.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description of the image to generate",
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
                "client": ("WAVESPEED_AI_API_CLIENT", {"tooltip": "WaveSpeed API client (optional if API key is configured in Settings)"}),
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
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "execute"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def execute(
        self,
        prompt,
        size_preset,
        client=None,
        width=2048,
        height=2048,
        show_aspect_ratio=True,
    ):
        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient().create_client()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        # Get dimensions from preset or use custom values
        preset_dims = SEEDREAM_V4_5_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV4_5(
            prompt=prompt,
            width=width,
            height=height,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        # Download and process images
        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return (images,)


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4_5": SeedreamV4_5Node}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4_5": "Bytedance Seedream V4.5 (Custom)"
}
