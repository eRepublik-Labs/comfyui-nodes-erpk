# ABOUTME: WaveSpeed LTX 2.3 text-to-video generation node.
# ABOUTME: Configurable resolution (480p/720p/1080p), aspect ratio, and duration 5-20s.

from comfy_api.latest import IO


class Ltx23TextToVideoNode(IO.ComfyNode):
    """WaveSpeed LTX 2.3 Text-to-Video."""

    RESOLUTIONS = ["480p", "720p", "1080p"]
    ASPECT_RATIOS = ["16:9", "9:16"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Ltx23TextToVideoNode",
            display_name="WaveSpeed LTX 2.3 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            description="Generate video from a text prompt using WaveSpeed's LTX 2.3 model.",
            inputs=[
                IO.String.Input(
                    "prompt", multiline=True, default="",
                    tooltip="Text description of the video to generate.",
                ),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input(
                    "client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "resolution", optional=True,
                    options=cls.RESOLUTIONS, default="720p",
                    tooltip="Output resolution.",
                ),
                IO.Combo.Input(
                    "aspect_ratio", optional=True,
                    options=cls.ASPECT_RATIOS, default="16:9",
                    tooltip="Output aspect ratio.",
                ),
                IO.Int.Input(
                    "duration", optional=True,
                    default=5, min=5, max=20, step=1,
                    tooltip="Video duration in seconds (5-20).",
                ),
                IO.Int.Input(
                    "seed", optional=True,
                    default=-1, min=-1, max=2147483647,
                    control_after_generate="randomize",
                    tooltip="Random seed for reproducibility (-1 for random).",
                ),
            ],
            outputs=[IO.String.Output("video_url")],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    def execute(cls, prompt="", client=None, resolution="720p", aspect_ratio="16:9",
                duration=5, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.ltx_2_3_text_to_video import Ltx23TextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt:
            raise ValueError("Prompt is required")

        request = Ltx23TextToVideo(
            prompt=prompt,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            duration=duration,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URL in the generated result")

        return IO.NodeOutput(video_urls[0])
