# ABOUTME: Qwen Image Edit Plus LoRA node for multi-reference image editing via WaveSpeed AI.
# ABOUTME: Combines multi-image editing with up to 3 LoRA models, supports Edit Plus and 2511 variants.

from comfy_api.latest import IO


class QwenImageEditPlusLoraNode(IO.ComfyNode):
    """
    Qwen Image Edit Plus LoRA Node

    Advanced image editing with multiple reference images and up to 3 LoRA model influences.
    Supports Edit Plus LoRA and Edit 2511 LoRA model variants.
    """

    MODELS = ["Qwen Edit Plus LoRA", "Qwen Edit 2511 LoRA"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageEditPlusLoraNode",
            display_name="Qwen Image Edit Plus LoRA",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Qwen Edit Plus LoRA",
                               tooltip="Model variant: Qwen Edit Plus LoRA or Qwen Edit 2511 LoRA (multi-person editing, improved consistency)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications (Chinese or English)"),
                IO.String.Input("images",
                                tooltip="Reference images to edit. Maximum of 3 images can be provided (comma-separated URLs or paths)"),
                IO.String.Input("lora_1_path",
                                tooltip="URL to first LoRA model file (required)"),
                IO.Float.Input("lora_1_scale", default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale factor for first LoRA (0.0 to 4.0)"),
                IO.String.Input("lora_2_path", optional=True, default="",
                                tooltip="URL to second LoRA model file (optional)"),
                IO.Float.Input("lora_2_scale", optional=True, default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale factor for second LoRA (0.0 to 4.0)"),
                IO.String.Input("lora_3_path", optional=True, default="",
                                tooltip="URL to third LoRA model file (optional)"),
                IO.Float.Input("lora_3_scale", optional=True, default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale factor for third LoRA (0.0 to 4.0)"),
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
    def execute(cls, model="Qwen Edit Plus LoRA", prompt="", images="",
                lora_1_path="", lora_1_scale=1.0,
                lora_2_path="", lora_2_scale=1.0, lora_3_path="", lora_3_scale=1.0,
                client=None, width=1024, height=1024, seed=-1,
                output_format="jpeg", enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_edit_plus_lora import QwenImageEditPlusLora
        from .wavespeed_api.requests.qwen_image_edit_2511_lora import QwenImageEdit2511Lora

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is None or images == "":
            raise ValueError("Images must be provided")

        if not lora_1_path or not lora_1_path.strip():
            raise ValueError("At least one LoRA path is required")

        if isinstance(images, str):
            images_list = [img.strip() for img in images.split(",") if img.strip()]
        else:
            images_list = images

        if len(images_list) > 3:
            raise ValueError("Maximum of 3 reference images can be uploaded")

        images_param = images_list[:3]

        loras = [{"path": lora_1_path.strip(), "scale": lora_1_scale}]
        if lora_2_path and lora_2_path.strip():
            loras.append({"path": lora_2_path.strip(), "scale": lora_2_scale})
        if lora_3_path and lora_3_path.strip():
            loras.append({"path": lora_3_path.strip(), "scale": lora_3_scale})

        size = f"{width}*{height}" if width and height else None

        request_cls = QwenImageEdit2511Lora if model == "Qwen Edit 2511 LoRA" else QwenImageEditPlusLora

        request = request_cls(
            prompt=prompt,
            images=images_param,
            loras=loras,
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
