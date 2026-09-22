# ABOUTME: ByteDance Seedream V5.0 Pro text-to-image node via WaveSpeed AI.
# ABOUTME: Sized by aspect ratio and a 1k/1.5k/2k resolution tier.

from comfy_api.latest import IO
from .wavespeed_api.requests.seedream_v5_pro import (
    ASPECT_RATIOS, OUTPUT_FORMATS, PROMPT_OPTIMIZATION_MODES, RESOLUTIONS,
)


class SeedreamV5ProNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.0 Pro text-to-image node.

    The endpoint takes no seed, so the seed input only controls ComfyUI's
    cache: a fixed seed reuses the last result, -1 generates again.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5ProNode",
            display_name="Bytedance Seedream V5.0 Pro",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("aspect_ratio", options=ASPECT_RATIOS, default="1:1",
                               tooltip="Aspect ratio of the generated image"),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. 1k and 1.5k cost $0.045, 2k costs $0.09."),
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
    async def execute(cls, prompt, aspect_ratio="1:1", resolution="1k", client=None,
                      output_format="jpeg", prompt_optimization_mode="standard",
                      enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v5_pro import SeedreamV5Pro

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        request = SeedreamV5Pro(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
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

        images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images, slot=0)
        return IO.NodeOutput(images, ui=ui)
