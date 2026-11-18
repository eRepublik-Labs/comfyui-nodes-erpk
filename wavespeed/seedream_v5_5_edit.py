# ABOUTME: ByteDance Seedream V5.5 edit node via WaveSpeed AI.
# ABOUTME: Edits from up to 10 images and outputs the result plus its alpha as a mask.

from comfy_api.latest import IO

from ..utils.image_grid import grid_cap_for, grid_input, register_grid_caps, validate_grid
from .wavespeed_api.requests.seedream_v5_5 import BACKGROUNDS
from .wavespeed_api.requests.seedream_v5_pro import ASPECT_RATIOS, OUTPUT_FORMATS, RESOLUTIONS

# WaveSpeed accepts up to 10 input images on the Seedream V5.5 edit endpoint.
MAX_INPUT_IMAGES = 10
register_grid_caps("SeedreamV5_5EditNode", {"*": MAX_INPUT_IMAGES}, model_widget=None)

# Sent as no aspect ratio, so the API keeps the ratio of the first image.
AUTO_ASPECT = "auto"


class SeedreamV5_5EditNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.5 edit node.

    The endpoint takes no seed, so the seed input only controls ComfyUI's
    cache: a fixed seed reuses the last result, -1 generates again.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5_5EditNode",
            display_name="Bytedance Seedream V5.5 Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired modifications"),
                IO.Image.Input("images", optional=True,
                               tooltip="Images to edit as a ComfyUI IMAGE batch. Each slice is one image, up to 10. "
                                       "Takes precedence over the grid and `image_url`. Sent inline as base64, no upload."),
                IO.String.Input("image_url", default="", multiline=True,
                                tooltip="Image URL(s) to edit, one per line or comma separated. Up to 10. "
                                        "Ignored when `images` is connected or the grid holds images."),
                IO.Combo.Input("aspect_ratio", options=[AUTO_ASPECT] + ASPECT_RATIOS, default=AUTO_ASPECT,
                               tooltip="Aspect ratio of the result. auto follows the first image."),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. 1k and 1.5k cost $0.02, 2k costs $0.035, "
                                       "plus $0.008 for every input image, including the first."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("output_format", options=OUTPUT_FORMATS, default="png", optional=True,
                               tooltip="Output image format. A transparent background always returns png."),
                IO.Combo.Input("background", options=BACKGROUNDS, default="auto", optional=True,
                               tooltip="Background of the result. transparent always returns a png with alpha."),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Cache control only, not sent to the API. -1 generates again every run."),
                grid_input(),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.Mask.Output("mask", tooltip="The result's alpha, 1 where opaque, 0 where transparent"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    def validate_inputs(cls, grid_images="[]"):
        return validate_grid(grid_images)

    @classmethod
    async def execute(cls, prompt, image_url="", images=None, aspect_ratio=AUTO_ASPECT, resolution="1k",
                      client=None, output_format="png", background="auto", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import NO_INPUT_IMAGE, imageurl2tensor_rgba, input_image_list
        from .wavespeed_api.requests.seedream_v5_5_edit import SeedreamV5_5Edit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        images_param = input_image_list(images, image_url, grid_cap_for("SeedreamV5_5EditNode", None), "Seedream",
                                        grid=kwargs.get("grid_images"))
        if images_param is None:
            raise ValueError(NO_INPUT_IMAGE)

        request = SeedreamV5_5Edit(
            prompt=prompt,
            images=images_param,
            aspect_ratio=None if aspect_ratio == AUTO_ASPECT else aspect_ratio,
            resolution=resolution,
            output_format=output_format,
            background=background,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result, masks = imageurl2tensor_rgba(image_urls)
        return IO.NodeOutput(result, masks)
