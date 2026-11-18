# ABOUTME: ByteDance Seedream V5.0 Flash layer-decomposition node via WaveSpeed AI.
# ABOUTME: Splits one image into a clean base plus up to 16 RGB images and alpha masks.

from comfy_api.latest import IO
from .wavespeed_api.requests.seedream_v5_pro import RESOLUTIONS


class SeedreamV5FlashLayersNode(IO.ComfyNode):
    """
    ByteDance Seedream V5.0 Flash layer decomposition node.

    The API returns the clean base image first, then up to 16 transparent PNG
    layers. Each layer comes back at its own size, so the layers are output as
    lists: downstream nodes run once per layer.

    The endpoint takes no seed, so the seed input only controls ComfyUI's cache.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="SeedreamV5FlashLayersNode",
            display_name="Bytedance Seedream V5.0 Flash Layers",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("images", optional=True,
                               tooltip="The image to decompose, as a ComfyUI IMAGE with one image. "
                                       "Takes precedence over `image_url`. Sent inline as base64, no upload."),
                IO.String.Input("image_url", default="",
                                tooltip="URL of the image to decompose. Ignored when `images` is connected."),
                IO.String.Input("prompt", multiline=True, default="", optional=True,
                                tooltip="Optional guidance, for example which objects to separate"),
                IO.Combo.Input("resolution", options=RESOLUTIONS, default="1k",
                               tooltip="Output resolution tier. Every tier costs a flat $0.459 per run."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("seed", default=-1, min=-1, max=2**31 - 1,
                             control_after_generate="randomize",
                             tooltip="Cache control only, not sent to the API. -1 decomposes again every run."),
            ],
            outputs=[
                IO.Image.Output("base", tooltip="The image with every separated object removed"),
                IO.Image.Output("layers", is_output_list=True,
                                tooltip="One RGB image per object, each at its own size, up to 16"),
                IO.Mask.Output("masks", is_output_list=True,
                               tooltip="One alpha mask per layer, 1 where the object is, 0 where transparent"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, image_url="", images=None, prompt="", resolution="1k", client=None, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import input_image_list, load_decomposed_layers
        from .wavespeed_api.requests.seedream_v5_flash_layers import SeedreamV5FlashLayers

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        sources = input_image_list(images, image_url, max_count=10, model="Seedream")
        if sources is None:
            raise ValueError("Connect an image or enter an image URL")
        if len(sources) != 1:
            raise ValueError(f"Layer decomposition takes one image, got {len(sources)}")

        request = SeedreamV5FlashLayers(
            image=sources[0],
            prompt=prompt.strip() or None,
            resolution=resolution,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        base, layers, masks = load_decomposed_layers(response.get("outputs", []))
        return IO.NodeOutput(base, layers, masks)
