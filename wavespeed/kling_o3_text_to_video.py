# ABOUTME: Kling O3 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard and Pro variants of the Kling O3 model.

import json

from comfy_api.latest import IO


class KlingO3TextToVideoNode(IO.ComfyNode):
    """
    Kling O3 Text-to-Video Generator Node

    Generates a short video from a text prompt using Kling O3 models.
    Exposes the full documented parameter set: sound, shot type, multi-prompt
    scene segmentation, and (Pro only) element list for visual consistency.
    """

    MODELS = ["Kling O3", "Kling O3 Pro"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    SHOT_TYPES = ["intelligent", "customize"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingO3TextToVideoNode",
            display_name="Kling O3 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling O3",
                               tooltip="Model variant: Kling O3 (standard) or Kling O3 Pro (higher quality, element_list support)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate (required unless multi_prompt is provided)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds. Std: 3-15. Pro: 5 or 10."),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Aspect ratio of the output video"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.Boolean.Input("sound", optional=True, default=False,
                                 tooltip="Enable synchronized audio generation (surcharge applies)"),
                IO.Combo.Input("shot_type", optional=True,
                               options=cls.SHOT_TYPES,
                               default="intelligent",
                               tooltip="Shot composition mode: 'intelligent' auto-determines, 'customize' allows manual control"),
                IO.String.Input("multi_prompt", optional=True, multiline=True, default="",
                                tooltip="JSON array of scene-segmented prompts (mutually exclusive with prompt)"),
                IO.String.Input("element_list", optional=True, multiline=True, default="",
                                tooltip="Pro only: JSON array of pre-generated element IDs for visual consistency"),
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
    async def execute(cls, model="Kling O3", prompt="", client=None,
                duration=5, aspect_ratio="16:9", seed=-1,
                sound=False, shot_type="intelligent",
                multi_prompt="", element_list="", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_o3_text_to_video import KlingO3TextToVideo
        from .wavespeed_api.requests.kling_o3_pro_text_to_video import KlingO3ProTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        multi_prompt_value = cls._parse_json_array(multi_prompt, "multi_prompt")
        element_list_value = cls._parse_json_array(element_list, "element_list")

        if (prompt is None or prompt == "") and not multi_prompt_value:
            raise ValueError("Either prompt or multi_prompt is required")

        if model == "Kling O3 Pro":
            request = KlingO3ProTextToVideo(
                prompt=prompt if prompt else None,
                duration=duration,
                aspect_ratio=aspect_ratio,
                sound=sound,
                shot_type=shot_type,
                multi_prompt=multi_prompt_value,
                element_list=element_list_value,
            )
        else:
            request = KlingO3TextToVideo(
                prompt=prompt if prompt else None,
                duration=duration,
                aspect_ratio=aspect_ratio,
                sound=sound,
                shot_type=shot_type,
                multi_prompt=multi_prompt_value,
            )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
