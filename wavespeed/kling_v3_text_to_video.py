# ABOUTME: Kling 3.0 text-to-video generation node for WaveSpeed AI.
# ABOUTME: Supports standard, Pro, and 4K variants of the Kling 3.0 model.

import json

from comfy_api.latest import IO


class KlingV3TextToVideoNode(IO.ComfyNode):
    """
    Kling 3.0 Text-to-Video Generator Node

    Generates a short video from a text prompt using Kling 3.0 models.
    Exposes the full documented parameter set: negative prompt, cfg_scale,
    sound, shot type, multi-prompt scene segmentation, and element list for
    visual consistency.
    """

    MODELS = ["Kling 3.0", "Kling 3.0 Pro", "Kling 3.0 4K"]
    ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
    SHOT_TYPES = ["customize", "intelligent"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingV3TextToVideoNode",
            display_name="Kling 3.0 Text-to-Video",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Kling 3.0",
                               tooltip="Model variant: Kling 3.0 (standard), Kling 3.0 Pro (higher quality), or Kling 3.0 4K (highest resolution)"),
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Text description of the video to generate (required unless multi_prompt is provided)"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Int.Input("duration", optional=True, default=5, min=3, max=15,
                             tooltip="Video duration in seconds (3 to 15)"),
                IO.Combo.Input("aspect_ratio", optional=True,
                               options=cls.ASPECT_RATIOS,
                               default="16:9",
                               tooltip="Aspect ratio of the output video"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Random seed for reproducibility (-1 for random)"),
                IO.String.Input("negative_prompt", optional=True, multiline=True, default="",
                                tooltip="Elements to exclude from the generation"),
                IO.Float.Input("cfg_scale", optional=True, default=0.5, min=0.0, max=1.0, step=0.05,
                               tooltip="Prompt adherence strength, 0-1"),
                IO.Boolean.Input("sound", optional=True, default=False,
                                 tooltip="Enable synchronized audio generation"),
                IO.Combo.Input("shot_type", optional=True,
                               options=cls.SHOT_TYPES,
                               default="customize",
                               tooltip="Shot composition mode. 'customize' is the API default; 'intelligent' auto-determines scope but requires multi_prompt to be set."),
                IO.String.Input("multi_prompt", optional=True, multiline=True, default="",
                                tooltip="JSON array of scene-segmented prompts (mutually exclusive with prompt)"),
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
    async def execute(cls, model="Kling 3.0", prompt="", client=None,
                duration=5, aspect_ratio="16:9", seed=-1,
                negative_prompt="", cfg_scale=0.5, sound=False,
                shot_type="customize", multi_prompt="", element_list="",
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.requests.kling_v3_text_to_video import KlingV3TextToVideo
        from .wavespeed_api.requests.kling_v3_pro_text_to_video import KlingV3ProTextToVideo
        from .wavespeed_api.requests.kling_v3_4k_text_to_video import KlingV34KTextToVideo

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        multi_prompt_value = cls._parse_json_array(multi_prompt, "multi_prompt")
        element_list_value = cls._parse_json_array(element_list, "element_list")

        if (prompt is None or prompt == "") and not multi_prompt_value:
            raise ValueError("Either prompt or multi_prompt is required")

        # The Wavespeed Kling 3.0 std API rejects shot_type="intelligent" when
        # multi_prompt is empty (intelligent mode auto-determines scope across
        # scene segments, which requires segments to exist). Saved workflows
        # from before the default flipped to "customize" still carry the old
        # widget value, so defensively drop the field here when it would fail.
        if shot_type == "intelligent" and not multi_prompt_value:
            print("[WaveSpeed] Kling shot_type='intelligent' requires multi_prompt; omitting field so API uses its default ('customize').")
            shot_type = None

        if model == "Kling 3.0 4K":
            request_cls = KlingV34KTextToVideo
        elif model == "Kling 3.0 Pro":
            request_cls = KlingV3ProTextToVideo
        else:
            request_cls = KlingV3TextToVideo

        request = request_cls(
            prompt=prompt if prompt else None,
            negative_prompt=negative_prompt if negative_prompt else None,
            duration=duration,
            aspect_ratio=aspect_ratio,
            cfg_scale=cfg_scale,
            sound=sound,
            shot_type=shot_type,
            multi_prompt=multi_prompt_value,
            element_list=element_list_value,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=900)

        video_url = response.get("outputs", [""])[0]
        return IO.NodeOutput(video_url)
