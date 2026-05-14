# ABOUTME: Qwen Image text-to-image generation node for WaveSpeed AI.
# ABOUTME: Generates high-quality images from bilingual (Chinese/English) text prompts.

from comfy_api.latest import IO


class QwenImageTextToImageNode(IO.ComfyNode):
    """
    Qwen Image Text-to-Image Generator Node

    This node uses Qwen Image model to generate high-quality images from text prompts.
    Supports bilingual (Chinese and English) prompts.
    """

    MODELS = ["Qwen Image", "Qwen Image 2512"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageTextToImageNode",
            display_name="Qwen Image Text-to-Image",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Qwen Image",
                               tooltip="Model variant: Qwen Image (20B MMDiT) or Qwen Image 2512 (7B, better text rendering)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate (Chinese or English)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=1024, min=256, max=1536, step=8,
                             tooltip="Image width (256 to 1536)"),
                IO.Int.Input("height", optional=True, default=1024, min=256, max=1536, step=8,
                             tooltip="Image height (256 to 1536)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.Combo.Input("output_format", optional=True,
                               options=["jpeg", "png", "webp"],
                               default="jpeg",
                               tooltip="Output image format"),
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="Wait for completion before returning response"),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="Return BASE64-encoded output instead of URL"),
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
    def execute(cls, model="Qwen Image", prompt="", client=None, width=1024, height=1024,
                seed=-1, output_format="jpeg", enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_text_to_image import QwenImageTextToImage
        from .wavespeed_api.requests.qwen_image_text_to_image_2512 import QwenImageTextToImage2512

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request_cls = QwenImageTextToImage2512 if model == "Qwen Image 2512" else QwenImageTextToImage

        request = request_cls(
            prompt=prompt,
            size=f"{width}*{height}",
            seed=seed,
            output_format=output_format,
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images, slot=0)
        return IO.NodeOutput(images, ui=ui)
