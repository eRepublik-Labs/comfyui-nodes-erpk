# ABOUTME: ByteDance Seedream V4 Edit Sequential node for multi-image editing via WaveSpeed AI.
# ABOUTME: Edits images with sequential generation for multiple coherent results.

from comfy_api.latest import IO
from .seedream_v4 import SEEDREAM_V4_SIZE_PRESETS


class SeedreamV4EditSequentialNode(IO.ComfyNode):
    """
    ByteDance Seedream V4 Edit Sequential Image Editor Node

    This node uses ByteDance's Seedream V4 Edit Sequential model to edit images
    with sequential generation for multiple coherent results.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV4EditSequentialNode",
            display_name="Bytedance Seedream V4 Edit Sequential",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of desired modifications. The node automatically appends the image count to your prompt."),
                IO.Int.Input("max_images", default=4, min=1, max=15, step=1,
                             tooltip="Number of images to generate (1-15). Automatically added to prompt for API compliance."),
                IO.Combo.Input("size_preset",
                               options=list(SEEDREAM_V4_SIZE_PRESETS.keys()),
                               default="Custom",
                               tooltip="Recommended resolution presets. Select 'Custom' to use manual width/height."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("image_url", optional=True,
                                tooltip="Image URL(s) to edit (optional). Accepts single URL (string) or multiple URLs (array). Max 10 images."),
                IO.Int.Input("width", optional=True, default=1408, min=320, max=4096, step=8,
                             tooltip="Custom width (only used when size_preset is 'Custom')"),
                IO.Int.Input("height", optional=True, default=1408, min=320, max=4096, step=8,
                             tooltip="Custom height (only used when size_preset is 'Custom')"),
                IO.Boolean.Input("show_aspect_ratio", optional=True, default=True,
                                 tooltip="Show aspect ratio in node title"),
                IO.Boolean.Input("enable_sync_mode", optional=True, default=False,
                                 tooltip="Wait for result generation before returning response"),
                IO.Boolean.Input("enable_base64_output", optional=True, default=False,
                                 tooltip="Return BASE64 encoded output instead of URLs"),
            ],
            outputs=[
                IO.Image.Output("images"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def execute(cls, prompt, max_images, size_preset, client=None, image_url=None,
                width=1408, height=1408, show_aspect_ratio=True, enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.seedream_v4_edit_sequential import SeedreamV4EditSequential

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if max_images < 1 or max_images > 15:
            raise ValueError("max_images must be between 1 and 15")

        images_param = None
        if image_url is not None and image_url != "":
            if isinstance(image_url, list):
                images_param = image_url[:10]
            else:
                images_param = [image_url]

        preset_dims = SEEDREAM_V4_SIZE_PRESETS.get(size_preset)
        if preset_dims:
            width, height = preset_dims

        generatePrompt = f"{prompt}. Generate a set of {max_images} consecutive."

        request = SeedreamV4EditSequential(
            prompt=generatePrompt,
            max_images=max_images,
            images=images_param,
            size=f"{width}*{height}",
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
