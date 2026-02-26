# ABOUTME: Qwen Image Layered node for image layer decomposition via WaveSpeed AI.
# ABOUTME: Decomposes images into N RGBA layers with separate RGB and alpha mask outputs.

from comfy_api.latest import IO


class QwenImageLayeredNode(IO.ComfyNode):
    """
    Qwen Image Layered Decomposition Node

    Decomposes a single image into 2-8 RGBA layers with transparency.
    Returns both RGB image layers and their corresponding alpha masks
    for use in compositing workflows.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageLayeredNode",
            display_name="Qwen Image Layered",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("image",
                                tooltip="The image to decompose into layers (URL or path)"),
                IO.String.Input("prompt", optional=True, multiline=True, default="",
                                tooltip="Optional text description to guide layer decomposition (Chinese or English)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("num_layers", optional=True, default=4, min=2, max=8,
                             tooltip="Number of layers to decompose into (2-8)"),
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="Wait for completion before returning response"),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="Return BASE64-encoded output instead of URL"),
            ],
            outputs=[
                IO.Image.Output("images"),
                IO.Mask.Output("masks"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def execute(cls, image="", prompt="", client=None, num_layers=4,
                enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor_rgba
        from .wavespeed_api.requests.qwen_image_layered import QwenImageLayered

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if image is None or image == "":
            raise ValueError("Image must be provided")

        request_kwargs = dict(
            image=image,
            num_layers=num_layers,
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        if prompt and prompt.strip():
            request_kwargs["prompt"] = prompt

        request = QwenImageLayered(**request_kwargs)

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, num_layers)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        rgb_tensor, alpha_tensor = imageurl2tensor_rgba(image_urls)
        return IO.NodeOutput(rgb_tensor, alpha_tensor)
