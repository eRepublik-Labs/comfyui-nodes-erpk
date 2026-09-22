# ABOUTME: ByteDance Seedream V5.0 Pro edit node via WaveSpeed AI.
# ABOUTME: Edits from up to 10 images, taken from an IMAGE batch or from URLs.

from comfy_api.latest import IO
from .wavespeed_api.requests.seedream_v5_pro import (
    ASPECT_RATIOS, OUTPUT_FORMATS, PROMPT_OPTIMIZATION_MODES, RESOLUTIONS,
)

# WaveSpeed accepts up to 10 input images on the Seedream Pro edit endpoint.
MAX_INPUT_IMAGES = 10

# Sent as no aspect ratio, so the API picks the ratio closest to the first image.
AUTO_ASPECT = "auto"


class SeedreamV5ProEditNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.0 Pro edit node.

    The endpoint takes no seed, so the seed input only controls ComfyUI's
    cache: a fixed seed reuses the last result, -1 generates again.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5ProEditNode",
            display_name="Bytedance Seedream V5.0 Pro Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired modifications"),
                IO.Image.Input("images", optional=True,
                               tooltip="Images to edit as a ComfyUI IMAGE batch. Each slice is one image, up to 10. "
                                       "Takes precedence over `image_url`. Sent inline as base64, no upload."),
                IO.String.Input("image_url", default="", multiline=True,
                                tooltip="Image URL(s) to edit, one per line or comma separated. Up to 10. "
                                        "Ignored when `images` is connected."),
                IO.Combo.Input("aspect_ratio", options=[AUTO_ASPECT] + ASPECT_RATIOS, default=AUTO_ASPECT,
                               tooltip="Aspect ratio of the result. auto follows the first image."),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. 1k and 1.5k cost $0.045, 2k costs $0.09, "
                                       "plus $0.003 per input image after the first."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("output_format", options=OUTPUT_FORMATS, default="jpeg", optional=True,
                               tooltip="Output image format"),
                IO.Combo.Input("prompt_optimization_mode", options=PROMPT_OPTIMIZATION_MODES,
                               default="standard", optional=True,
                               tooltip="The model rewrites the prompt first. fast is several times quicker "
                                       "but follows long or intricate prompts less closely."),
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="Wait for result generation before returning response"),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="Return BASE64 encoded output instead of URLs"),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Cache control only, not sent to the API. -1 generates again every run."),
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
    async def execute(cls, prompt, image_url="", images=None, aspect_ratio=AUTO_ASPECT, resolution="1k",
                      client=None, output_format="jpeg", prompt_optimization_mode="standard",
                      enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, input_image_list
        from .wavespeed_api.requests.seedream_v5_pro_edit import SeedreamV5ProEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        images_param = input_image_list(images, image_url, MAX_INPUT_IMAGES)
        if images_param is None:
            raise ValueError("Connect images or enter at least one image URL")

        request = SeedreamV5ProEdit(
            prompt=prompt,
            images=images_param,
            aspect_ratio=None if aspect_ratio == AUTO_ASPECT else aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            prompt_optimization_mode=prompt_optimization_mode,
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, result, slot=0)
        return IO.NodeOutput(result, ui=ui)
