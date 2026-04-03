# ABOUTME: ByteDance Seedream V4 text-to-image generation node for WaveSpeed AI.
# ABOUTME: Generates high-quality images from text prompts with configurable size presets.

from comfy_api.latest import IO

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


class SeedreamV4Node(IO.ComfyNode):
    """
    ByteDance Seedream-V4 Image Generator Node

    This node uses ByteDance's Seedream-V4 model to generate high-quality images.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV4Node",
            display_name="Bytedance Seedream V4",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("size_preset",
                               options=list(SEEDREAM_V4_SIZE_PRESETS.keys()),
                               default="Custom",
                               tooltip="Recommended resolution presets. Select 'Custom' to use manual width/height."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=1408, min=320, max=4096, step=8,
                             tooltip="Custom width (only used when size_preset is 'Custom')"),
                IO.Int.Input("height", optional=True, default=1408, min=320, max=4096, step=8,
                             tooltip="Custom height (only used when size_preset is 'Custom')"),
                IO.Boolean.Input("show_aspect_ratio", optional=True, default=True,
                                 tooltip="Show aspect ratio in node title"),
                IO.Int.Input("seed", default=0, min=0, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Seed for cache control. Randomizes by default."),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
            not_idempotent=True,
        )


    @classmethod
    def execute(cls, prompt, size_preset, client=None, width=1408, height=1408,
                show_aspect_ratio=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v4 import SeedreamV4

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

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

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
