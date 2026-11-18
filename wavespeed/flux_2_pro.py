# ABOUTME: FLUX.2 Pro text-to-image node via WaveSpeed AI.
# ABOUTME: Sized by width and height, with a seed sent to the API.

from comfy_api.latest import IO


class Flux2ProNode(IO.ComfyNode):
    """FLUX.2 Pro text-to-image node."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Flux2ProNode",
            display_name="FLUX.2 Pro",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate. Costs $0.03 per image."),
                IO.Int.Input("width", default=1024, min=256, max=2048, step=16,
                             tooltip="Output width in pixels"),
                IO.Int.Input("height", default=1024, min=256, max=2048, step=16,
                             tooltip="Output height in pixels"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Sent to the API. -1 picks a random seed and generates again every run; "
                                     "a fixed value reuses the cached result."),
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
    async def execute(cls, prompt, width=1024, height=1024, client=None, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.flux_2_pro import Flux2Pro

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        request = Flux2Pro(prompt=prompt, size=f"{width}*{height}", seed=seed)

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
