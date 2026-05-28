# ABOUTME: Grok (xAI) V3 video nodes for ComfyUI — text-to-video, reference-to-video, edit, extend.
# ABOUTME: All nodes output a video URL string; GrokClient.generate/edit/extend_video handle polling.

from comfy_api.latest import IO

from .grok_api.client import GrokClient


def _make_client(client_dict):
    """Return a GrokClient from the passed dict or by falling through to key resolution."""
    if client_dict is not None:
        return GrokClient(api_key=client_dict["api_key"])
    return GrokClient()


class GrokTextToVideo(IO.ComfyNode):
    """Generates a video from a text prompt using xAI's Grok video model."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokTextToVideo",
            display_name="Grok Text to Video",
            category="ERPK/Grok/Video",
            description="Generate a video from a text prompt using xAI Grok.",
            not_idempotent=True,
            inputs=[
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Grok API client from Grok API Client node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings, XAI_API_KEY env var, or grok/config.ini."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text description of the video to generate.",
                ),
                IO.Combo.Input(
                    "model",
                    options=[GrokClient.DEFAULT_VIDEO_MODEL],
                    default=GrokClient.DEFAULT_VIDEO_MODEL,
                    optional=True,
                    tooltip="xAI video model.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=GrokClient.VIDEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Output aspect ratio.",
                ),
                IO.Combo.Input(
                    "resolution",
                    options=GrokClient.VIDEO_RESOLUTIONS,
                    default="720p",
                    optional=True,
                    tooltip="Output resolution. 480p is faster; 720p is HD.",
                ),
                IO.Int.Input(
                    "duration",
                    default=5,
                    min=1,
                    max=15,
                    optional=True,
                    tooltip="Video duration in seconds (1–15).",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xFFFFFFFF,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation only — not forwarded to the API. "
                        "-1 for random."
                    ),
                ),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", GrokClient.DEFAULT_VIDEO_MODEL)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "720p")
        duration = kwargs.get("duration", 5)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        grok = _make_client(client_dict)
        print(f"[Grok] Text-to-video: model={model}, aspect_ratio={aspect_ratio}, "
              f"resolution={resolution}, duration={duration}s")
        print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        video_url = await grok.generate_video(
            prompt=prompt.strip(),
            model=model,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )
        if not video_url:
            raise ValueError("xAI returned an empty video URL")
        print(f"[Grok] Video URL: {video_url}")
        return IO.NodeOutput(video_url)


class GrokRefToVideo(IO.ComfyNode):
    """Generates a video guided by reference images and a text prompt using xAI Grok.
    Prompt may reference images via <IMAGE_1>/<IMAGE_2>/<IMAGE_3> tokens."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokRefToVideo",
            display_name="Grok Reference to Video",
            category="ERPK/Grok/Video",
            description=(
                "Generate a video from reference images and a text prompt using xAI Grok. "
                "Up to 3 images; prompt may use <IMAGE_1>, <IMAGE_2>, <IMAGE_3> tokens."
            ),
            not_idempotent=True,
            inputs=[
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Grok API client from Grok API Client node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings, XAI_API_KEY env var, or grok/config.ini."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip=(
                        "Text description of the video. Use <IMAGE_1>, <IMAGE_2>, <IMAGE_3> "
                        "tokens to reference the connected images."
                    ),
                ),
                IO.Image.Input(
                    "reference_images",
                    tooltip=(
                        "Batched IMAGE input — up to 3 frames. Used as visual reference "
                        "for the generated video. Convert to data URIs automatically."
                    ),
                ),
                IO.Combo.Input(
                    "model",
                    options=[GrokClient.DEFAULT_VIDEO_MODEL],
                    default=GrokClient.DEFAULT_VIDEO_MODEL,
                    optional=True,
                    tooltip="xAI video model.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=GrokClient.VIDEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Output aspect ratio.",
                ),
                IO.Combo.Input(
                    "resolution",
                    options=GrokClient.VIDEO_RESOLUTIONS,
                    default="720p",
                    optional=True,
                    tooltip="Output resolution. 480p is faster; 720p is HD.",
                ),
                IO.Int.Input(
                    "duration",
                    default=5,
                    min=1,
                    max=15,
                    optional=True,
                    tooltip="Video duration in seconds (1–15).",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xFFFFFFFF,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation only — not forwarded to the API. "
                        "-1 for random."
                    ),
                ),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .grok_api.utils import images_to_data_uris

        client_dict = kwargs.get("client")
        prompt = kwargs.get("prompt", "")
        reference_images = kwargs.get("reference_images")
        model = kwargs.get("model", GrokClient.DEFAULT_VIDEO_MODEL)
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "720p")
        duration = kwargs.get("duration", 5)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if reference_images is None:
            raise ValueError("reference_images is required for reference-to-video")

        data_uris = images_to_data_uris(reference_images, max_count=GrokClient.MAX_EDIT_IMAGES)
        if not data_uris:
            raise ValueError("Could not convert reference_images to data URIs")

        grok = _make_client(client_dict)
        print(f"[Grok] Ref-to-video: model={model}, {len(data_uris)} reference image(s), "
              f"aspect_ratio={aspect_ratio}, resolution={resolution}, duration={duration}s")
        print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        video_url = await grok.generate_video(
            prompt=prompt.strip(),
            model=model,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            reference_images=data_uris,
        )
        if not video_url:
            raise ValueError("xAI returned an empty video URL")
        print(f"[Grok] Video URL: {video_url}")
        return IO.NodeOutput(video_url)


