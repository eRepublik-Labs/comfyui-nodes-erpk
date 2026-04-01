# ABOUTME: ByteDance Seedream V4.5 text-to-image generation node for WaveSpeed AI.
# ABOUTME: Enhanced typography and text rendering for posters, logos, UI, and marketing layouts.

from comfy_api.latest import IO

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


class SeedreamV4_5Node(IO.ComfyNode):
    """
    ByteDance Seedream-V4.5 Image Generator Node

    Enhanced typography and text rendering for posters, logos, UI, and marketing layouts.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV4_5Node",
            display_name="Bytedance Seedream V4.5",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("size_preset",
                               options=list(SEEDREAM_V4_5_SIZE_PRESETS.keys()),
                               default="Custom",
                               tooltip="Recommended resolution presets. Select 'Custom' to use manual width/height."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=2048, min=1024, max=4096, step=8,
                             tooltip="Custom width (only used when size_preset is 'Custom')"),
                IO.Int.Input("height", optional=True, default=2048, min=1024, max=4096, step=8,
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
    def execute(cls, prompt, size_preset, client=None, width=2048, height=2048,
                show_aspect_ratio=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v4_5 import SeedreamV4_5

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

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

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
