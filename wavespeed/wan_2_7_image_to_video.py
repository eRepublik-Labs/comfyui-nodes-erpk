# ABOUTME: Alibaba WAN 2.7 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Animates a source image into a video clip; returns a video_url string.

from comfy_api.latest import IO


class Wan27ImageToVideoNode(IO.ComfyNode):
    """
    Alibaba WAN 2.7 Image-to-Video Generator Node

    Animates a source image into a video clip via the WaveSpeed AI WAN 2.7 endpoint.
    Accepts an optional end-frame image for smooth transitions.
    Returns a URL to the generated video.
    """

    RESOLUTIONS = ["720p", "1080p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Wan27ImageToVideoNode",
            display_name="Alibaba WAN 2.7 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate"),
                IO.String.Input("image", default="",
                                tooltip="Source image URL (first frame of the video)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("last_image", optional=True, default="",
                                tooltip="Optional end-frame image URL for smooth transition"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from the generated video"),
                IO.String.Input("audio", optional=True, default="",
                                tooltip="Optional audio URL used to guide generation"),
                IO.Int.Input("duration", optional=True, default=5, min=2, max=15, step=1,
                             tooltip="Clip length in seconds (2-15)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Output resolution"),
                IO.Boolean.Input("enable_prompt_expansion", optional=True, default=False,
                                 tooltip="Automatically enrich the prompt before generation"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt="", image="", client=None, last_image="", negative_prompt="",
                audio="", duration=5, resolution="720p",
                enable_prompt_expansion=False, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.wan_2_7_image_to_video import Wan27ImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image is None or image == "":
            raise ValueError("Image URL is required")

        request = Wan27ImageToVideo(
            prompt=prompt,
            image=image,
            last_image=last_image or None,
            audio=audio or None,
            negative_prompt=negative_prompt or None,
            duration=duration,
            resolution=resolution,
            enable_prompt_expansion=enable_prompt_expansion,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        return IO.NodeOutput(response.get("outputs", [""])[0])
