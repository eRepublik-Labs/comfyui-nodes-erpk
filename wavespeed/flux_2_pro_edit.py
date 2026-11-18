# ABOUTME: FLUX.2 Pro edit node via WaveSpeed AI.
# ABOUTME: Edits from up to 3 images, taken from an IMAGE batch, the grid or URLs.

from comfy_api.latest import IO

from ..utils.image_grid import grid_cap_for, grid_input, register_grid_caps, validate_grid

# WaveSpeed accepts up to 3 input images on the FLUX.2 Pro edit endpoint.
MAX_INPUT_IMAGES = 3
register_grid_caps("Flux2ProEditNode", {"*": MAX_INPUT_IMAGES}, model_widget=None)

MIN_SIDE = 256
MAX_SIDE = 2048


def _output_size(width, height):
    """The API's `size` for these widgets, or None when both are 0."""
    if width == 0 and height == 0:
        return None
    if not (MIN_SIDE <= width <= MAX_SIDE and MIN_SIDE <= height <= MAX_SIDE):
        raise ValueError(f"Set width and height together, each {MIN_SIDE}-{MAX_SIDE}, or leave both at 0: "
                         f"got width={width}, height={height}")
    return f"{width}*{height}"


class Flux2ProEditNode(IO.ComfyNode):
    """FLUX.2 Pro edit node."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Flux2ProEditNode",
            display_name="FLUX.2 Pro Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired modifications. Costs $0.06 per image."),
                IO.Image.Input("images", optional=True,
                               tooltip="Images to edit as a ComfyUI IMAGE batch. Each slice is one image, up to 3. "
                                       "Takes precedence over the grid and `image_url`. Sent inline as base64, no upload."),
                IO.String.Input("image_url", default="", multiline=True,
                                tooltip="Image URL(s) to edit, one per line or comma separated. Up to 3. "
                                        "Ignored when `images` is connected or the grid holds images."),
                IO.Int.Input("width", default=0, min=0, max=MAX_SIDE, step=16,
                             tooltip="Output width, 256-2048. Leave width and height at 0 to let the API choose."),
                IO.Int.Input("height", default=0, min=0, max=MAX_SIDE, step=16,
                             tooltip="Output height, 256-2048. Leave width and height at 0 to let the API choose."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Sent to the API. -1 picks a random seed and generates again every run; "
                                     "a fixed value reuses the cached result."),
                grid_input(),
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
    def validate_inputs(cls, grid_images="[]"):
        return validate_grid(grid_images)

    @classmethod
    async def execute(cls, prompt, image_url="", images=None, width=0, height=0, client=None, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import NO_INPUT_IMAGE, imageurl2tensor, input_image_list
        from .wavespeed_api.requests.flux_2_pro_edit import Flux2ProEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required")

        size = _output_size(width, height)

        images_param = input_image_list(images, image_url, grid_cap_for("Flux2ProEditNode", None), "FLUX.2 Pro",
                                        grid=kwargs.get("grid_images"))
        if images_param is None:
            raise ValueError(NO_INPUT_IMAGE)

        request = Flux2ProEdit(prompt=prompt, images=images_param, size=size, seed=seed)

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        result = imageurl2tensor(image_urls)
        return IO.NodeOutput(result)
