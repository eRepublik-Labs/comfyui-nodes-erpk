# ABOUTME: Seedance 2.0 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard, Fast, and Turbo model tiers via a single Combo input.

from comfy_api.latest import IO


class Seedance20TextToVideoNode(IO.ComfyNode):
    """
    Seedance 2.0 Text-to-Video Generator Node

    Generates a short video clip from a text prompt using Bytedance Seedance 2.0.
    Supports three tiers — standard, Fast, Turbo — routed to distinct WaveSpeed endpoints.
    Returns a URL string suitable for the Preview Anything utility.
    """

    MODELS = ["Seedance 2.0", "Seedance 2.0 Fast", "Seedance 2.0 Turbo"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    RESOLUTIONS = ["480p", "720p", "1080p"]

    @classmethod
    def _request_class_for(cls, model):
        from .wavespeed_api.requests.seedance_2_0_text_to_video import Seedance20TextToVideo
        from .wavespeed_api.requests.seedance_2_0_text_to_video_fast import Seedance20TextToVideoFast
        from .wavespeed_api.requests.seedance_2_0_text_to_video_turbo import Seedance20TextToVideoTurbo

        if model == "Seedance 2.0 Fast":
            return Seedance20TextToVideoFast
        if model == "Seedance 2.0 Turbo":
            return Seedance20TextToVideoTurbo
        return Seedance20TextToVideo

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance20TextToVideoNode",
            display_name="Bytedance Seedance 2.0 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Seedance 2.0",
                               tooltip="Model tier: Seedance 2.0 (standard quality), Seedance 2.0 Fast, or Seedance 2.0 Turbo"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=12,
                             tooltip="Video duration in seconds (3-12)"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Video aspect ratio"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Video resolution"),
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
    def execute(cls, model="Seedance 2.0", prompt="", client=None,
                duration=5, aspect_ratio="16:9", resolution="720p", seed=-1,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request_cls = cls._request_class_for(model)

        request = request_cls(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
