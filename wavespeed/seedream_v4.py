from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.requests.seedream_v4 import SeedreamV4


# Recommended resolutions from WaveSpeed API docs
SEEDREAM_V4_SIZE_PRESETS = {
    "Custom": None,
    "1:1 2K (1408x1408)": (1408, 1408),
    "1:1 1K (1024x1024)": (1024, 1024),
    "3:2 2K (1728x1152)": (1728, 1152),
    "3:2 1K (1216x832)": (1216, 832),
    "2:3 2K (1152x1728)": (1152, 1728),
    "2:3 1K (832x1216)": (832, 1216),
    "4:3 2K (1664x1216)": (1664, 1216),
    "4:3 1K (1152x896)": (1152, 896),
    "3:4 2K (1216x1664)": (1216, 1664),
    "3:4 1K (896x1152)": (896, 1152),
    "16:9 2K (1920x1088)": (1920, 1088),
    "16:9 1K (1344x768)": (1344, 768),
    "9:16 2K (1088x1920)": (1088, 1920),
    "9:16 1K (768x1344)": (768, 1344),
    "21:9 2K (2176x960)": (2176, 960),
    "21:9 1K (1536x640)": (1536, 640),
    "9:21 2K (960x2176)": (960, 2176),
    "9:21 1K (640x1536)": (640, 1536),
}


class SeedreamV4Node:
    """
    ByteDance Seedream-V4 Image Generator Node

    This node uses ByteDance's Seedream-V4 model to generate high-quality images.
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
                        "tooltip": "Text description of the image to generate",
                    },
                ),
                "size_preset": (
                    list(SEEDREAM_V4_SIZE_PRESETS.keys()),
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
                        "default": 1408,
                        "min": 320,
                        "max": 4096,
                        "step": 8,
                        "display": "number",
                        "tooltip": "Custom width (only used when size_preset is 'Custom')",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1408,
                        "min": 320,
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
        client,
        prompt,
        size_preset,
        width=1408,
        height=1408,
        show_aspect_ratio=True,
    ):
        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        # Get dimensions from preset or use custom values
        preset_dims = SEEDREAM_V4_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV4(
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


NODE_CLASS_MAPPINGS = {"WaveSpeed Custom SeedreamV4": SeedreamV4Node}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeed Custom SeedreamV4": "Bytedance Seedream V4 (Custom)"
}
