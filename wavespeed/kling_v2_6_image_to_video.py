# ABOUTME: Kling 2.6 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports Std and Pro variants of the Kling 2.6 model.

from comfy_api.latest import IO


class KlingV2_6ImageToVideoNode(IO.ComfyNode):
    """
    Kling 2.6 Image-to-Video Generator Node

    Animates a starting image into a short video using Kling 2.6 models.
    The Pro variant additionally supports cfg_scale, an end-frame image, and
    joint audio-video co-generation.

    Image inputs accept either a ComfyUI IMAGE tensor (sent as a base64 data
    URI) or a URL string. When both are provided for the same field, the
    IMAGE input takes precedence.
    """

    MODELS = ["Kling 2.6", "Kling 2.6 Pro"]
    DURATIONS = ["5", "10"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV2_6ImageToVideoNode",
            display_name="Kling 2.6 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("image", optional=True,
                               tooltip="Starting image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `image_url` when connected."),
                IO.Image.Input("end_image", optional=True,
                               tooltip="Pro only: end-frame image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `end_image_url` when connected. Cannot be combined with sound."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 2.6",
                               tooltip="Model variant: Kling 2.6 (Std) or Kling 2.6 Pro (cfg_scale, end_image, sound)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of scene motion, camera moves, and audio"),
                IO.String.Input("image_url", default="",
                                tooltip="Starting image URL (JPG/JPEG/PNG, max 10MB, min 300px each side, aspect 1:2.5-2.5:1). Fallback when the IMAGE input is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from visuals and audio"),
                IO.Combo.Input("duration", optional=True, options=cls.DURATIONS,
                               default="5",
                               tooltip="Video duration in seconds (5 or 10)"),
                IO.String.Input("end_image_url", optional=True, default="",
                                tooltip="Pro only: end-frame URL; cannot be combined with sound. Fallback when the end_image IMAGE input is not connected."),
                IO.Float.Input("cfg_scale", optional=True, default=0.5, min=0.3, max=0.8, step=0.01,
                               tooltip="Pro only: guidance strength (0.3-0.8); higher follows the prompt more closely"),
                IO.Boolean.Input("sound", optional=True, default=True,
                                 tooltip="Pro only: enable joint audio-video generation (doubles cost); cannot be combined with end_image"),
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
    async def execute(cls, model="Kling 2.6", prompt="", image=None, end_image=None,
                image_url="", client=None, negative_prompt="", duration="5",
                end_image_url="", cfg_scale=0.5, sound=True, **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import resolve_image_input
        from .wavespeed_api.requests.kling_v2_6_std_image_to_video import KlingV2_6StdImageToVideo
        from .wavespeed_api.requests.kling_v2_6_pro_image_to_video import KlingV2_6ProImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        image_value = resolve_image_input(image, image_url)
        if not image_value:
            raise ValueError("Starting image is required (IMAGE input or image_url)")

        end_image_value = resolve_image_input(end_image, end_image_url)

        duration_int = int(duration)

        if model == "Kling 2.6 Pro":
            request = KlingV2_6ProImageToVideo(
                prompt=prompt,
                image=image_value,
                negative_prompt=negative_prompt,
                end_image=end_image_value or "",
                cfg_scale=cfg_scale,
                sound=sound,
                duration=duration_int,
            )
        else:
            request = KlingV2_6StdImageToVideo(
                prompt=prompt,
                image=image_value,
                negative_prompt=negative_prompt,
                duration=duration_int,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
