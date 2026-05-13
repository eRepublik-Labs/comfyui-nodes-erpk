# ABOUTME: Kling 3.0 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard, Pro, and 4K variants of the Kling 3.0 model.

import json

from comfy_api.latest import IO


class KlingV3ImageToVideoNode(IO.ComfyNode):
    """
    Kling 3.0 Image-to-Video Generator Node

    Animates a starting image into a short video using Kling 3.0 models.
    All three variants (Std, Pro, 4K) share a common parameter surface
    covering negative prompts, end-frame guidance, cfg_scale, optional
    audio, shot composition mode, multi-prompt scene segmentation, and
    element lists. Aspect ratio is derived from the input image on all
    Kling 3.0 i2v variants.

    Image inputs accept either a ComfyUI IMAGE tensor (sent as a base64
    data URI) or a URL string. When both are provided for the same field,
    the IMAGE input takes precedence.
    """

    MODELS = ["Kling 3.0", "Kling 3.0 Pro", "Kling 3.0 4K"]
    SHOT_TYPES = ["customize", "intelligent"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV3ImageToVideoNode",
            display_name="Kling 3.0 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("image", optional=True,
                               tooltip="Starting image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `image_url` when connected."),
                IO.Image.Input("end_image", optional=True,
                               tooltip="Optional end-frame guidance image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `end_image_url` when connected."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 3.0",
                               tooltip="Model variant: Kling 3.0 (standard), Kling 3.0 Pro (higher quality), or Kling 3.0 4K (highest resolution; derives aspect ratio from the input image)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the desired motion/scene"),
                IO.String.Input("image_url", default="",
                                tooltip="Starting image URL (use WaveSpeed Upload Image to produce one). Fallback when the IMAGE input is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds (3 to 15)"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from the generation"),
                IO.String.Input("end_image_url", optional=True, default="",
                                tooltip="End-frame guidance image URL. Fallback when the end_image IMAGE input is not connected."),
                IO.Float.Input("cfg_scale", optional=True, default=0.5, min=0.0, max=1.0, step=0.05,
                               tooltip="Prompt adherence strength, 0-1"),
                IO.Boolean.Input("sound", optional=True, default=False,
                                 tooltip="Enable synchronized audio generation (applies a 1.5x cost multiplier)"),
                IO.Combo.Input("shot_type", optional=True,
                               options=cls.SHOT_TYPES,
                               default="customize",
                               tooltip="Shot composition mode: 'customize' or 'intelligent'"),
                IO.String.Input("multi_prompt", optional=True, multiline=True, default="",
                                tooltip="JSON array of scene-segmented prompts (mutually exclusive with prompt on 4K)"),
                IO.String.Input("element_list", optional=True, multiline=True, default="",
                                tooltip="JSON array of pre-generated element IDs for visual consistency"),
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
    def _parse_json_array(cls, raw, field_name):
        if raw is None or raw == "":
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name} must be valid JSON: {exc}")
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} must be a JSON array")
        return parsed

    @classmethod
    def execute(cls, model="Kling 3.0", prompt="", image=None, end_image=None,
                image_url="", client=None, duration=5, seed=-1,
                negative_prompt=None, end_image_url="", cfg_scale=None, sound=None,
                shot_type=None, multi_prompt=None, element_list=None,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import resolve_image_input
        from .wavespeed_api.requests.kling_v3_image_to_video import KlingV3ImageToVideo
        from .wavespeed_api.requests.kling_v3_pro_image_to_video import KlingV3ProImageToVideo
        from .wavespeed_api.requests.kling_v3_4k_image_to_video import KlingV34KImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        image_value = resolve_image_input(image, image_url)
        if not image_value:
            raise ValueError("Starting image is required (IMAGE input or image_url)")

        end_image_value = resolve_image_input(end_image, end_image_url)

        multi_prompt_value = cls._parse_json_array(multi_prompt, "multi_prompt")
        element_list_value = cls._parse_json_array(element_list, "element_list")

        negative_prompt_value = negative_prompt if negative_prompt else None
        shot_type_value = shot_type if shot_type else None

        if model == "Kling 3.0 4K":
            if (prompt is None or prompt == "") and not multi_prompt_value:
                raise ValueError("Either prompt or multi_prompt is required")

            request = KlingV34KImageToVideo(
                prompt=prompt if prompt else None,
                image=image_value,
                negative_prompt=negative_prompt_value,
                end_image=end_image_value,
                duration=duration,
                cfg_scale=cfg_scale if cfg_scale is not None else 0.5,
                sound=sound if sound is not None else False,
                shot_type=shot_type_value if shot_type_value is not None else "customize",
                multi_prompt=multi_prompt_value,
                element_list=element_list_value,
            )
        else:
            if prompt is None or prompt == "":
                raise ValueError("Prompt is required")
            request_cls = KlingV3ProImageToVideo if model == "Kling 3.0 Pro" else KlingV3ImageToVideo
            request = request_cls(
                prompt=prompt,
                image=image_value,
                negative_prompt=negative_prompt_value,
                end_image=end_image_value,
                duration=duration,
                cfg_scale=cfg_scale,
                sound=sound,
                shot_type=shot_type_value,
                multi_prompt=multi_prompt_value,
                element_list=element_list_value,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
