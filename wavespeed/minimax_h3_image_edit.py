# ABOUTME: MiniMax H3 image-edit node for WaveSpeed AI.
# ABOUTME: Re-renders a subject from up to 9 reference images per a text instruction.

from comfy_api.latest import IO


class MinimaxH3ImageEditNode(IO.ComfyNode):
    """
    MiniMax H3 Image Edit Node

    Re-renders the subject of 1 to 9 reference images into a new scene,
    outfit, pose or style while preserving identity. The prompt cites each
    reference as `<Picture N>`. Connecting a LoRA stack routes the call to
    the -lora twin.
    """

    ASPECT_RATIOS = [""] + ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    RESOLUTIONS = ["1k", "2k"]
    MAX_IMAGES = 9

    @staticmethod
    def _normalize_url_list(value, max_count):
        if value is None or value == "":
            return None
        if isinstance(value, list):
            urls = [u for u in value if u]
        else:
            urls = [value]
        urls = urls[:max_count]
        return urls or None

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3ImageEditNode",
            display_name="MiniMax H3 Image Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Edit instruction. Cite references as <Picture 1> through <Picture 9>."),
                IO.Image.Input("images", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch (B,H,W,C). Each slice is one reference, capped at 9. Takes precedence over `image_urls`. Sent as base64 data URIs."),
                IO.String.Input("image_urls", optional=True, default="",
                                tooltip="Reference image URL(s), single URL or list, up to 9. Fallback when `images` is not connected. Each extra reference adds about $0.005."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="",
                               tooltip="Output aspect ratio. Leave empty to follow the first reference image."),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="1k",
                               tooltip="Output resolution. 1k is about $0.03/image, 2k about $0.09."),
                IO.Combo.Input("output_format", optional=True,
                               options=["jpeg", "png", "webp"], default="jpeg",
                               tooltip="Output image format"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same result and lets ComfyUI reuse the cached output; -1 generates a new one each queue."),
                IO.Custom("MINIMAX_H3_LORAS").Input("loras", optional=True,
                    tooltip="LoRA stack from the MiniMax H3 LoRA Stack node. When connected, the call goes to the endpoint's -lora twin (+$0.015 per image)."),
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
    async def execute(cls, prompt="", images=None, image_urls="", client=None,
                aspect_ratio="", resolution="1k", output_format="jpeg", seed=-1,
                loras=None, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, images_to_data_uris
        from .wavespeed_api.requests.minimax_h3_image_edit import MinimaxH3ImageEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if images is not None:
            images_value = images_to_data_uris(images, max_count=cls.MAX_IMAGES)
        else:
            images_value = cls._normalize_url_list(image_urls, cls.MAX_IMAGES)
        if not images_value:
            raise ValueError("At least one reference image is required, as an IMAGE batch or a URL")

        request = MinimaxH3ImageEdit(
            prompt=prompt,
            images=images_value,
            aspect_ratio=aspect_ratio or None,
            resolution=resolution,
            output_format=output_format,
            seed=seed,
            loras=loras or None,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=2, timeout=300)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        from ..utils.inline_preview import inline_preview_image
        ui = inline_preview_image(cls, images, slot=0)
        return IO.NodeOutput(images, ui=ui)
