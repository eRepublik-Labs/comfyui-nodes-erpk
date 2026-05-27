# ABOUTME: Kling 2.5 Turbo text-to-video generation node for WaveSpeed AI.
# ABOUTME: Wraps the Pro text-to-video endpoint (the only tier WaveSpeed offers for t2v).

from comfy_api.latest import IO


class KlingV2_5TurboTextToVideoNode(IO.ComfyNode):
    """
    Kling 2.5 Turbo Text-to-Video Generator Node

    Generates a short video from a text prompt using the Kling 2.5 Turbo Pro
    model. WaveSpeed only exposes a Pro tier for this modality; the Combo is
    kept single-option so the UX matches the rest of the Kling node family.
    """

    MODELS = ["Kling 2.5 Turbo Pro"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    DURATIONS = ["5", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV2_5TurboTextToVideoNode",
            display_name="Kling 2.5 Turbo Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 2.5 Turbo Pro",
                               tooltip="Model variant (only Pro is offered for text-to-video)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired scene and motion (max 2500 chars)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to suppress or avoid in the generated video"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Aspect ratio of the output video"),
                IO.Float.Input("guidance_scale", optional=True, default=0.5, min=0.0, max=1.0, step=0.01,
                               tooltip="Prompt adherence; higher values reduce creative deviation (0.0-1.0)"),
                IO.Combo.Input("duration", optional=True, options=cls.DURATIONS,
                               default="5",
                               tooltip="Video duration in seconds (5 or 10)"),
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
    async def execute(cls, model="Kling 2.5 Turbo Pro", prompt="", client=None,
                negative_prompt="", aspect_ratio="16:9", guidance_scale=0.5,
                duration="5", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_v2_5_turbo_pro_text_to_video import KlingV2_5TurboProTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        duration_int = int(duration)

        request = KlingV2_5TurboProTextToVideo(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            guidance_scale=guidance_scale,
            duration=duration_int,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
