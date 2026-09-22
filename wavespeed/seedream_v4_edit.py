# ABOUTME: ByteDance Seedream V4 Edit node for image editing via WaveSpeed AI.
# ABOUTME: Edits images based on text prompts with configurable size presets.

from comfy_api.latest import IO

# WaveSpeed accepts up to 10 input images on every Seedream edit endpoint.
MAX_INPUT_IMAGES = 10
from .seedream_v4 import SEEDREAM_V4_SIZE_PRESETS


class SeedreamV4EditNode(IO.ComfyNode):
    """
    ByteDance Seedream V4 Edit Image Editor Node

    This node uses ByteDance's Seedream V4 Edit model to edit images based on text prompts.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV4EditNode",
            display_name="Bytedance Seedream V4 Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications"),
                IO.String.Input("image_url", default="", multiline=True,
                                tooltip="Image URL(s) to edit, one per line or comma separated. Up to 10. "
                                         "Ignored when `images` is connected."),
                IO.Image.Input("images", optional=True,
                               tooltip="Images to edit as a ComfyUI IMAGE batch. Each slice is one image, up to 10. "
                                       "Takes precedence over `image_url`. Sent inline as base64, no upload."),
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
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="If set to true, the function will wait for the result to be generated and uploaded before returning the response. It allows you to get the result directly in the response. This property is only available through the API."),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="If enabled, the output will be encoded into a BASE64 string instead of a URL. This property is only available through the API."),
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
    async def execute(cls, prompt, size_preset, image_url="", images=None, client=None, width=1408, height=1408,
                show_aspect_ratio=True, enable_sync_mode=False, enable_base64_output=False,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, input_image_list
        from .wavespeed_api.requests.seedream_v4_edit import SeedreamV4Edit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        images_param = input_image_list(images, image_url, MAX_INPUT_IMAGES)
        if images_param is None:
            raise ValueError("Connect images or enter at least one image URL")

        preset_dims = SEEDREAM_V4_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        request = SeedreamV4Edit(
            prompt=prompt,
            images=images_param,
            size=f"{width}*{height}",
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
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
