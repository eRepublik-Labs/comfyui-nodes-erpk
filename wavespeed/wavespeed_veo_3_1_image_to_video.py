# ABOUTME: Google Veo 3.1 image-to-video generation node billed via WaveSpeed.
# ABOUTME: Distinct from gemini/veo_nodes.py which uses Google's direct API.

from comfy_api.latest import IO


class WaveSpeedVeo31ImageToVideoNode(IO.ComfyNode):
    """
    WaveSpeed Veo 3.1 Image-to-Video Node

    Generates videos from an input image plus text prompt using Google's
    Veo 3.1 model, billed through WaveSpeed. Produces video with
    synchronized native audio.
    """

    ASPECT_RATIOS = ["16:9", "9:16"]
    RESOLUTIONS = ["720p", "1080p"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="WaveSpeedVeo31ImageToVideoNode",
            display_name="WaveSpeed Veo 3.1 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            description="Generate video from an image and prompt using Veo 3.1 (billed via WaveSpeed).",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the motion/scene."),
                IO.String.Input("image",
                                tooltip="URL of the input image (JPEG/PNG/WEBP). Use WaveSpeed Upload Image node to obtain a URL."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.Int.Input("duration", optional=True, default=8, min=4, max=8, step=1,
                             tooltip="Video duration in seconds (4, 6, or 8)."),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS, default="16:9",
                               tooltip="Video aspect ratio (16:9 landscape or 9:16 portrait)."),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS, default="1080p",
                               tooltip="Output resolution (720p or 1080p)."),
                IO.Boolean.Input("audio_enabled", optional=True, default=True,
                                 tooltip="Generate synchronized native audio (Veo 3.1 feature)."),
                IO.String.Input("last_image", optional=True, default="",
                                tooltip="Optional end-frame image URL for interpolation."),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from the video (optional)."),
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
    def execute(cls, prompt="", image="", client=None, seed=-1, duration=8,
                aspect_ratio="16:9", resolution="1080p", audio_enabled=True,
                last_image="", negative_prompt="", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.wavespeed_veo_3_1_image_to_video import (
            WaveSpeedVeo31ImageToVideo,
        )

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image is None or image == "":
            raise ValueError("Image URL is required")

        request = WaveSpeedVeo31ImageToVideo(
            prompt=prompt,
            image=image,
            last_image=last_image if last_image else None,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            generate_audio=audio_enabled,
            negative_prompt=negative_prompt if negative_prompt else None,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URL in the generated result")

        return IO.NodeOutput(video_urls[0])
