# ABOUTME: MiniMax H3 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Produces picture and native stereo audio in a single pass at 24fps.

from comfy_api.latest import IO


class MinimaxH3TextToVideoNode(IO.ComfyNode):
    """
    MiniMax H3 Text-to-Video Generator Node

    Generates a video clip with native stereo audio from a text prompt.
    Audio is steered by an `Audio:` line inside the prompt rather than a toggle.
    Returns a URL string suitable for the Preview Anything utility.
    """

    ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"]
    RESOLUTIONS = ["480p", "768p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3TextToVideoNode",
            display_name="MiniMax H3 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Scene, action and camera movement. Add an 'Audio:' line to steer the soundtrack, for example 'Audio: rain on a tin roof, distant thunder'."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds (3-15). Snaps to the model's frame grid, so a 5s request lands near 5.2s."),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="16:9",
                               tooltip="Video aspect ratio"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="480p",
                               tooltip="Video resolution. Roughly $0.04/s at 480p and $0.10/s at 768p."),
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
    async def execute(cls, prompt="", client=None, duration=5,
                aspect_ratio="16:9", resolution="480p", seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.minimax_h3_text_to_video import MinimaxH3TextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request = MinimaxH3TextToVideo(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
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
