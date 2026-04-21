# ABOUTME: Kling 3.0 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard and Pro variants of the Kling 3.0 model.

from comfy_api.latest import IO


class KlingV3ImageToVideoNode(IO.ComfyNode):
    """
    Kling 3.0 Image-to-Video Generator Node

    Animates a starting image into a short video using Kling 3.0 models.
    """

    MODELS = ["Kling 3.0", "Kling 3.0 Pro"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV3ImageToVideoNode",
            display_name="Kling 3.0 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 3.0",
                               tooltip="Model variant: Kling 3.0 (standard) or Kling 3.0 Pro (higher quality)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired motion/scene"),
                IO.String.Input("image", default="",
                                tooltip="URL of the starting image (use WaveSpeed Upload Image to produce one)"),
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
    def execute(cls, model="Kling 3.0", prompt="", image="", client=None,
                duration=5, aspect_ratio="16:9", seed=-1, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_v3_image_to_video import KlingV3ImageToVideo
        from .wavespeed_api.requests.kling_v3_pro_image_to_video import KlingV3ProImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        if image is None or image == "":
            raise ValueError("Image URL is required")

        request_cls = KlingV3ProImageToVideo if model == "Kling 3.0 Pro" else KlingV3ImageToVideo

        request = request_cls(
            prompt=prompt,
            image=image,
            duration=duration,
            aspect_ratio=aspect_ratio,
            seed=seed,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
