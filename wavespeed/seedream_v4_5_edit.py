# ABOUTME: ByteDance Seedream V4.5 Edit node for image editing via WaveSpeed AI.
# ABOUTME: Enhanced typography and text rendering for editing images with text overlays.

from comfy_api.latest import IO
from .seedream_v4_5 import SEEDREAM_V4_5_SIZE_PRESETS


class SeedreamV4_5EditNode(IO.ComfyNode):
    """
    ByteDance Seedream V4.5 Edit Image Editor Node

    Enhanced typography and text rendering for editing images with text overlays.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV4_5EditNode",
            display_name="Bytedance Seedream V4.5 Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications"),
                IO.String.Input("image_url",
                                tooltip="Image URL(s) to edit. Accepts single URL (string) or multiple URLs (array). Max 10 images."),
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
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="Wait for result generation before returning response"),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="Return BASE64 encoded output instead of URLs"),
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
    def execute(cls, prompt, image_url, size_preset, client=None, width=2048, height=2048,
                show_aspect_ratio=True, enable_sync_mode=False, enable_base64_output=False,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v4_5_edit import SeedreamV4_5Edit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image_url is None or image_url == "":
            raise ValueError("Image URL must be provided")

        if isinstance(image_url, list):
            images_param = image_url[:10]
        else:
            images_param = [image_url]

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

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
