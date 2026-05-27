# ABOUTME: Lightricks LTX 2 Pro text-to-video generation node.
# ABOUTME: Short-form video with optional audio from a text prompt.

from comfy_api.latest import IO


class Ltx2ProTextToVideoNode(IO.ComfyNode):
    """Lightricks LTX 2 Pro Text-to-Video."""

    DURATIONS = ["6", "8", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Ltx2ProTextToVideoNode",
            display_name="Lightricks LTX 2 Pro Text-to-Video",
            category="ERPK/WaveSpeedAI",
            description="Generate short-form video from a text prompt using Lightricks LTX 2 Pro.",
            inputs=[
                IO.String.Input(
                    "prompt", multiline=True, default="",
                    tooltip="Text description of the video to generate (max 5000 chars).",
                ),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input(
                    "client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "duration", optional=True,
                    options=cls.DURATIONS, default="6",
                    tooltip="Output duration in seconds. LTX 2 Pro supports 6, 8, or 10.",
                ),
                IO.Boolean.Input(
                    "generate_audio", optional=True, default=True,
                    tooltip="Generate synchronized audio with the video.",
                ),
            ],
            outputs=[IO.String.Output("video_url")],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    async def execute(cls, prompt="", client=None, duration="6", generate_audio=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.ltx_2_pro_text_to_video import Ltx2ProTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not prompt:
            raise ValueError("Prompt is required")

        request = Ltx2ProTextToVideo(
            prompt=prompt,
            duration=int(duration),
            generate_audio=generate_audio,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URL in the generated result")

        return IO.NodeOutput(video_urls[0])
