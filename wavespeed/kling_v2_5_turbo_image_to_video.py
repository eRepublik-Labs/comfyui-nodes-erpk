# ABOUTME: Kling 2.5 Turbo image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports Std and Pro variants of the Kling 2.5 Turbo model.

from comfy_api.latest import IO


class KlingV2_5TurboImageToVideoNode(IO.ComfyNode):
    """
    Kling 2.5 Turbo Image-to-Video Generator Node

    Animates a starting image into a short video using Kling 2.5 Turbo models.
    The Pro variant additionally supports an optional end-frame for keyframe
    interpolation.

    Image inputs accept either a ComfyUI IMAGE tensor (sent as a base64 data
    URI) or a URL string. When both are provided for the same field, the
    IMAGE input takes precedence.
    """

    MODELS = ["Kling 2.5 Turbo", "Kling 2.5 Turbo Pro"]
    DURATIONS = ["5", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV2_5TurboImageToVideoNode",
            display_name="Kling 2.5 Turbo Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("image", optional=True,
                               tooltip="Starting image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `image_url` when connected."),
                IO.Image.Input("last_image", optional=True,
                               tooltip="Pro only: end-frame image as a ComfyUI IMAGE tensor for keyframe interpolation. Preferred — takes precedence over `last_image_url` when connected."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 2.5 Turbo",
                               tooltip="Model variant: Kling 2.5 Turbo (Std) or Kling 2.5 Turbo Pro (higher quality, supports last_image)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired motion/scene (max 2500 chars)"),
                IO.String.Input("image_url", default="",
                                tooltip="Starting image URL (JPG/JPEG/PNG, min 300x300, aspect 1:2.5-2.5:1). Fallback when the IMAGE input is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to suppress or avoid in the generated video"),
                IO.Float.Input("guidance_scale", optional=True, default=0.5, min=0.0, max=1.0, step=0.01,
                               tooltip="Prompt adherence; higher values reduce creative deviation (0.0-1.0)"),
                IO.Combo.Input("duration", optional=True, options=cls.DURATIONS,
                               default="5",
                               tooltip="Video duration in seconds (5 or 10)"),
                IO.String.Input("last_image_url", optional=True, default="",
                                tooltip="Pro only: end-frame URL for keyframe interpolation. Fallback when the last_image IMAGE input is not connected."),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647, control_after_generate="randomize",
                             tooltip="Cache control: randomize re-runs generation each queue; a fixed value reuses the cached video. This endpoint has no seed parameter, so it is not sent to the API."),
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
    async def execute(cls, model="Kling 2.5 Turbo", prompt="", image=None, last_image=None,
                image_url="", client=None, negative_prompt="", guidance_scale=0.5,
                duration="5", last_image_url="", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import resolve_image_input
        from .wavespeed_api.requests.kling_v2_5_turbo_std_image_to_video import KlingV2_5TurboStdImageToVideo
        from .wavespeed_api.requests.kling_v2_5_turbo_pro_image_to_video import KlingV2_5TurboProImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        image_value = resolve_image_input(image, image_url)
        if not image_value:
            raise ValueError("Starting image is required (IMAGE input or image_url)")

        last_image_value = resolve_image_input(last_image, last_image_url)

        duration_int = int(duration)

        if model == "Kling 2.5 Turbo Pro":
            request = KlingV2_5TurboProImageToVideo(
                prompt=prompt,
                image=image_value,
                last_image=last_image_value or "",
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                duration=duration_int,
            )
        else:
            request = KlingV2_5TurboStdImageToVideo(
                prompt=prompt,
                image=image_value,
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                duration=duration_int,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
