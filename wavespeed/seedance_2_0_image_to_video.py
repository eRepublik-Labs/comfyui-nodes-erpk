# ABOUTME: Seedance 2.0 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Animates a source image via three Seedance 2.0 model tiers.

from comfy_api.latest import IO


class Seedance20ImageToVideoNode(IO.ComfyNode):
    """
    Seedance 2.0 Image-to-Video Generator Node

    Animates a source image into a short video clip guided by a text prompt.
    Supports four endpoint variants (standard, Turbo, Fast, Fast Turbo) routed to
    distinct WaveSpeed paths. Accepts an optional end-frame image for video continuation.
    Returns a URL string suitable for the Preview Anything utility.
    """

    MODELS = ["Seedance 2.0", "Seedance 2.0 Turbo", "Seedance 2.0 Fast", "Seedance 2.0 Fast Turbo"]
    ASPECT_RATIOS = ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9"]
    RESOLUTIONS = ["480p", "720p", "1080p"]

    @classmethod
    def _request_class_for(cls, model):
        from .wavespeed_api.requests.seedance_2_0_image_to_video import Seedance20ImageToVideo
        from .wavespeed_api.requests.seedance_2_0_image_to_video_fast import Seedance20ImageToVideoFast
        from .wavespeed_api.requests.seedance_2_0_image_to_video_turbo import Seedance20ImageToVideoTurbo
        from .wavespeed_api.requests.seedance_2_0_image_to_video_fast_turbo import Seedance20ImageToVideoFastTurbo

        if model == "Seedance 2.0 Fast Turbo":
            return Seedance20ImageToVideoFastTurbo
        if model == "Seedance 2.0 Fast":
            return Seedance20ImageToVideoFast
        if model == "Seedance 2.0 Turbo":
            return Seedance20ImageToVideoTurbo
        return Seedance20ImageToVideo

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance20ImageToVideoNode",
            display_name="Bytedance Seedance 2.0 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Seedance 2.0",
                               tooltip="Model variant: standard, Turbo (faster, 720p/1080p only), Fast (cheaper), or Fast Turbo (Fast family + turbo, 720p/1080p only)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired motion"),
                IO.String.Input("start_frame",
                                tooltip="Start frame image URL to guide the video generation"),
                IO.String.Input("end_frame", optional=True, default="",
                                tooltip="End frame image URL for video continuation (optional)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=4, max=15,
                             tooltip="Video duration in seconds (4-15)"),
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
                IO.Boolean.Input("enable_web_search", optional=True, default=False,
                                 tooltip="Enable web search for real-time information during generation"),
                IO.Boolean.Input("generate_audio", optional=True, default=True,
                                 tooltip="Generate native audio synchronized with the output video"),
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
    def execute(cls, model="Seedance 2.0", prompt="", start_frame="",
                end_frame="", client=None, duration=5, aspect_ratio="16:9", resolution="720p", seed=-1,
                enable_web_search=False, generate_audio=True,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if start_frame is None or start_frame == "":
            raise ValueError("Start frame image must be provided")

        request_cls = cls._request_class_for(model)

        request = request_cls(
            prompt=prompt,
            image=start_frame,
            last_image=end_frame or None,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            enable_web_search=enable_web_search,
            generate_audio=generate_audio,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
