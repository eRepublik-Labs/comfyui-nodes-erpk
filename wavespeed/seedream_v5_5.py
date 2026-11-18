# ABOUTME: ByteDance Seedream V5.5 text-to-image node via WaveSpeed AI.
# ABOUTME: Outputs the image plus its alpha as a mask, so transparent backgrounds survive.

from comfy_api.latest import IO
from .wavespeed_api.requests.seedream_v5_5 import BACKGROUNDS
from .wavespeed_api.requests.seedream_v5_pro import ASPECT_RATIOS, OUTPUT_FORMATS, RESOLUTIONS


class SeedreamV5_5Node(IO.ComfyNode):
    """
    ByteDance Seedream V5.5 text-to-image node.

    The endpoint takes no seed, so the seed input only controls ComfyUI's
    cache: a fixed seed reuses the last result, -1 generates again.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5_5Node",
            display_name="Bytedance Seedream V5.5",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("aspect_ratio", options=ASPECT_RATIOS, default="1:1",
                               tooltip="Aspect ratio of the generated image"),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. 1k and 1.5k cost $0.02, 2k costs $0.035."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("output_format", options=OUTPUT_FORMATS, default="png", optional=True,
                               tooltip="Output image format. A transparent background needs png."),
                IO.Combo.Input("background", options=BACKGROUNDS, default="auto", optional=True,
                               tooltip="Background of the result. transparent needs png output."),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Cache control only, not sent to the API. -1 generates again every run."),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask", tooltip="The result's alpha, 1 where opaque, 0 where transparent"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt, aspect_ratio="1:1", resolution="1k", client=None,
                      output_format="png", background="auto", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor_rgba
        from .wavespeed_api.requests.seedream_v5_5 import SeedreamV5_5

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        request = SeedreamV5_5(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            background=background,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images, masks = imageurl2tensor_rgba(image_urls)
        return IO.NodeOutput(images, masks)
