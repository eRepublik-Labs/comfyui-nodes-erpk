# ABOUTME: Kling O3 image-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports Std and Pro variants of the Kling O3 model.

import json

from comfy_api.latest import IO


class KlingO3ImageToVideoNode(IO.ComfyNode):
    """
    Kling O3 Image-to-Video Generator Node

    Animates a starting image into a short video using Kling O3 models.
    Both Std and Pro variants share end_image, sound, shot_type, and
    multi_prompt controls; Pro additionally supports element_list for
    visual consistency.

    Image inputs accept either a ComfyUI IMAGE tensor (sent as a base64
    data URI) or a URL string. When both are provided for the same field,
    the IMAGE input takes precedence.
    """

    MODELS = ["Kling O3", "Kling O3 Pro"]
    SHOT_TYPES = ["intelligent", "customize"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingO3ImageToVideoNode",
            display_name="Kling O3 Image-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("image", optional=True,
                               tooltip="Starting image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `image_url` when connected."),
                IO.Image.Input("end_image", optional=True,
                               tooltip="Optional end-frame image as a ComfyUI IMAGE tensor for guided transitions. Preferred — takes precedence over `end_image_url` when connected."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling O3",
                               tooltip="Model variant: Kling O3 (standard) or Kling O3 Pro (adds element_list)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of motion, camera movement, and action"),
                IO.String.Input("image_url", default="",
                                tooltip="Starting image URL (use WaveSpeed Upload Image to produce one). Fallback when the IMAGE input is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds. Std accepts 3-15; Pro accepts 5 or 10."),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Retained for workflow compatibility; the O3 API does not accept a seed parameter."),
                IO.String.Input("end_image_url", optional=True, default="",
                                tooltip="End-frame image URL for guided transitions. Fallback when the end_image IMAGE input is not connected."),
                IO.Boolean.Input("sound", optional=True, default=False,
                                 tooltip="Enable synchronized audio generation (raises base cost)"),
                IO.Combo.Input("shot_type", optional=True,
                               options=cls.SHOT_TYPES,
                               default="intelligent",
                               tooltip="Shot composition mode: 'intelligent' (auto) or 'customize' (manual)"),
                IO.String.Input("multi_prompt", optional=True, multiline=True, default="",
                                tooltip="JSON array of scene-segmented prompts guiding scene transitions"),
                IO.String.Input("element_list", optional=True, multiline=True, default="",
                                tooltip="Pro only: JSON array of Kling Elements IDs to lock for visual consistency"),
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
    def execute(cls, model="Kling O3", prompt="", image=None, end_image=None,
                image_url="", client=None, duration=5, seed=-1,
                end_image_url="", sound=False, shot_type="intelligent",
                multi_prompt="", element_list="", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import resolve_image_input
        from .wavespeed_api.requests.kling_o3_image_to_video import KlingO3ImageToVideo
        from .wavespeed_api.requests.kling_o3_pro_image_to_video import KlingO3ProImageToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")

        image_value = resolve_image_input(image, image_url)
        if not image_value:
            raise ValueError("Starting image is required (IMAGE input or image_url)")

        end_image_value = resolve_image_input(end_image, end_image_url)

        multi_prompt_value = cls._parse_json_array(multi_prompt, "multi_prompt")

        if model == "Kling O3 Pro":
            element_list_value = cls._parse_json_array(element_list, "element_list")
            request = KlingO3ProImageToVideo(
                prompt=prompt,
                image=image_value,
                end_image=end_image_value,
                duration=duration,
                sound=sound,
                shot_type=shot_type,
                multi_prompt=multi_prompt_value,
                element_list=element_list_value,
            )
        else:
            request = KlingO3ImageToVideo(
                prompt=prompt,
                image=image_value,
                end_image=end_image_value,
                duration=duration,
                sound=sound,
                shot_type=shot_type,
                multi_prompt=multi_prompt_value,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
