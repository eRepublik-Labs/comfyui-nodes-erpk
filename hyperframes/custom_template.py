# ABOUTME: HyperFrames Custom Template V3 node - renders a user-provided HTML composition.
# ABOUTME: Substitutes {{image_N}} placeholders with 1-indexed input images before rendering.

"""
HyperFramesCustomTemplate lets a user supply a full HyperFrames HTML
composition and optionally plug in images via 1-indexed {{image_N}}
placeholders. The node writes each image as image_1.png, image_2.png,
etc. and replaces the placeholders with local ./image_N.png paths before
invoking the subprocess renderer.
"""

from comfy_api.latest import IO

from .runner import render_html_to_mp4, temp_view_url, tensor_to_png_bytes


class HyperFramesCustomTemplate(IO.ComfyNode):
    """Render a user-provided HyperFrames HTML composition."""

    FORMATS = ["mp4", "mov", "webm"]
    QUALITIES = ["draft", "standard", "high"]
    FPS_OPTIONS = ["24", "30", "60"]

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="HyperFramesCustomTemplate",
            display_name="HyperFrames Custom Template",
            category="ERPK/HyperFrames",
            description=(
                "Render a user-provided HyperFrames HTML composition. Use "
                "{{image_1}}, {{image_2}}, ... as src placeholders to reference "
                "connected images (1-indexed)."
            ),
            inputs=[
                IO.String.Input(
                    "html_template",
                    multiline=True,
                    default="",
                    tooltip=(
                        "Full HyperFrames HTML. Use {{image_1}}, {{image_2}}, ... "
                        "as src placeholders for input images (1-indexed)."
                    ),
                ),
                IO.Image.Input(
                    "images",
                    optional=True,
                    tooltip=(
                        "Optional image batch mapped to {{image_1}}, "
                        "{{image_2}}, etc."
                    ),
                ),
                IO.Combo.Input(
                    "output_format",
                    options=cls.FORMATS,
                    default="mp4",
                    optional=True,
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
        html_template="",
        images=None,
        output_format="mp4",
        fps="30",
        quality="standard",
        **kwargs,
    ):
        if not (html_template or "").strip():
            raise ValueError("HyperFramesCustomTemplate requires html_template")

        assets = {}
        html_content = html_template

        if images is not None:
            n_images = _count_images(images)
            for i in range(n_images):
                frame = _select_frame(images, i)
                filename = f"image_{i + 1}.png"
                assets[filename] = tensor_to_png_bytes(frame)
                placeholder = "{{image_" + str(i + 1) + "}}"
                html_content = html_content.replace(placeholder, f"./{filename}")

        output_path = render_html_to_mp4(
            html_content=html_content,
            asset_files=assets,
            output_format=output_format,
            fps=int(fps),
            quality=quality,
        )

        return IO.NodeOutput(temp_view_url(output_path))


def _count_images(images) -> int:
    if hasattr(images, "ndim"):
        if images.ndim == 4:
            return int(images.shape[0])
        return 1
    try:
        return len(images)
    except TypeError:
        return 1


def _select_frame(images, i):
    if hasattr(images, "ndim") and images.ndim == 4:
        return images[i:i + 1]
    return images
