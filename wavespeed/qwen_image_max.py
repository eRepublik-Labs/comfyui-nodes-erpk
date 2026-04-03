# ABOUTME: Qwen Image Max text-to-image generation node for WaveSpeed AI.
# ABOUTME: Simplified node with no model selector, output_format, sync_mode, or base64 options.

from comfy_api.latest import IO


class QwenImageMaxNode(IO.ComfyNode):
    """
    Qwen Image Max Text-to-Image Generator Node

    Generates high-quality images from text prompts using Qwen Image Max.
    Simplified interface with fewer output options.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageMaxNode",
            display_name="Qwen Image Max",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate (max 800 chars)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=1024, min=256, max=1536, step=8,
                             tooltip="Image width (256 to 1536)"),
                IO.Int.Input("height", optional=True, default=1024, min=256, max=1536, step=8,
                             tooltip="Image height (256 to 1536)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
            not_idempotent=True,
        )


    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return kwargs.get("seed", 0)

    @classmethod
    def execute(cls, prompt="", client=None, width=1024, height=1024,
                seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_max import QwenImageMax

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request = QwenImageMax(
            prompt=prompt,
            size=f"{width}*{height}",
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
