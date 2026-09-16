# ABOUTME: MiniMax H3 text-to-image generation node for WaveSpeed AI.
# ABOUTME: Produces a 1k or 2k image in one of fifteen aspect ratios, optionally with LoRAs.

from comfy_api.latest import IO


class MinimaxH3TextToImageNode(IO.ComfyNode):
    """
    MiniMax H3 Text-to-Image Generator Node

    Generates a single image from a text prompt at 1k (~1MP) or 2k (~4MP).
    Connecting a LoRA stack routes the call to the -lora twin.
    """

    ASPECT_RATIOS = ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    RESOLUTIONS = ["1k", "2k"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3TextToImageNode",
            display_name="MiniMax H3 Text-to-Image",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="1:1",
                               tooltip="Output aspect ratio"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="1k",
                               tooltip="Output resolution. 1k (~1MP) is about $0.02/image, 2k (~4MP) about $0.06."),
                IO.Combo.Input("output_format", optional=True,
                               options=["jpeg", "png", "webp"], default="jpeg",
                               tooltip="Output image format"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same result and lets ComfyUI reuse the cached output; -1 generates a new one each queue."),
                IO.Custom("MINIMAX_H3_LORAS").Input("loras", optional=True,
                    tooltip="LoRA stack from the MiniMax H3 LoRA Stack node. When connected, the call goes to the endpoint's -lora twin (+$0.015 per image)."),
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
    async def execute(cls, prompt="", client=None, aspect_ratio="1:1", resolution="1k",
                output_format="jpeg", seed=-1, loras=None, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.minimax_h3_text_to_image import MinimaxH3TextToImage

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request = MinimaxH3TextToImage(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            seed=seed,
            loras=loras or None,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=2, timeout=300)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images, slot=0)
        return IO.NodeOutput(images, ui=ui)
