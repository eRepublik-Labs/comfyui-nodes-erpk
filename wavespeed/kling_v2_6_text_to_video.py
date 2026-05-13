# ABOUTME: Kling 2.6 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports Std and Pro variants of the Kling 2.6 model.

from comfy_api.latest import IO


class KlingV2_6TextToVideoNode(IO.ComfyNode):
    """
    Kling 2.6 Text-to-Video Generator Node

    Generates a short video from a text prompt using Kling 2.6 models.
    The Pro variant additionally supports cfg_scale and joint audio-video
    co-generation.
    """

    MODELS = ["Kling 2.6", "Kling 2.6 Pro"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    DURATIONS = ["5", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV2_6TextToVideoNode",
            display_name="Kling 2.6 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 2.6",
                               tooltip="Model variant: Kling 2.6 (Std) or Kling 2.6 Pro (cfg_scale, sound)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired scene, motion, and audio"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from visuals and audio"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Aspect ratio of the output video"),
                IO.Combo.Input("duration", optional=True, options=cls.DURATIONS,
                               default="5",
                               tooltip="Video duration in seconds (5 or 10)"),
                IO.Float.Input("cfg_scale", optional=True, default=0.5, min=0.0, max=1.0, step=0.01,
                               tooltip="Pro only: guidance strength (0.0-1.0); higher follows the prompt more closely"),
                IO.Boolean.Input("sound", optional=True, default=True,
                                 tooltip="Pro only: enable joint audio-video generation (doubles cost)"),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def execute(cls, model="Kling 2.6", prompt="", client=None,
                negative_prompt="", aspect_ratio="16:9", duration="5",
                cfg_scale=0.5, sound=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_v2_6_std_text_to_video import KlingV2_6StdTextToVideo
        from .wavespeed_api.requests.kling_v2_6_pro_text_to_video import KlingV2_6ProTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        duration_int = int(duration)

        if model == "Kling 2.6 Pro":
            request = KlingV2_6ProTextToVideo(
                prompt=prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                cfg_scale=cfg_scale,
                sound=sound,
                duration=duration_int,
            )
        else:
            request = KlingV2_6StdTextToVideo(
                prompt=prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                duration=duration_int,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
