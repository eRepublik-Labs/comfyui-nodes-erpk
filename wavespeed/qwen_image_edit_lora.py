# ABOUTME: Qwen Image Edit LoRA node for single-image editing via WaveSpeed AI.
# ABOUTME: Combines image editing with up to 3 LoRA models for style-guided edits.

from comfy_api.latest import IO


class QwenImageEditLoraNode(IO.ComfyNode):
    """
    Qwen Image Edit LoRA Node

    Edits images based on text prompts with up to 3 LoRA model influences.
    Each LoRA accepts a URL path and a scale factor (0.0 to 4.0).
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageEditLoraNode",
            display_name="Qwen Image Edit LoRA",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications (Chinese or English)"),
                IO.String.Input("image",
                                tooltip="The image to edit (URL or path)"),
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
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate=True,
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
    def execute(cls, prompt="", image="", lora_1_path="", lora_1_scale=1.0,
                lora_2_path="", lora_2_scale=1.0, lora_3_path="", lora_3_scale=1.0,
                client=None, width=1024, height=1024, seed=-1,
                output_format="jpeg", enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_edit_lora import QwenImageEditLora

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image is None or image == "":
            raise ValueError("Image must be provided")

        if not lora_1_path or not lora_1_path.strip():
            raise ValueError("At least one LoRA path is required")

        loras = [{"path": lora_1_path.strip(), "scale": lora_1_scale}]
        if lora_2_path and lora_2_path.strip():
            loras.append({"path": lora_2_path.strip(), "scale": lora_2_scale})
        if lora_3_path and lora_3_path.strip():
            loras.append({"path": lora_3_path.strip(), "scale": lora_3_scale})

        size = f"{width}*{height}" if width and height else None

        request = QwenImageEditLora(
            prompt=prompt,
            image=image,
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

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
