# ABOUTME: MiniMax H3 video-edit node for WaveSpeed AI.
# ABOUTME: Rewrites an existing clip from a prompt; chains off any node's video_url output.

from comfy_api.latest import IO


class MinimaxH3VideoEditNode(IO.ComfyNode):
    """
    MiniMax H3 Video Edit Node

    Rewrites lighting, style, environment or specific elements of an input
    video while the video drives identity, composition and motion. Takes the
    source clip as a URL, so it chains directly off the video_url output of
    any video node in this package. Billing counts input plus output seconds.
    Returns a URL string suitable for the Preview Anything utility.
    """

    ASPECT_RATIOS = ["auto"] + ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"]
    RESOLUTIONS = ["480p", "540p", "768p", "1080p"]
    MAX_IMAGES = 9
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

    @staticmethod
    def _duration_or_none(duration):
        """Below the endpoint's 3s floor means follow the input clip, which it does when duration is omitted."""
        return None if not duration or duration < 3 else duration

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3VideoEditNode",
            display_name="MiniMax H3 Video Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="What to change: lighting, weather, style, environment or specific elements. Cite references as <Picture N> and <Audio N>."),
                IO.String.Input("video_url", optional=True, default="",
                                tooltip="Source video URL. Connect the video_url output of any video node in this package. Input seconds are billed alongside output seconds, each capped at 15."),
                IO.String.Input("reference_images", optional=True, default="",
                                tooltip="Reference image URL(s), cited as <Picture N>. Up to 9, about $0.02 each. Ignored when `reference_images_tensor` is connected."),
                IO.String.Input("reference_audios", optional=True, default="",
                                tooltip="Reference audio URL(s), cited as <Audio N>. Up to 3, about $0.02 each."),
                IO.Image.Input("reference_images_tensor", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch (B,H,W,C), capped at 9. Takes precedence over `reference_images` URLs."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="480p",
                               tooltip="Output resolution. Roughly $0.05 per counted second at 480p, $0.075 at 540p, $0.125 at 768p and $0.25 at 1080p; counted seconds are input plus output."),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="auto",
                               tooltip="Output aspect ratio. auto adapts to the input video."),
                IO.Int.Input("duration", optional=True, default=0, min=0, max=15,
                             tooltip="Output duration in seconds (3-15). Below 3 follows the input clip."),
                IO.Boolean.Input("generate_audio", optional=True, default=True,
                                 tooltip="Generate a new soundtrack. Off keeps the input video's audio track."),
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
    async def execute(cls, prompt="", video_url="", reference_images="", reference_audios="",
                reference_images_tensor=None, client=None, resolution="480p", aspect_ratio="auto",
                duration=0, generate_audio=True, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import images_to_data_uris
        from .wavespeed_api.requests.minimax_h3_video_edit import MinimaxH3VideoEdit

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")
        if not video_url:
            raise ValueError("A source video URL is required")

        if reference_images_tensor is not None:
            images_value = images_to_data_uris(reference_images_tensor, max_count=cls.MAX_IMAGES)
        else:
            images_value = cls._normalize_url_list(reference_images, cls.MAX_IMAGES)

        request = MinimaxH3VideoEdit(
            prompt=prompt,
            video=video_url,
            reference_images=images_value,
            reference_audios=cls._normalize_url_list(reference_audios, cls.MAX_AUDIOS),
            resolution=resolution,
            aspect_ratio=None if aspect_ratio in ("auto", "") else aspect_ratio,
            duration=cls._duration_or_none(duration),
            generate_audio=generate_audio,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=1800)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
