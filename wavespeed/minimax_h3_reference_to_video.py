# ABOUTME: MiniMax H3 reference-to-video generation node for WaveSpeed AI.
# ABOUTME: Guides generation with up to 9 reference images, 3 videos and 3 audios.

from comfy_api.latest import IO


class MinimaxH3ReferenceToVideoNode(IO.ComfyNode):
    """
    MiniMax H3 Reference-to-Video Generator Node

    Generates video guided by reference images, videos and audio.
    The prompt must cite each reference with bracket tags such as `<Picture 1>`,
    `<Video 1>` and `<Audio 1>`; a reference mentioned only in plain text is
    ignored by the model.
    Returns a URL string suitable for the Preview Anything utility.
    """

    ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"]
    RESOLUTIONS = ["480p", "768p"]
    MAX_IMAGES = 9
    MAX_VIDEOS = 3
    MAX_AUDIOS = 3

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
            node_id="MinimaxH3ReferenceToVideoNode",
            display_name="MiniMax H3 Reference-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Cite every reference with bracket tags: <Picture 1>-<Picture 9>, <Video 1>-<Video 3>, <Audio 1>-<Audio 3>. A reference mentioned only in plain text is ignored. Add an 'Audio:' line to steer the soundtrack."),
                IO.String.Input("reference_images", optional=True, default="",
                                tooltip="Reference image URL(s), cited as <Picture N>. Single URL or list. Up to 9. Billed $0.02 each. Ignored when `reference_images_tensor` is connected."),
                IO.String.Input("reference_videos", optional=True, default="",
                                tooltip="Reference video URL(s), cited as <Video N>. Up to 3, sharing a 15s budget. Supplying any forces 480p output. Billed $0.05 per second."),
                IO.String.Input("reference_audios", optional=True, default="",
                                tooltip="Reference audio URL(s), cited as <Audio N>. Up to 3, each trimmed to 15s. Billed $0.02 each. A reference video's own audio fills the earliest <Audio> slots first."),
                IO.Image.Input("reference_images_tensor", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch (B,H,W,C). Each batch slice becomes one reference, capped at 9. Takes precedence over `reference_images` URLs when connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds (3-15). Snaps to the model's frame grid, so a 5s request lands near 5.2s."),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="16:9",
                               tooltip="Video aspect ratio"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="480p",
                               tooltip="Video resolution. Roughly $0.05/s at 480p and $0.125/s at 768p, before reference charges. Reference videos force 480p."),
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
    async def execute(cls, prompt="", reference_images="", reference_videos="",
                reference_audios="", reference_images_tensor=None, client=None,
                duration=5, aspect_ratio="16:9", resolution="480p", seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import images_to_data_uris
        from .wavespeed_api.requests.minimax_h3_reference_to_video import MinimaxH3ReferenceToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if reference_images_tensor is not None:
            images_value = images_to_data_uris(reference_images_tensor, max_count=cls.MAX_IMAGES)
        else:
            images_value = cls._normalize_url_list(reference_images, cls.MAX_IMAGES)

        videos_value = cls._normalize_url_list(reference_videos, cls.MAX_VIDEOS)

        if not images_value and not videos_value:
            raise ValueError("At least one reference image or reference video is required")

        request = MinimaxH3ReferenceToVideo(
            prompt=prompt,
            reference_images=images_value,
            reference_videos=videos_value,
            reference_audios=cls._normalize_url_list(reference_audios, cls.MAX_AUDIOS),
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            duration=duration,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=1200)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
