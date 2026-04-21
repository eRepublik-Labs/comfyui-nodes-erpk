# ABOUTME: Qwen Image 2.0 edit node for image editing via WaveSpeed AI.
# ABOUTME: Supports standard and Pro variants; accepts up to 3 reference images.

from comfy_api.latest import IO


class QwenImage20EditNode(IO.ComfyNode):
    """
    Qwen Image 2.0 Edit Node

    This node uses Qwen Image 2.0 Edit models for image editing with multiple reference images.
    Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.
    """

    MODELS = ["Qwen Image 2.0", "Qwen Image 2.0 Pro"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImage20EditNode",
            display_name="Qwen Image 2.0 Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Qwen Image 2.0",
                               tooltip="Model variant: Qwen Image 2.0 (standard) or Qwen Image 2.0 Pro (higher quality)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications (Chinese or English)"),
                IO.String.Input("images",
                                tooltip="Reference images to edit. Maximum of 3 images can be provided (comma-separated URLs or paths)"),
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
    def execute(cls, model="Qwen Image 2.0", prompt="", images="", client=None,
                width=1024, height=1024, seed=-1, output_format="jpeg",
                enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_2_0_edit import QwenImage20Edit
        from .wavespeed_api.requests.qwen_image_2_0_pro_edit import QwenImage20ProEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is None or images == "":
            raise ValueError("Images must be provided")

        if isinstance(images, str):
            images_list = [img.strip() for img in images.split(",") if img.strip()]
        else:
            images_list = images

        if len(images_list) > 3:
            raise ValueError("Maximum of 3 reference images can be uploaded")

        images_param = images_list[:3]

        size = f"{width}*{height}" if width and height else None

        request_cls = QwenImage20ProEdit if model == "Qwen Image 2.0 Pro" else QwenImage20Edit

        request = request_cls(
            prompt=prompt,
            images=images_param,
            size=size,
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

        result_images = imageurl2tensor(image_urls)
        return IO.NodeOutput(result_images)
