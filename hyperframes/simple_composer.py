# ABOUTME: HyperFrames Simple Composer V3 node - builds a video from images + captions.
# ABOUTME: Generates a HyperFrames-compliant HTML composition and renders it via subprocess.

"""
HyperFramesSimpleComposer generates a video from a batch of images, with
optional captions, background audio, and scene transitions. The HTML is
built following the strict HyperFrames schema (root div with composition
id, clip classes, GSAP timeline registration, and an explicit timeline
extension so the full composition length is rendered).
"""

from html import escape

from comfy_api.latest import IO

from .runner import render_html_to_mp4, temp_view_url, tensor_to_png_bytes

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><style>
html, body {{ margin: 0; padding: 0; overflow: hidden; background: black; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
#root {{ position: relative; }}
.scene {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
.caption {{ position: absolute; bottom: 8%; left: 5%; right: 5%; text-align: center; font-size: 48px; font-weight: 600; color: white; text-shadow: 0 4px 12px rgba(0,0,0,0.9); line-height: 1.2; }}
</style></head><body>
<div id="root" data-composition-id="erpk_simple" data-start="0"
     data-width="{stage_width}" data-height="{stage_height}"
     style="width: {stage_width}px; height: {stage_height}px;">
{scene_elements}
{audio_element}
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
const tl = gsap.timeline({{ paused: true }});
{animations}
// Extend timeline to the full composition length so the render does not cut off early.
tl.set({{}}, {{}}, {total_duration});
window.__timelines = window.__timelines || {{}};
window.__timelines["erpk_simple"] = tl;
</script>
</div>
</body></html>
"""


class HyperFramesSimpleComposer(IO.ComfyNode):
    """Compose a video from a batch of images with optional captions and audio."""

    TRANSITIONS = ["cut", "fade", "crossfade"]
    FORMATS = ["mp4", "mov", "webm"]
    QUALITIES = ["draft", "standard", "high"]
    FPS_OPTIONS = ["24", "30", "60"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="HyperFramesSimpleComposer",
            display_name="HyperFrames Simple Composer",
            category="ERPK/HyperFrames",
            description=(
                "Compose a video from images + captions using the HyperFrames "
                "local renderer. Requires Node.js >= 22 and FFmpeg on PATH; the "
                "hyperframes npm package is auto-installed on first use."
            ),
            inputs=[
                IO.Image.Input(
                    "images",
                    tooltip="Scene images (batch). Each image becomes one scene.",
                ),
                IO.String.Input(
                    "captions",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip=(
                        "One caption per scene, separated by newlines. "
                        "Leave blank for no captions."
                    ),
                ),
                IO.Int.Input(
                    "duration_per_scene",
                    default=3,
                    min=1,
                    max=30,
                    step=1,
                    optional=True,
                    tooltip="Seconds each scene is displayed.",
                ),
                IO.Int.Input(
                    "stage_width",
                    default=1920,
                    min=320,
                    max=4096,
                    step=2,
                    optional=True,
                ),
                IO.Int.Input(
                    "stage_height",
                    default=1080,
                    min=320,
                    max=4096,
                    step=2,
                    optional=True,
                ),
                IO.String.Input(
                    "audio_url",
                    default="",
                    optional=True,
                    tooltip=(
                        "Optional URL or local path to an audio file "
                        "(mp3, wav, m4a)."
                    ),
                ),
                IO.Combo.Input(
                    "transition",
                    options=cls.TRANSITIONS,
                    default="fade",
                    optional=True,
                    tooltip="Scene transition style.",
                ),
                IO.Combo.Input(
                    "output_format",
                    options=cls.FORMATS,
                    default="mp4",
                    optional=True,
                    tooltip=(
                        "Output container: mp4 (standard), mov (ProRes with "
                        "alpha), webm (VP9 with alpha)."
                    ),
                ),
                IO.Combo.Input(
                    "fps",
                    options=cls.FPS_OPTIONS,
                    default="30",
                    optional=True,
                ),
                IO.Combo.Input(
                    "quality",
                    options=cls.QUALITIES,
                    default="standard",
                    optional=True,
                    tooltip=(
                        "draft (fast, CRF 28), standard (CRF 18), "
                        "high (best, CRF 15, slow)."
                    ),
                ),
            ],
            outputs=[IO.String.Output("video_url")],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def execute(
        cls,
        images=None,
        captions="",
        duration_per_scene=3,
        stage_width=1920,
        stage_height=1080,
        audio_url="",
        transition="fade",
        output_format="mp4",
        fps="30",
        quality="standard",
        **kwargs,
    ):
        if images is None:
            raise ValueError("HyperFramesSimpleComposer requires at least one image")

        n_scenes = _count_images(images)
        if n_scenes == 0:
            raise ValueError("Image batch is empty")

        total_duration = n_scenes * duration_per_scene

        caption_list = _split_captions(captions, n_scenes)

        # Build asset dict: one PNG per scene
        assets = {}
        for i in range(n_scenes):
            frame = _select_frame(images, i)
            assets[f"scene_{i}.png"] = tensor_to_png_bytes(frame)

        scene_elements = _build_scene_elements(
            n_scenes=n_scenes,
            caption_list=caption_list,
            duration_per_scene=duration_per_scene,
        )
        audio_element = _build_audio_element(audio_url, total_duration)
        animations = _build_animations(
            n_scenes=n_scenes,
            caption_list=caption_list,
            duration_per_scene=duration_per_scene,
            transition=transition,
        )

        html_content = HTML_TEMPLATE.format(
            stage_width=stage_width,
            stage_height=stage_height,
            scene_elements=scene_elements,
            audio_element=audio_element,
            animations=animations,
            total_duration=total_duration,
        )

        output_path = render_html_to_mp4(
            html_content=html_content,
            asset_files=assets,
            output_format=output_format,
            fps=int(fps),
            quality=quality,
        )

        return IO.NodeOutput(temp_view_url(output_path))


def _count_images(images) -> int:
    """Return the number of frames in an IMAGE tensor (or list-like) input."""
    if hasattr(images, "ndim"):
        if images.ndim == 4:
            return int(images.shape[0])
        return 1
    try:
        return len(images)
    except TypeError:
        return 1


def _select_frame(images, i):
    """Return a single-frame tensor for index i, suitable for encoding."""
    if hasattr(images, "ndim") and images.ndim == 4:
        return images[i:i + 1]
    return images


def _split_captions(captions: str, n_scenes: int) -> list:
    """Split a newline-separated caption string into exactly n_scenes entries."""
    items = [line.strip() for line in (captions or "").split("\n")]
    # Strip trailing blank entries (common when no captions provided)
    while len(items) > 0 and items[-1] == "":
        items.pop()
    while len(items) < n_scenes:
        items.append("")
    return items[:n_scenes]


def _build_scene_elements(n_scenes: int, caption_list: list, duration_per_scene: int) -> str:
    parts = []
    for i in range(n_scenes):
        start = i * duration_per_scene
        parts.append(
            f'<img id="scene-{i}" class="clip scene" '
            f'data-start="{start}" data-duration="{duration_per_scene}" '
            f'data-track-index="0" src="./scene_{i}.png" />'
        )
        caption = caption_list[i] if i < len(caption_list) else ""
        if caption:
            parts.append(
                f'<div id="caption-{i}" class="clip caption" '
                f'data-start="{start}" data-duration="{duration_per_scene}" '
                f'data-track-index="1">{escape(caption)}</div>'
            )
    return "\n".join(parts)


def _build_audio_element(audio_url: str, total_duration: int) -> str:
    if not audio_url:
        return ""
    return (
        f'<audio id="bg-audio" data-start="0" '
        f'data-duration="{total_duration}" data-track-index="99" '
        f'data-volume="0.8" src="{escape(audio_url, quote=True)}"></audio>'
    )


def _build_animations(
    n_scenes: int,
    caption_list: list,
    duration_per_scene: int,
    transition: str,
) -> str:
    lines = []
    for i in range(n_scenes):
        start = i * duration_per_scene
        if transition == "fade":
            lines.append(
                f'tl.from("#scene-{i}", {{ opacity: 0, duration: 0.4 }}, {start});'
            )
        elif transition == "crossfade" and i > 0:
            overlap_start = max(0, start - 0.25)
            lines.append(
                f'tl.from("#scene-{i}", {{ opacity: 0, duration: 0.5 }}, {overlap_start});'
            )
        # "cut" transition => no animation
        caption = caption_list[i] if i < len(caption_list) else ""
        if caption:
            lines.append(
                f'tl.from("#caption-{i}", {{ opacity: 0, y: 30, duration: 0.4 }}, {start});'
            )
    return "\n".join(lines)
