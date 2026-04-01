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
                IO.String.Input("images",
                                tooltip="Reference images to edit. Maximum of 6 images (comma-separated URLs or paths)"),
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
    def execute(cls, prompt="", images="", client=None, width=1024, height=1024,
                seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_max_edit import QwenImageMaxEdit

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

        if len(images_list) > 6:
            raise ValueError("Maximum of 6 reference images can be uploaded")

        images_param = images_list[:6]

        size = f"{width}*{height}" if width and height else None

        request = QwenImageMaxEdit(
            prompt=prompt,
            images=images_param,
            size=size,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result_images = imageurl2tensor(image_urls)
        return IO.NodeOutput(result_images)
