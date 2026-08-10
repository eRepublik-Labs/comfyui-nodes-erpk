# ABOUTME: Seedance 2.5 video-extend node for WaveSpeed AI.
# ABOUTME: Continues an existing clip past its final frame; chains off any node's video_url output.

from comfy_api.latest import IO


class Seedance25VideoExtendNode(IO.ComfyNode):
    """
    Seedance 2.5 Video Extend Node

    Continues an existing video clip past its final frame using Bytedance
    Seedance 2.5, reading up to the last 30 seconds of the source as context.
    Takes the source clip as a URL, so it chains directly off the video_url
    output of any video node in this package.
    Returns a URL string suitable for the Preview Anything utility.
    """

    RESOLUTIONS = ["480p", "720p", "1080p", "4k"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance25VideoExtendNode",
            display_name="Bytedance Seedance 2.5 Video Extend",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="How the video should continue: action, camera, lighting, mood"),
                IO.String.Input("video_url", optional=True, default="",
                                tooltip="Source video URL. Connect the video_url output of any video node in this package. Up to the last 30s is read as context."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=4, max=30,
                             tooltip="Length of the new segment in seconds (4-30)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Video resolution. Billing counts the context read from the source plus the new segment, roughly $0.11/s at 480p to $1.10/s at 4k."),
                IO.Boolean.Input("generate_audio", optional=True, default=True,
                                 tooltip="Generate audio for the new segment while preserving the original audio"),
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
    async def execute(cls, prompt="", video_url="", client=None,
                duration=5, resolution="720p", generate_audio=True, seed=-1,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.seedance_2_5_video_extend import Seedance25VideoExtend

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")
        if not video_url:
            raise ValueError("A source video URL is required")

        request = Seedance25VideoExtend(
            prompt=prompt,
            video=video_url,
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
