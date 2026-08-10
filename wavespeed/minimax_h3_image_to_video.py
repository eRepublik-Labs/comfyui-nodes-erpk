# ABOUTME: MiniMax H3 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Animates a first frame, optionally interpolating toward a last frame.

from comfy_api.latest import IO


class MinimaxH3ImageToVideoNode(IO.ComfyNode):
    """
    MiniMax H3 Image-to-Video Generator Node

    Animates a first-frame image with native stereo audio, optionally
    interpolating toward a supplied last frame.
    The output canvas follows the first image, so there is no aspect ratio control.
    Returns a URL string suitable for the Preview Anything utility.
    """

    RESOLUTIONS = ["480p", "768p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3ImageToVideoNode",
            display_name="MiniMax H3 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Motion and camera movement. Add an 'Audio:' line to steer the soundtrack."),
                IO.Image.Input("first_frame", optional=True,
                               tooltip="First frame as a ComfyUI IMAGE tensor. Preferred input, takes precedence over `first_frame_url` when connected. Sent as a base64 data URI."),
                IO.String.Input("first_frame_url", optional=True, default="",
                                tooltip="First frame image URL. Fallback when `first_frame` is not connected. The output canvas follows this image's aspect ratio."),
                IO.Image.Input("last_frame", optional=True,
                               tooltip="Last frame as a ComfyUI IMAGE tensor. The model interpolates between the two frames. Takes precedence over `last_frame_url`."),
                IO.String.Input("last_frame_url", optional=True, default="",
                                tooltip="Last frame image URL. Fallback when `last_frame` is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds (3-15). Snaps to the model's frame grid, so a 5s request lands near 5.2s."),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="480p",
                               tooltip="Video resolution. Roughly $0.04/s at 480p and $0.10/s at 768p."),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same video and lets ComfyUI reuse the cached result; -1 generates a new one each queue."),
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
    async def execute(cls, prompt="", first_frame=None, first_frame_url="",
                last_frame=None, last_frame_url="", client=None,
                duration=5, resolution="480p", seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import image_to_data_uri
        from .wavespeed_api.requests.minimax_h3_image_to_video import MinimaxH3ImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        first_value = image_to_data_uri(first_frame) if first_frame is not None else (first_frame_url or None)
        if not first_value:
            raise ValueError("First frame must be provided as either an IMAGE tensor or a URL")

        last_value = image_to_data_uri(last_frame) if last_frame is not None else (last_frame_url or None)

        request = MinimaxH3ImageToVideo(
            prompt=prompt,
            image=first_value,
            last_image=last_value,
            resolution=resolution,
            duration=duration,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
