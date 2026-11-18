# ABOUTME: ByteDance Seedream V5.0 Flash text-to-image node via WaveSpeed AI.
# ABOUTME: Sized by aspect ratio and a 1k/1.5k/2k resolution tier, at a flat price per image.

from comfy_api.latest import IO
from .wavespeed_api.requests.seedream_v5_pro import ASPECT_RATIOS, OUTPUT_FORMATS, RESOLUTIONS


class SeedreamV5FlashNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.0 Flash text-to-image node.

    The endpoint takes no seed, so the seed input only controls ComfyUI's
    cache: a fixed seed reuses the last result, -1 generates again.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5FlashNode",
            display_name="Bytedance Seedream V5.0 Flash",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Combo.Input("aspect_ratio", options=ASPECT_RATIOS, default="1:1",
                               tooltip="Aspect ratio of the generated image"),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. Every tier costs a flat $0.027 per image."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("output_format", options=OUTPUT_FORMATS, default="jpeg", optional=True,
                               tooltip="Output image format"),
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
                      output_format="jpeg", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v5_flash import SeedreamV5Flash

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        request = SeedreamV5Flash(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
