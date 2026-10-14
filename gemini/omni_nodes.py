# ABOUTME: ComfyUI V3 nodes for Gemini Omni Flash video via the Interactions API.
# ABOUTME: Generation and reference-to-video at 360p-4k/24fps, saved as .mp4.

import asyncio
import base64
import io
import os
import re
import time

from comfy_api.latest import IO

from .gemini_api.cooperative_call import GeminiCallInterrupted, _resolve_interrupt_checker, resolve_timeout_ms


# Stable Omni Flash 1.1 ID from the Interactions API guide. The earlier
# gemini-omni-flash-preview ID shuts down on 2026-09-30.
OMNI_MODEL = "gemini-omni-1.1-flash"

ASPECT_RATIOS = ["16:9", "9:16"]

# Values the API's validation error lists for response_format.resolution;
# 1080p and 4k are upscaled from the native render.
RESOLUTIONS = ["360p", "720p", "1080p", "4k"]
DEFAULT_RESOLUTION = "720p"

# Omni docs: "For videos larger than 4MB (>720p when available), use
# delivery="uri" in response_format to avoid payload size limits."
_URI_DELIVERY_RESOLUTIONS = {"1080p", "4k"}

_FILE_POLL_INTERVAL_S = 5
_FILE_POLL_TIMEOUT_S = 600


def _generation_task(has_image):
    return "image_to_video" if has_image else "text_to_video"


def _build_omni_video_request(task, resolution, aspect_ratio=None):
    """Build the non-content kwargs for an Omni Flash video interaction.

    Omni Flash rejects system instructions, temperature, top_p, stop sequences
    and negative prompts, so none of them appear here — put negatives in the
    prompt itself ("Do not do X"). Output is 3-10s at 24 FPS. aspect_ratio is
    omitted when None so tasks that start from a source video keep its shape.

    background/store/stream are disabled: that is the documented fast path for
    a single synchronous generation, which is what a node execution wants. URI
    delivery (1080p/4k) is the exception: the API requires store=true for it.
    """
    uri_delivery = resolution in _URI_DELIVERY_RESOLUTIONS
    response_format = {"type": "video", "resolution": resolution}
    if aspect_ratio is not None:
        response_format["aspect_ratio"] = aspect_ratio
    if uri_delivery:
        response_format["delivery"] = "uri"
    return {
        "response_format": response_format,
        "generation_config": {"video_config": {"task": task}},
        "background": False,
        "store": uri_delivery,
        "stream": False,
    }


async def _wait_for_active_file(genai_client, name, what):
    """Poll the Files API until a file is ACTIVE, returning it.

    Raises ValueError when the file FAILED, GeminiCallInterrupted on ComfyUI
    /interrupt, and TimeoutError after _FILE_POLL_TIMEOUT_S.
    """
    is_interrupted = _resolve_interrupt_checker()
    deadline = time.monotonic() + _FILE_POLL_TIMEOUT_S
    while True:
        file = await asyncio.to_thread(genai_client.files.get, name=name)
        state = getattr(file.state, "name", str(file.state))
        if state == "ACTIVE":
            return file
        if state == "FAILED":
            raise ValueError(f"Gemini Files API reports the {what} ({name}) as FAILED")
        if is_interrupted():
            raise GeminiCallInterrupted(f"Waiting for the {what} ({name}) aborted by ComfyUI /interrupt")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"The {what} ({name}) was still {state} after {_FILE_POLL_TIMEOUT_S}s")
        await asyncio.sleep(_FILE_POLL_INTERVAL_S)


async def _output_video_bytes(genai_client, interaction):
    """Return the mp4 bytes of a completed interaction, inline or by URI.

    URI delivery hands back a Files API file that has to reach ACTIVE before
    it can be downloaded.
    """
    output_video = getattr(interaction, "output_video", None)
    if output_video is not None and getattr(output_video, "data", None):
        return base64.b64decode(output_video.data)
    uri = getattr(output_video, "uri", None) if output_video is not None else None
    if uri:
        match = re.search(r"files/([a-z0-9]+)", uri)
        if match is None:
            raise ValueError(f"Omni Flash returned a video URI with no file name in it: {uri}")
        name = f"files/{match.group(1)}"
        await _wait_for_active_file(genai_client, name, "generated video")
        video_bytes = await asyncio.to_thread(genai_client.files.download, file=uri)
        await asyncio.to_thread(genai_client.files.delete, name=name)
        return video_bytes
    raise ValueError(
        "Omni Flash returned no video. This usually means the prompt was "
        "refused or the interaction is still running."
    )


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


def _image_parts(pil_images):
    """Inline PNG image parts, in the order given."""
    parts = []
    for pil_image in pil_images:
        buffer = io.BytesIO()
        pil_image.save(buffer, "PNG")
        parts.append({
            "type": "image",
            "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
            "mime_type": "image/png",
        })
    return parts


def _text_part(text):
    return {"type": "text", "text": text}


def _generation_contents(prompt, start_image):
    """Input parts for text-to-video, or image-to-video when start_image is a PIL image."""
    images = [start_image] if start_image is not None else []
    return _image_parts(images) + [_text_part(prompt)]


