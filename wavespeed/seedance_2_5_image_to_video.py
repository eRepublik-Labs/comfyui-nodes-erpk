# ABOUTME: Seedance 2.5 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports the standard, Turbo and Spicy tiers via a single Combo input.

from comfy_api.latest import IO


class Seedance25ImageToVideoNode(IO.ComfyNode):
    """
    Seedance 2.5 Image-to-Video Generator Node

    Animates a start image using Bytedance Seedance 2.5, optionally steering
    toward a supplied ending frame.
    Output aspect ratio follows the input image.
    Returns a URL string suitable for the Preview Anything utility.
    """

    MODELS = ["Seedance 2.5", "Seedance 2.5 Turbo", "Seedance 2.5 Spicy"]
    RESOLUTIONS = ["480p", "720p", "1080p", "4k"]

    @classmethod
    def _request_class_for(cls, model):
        from .wavespeed_api.requests.seedance_2_5_image_to_video import Seedance25ImageToVideo
        from .wavespeed_api.requests.seedance_2_5_image_to_video_turbo import Seedance25ImageToVideoTurbo
        from .wavespeed_api.requests.seedance_2_5_image_to_video_spicy import Seedance25ImageToVideoSpicy

        if model == "Seedance 2.5 Turbo":
            return Seedance25ImageToVideoTurbo
        if model == "Seedance 2.5 Spicy":
            return Seedance25ImageToVideoSpicy
        return Seedance25ImageToVideo

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance25ImageToVideoNode",
            display_name="Bytedance Seedance 2.5 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the motion to generate"),
                IO.Image.Input("start_frame", optional=True,
                               tooltip="Start frame as a ComfyUI IMAGE tensor. Preferred input, takes precedence over `start_frame_url` when connected. Sent to WaveSpeed as a base64 data URI."),
                IO.String.Input("start_frame_url", optional=True, default="",
                                tooltip="Start frame image URL. Fallback when `start_frame` IMAGE input is not connected."),
                IO.Image.Input("last_frame", optional=True,
                               tooltip="Ending frame as a ComfyUI IMAGE tensor. Steers the clip toward this image. Takes precedence over `last_frame_url` when connected."),
                IO.String.Input("last_frame_url", optional=True, default="",
                                tooltip="Ending frame image URL. Fallback when `last_frame` IMAGE input is not connected."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Seedance 2.5",
                               tooltip="Model tier: standard, Turbo (faster), or Spicy (tuned for high-volume generation)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=4, max=30,
                             tooltip="Video duration in seconds (4-30)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Video resolution. Cost per second rises steeply: roughly $0.18/s at 480p to $1.80/s at 4k."),
                IO.Boolean.Input("generate_audio", optional=True, default=True,
                                 tooltip="Generate native audio synchronized with the output video"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Cache control only. Seedance 2.5 takes no API seed, so this is never sent. A fixed seed reuses the video you already paid for; -1 generates again on every queue."),
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
    async def execute(cls, model="Seedance 2.5", prompt="",
                start_frame=None, start_frame_url="",
                last_frame=None, last_frame_url="",
                client=None, duration=5, resolution="720p",
                generate_audio=True, seed=-1,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import image_to_data_uri

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        start_value = image_to_data_uri(start_frame) if start_frame is not None else (start_frame_url or None)
        if not start_value:
            raise ValueError("Start frame must be provided as either an IMAGE tensor or a URL")

        last_value = image_to_data_uri(last_frame) if last_frame is not None else (last_frame_url or None)

        request_cls = cls._request_class_for(model)

        request = request_cls(
            prompt=prompt,
            image=start_value,
            last_image=last_value,
            duration=duration,
            resolution=resolution,
            generate_audio=generate_audio,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=1800)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