class GrokVideoEdit(IO.ComfyNode):
    """Edits an existing video guided by a text prompt using xAI Grok.
    The output inherits the source video's duration, aspect ratio, and resolution."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokVideoEdit",
            display_name="Grok Video Edit",
            category="ERPK/Grok/Video",
            description=(
                "Edit an existing video with a text prompt using xAI Grok. "
                "The source video must be a public HTTPS URL."
            ),
            not_idempotent=True,
            inputs=[
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Grok API client from Grok API Client node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings, XAI_API_KEY env var, or grok/config.ini."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Editing instructions describing the desired changes.",
                ),
                IO.String.Input(
                    "video_url",
                    default="",
                    tooltip="Public HTTPS URL of the source video to edit.",
                ),
                IO.Combo.Input(
                    "model",
                    options=[GrokClient.DEFAULT_VIDEO_MODEL],
                    default=GrokClient.DEFAULT_VIDEO_MODEL,
                    optional=True,
                    tooltip="xAI video model.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xFFFFFFFF,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation only — not forwarded to the API. "
                        "-1 for random."
                    ),
                ),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        prompt = kwargs.get("prompt", "")
        source_url = kwargs.get("video_url", "")
        model = kwargs.get("model", GrokClient.DEFAULT_VIDEO_MODEL)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if not source_url or not source_url.strip():
            raise ValueError("video_url cannot be empty")

        grok = _make_client(client_dict)
        print(f"[Grok] Video edit: model={model}, source={source_url[:80]}")
        print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        video_url = await grok.edit_video(
            prompt=prompt.strip(),
            video_url=source_url.strip(),
            model=model,
        )
        if not video_url:
            raise ValueError("xAI returned an empty video URL")
        print(f"[Grok] Video URL: {video_url}")
        return IO.NodeOutput(video_url)


class GrokVideoExtend(IO.ComfyNode):
    """Extends an existing video by appending new content using xAI Grok."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GrokVideoExtend",
            display_name="Grok Video Extend",
            category="ERPK/Grok/Video",
            description=(
                "Extend an existing video by appending new content using xAI Grok. "
                "The source video must be a public HTTPS URL."
            ),
            not_idempotent=True,
            inputs=[
                IO.Custom("GROK_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Grok API client from Grok API Client node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings, XAI_API_KEY env var, or grok/config.ini."
                    ),
                ),
                IO.String.Input(
                    "video_url",
                    default="",
                    tooltip="Public HTTPS URL of the source video to extend.",
                ),
                IO.Int.Input(
                    "duration",
                    default=5,
                    min=1,
                    max=15,
                    tooltip="Duration in seconds to append (1–15).",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Optional prompt to guide the extended content.",
                ),
                IO.Combo.Input(
                    "model",
                    options=[GrokClient.DEFAULT_VIDEO_MODEL],
                    default=GrokClient.DEFAULT_VIDEO_MODEL,
                    optional=True,
                    tooltip="xAI video model.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xFFFFFFFF,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation only — not forwarded to the API. "
                        "-1 for random."
                    ),
                ),
            ],
            outputs=[
                IO.String.Output("video_url"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        client_dict = kwargs.get("client")
        source_url = kwargs.get("video_url", "")
        duration = kwargs.get("duration", 5)
        prompt = kwargs.get("prompt", "") or None
        model = kwargs.get("model", GrokClient.DEFAULT_VIDEO_MODEL)

        if not source_url or not source_url.strip():
            raise ValueError("video_url cannot be empty")

        grok = _make_client(client_dict)
        print(f"[Grok] Video extend: model={model}, duration={duration}s, "
              f"source={source_url[:80]}")
        if prompt:
            print(f"[Grok] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        video_url = await grok.extend_video(
            video_url=source_url.strip(),
            duration=duration,
            prompt=prompt,
            model=model,
        )
        if not video_url:
            raise ValueError("xAI returned an empty video URL")
        print(f"[Grok] Video URL: {video_url}")
        return IO.NodeOutput(video_url)
