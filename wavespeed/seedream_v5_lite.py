# ABOUTME: ByteDance Seedream V5.0 Lite text-to-image generation node for WaveSpeed AI.
# ABOUTME: Higher minimum resolution (1440px) text-to-image generation with enhanced typography.

from comfy_api.latest import IO

# Recommended resolutions from WaveSpeed API docs for V5.0 Lite
SEEDREAM_V5_LITE_SIZE_PRESETS = {
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


class SeedreamV5LiteNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.0 Lite Image Generator Node

    Higher minimum resolution text-to-image generation with enhanced typography.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5LiteNode",
            display_name="Bytedance Seedream V5.0 Lite",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("size_preset",
                               options=list(SEEDREAM_V5_LITE_SIZE_PRESETS.keys()),
                               default="Custom",
                               tooltip="Recommended resolution presets. Select 'Custom' to use manual width/height."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=2048, min=1440, max=4096, step=8,
                             tooltip="Custom width (only used when size_preset is 'Custom')"),
                IO.Int.Input("height", optional=True, default=2048, min=1440, max=4096, step=8,
                             tooltip="Custom height (only used when size_preset is 'Custom')"),
                IO.Boolean.Input("show_aspect_ratio", optional=True, default=True,
                                 tooltip="Show aspect ratio in node title"),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Seed for cache control. Randomizes by default."),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
            not_idempotent=True,
        )


    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt, size_preset, client=None, width=2048, height=2048,
                show_aspect_ratio=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v5_lite import SeedreamV5Lite

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        preset_dims = SEEDREAM_V5_LITE_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV5Lite(
            prompt=prompt,
            width=width,
            height=height,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images, slot=0)
        return IO.NodeOutput(images, ui=ui)
