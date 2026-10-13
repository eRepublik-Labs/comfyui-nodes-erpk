# ABOUTME: Qwen Image Max Edit node for multi-reference image editing via WaveSpeed AI.
# ABOUTME: Accepts up to 6 reference images with no output_format, sync_mode, or base64 options.

from comfy_api.latest import IO


class QwenImageMaxEditNode(IO.ComfyNode):
    """
    Qwen Image Max Edit Node

    Edits images using Qwen Image Max with up to 6 reference images.
    Simplified interface with fewer output options.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageMaxEditNode",
            display_name="Qwen Image Max Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications"),
                IO.String.Input("images", default="",
                                tooltip="Reference image URLs to edit, up to 6, separated by commas or newlines. "
                                        "Ignored when `reference_images` is connected."),
                IO.Image.Input("reference_images", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch, up to 6. Each slice is one image. "
                                       "Takes precedence over `images`. Sent inline as base64, no upload."),
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
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt="", images="", reference_images=None, client=None,
                width=1024, height=1024, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, input_image_list
        from .wavespeed_api.requests.qwen_image_max_edit import QwenImageMaxEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        images_param = input_image_list(reference_images, images, 6, "Qwen Image Max Edit")
        if not images_param:
            raise ValueError("Connect reference_images or enter at least one image URL")

        size = f"{width}*{height}" if width and height else None

        request = QwenImageMaxEdit(
            prompt=prompt,
            images=images_param,
            size=size,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result_images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, result_images, slot=0)
        return IO.NodeOutput(result_images, ui=ui)
