# ABOUTME: Kling O3 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard and Pro variants of the Kling O3 model.

from comfy_api.latest import IO


class KlingO3TextToVideoNode(IO.ComfyNode):
    """
    Kling O3 Text-to-Video Generator Node

    Generates a short video from a text prompt using Kling O3 models.
    """

    MODELS = ["Kling O3", "Kling O3 Pro"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingO3TextToVideoNode",
            display_name="Kling O3 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling O3",
                               tooltip="Model variant: Kling O3 (standard) or Kling O3 Pro (higher quality)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=10,
                             tooltip="Video duration in seconds (3 to 10)"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Aspect ratio of the output video"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
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
    def execute(cls, model="Kling O3", prompt="", client=None,
                duration=5, aspect_ratio="16:9", seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_o3_text_to_video import KlingO3TextToVideo
        from .wavespeed_api.requests.kling_o3_pro_text_to_video import KlingO3ProTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        request_cls = KlingO3ProTextToVideo if model == "Kling O3 Pro" else KlingO3TextToVideo

        request = request_cls(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
