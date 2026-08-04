# ABOUTME: ComfyUI V3 node for Gemini Omni Flash video generation via the Interactions API.
# ABOUTME: Text-to-video and image-to-video at 720p/24fps, saved to disk as .mp4.

import asyncio
import base64
import os
import tempfile
import time

from comfy_api.latest import IO


# The models overview table shows the code as "gemini-omni-flash"; the model
# reference page and the Interactions API guide both give the -preview suffix,
# which is the string the API accepts.
OMNI_MODEL = "gemini-omni-flash-preview"

ASPECT_RATIOS = ["16:9", "9:16"]


def _build_omni_video_request(aspect_ratio, has_image):
    """Build the non-content kwargs for an Omni Flash video interaction.

    Omni Flash rejects system instructions, temperature, top_p, stop sequences
    and negative prompts, so none of them appear here — put negatives in the
    prompt itself ("Do not do X"). Output is fixed at 720p / 24 FPS / 3-10s, so
    there is no resolution or duration knob to expose.

    background/store/stream are all disabled: that is the documented fast path
    for a single synchronous generation, which is what a node execution wants.
    """
    return {
        "response_format": {"type": "video", "aspect_ratio": aspect_ratio},
        "generation_config": {
            "video_config": {"task": "image_to_video" if has_image else "text_to_video"},
        },
        "background": False,
        "store": False,
        "stream": False,
    }


def _decode_output_video(interaction):
    """Return the mp4 bytes carried by a completed interaction."""
    output_video = getattr(interaction, "output_video", None)
    if output_video is None or not getattr(output_video, "data", None):
        raise ValueError(
            "Omni Flash returned no video. This usually means the prompt was "
            "refused or the interaction is still running."
        )
    return base64.b64decode(output_video.data)


def _write_video(video_bytes, output_directory, prefix="gemini_omni"):
    """Write mp4 bytes to the output directory, returning the path."""
    if output_directory and output_directory.strip():
        out_dir = output_directory.strip()
    else:
        import folder_paths
        out_dir = folder_paths.get_output_directory()
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, f"{prefix}_{int(time.time())}.mp4")
    with open(output_path, "wb") as f:
        f.write(video_bytes)
    return output_path


def _pil_to_genai_image(pil_image):
    """Persist a PIL image to a temp file and return (types.Image, tmp_path)."""
    from google.genai import types
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    pil_image.save(tmp.name, "PNG")
    return types.Image.from_file(location=tmp.name), tmp.name


class GeminiOmniVideoGeneration(IO.ComfyNode):
    """Generates video from a prompt, optionally conditioned on a start image."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiOmniVideoGeneration",
            display_name="Gemini Omni Video Generation",
            category="ERPK/Gemini",
            description=(
                "Generate 3-10s video at 720p/24fps with Gemini Omni Flash. "
                "Connect an image to animate it instead of generating from text alone."
            ),
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip=(
                        "What the video should show. Negative prompts are not supported — "
                        "state exclusions inline, e.g. 'Do not show text on screen'."
                    ),
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client. Optional when the key is in ComfyUI Settings.",
                ),
                IO.Image.Input(
                    "image",
                    optional=True,
                    tooltip="Optional start image. Connecting one switches the model to image-to-video.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Video aspect ratio. Output is always 720p at 24 FPS.",
                ),
                IO.String.Input(
                    "output_directory",
                    default="",
                    optional=True,
                    tooltip="Directory to save video. Empty uses the ComfyUI output folder.",
                ),
                IO.Int.Input(
                    "seed",
                    default=0,
                    min=-1,
                    max=0xffffffff,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Cache control only — Omni Flash takes no API seed, so this is "
                        "never sent. A fixed seed reuses the video you already paid for; "
                        "-1 (randomize) generates again on every queue."
                    ),
                ),
            ],
            outputs=[
                IO.String.Output("video_path"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        client = kwargs.get("client")
        if client is None:
            from .gemini_api.client import GeminiClient
            client = GeminiClient(api_key=None)

        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        output_directory = kwargs.get("output_directory", "")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        contents = [prompt.strip()]
        temp_path = None
        if image is not None:
            from .gemini_api.utils import ImageConverter
            pil_list = ImageConverter.tensors_to_pil_list(image)
            if pil_list:
                genai_image, temp_path = _pil_to_genai_image(pil_list[0])
                contents.append(genai_image)

        request = _build_omni_video_request(aspect_ratio, has_image=temp_path is not None)
        task = request["generation_config"]["video_config"]["task"]
        print(f"[Gemini Omni] {task} — {aspect_ratio}, 720p/24fps")

        try:
            interaction = await asyncio.to_thread(
                client.client.interactions.create,
                model=OMNI_MODEL,
                input=contents,
                **request,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

        video_bytes = _decode_output_video(interaction)
        output_path = _write_video(video_bytes, output_directory)
        print(f"[Gemini Omni] Saved video to {output_path}")
        return IO.NodeOutput(output_path)
