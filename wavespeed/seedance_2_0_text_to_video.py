# ABOUTME: Seedance 2.0 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard, Fast, and Turbo model tiers via a single Combo input.

from comfy_api.latest import IO


class Seedance20TextToVideoNode(IO.ComfyNode):
    """
    Seedance 2.0 Text-to-Video Generator Node

    Generates a short video clip from a text prompt using Bytedance Seedance 2.0.
    Supports three tiers — standard, Fast, Turbo — routed to distinct WaveSpeed endpoints.
    Accepts optional reference images, videos, and audios (up to 4 of each) for
    style and composition guidance.
    Returns a URL string suitable for the Preview Anything utility.
    """

    MODELS = ["Seedance 2.0", "Seedance 2.0 Turbo", "Seedance 2.0 Fast", "Seedance 2.0 Fast Turbo"]
    ASPECT_RATIOS = ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9"]
    RESOLUTIONS = ["480p", "720p", "1080p"]

    @classmethod
    def _request_class_for(cls, model):
        from .wavespeed_api.requests.seedance_2_0_text_to_video import Seedance20TextToVideo
        from .wavespeed_api.requests.seedance_2_0_text_to_video_fast import Seedance20TextToVideoFast
        from .wavespeed_api.requests.seedance_2_0_text_to_video_turbo import Seedance20TextToVideoTurbo
        from .wavespeed_api.requests.seedance_2_0_text_to_video_fast_turbo import Seedance20TextToVideoFastTurbo

        if model == "Seedance 2.0 Fast Turbo":
            return Seedance20TextToVideoFastTurbo
        if model == "Seedance 2.0 Fast":
            return Seedance20TextToVideoFast
        if model == "Seedance 2.0 Turbo":
            return Seedance20TextToVideoTurbo
        return Seedance20TextToVideo

    @staticmethod
    def _normalize_url_list(value):
        if value is None or value == "":
            return None
        if isinstance(value, list):
            urls = [u for u in value if u]
        else:
            urls = [value]
        urls = urls[:4]
        return urls or None

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance20TextToVideoNode",
            display_name="Bytedance Seedance 2.0 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Seedance 2.0",
                               tooltip="Model variant: standard, Turbo (faster, 720p/1080p only), Fast (cheaper), or Fast Turbo (Fast family + turbo, 720p/1080p only)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate"),
                IO.String.Input("reference_images", optional=True, default="",
                                tooltip="Reference image URL(s) for style/character/composition guidance. Single URL or list from WaveSpeed Upload Image. Up to 4 images. Ignored when `reference_images_tensor` is connected."),
                IO.String.Input("reference_videos", optional=True, default="",
                                tooltip="Reference video URL(s) for motion/style guidance. Single URL or list. Up to 4 videos; total duration should not exceed 15s."),
                IO.String.Input("reference_audios", optional=True, default="",
                                tooltip="Reference audio URL(s) for audio style guidance. Single URL or list. Up to 4 audios; total duration should not exceed 15s."),
                IO.Image.Input("reference_images_tensor", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch (B,H,W,C). Each batch slice becomes one reference, capped at 4. Takes precedence over `reference_images` URLs when connected. Sent as base64 data URIs."),
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
    def execute(cls, model="Seedance 2.0", prompt="",
                reference_images="", reference_videos="", reference_audios="",
                reference_images_tensor=None,
                client=None, duration=5, aspect_ratio="16:9", resolution="720p", seed=-1,
                enable_web_search=False, generate_audio=True,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import images_to_data_uris

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if reference_images_tensor is not None:
            reference_images_value = images_to_data_uris(reference_images_tensor, max_count=4)
        else:
            reference_images_value = cls._normalize_url_list(reference_images)

        request_cls = cls._request_class_for(model)

        request = request_cls(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            reference_images=reference_images_value,
            reference_videos=cls._normalize_url_list(reference_videos),
            reference_audios=cls._normalize_url_list(reference_audios),
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
