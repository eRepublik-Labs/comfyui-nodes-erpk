# ABOUTME: Qwen Image LoRA text-to-image node for WaveSpeed AI.
# ABOUTME: Generates images guided by up to 3 LoRA models with configurable scales.

from comfy_api.latest import IO


class QwenImageLoraNode(IO.ComfyNode):
    """
    Qwen Image LoRA Text-to-Image Node

    Generates images from text prompts with up to 3 LoRA model influences.
    Each LoRA accepts a URL path and a scale factor (0.0 to 4.0).
    Maximum resolution: 1024x1024.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageLoraNode",
            display_name="Qwen Image LoRA",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the image to generate (Chinese or English)"),
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
                IO.Int.Input("width", optional=True, default=1024, min=256, max=1024, step=8,
                             tooltip="Image width (256 to 1024)"),
                IO.Int.Input("height", optional=True, default=1024, min=256, max=1024, step=8,
                             tooltip="Image height (256 to 1024)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
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
        return float("NaN")

    @classmethod
    def execute(cls, prompt="", lora_1_path="", lora_1_scale=1.0,
                lora_2_path="", lora_2_scale=1.0, lora_3_path="", lora_3_scale=1.0,
                client=None, width=1024, height=1024, seed=-1,
                output_format="jpeg", enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_lora import QwenImageLora

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if not lora_1_path or not lora_1_path.strip():
            raise ValueError("At least one LoRA path is required")

        loras = [{"path": lora_1_path.strip(), "scale": lora_1_scale}]
        if lora_2_path and lora_2_path.strip():
            loras.append({"path": lora_2_path.strip(), "scale": lora_2_scale})
        if lora_3_path and lora_3_path.strip():
            loras.append({"path": lora_3_path.strip(), "scale": lora_3_scale})

        request = QwenImageLora(
            prompt=prompt,
            loras=loras,
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
        return IO.NodeOutput(images)
