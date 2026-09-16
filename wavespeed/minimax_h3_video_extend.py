# ABOUTME: MiniMax H3 video-extend node for WaveSpeed AI.
# ABOUTME: Appends a new segment after a clip's last frame; chains off any node's video_url output.

from comfy_api.latest import IO


class MinimaxH3VideoExtendNode(IO.ComfyNode):
    """
    MiniMax H3 Video Extend Node

    Generates a new segment from the input video's last frame and appends it
    to the original, optionally interpolating toward a target last image.
    Takes the source clip as a URL, so it chains directly off the video_url
    output of any video node in this package.
    Returns a URL string suitable for the Preview Anything utility.
    """

    RESOLUTIONS = ["480p", "540p", "768p", "1080p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3VideoExtendNode",
            display_name="MiniMax H3 Video Extend",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="How the video continues: motion, scene, soundtrack. Add an 'Audio:' line to steer the sound."),
                IO.String.Input("video_url", optional=True, default="",
                                tooltip="Source video URL. Connect the video_url output of any video node in this package. The new segment starts from its last frame."),
                IO.Image.Input("last_frame", optional=True,
                               tooltip="Target end frame for the new segment as a ComfyUI IMAGE tensor. Takes precedence over `last_frame_url`."),
                IO.String.Input("last_frame_url", optional=True, default="",
                                tooltip="Target end frame image URL. Fallback when `last_frame` is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Length of the new segment in seconds (3-15), not the total output."),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="480p",
                               tooltip="Resolution of the new segment. Roughly $0.04/s at 480p, $0.06/s at 540p, $0.08/s at 768p and $0.16/s at 1080p."),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same video and lets ComfyUI reuse the cached result; -1 generates a new one each queue."),
                IO.Video.Input("video", optional=True,
                               tooltip="Source clip as a ComfyUI VIDEO. Uploaded to WaveSpeed and used instead of `video_url` when connected."),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
            not_idempotent=True,
        )


    @staticmethod
    async def _media_url(client, media, to_bytes):
        """Upload a connected VIDEO or AUDIO and return its URL."""
        from .wavespeed_api.client import WaveSpeedClient

        filename, content_type, data = to_bytes(media)
        uploader = WaveSpeedClient(client["api_key"])
        return await uploader.upload_media(filename, content_type, data)

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt="", video_url="", last_frame=None, last_frame_url="",
                client=None, duration=5, resolution="480p", seed=-1, video=None, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import image_to_data_uri
        from .wavespeed_api.requests.minimax_h3_video_extend import MinimaxH3VideoExtend

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if video is not None:
            from .wavespeed_api.media import video_to_bytes
            video_value = await cls._media_url(client, video, video_to_bytes)
        else:
            video_value = video_url
        if not video_value:
            raise ValueError("A source video is required, as either a VIDEO input or a URL")

        last_value = image_to_data_uri(last_frame) if last_frame is not None else (last_frame_url or None)

        request = MinimaxH3VideoExtend(
            prompt=prompt,
            video=video_value,
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
