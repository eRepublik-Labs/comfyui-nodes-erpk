# ABOUTME: Qwen Image 3.0 edit node for WaveSpeed AI.
# ABOUTME: Edits up to 3 reference images per instruction, on the standard or Pro model.

from comfy_api.latest import IO


class QwenImage30EditNode(IO.ComfyNode):
    """
    Qwen Image 3.0 Edit Node

    Edits 1 to 3 reference images from a Chinese or English instruction, at
    1k or 2k. An `auto` aspect ratio follows the first reference image.
    """

    MODELS = ["Qwen Image 3.0", "Qwen Image 3.0 Pro"]
    ASPECT_RATIOS = ["auto", "1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3",
                     "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    RESOLUTIONS = ["1k", "2k"]
    MAX_IMAGES = 3

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImage30EditNode",
            display_name="Qwen Image 3.0 Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS, default="Qwen Image 3.0",
                               tooltip="Qwen Image 3.0: $0.03 per image at 1k or 2k. "
                                       "Qwen Image 3.0 Pro: $0.04 at 1k, $0.075 at 2k. "
                                       "Both add $0.003 per reference image."),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Edit instruction in Chinese or English. WaveSpeed recommends at most 800 characters."),
                IO.Image.Input("reference_images", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch, up to 3, 384-2048 px per side. "
                                       "Each slice is one image. Takes precedence over `reference_images_url`. "
                                       "Sent inline as base64, no upload."),
                IO.String.Input("reference_images_url", optional=True, default="",
                                tooltip="Reference image URLs, up to 3, separated by commas or newlines. "
                                        "Ignored when `reference_images` is connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("aspect_ratio", optional=True, options=cls.ASPECT_RATIOS, default="auto",
                               tooltip="Output aspect ratio. auto follows the first reference image."),
                IO.Combo.Input("resolution", optional=True, options=cls.RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier"),
                IO.Boolean.Input("enable_prompt_expansion", optional=True, default=False,
                                 tooltip="Let the model rewrite the instruction into a more detailed prompt"),
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
    async def execute(cls, model="Qwen Image 3.0", prompt="", reference_images=None, reference_images_url="",
                      client=None, aspect_ratio="auto", resolution="1k", enable_prompt_expansion=False,
                      seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, input_image_list
        from .wavespeed_api.requests.qwen_image_3_0_edit import QwenImage30Edit, QwenImage30ProEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        images_param = input_image_list(reference_images, reference_images_url, cls.MAX_IMAGES, model)
        if not images_param:
            raise ValueError("Connect reference_images or enter at least one image URL")

        request_cls = {"Qwen Image 3.0": QwenImage30Edit, "Qwen Image 3.0 Pro": QwenImage30ProEdit}[model]
        request = request_cls(
            prompt=prompt,
            images=images_param,
            aspect_ratio=None if aspect_ratio == "auto" else aspect_ratio,
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
        return IO.NodeOutput(images)
