# ABOUTME: Qwen Image Edit Plus node for advanced multi-reference image editing via WaveSpeed AI.
# ABOUTME: Accepts up to 3 reference images with bilingual (Chinese/English) text prompts.

from comfy_api.latest import IO


class QwenImageEditPlusNode(IO.ComfyNode):
    """
    Qwen Image Edit Plus Node

    This node uses Qwen Image Edit Plus model for advanced image editing with multiple reference images.
    Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.
    """

    MODELS = ["Qwen Edit Plus", "Qwen Edit 2511"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageEditPlusNode",
            display_name="Qwen Image Edit Plus",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Qwen Edit Plus",
                               tooltip="Model variant: Qwen Edit Plus or Qwen Edit 2511 (multi-person editing, improved consistency)"),
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
    def execute(cls, model="Qwen Edit Plus", prompt="", images="", client=None,
                width=1024, height=1024, seed=-1, output_format="jpeg",
                enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_edit_plus import QwenImageEditPlus
        from .wavespeed_api.requests.qwen_image_edit_2511 import QwenImageEdit2511

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

        request_cls = QwenImageEdit2511 if model == "Qwen Edit 2511" else QwenImageEditPlus

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
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, result_images, slot=0)
        return IO.NodeOutput(result_images, ui=ui)