async def _generate_and_save(client, contents, request, output_directory):
    """Run one Omni interaction and write its video to disk, returning the path."""
    interaction = await asyncio.to_thread(
        client.client.interactions.create,
        model=OMNI_MODEL,
        input=contents,
        timeout=resolve_timeout_ms(OMNI_MODEL) / 1000,
        **request,
    )
    video_bytes = await _output_video_bytes(client.client, interaction)
    output_path = _write_video(video_bytes, output_directory)
    print(f"[Gemini Omni] Saved video to {output_path}")
    return output_path


def _resolve_client(client):
    if client is not None:
        return client
    from .gemini_api.client import GeminiClient
    return GeminiClient(api_key=None)


def _require_prompt(prompt):
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    return prompt.strip()


def _client_input():
    return IO.Custom("GEMINI_API_CLIENT").Input(
        "client",
        optional=True,
        tooltip="Gemini API client. Optional when the key is in ComfyUI Settings.",
    )


def _aspect_ratio_input():
    return IO.Combo.Input(
        "aspect_ratio",
        options=ASPECT_RATIOS,
        default="16:9",
        optional=True,
        tooltip="Video aspect ratio. Output is 24 FPS at the chosen resolution.",
    )


def _resolution_input():
    return IO.Combo.Input(
        "resolution",
        options=RESOLUTIONS,
        default=DEFAULT_RESOLUTION,
        optional=True,
        tooltip=(
            "Output resolution. 1080p and 4k are upscaled by Google and fetched "
            "through the Files API, since they exceed the 4MB inline limit. That "
            "delivery requires Google to store the interaction; the downloaded file "
            "is deleted right after."
        ),
    )


def _output_directory_input():
    return IO.String.Input(
        "output_directory",
        default="",
        optional=True,
        tooltip="Directory to save video. Empty uses the ComfyUI output folder.",
    )


def _seed_input():
    return IO.Int.Input(
        "seed",
        default=-1,
        min=-1,
        max=0xffffffff,
        optional=True,
        control_after_generate="randomize",
        tooltip=(
            "Cache control only — Omni Flash takes no API seed, so this is "
            "never sent. A fixed seed reuses the video you already paid for; "
            "-1 (randomize) generates again on every queue."
        ),
    )


def _pil_images(image):
    from .gemini_api.utils import ImageConverter
    return ImageConverter.tensors_to_pil_list(image)


class GeminiOmniVideoGeneration(IO.ComfyNode):
    """Generates video from a prompt, optionally conditioned on a start image."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiOmniVideoGeneration",
            display_name="Gemini Omni Video Generation",
            category="ERPK/Gemini",
            description=(
                "Generate 3-10s video at 24fps with Gemini Omni Flash. "
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
                _client_input(),
                IO.Image.Input(
                    "image",
                    optional=True,
                    tooltip="Optional start image. Connecting one switches the model to image-to-video.",
                ),
                _aspect_ratio_input(),
                _output_directory_input(),
                _seed_input(),
                _resolution_input(),
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
        client = _resolve_client(kwargs.get("client"))
        prompt = _require_prompt(kwargs.get("prompt", ""))
        image = kwargs.get("image")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        output_directory = kwargs.get("output_directory", "")
        resolution = kwargs.get("resolution", DEFAULT_RESOLUTION)

        start_image = None
        if image is not None:
            from .gemini_api.utils import ImageConverter
            pil_list = ImageConverter.tensors_to_pil_list(image)
            if pil_list:
                start_image = pil_list[0]

        contents = _generation_contents(prompt, start_image)
        task = _generation_task(has_image=start_image is not None)
        request = _build_omni_video_request(task, resolution, aspect_ratio=aspect_ratio)
        print(f"[Gemini Omni] {task} — {aspect_ratio}, {resolution}/24fps")

        output_path = await _generate_and_save(client, contents, request, output_directory)
        return IO.NodeOutput(output_path)


class GeminiOmniReferenceToVideo(IO.ComfyNode):
    """Generates video that features the subjects shown in reference images."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiOmniReferenceToVideo",
            display_name="Gemini Omni Reference to Video",
            category="ERPK/Gemini",
            description=(
                "Generate 3-10s video at 24fps with Gemini Omni Flash that features the "
                "people, objects or style shown in reference images."
            ),
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip=(
                        "What the video should show. Cite references in order as <IMAGE_REF_0>, "
                        "<IMAGE_REF_1>, ... e.g. 'The cat <IMAGE_REF_0> bats at <IMAGE_REF_1>'."
                    ),
                ),
                IO.Image.Input(
                    "reference_images",
                    tooltip="Reference images, sent in batch order. Use Batch Images to combine several.",
                ),
                _client_input(),
                _aspect_ratio_input(),
                _resolution_input(),
                _output_directory_input(),
                _seed_input(),
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
        client = _resolve_client(kwargs.get("client"))
        prompt = _require_prompt(kwargs.get("prompt", ""))
        references = _pil_images(kwargs.get("reference_images"))
        if not references:
            raise ValueError("Connect at least one reference image")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", DEFAULT_RESOLUTION)

        contents = _image_parts(references) + [_text_part(prompt)]
        request = _build_omni_video_request("reference_to_video", resolution, aspect_ratio=aspect_ratio)
        print(f"[Gemini Omni] reference_to_video — {len(references)} reference(s), "
              f"{aspect_ratio}, {resolution}/24fps")
        output_path = await _generate_and_save(client, contents, request, kwargs.get("output_directory", ""))
        return IO.NodeOutput(output_path)
