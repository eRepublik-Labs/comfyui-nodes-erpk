# ABOUTME: Alibaba WAN 2.7 video-extend generation node for WaveSpeed AI.
# ABOUTME: Extends a source video clip with a continuation prompt; returns a video_url string.

from comfy_api.latest import IO


class Wan27VideoExtendNode(IO.ComfyNode):
    """
    Alibaba WAN 2.7 Video Extend Node

    Extends an existing video clip with a continuation prompt.
    The node input is named `video_url` per ERPK node convention; it maps to the
    WAN 2.7 request's `video` field.
    Returns a URL to the extended video.
    """

    RESOLUTIONS = ["720p", "1080p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Wan27VideoExtendNode",
            display_name="Alibaba WAN 2.7 Video Extend",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the continuation"),
                IO.String.Input("video_url", default="",
                                tooltip="Source video URL to extend"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from the generated video"),
                IO.String.Input("audio", optional=True, default="",
                                tooltip="Optional audio URL used to guide generation"),
                IO.Int.Input("extend_duration", optional=True, default=5, min=2, max=15, step=1,
                             tooltip="Length of the extension in seconds (2-15)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Output resolution"),
                IO.Boolean.Input("enable_prompt_expansion", optional=True, default=False,
                                 tooltip="Automatically enrich the prompt before generation"),
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
    async def execute(cls, prompt="", video_url="", client=None, negative_prompt="",
                audio="", extend_duration=5, resolution="720p",
                enable_prompt_expansion=False, seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.wan_2_7_video_extend import Wan27VideoExtend

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if video_url is None or video_url == "":
            raise ValueError("Video URL is required")

        request = Wan27VideoExtend(
            prompt=prompt,
            video=video_url,
            audio=audio or None,
            negative_prompt=negative_prompt or None,
            duration=extend_duration,
            resolution=resolution,
            enable_prompt_expansion=enable_prompt_expansion,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        return IO.NodeOutput(response.get("outputs", [""])[0])
