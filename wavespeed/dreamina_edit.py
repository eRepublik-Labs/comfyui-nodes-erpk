# ABOUTME: ByteDance Dreamina Edit node for single-image editing via WaveSpeed AI.
# ABOUTME: Edits a single image based on a text prompt using Dreamina V3.0.

from comfy_api.latest import IO


class DreaminaEditNode(IO.ComfyNode):
    """
    ByteDance Dreamina Edit Node

    Edits a single image based on a text prompt using Dreamina V3.0.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="DreaminaEditNode",
            display_name="Bytedance Dreamina Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired image modifications"),
                IO.String.Input("image_url",
                                tooltip="URL of the image to edit"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("width", optional=True, default=1328, min=512, max=2048, step=8,
                             tooltip="Image width (512 to 2048)"),
                IO.Int.Input("height", optional=True, default=1328, min=512, max=2048, step=8,
                             tooltip="Image height (512 to 2048)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
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
        return kwargs.get("seed", 0)

    @classmethod
    def execute(cls, prompt="", image_url="", client=None, width=1328, height=1328,
                seed=-1, enable_sync_mode=False, enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.dreamina_v3_edit import DreaminaV3Edit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image_url is None or image_url == "":
            raise ValueError("Image URL must be provided")

        request = DreaminaV3Edit(
            image=image_url,
            prompt=prompt,
            size=f"{width}*{height}",
            seed=seed,
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
