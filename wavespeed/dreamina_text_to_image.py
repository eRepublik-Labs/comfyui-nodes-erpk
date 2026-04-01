# ABOUTME: ByteDance Dreamina text-to-image node for WaveSpeed AI.
# ABOUTME: Supports V3.0 and V3.1 model variants with optional prompt expansion.

from comfy_api.latest import IO


class DreaminaTextToImageNode(IO.ComfyNode):
    """
    ByteDance Dreamina Text-to-Image Generator Node

    Generates images from text prompts using Dreamina V3.0 or V3.1 models.
    """

    MODELS = ["Dreamina V3.1", "Dreamina V3.0"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="DreaminaTextToImageNode",
            display_name="Bytedance Dreamina Text-to-Image",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Dreamina V3.1",
                               tooltip="Model variant: Dreamina V3.0 or V3.1"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=1328, min=512, max=2048, step=8,
                             tooltip="Image width (512 to 2048)"),
                IO.Int.Input("height", optional=True, default=1328, min=512, max=2048, step=8,
                             tooltip="Image height (512 to 2048)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.Boolean.Input("enable_prompt_expansion", optional=True, default=True,
                                 tooltip="Automatically expand and enhance the prompt for better results"),
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
    def execute(cls, model="Dreamina V3.1", prompt="", client=None, width=1328, height=1328,
                seed=-1, enable_prompt_expansion=True, enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.dreamina_v3_text_to_image import DreaminaV3TextToImage
        from .wavespeed_api.requests.dreamina_v3_1_text_to_image import DreaminaV3_1TextToImage

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request_cls = DreaminaV3TextToImage if model == "Dreamina V3.0" else DreaminaV3_1TextToImage

        request = request_cls(
            prompt=prompt,
            size=f"{width}*{height}",
            seed=seed,
            enable_prompt_expansion=enable_prompt_expansion,
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
