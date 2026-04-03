# ABOUTME: Qwen Image Multiple Angles node for angle-based image editing via WaveSpeed AI.
# ABOUTME: Rotates/repositions subjects using horizontal, vertical angles and distance parameters.

from comfy_api.latest import IO


class QwenImageMultipleAnglesNode(IO.ComfyNode):
    """
    Qwen Image Multiple Angles Node

    Transforms reference images by adjusting viewing angle and distance.
    Supports horizontal rotation (-90 to 90), vertical rotation (-30 to 60),
    and distance adjustment (0 to 2). Prompt is optional.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageMultipleAnglesNode",
            display_name="Qwen Image Multiple Angles",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("images",
                                tooltip="Reference images to transform (comma-separated URLs, max 3)"),
                IO.String.Input("prompt", optional=True, multiline=True, default="",
                                tooltip="Optional text description to guide the transformation (Chinese or English)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("horizontal_angle", optional=True, default=0, min=-90, max=90,
                             tooltip="Horizontal rotation angle (-90 to 90 degrees)"),
                IO.Int.Input("vertical_angle", optional=True, default=0, min=-30, max=60,
                             tooltip="Vertical rotation angle (-30 to 60 degrees)"),
                IO.Float.Input("distance", optional=True, default=1.0, min=0.0, max=2.0, step=0.1,
                               tooltip="Subject distance factor (0 to 2, default 1)"),
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
    def execute(cls, images="", prompt="", client=None, horizontal_angle=0,
                vertical_angle=0, distance=1.0, width=1024, height=1024,
                seed=-1, output_format="jpeg", enable_sync_mode=False,
                enable_base64_output=False, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor
        from .wavespeed_api.requests.qwen_image_multiple_angles import QwenImageMultipleAngles

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if images is None or images == "":
            raise ValueError("Images must be provided")

        if isinstance(images, str):
            images_list = [img.strip() for img in images.split(",") if img.strip()]
        else:
            images_list = images

        if len(images_list) > 3:
            raise ValueError("Maximum of 3 reference images can be provided")

        size = f"{width}*{height}" if width and height else None

        request_kwargs = dict(
            images=images_list[:3],
            size=size,
            seed=seed,
            output_format=output_format,
            enable_sync_mode=enable_sync_mode,
            enable_base64_output=enable_base64_output,
        )

        if prompt and prompt.strip():
            request_kwargs["prompt"] = prompt
        if horizontal_angle != 0:
            request_kwargs["horizontal_angle"] = horizontal_angle
        if vertical_angle != 0:
            request_kwargs["vertical_angle"] = vertical_angle
        if distance != 1.0:
            request_kwargs["distance"] = distance

        request = QwenImageMultipleAngles(**request_kwargs)

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result_images = imageurl2tensor(image_urls)
        return IO.NodeOutput(result_images)
