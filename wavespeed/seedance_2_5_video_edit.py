# ABOUTME: Seedance 2.5 video-edit node for WaveSpeed AI.
# ABOUTME: Rewrites an existing clip from a prompt; chains off any node's video_url output.

from comfy_api.latest import IO


class Seedance25VideoEditNode(IO.ComfyNode):
    """
    Seedance 2.5 Video Edit Node

    Rewrites an existing video clip from a text prompt using Bytedance Seedance 2.5.
    Takes the source clip as a URL, so it chains directly off the video_url output
    of any video node in this package.
    Output duration and aspect ratio follow the input clip.
    Returns a URL string suitable for the Preview Anything utility.
    """

    MODELS = ["Seedance 2.5", "Seedance 2.5 Turbo"]
    RESOLUTIONS = ["480p", "720p", "1080p", "4k"]

    @classmethod
    def _request_class_for(cls, model):
        from .wavespeed_api.requests.seedance_2_5_video_edit import Seedance25VideoEdit
        from .wavespeed_api.requests.seedance_2_5_video_edit_turbo import Seedance25VideoEditTurbo

        if model == "Seedance 2.5 Turbo":
            return Seedance25VideoEditTurbo
        return Seedance25VideoEdit

    @staticmethod
    def _normalize_url_list(value):
        if value is None or value == "":
            return None
        if isinstance(value, list):
            urls = [u for u in value if u]
        else:
            urls = [value]
        urls = urls[:4]
        return urls or None

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="Seedance25VideoEditNode",
            display_name="Bytedance Seedance 2.5 Video Edit",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="What to change in the video. The service prepends 'Edit the input video.' to this prompt."),
                IO.String.Input("video_url", optional=True, default="",
                                tooltip="Source video URL. Connect the video_url output of any video node in this package. Clips over 30s are trimmed; clips under 4s are padded."),
                IO.Combo.Input("model", options=cls.MODELS,
                               default="Seedance 2.5",
                               tooltip="Model tier: standard or Turbo (faster)"),
                IO.String.Input("reference_images", optional=True, default="",
                                tooltip="Reference image URL(s) guiding style, identity, or appearance. Single URL or list. Up to 4 images. Ignored when `reference_images_tensor` is connected."),
                IO.String.Input("reference_audios", optional=True, default="",
                                tooltip="Reference audio URL(s) guiding the soundtrack or voice. Single URL or list. Up to 4 audios."),
                IO.Image.Input("reference_images_tensor", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch (B,H,W,C). Each batch slice becomes one reference, capped at 4. Takes precedence over `reference_images` URLs when connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("resolution", optional=True,
                               options=cls.RESOLUTIONS,
                               default="720p",
                               tooltip="Video resolution. Billing counts input plus output duration, roughly $0.11/s at 480p to $1.10/s at 4k."),
                IO.Boolean.Input("generate_audio", optional=True, default=True,
                                 tooltip="Generate audio synchronized with the edited video"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Cache control only. Seedance 2.5 takes no API seed, so this is never sent. A fixed seed reuses the video you already paid for; -1 generates again on every queue."),
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
    async def execute(cls, model="Seedance 2.5", prompt="", video_url="",
                reference_images="", reference_audios="", reference_images_tensor=None,
                client=None, resolution="720p", generate_audio=True, seed=-1,
                **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import images_to_data_uris

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if prompt is None or prompt == "":
            raise ValueError("Prompt is required")
        if not video_url:
            raise ValueError("A source video URL is required")

        if reference_images_tensor is not None:
            reference_images_value = images_to_data_uris(reference_images_tensor, max_count=4)
        else:
            reference_images_value = cls._normalize_url_list(reference_images)

        request_cls = cls._request_class_for(model)

        request = request_cls(
            prompt=prompt,
            video=video_url,
            resolution=resolution,
            reference_images=reference_images_value,
            reference_audios=cls._normalize_url_list(reference_audios),
            generate_audio=generate_audio,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, polling_interval=10, timeout=1800)

        video_urls = response.get("outputs", [])
        if not video_urls:
            raise ValueError("No video URLs in the generated result")

        return IO.NodeOutput(video_urls[0])
