# ABOUTME: Lightricks LTX 2 Pro image-to-video generation node.
# ABOUTME: Animates a source image into short-form video with optional audio.

from comfy_api.latest import IO


class Ltx2ProImageToVideoNode(IO.ComfyNode):
    """Lightricks LTX 2 Pro Image-to-Video."""

    DURATIONS = ["6", "8", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Ltx2ProImageToVideoNode",
            display_name="Lightricks LTX 2 Pro Image-to-Video",
            category="ERPK/WaveSpeedAI",
            description="Animate a source image into short-form video using Lightricks LTX 2 Pro.",
            inputs=[
                IO.String.Input(
                    "image", default="",
                    tooltip="Source image URL to animate.",
                ),
                IO.String.Input(
                    "prompt", multiline=True, default="",
                    tooltip="Text description guiding the animation (max 5000 chars).",
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
                IO.Int.Input(
                    "seed", optional=True, default=-1, min=-1, max=2147483647,
                    control_after_generate="randomize",
                    tooltip="Cache control: randomize re-runs generation each queue; a fixed value reuses the cached video. This endpoint has no seed parameter, so it is not sent to the API.",
                ),
            ],
            outputs=[IO.String.Output("video_url")],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, image="", prompt="", client=None, duration="6", generate_audio=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.ltx_2_pro_image_to_video import Ltx2ProImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if not image:
            raise ValueError("Image URL is required")
        if not prompt:
            raise ValueError("Prompt is required")

        request = Ltx2ProImageToVideo(
            image=image,
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
