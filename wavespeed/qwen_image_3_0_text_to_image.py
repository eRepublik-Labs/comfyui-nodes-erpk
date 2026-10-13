# ABOUTME: Qwen Image 3.0 text-to-image node for WaveSpeed AI.
# ABOUTME: Generates an image from a prompt on the standard or Pro model, at 1k or 2k.

from comfy_api.latest import IO


class QwenImage30TextToImageNode(IO.ComfyNode):
    """
    Qwen Image 3.0 Text-to-Image Node

    Generates an image from a Chinese or English prompt at one of 15 aspect
    ratios and a 1k or 2k resolution tier.
    """

    MODELS = ["Qwen Image 3.0", "Qwen Image 3.0 Pro"]
    ASPECT_RATIOS = ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3",
                     "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    RESOLUTIONS = ["1k", "2k"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImage30TextToImageNode",
            display_name="Qwen Image 3.0 Text-to-Image",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS, default="Qwen Image 3.0",
                               tooltip="Qwen Image 3.0: $0.03 per image at 1k or 2k. "
                                       "Qwen Image 3.0 Pro: $0.04 at 1k, $0.075 at 2k."),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Image description in Chinese or English. WaveSpeed recommends at most 800 characters."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("aspect_ratio", optional=True, options=cls.ASPECT_RATIOS, default="1:1",
                               tooltip="Output aspect ratio"),
                IO.Combo.Input("resolution", optional=True, options=cls.RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier"),
                IO.Boolean.Input("enable_prompt_expansion", optional=True, default=False,
                                 tooltip="Let the model rewrite the prompt into a more detailed one"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same result and "
                                     "lets ComfyUI reuse the cached output; -1 generates a new one each queue."),
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
    async def execute(cls, model="Qwen Image 3.0", prompt="", client=None, aspect_ratio="1:1",
                      resolution="1k", enable_prompt_expansion=False, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_3_0_text_to_image import (
            QwenImage30TextToImage, QwenImage30ProTextToImage,
        )

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request_cls = {"Qwen Image 3.0": QwenImage30TextToImage,
                       "Qwen Image 3.0 Pro": QwenImage30ProTextToImage}[model]
        request = request_cls(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enable_prompt_expansion=enable_prompt_expansion,
            seed=seed,
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
