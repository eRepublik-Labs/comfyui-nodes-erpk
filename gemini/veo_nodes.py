# ABOUTME: ComfyUI V3 nodes for Google Veo video generation API.
# ABOUTME: Provides text-to-video and image-to-video generation nodes.

import asyncio
import os
import time
import tempfile

from comfy_api.latest import IO


VEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.1-fast-generate-preview",
    "veo-3.1-lite-generate-preview",
    "veo-3.0-generate-001",
    "veo-3.0-fast-generate-001",
    "veo-2.0-generate-001",
]

VEO_ASPECT_RATIOS = ["16:9", "9:16"]
# Combo options must be strings for ComfyUI's left/right arrow cycling to work
# (integer-option combos hit a type mismatch in indexOf). Parsed back to int in execute().
VEO_DURATIONS = ["4", "5", "6", "8"]
VEO_RESOLUTIONS = ["720p", "1080p", "4k"]
VEO_PERSON_GENERATION_OPTIONS = ["allow_adult", "dont_allow", "allow_all"]


_VEO_LITE = "veo-3.1-lite-generate-preview"
_VEO_2 = "veo-2.0-generate-001"
_VEO_3_FAMILY = {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}
_VEO_31_FAMILY = {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"}

# Per-model capability gates derived from
# https://ai.google.dev/gemini-api/docs/video and the lite preview model card.
_MODELS_NO_4K = {_VEO_LITE, _VEO_2}
_MODELS_NO_RESOLUTION_PARAM = {_VEO_2}        # Veo 2 has no resolution control; skip the param.
_MODELS_WITH_REFERENCE_IMAGES = _VEO_31_FAMILY  # Lite, Veo 3, Veo 2 do not support reference_images.


def _veo_valid_durations(model):
    """Allowed durationSeconds values per the Veo API parameters table."""
    if model == _VEO_2:
        return {5, 6, 8}
    return {4, 6, 8}


def _validate_veo_config(model, duration, resolution, has_reference_images=False):
    """Normalize duration / resolution against per-model rules.

    Returns (duration, resolution_or_None, warnings). `has_reference_images` is
    used by the 8s gate on Veo 3.1 family + Lite, where 8s requires either an
    upscaled resolution or reference images.
    """
    warnings = []
    valid_durations = _veo_valid_durations(model)
    if duration not in valid_durations:
        nearest = min(valid_durations, key=lambda x: abs(x - duration))
        warnings.append(
            f"duration={duration}s is not supported by {model} (valid: {sorted(valid_durations)}); "
            f"using {nearest}s instead"
        )
        duration = nearest

    if model in _MODELS_NO_RESOLUTION_PARAM:
        if resolution and resolution != "720p":
            warnings.append(
                f"{model} does not accept a resolution parameter; dropping resolution={resolution}"
            )
        return duration, None, warnings

    if resolution == "4k" and model in _MODELS_NO_4K:
        warnings.append(f"{model} does not support 4k output; clamping to 1080p")
        resolution = "1080p"

    # 8s gate per Veo API docs: 8s requires resolution >= 1080p OR reference_images.
    # Applies uniformly across all Veo 3.x models; Veo 2 has no such gate.
    if duration == 8 and model != _VEO_2:
        if resolution == "720p" and not has_reference_images:
            warnings.append(
                f"{model} requires resolution >= 1080p (or reference_images) for 8s output; "
                f"bumping resolution from 720p to 1080p"
            )
            resolution = "1080p"

    return duration, resolution, warnings


def _veo_valid_person_generation(model, is_image_to_video):
    """Allowed person_generation values per the Gemini Developer API.

    Veo 3.x image-to-video rejects allow_all server-side; only allow_adult and
    dont_allow are accepted. Veo 2 and all text-to-video paths accept the full
    enum. The API returns 400 INVALID_ARGUMENT with the message
    "allow_all for personGeneration is currently not supported" when violated.
    """
    veo_3x_models = _VEO_31_FAMILY | _VEO_3_FAMILY | {_VEO_LITE}
    if is_image_to_video and model in veo_3x_models:
        return {"allow_adult", "dont_allow"}
    return set(VEO_PERSON_GENERATION_OPTIONS)


def _validate_person_generation(model, person_generation, is_image_to_video):
    """Raise ValueError if person_generation is not accepted for this model/mode."""
    valid = _veo_valid_person_generation(model, is_image_to_video)
    if person_generation in valid:
        return
    mode = "image-to-video" if is_image_to_video else "text-to-video"
    raise ValueError(
        f"{model} {mode} does not accept person_generation={person_generation!r}; "
        f"valid values are: {sorted(valid)}"
    )


def _validate_interpolation_constraints(has_last_frame, has_reference_images, duration, aspect_ratio):
    """Raise ValueError if i2v feature combos violate Veo's undocumented gates.

    Per community-confirmed reports (https://discuss.ai.google.dev/t/veo-3-1-reference-images-docs-say-available-api-says-not-supported/111853
    and https://discuss.ai.google.dev/t/veo-3-1-last-frame-parameter-not-supported/107529),
    the Gemini Developer API returns the opaque "Your use case is currently not supported"
    400 when these combos are violated, often AFTER running a 4-5 minute generation pipeline:

    - image + last_frame interpolation requires duration_seconds=8 (4s/6s rejected).
    - reference_images requires duration_seconds=8.
    - reference_images requires aspect_ratio=16:9 (9:16 rejected).
    - reference_images is mutually exclusive with image/last_frame (the API rejects
      requests that mix them).

    None of these are in Google's parameter table — they're docs gaps confirmed by
    Google staff and developers in the linked forum threads.
    """
    if has_last_frame and duration != 8:
        raise ValueError(
            f"Veo image+last_frame interpolation requires duration_seconds=8 "
            f"(got {duration}). The Gemini API rejects 4s and 6s for interpolation "
            f"with an opaque 'use case not supported' 400 after running generation. "
            f"Set duration_seconds to 8."
        )
    if has_reference_images:
        if duration != 8:
            raise ValueError(
                f"Veo reference_images requires duration_seconds=8 (got {duration}). "
                f"Set duration_seconds to 8."
            )
        if aspect_ratio != "16:9":
            raise ValueError(
                f"Veo reference_images requires aspect_ratio='16:9' (got {aspect_ratio!r}). "
                f"9:16 is not currently supported with reference_images."
            )
        if has_last_frame:
            raise ValueError(
                "Veo reference_images is mutually exclusive with last_frame_image. "
                "Disconnect one of them."
            )


def _pil_to_genai_image(pil_image, suffix=".png"):
    """Persist a PIL image to a temp file and return (types.Image, tmp_path).

    Caller is responsible for deleting tmp_path after the API call returns.
    """
    from google.genai import types
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    pil_image.save(tmp.name, "PNG")
    return types.Image.from_file(location=tmp.name), tmp.name


def _build_reference_images(image_batch, max_count=3):
    """Convert a ComfyUI IMAGE batch tensor into a list of types.Image objects.

    Returns (reference_image_list, temp_paths_to_clean_up). The caller must
    delete the temp paths once the generate_videos call returns. Capped at
    `max_count` slices (Veo 3.1 supports up to 3 reference images).
    """
    if image_batch is None:
        return None, []
    from .gemini_api.utils import ImageConverter
    pil_list = ImageConverter.tensors_to_pil_list(image_batch)
    if not pil_list:
        return None, []
    pil_list = pil_list[:max_count]
    images = []
    temp_paths = []
    for pil in pil_list:
        img, path = _pil_to_genai_image(pil)
        images.append(img)
        temp_paths.append(path)
    return images, temp_paths


def _save_video(video, client, output_directory, prefix):
    """Save a Veo response video to disk, returning the output path."""
    if output_directory and output_directory.strip():
        out_dir = output_directory.strip()
    else:
        import folder_paths
        out_dir = folder_paths.get_output_directory()
    os.makedirs(out_dir, exist_ok=True)
    timestamp = int(time.time())
    output_path = os.path.join(out_dir, f"{prefix}_{timestamp}.mp4")

    # Gemini Developer API returns videos as remote URIs; Vertex AI returns inline bytes.
    # files.download() fetches the URI authenticated and sets video_bytes as a side effect,
    # so the uniform video.save() call below works for both backends.
    if not getattr(video, "video_bytes", None):
        if not getattr(video, "uri", None):
            raise ValueError("Could not extract video data from response (no bytes, no URI)")
        client.client.files.download(file=video)

    video.save(output_path)
    return output_path


async def _poll_until_done(operation, client, max_minutes=40):
    """Poll until a Veo operation completes; returns the completed operation.

    Uses await asyncio.sleep so the event loop is free for other parallel Veo
    or Gemini nodes between status checks. operations.get runs in a thread so
    the sync SDK call doesn't block the loop during the HTTP round-trip.
    """
    poll_count = 0
    max_polls = max_minutes * 3  # 20s intervals → 3 polls/min
    while not operation.done:
        poll_count += 1
        if poll_count > max_polls:
            raise TimeoutError(f"Video generation timed out after {max_minutes} minutes")
        print(f"[Veo] Waiting for video generation... ({poll_count * 20}s elapsed)")
        await asyncio.sleep(20)
        operation = await asyncio.to_thread(client.client.operations.get, operation)
    return operation


def _veo_models_for(target):
    """Filter model list to those supporting the given capability tag."""
    if target == "reference_images":
        return [m for m in VEO_MODELS if m in _MODELS_WITH_REFERENCE_IMAGES]
    return VEO_MODELS


class VeoTextToVideo(IO.ComfyNode):
    """Generates videos from text prompts using Google's Veo models.
    Veo 3 generates videos with synchronized audio."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="VeoTextToVideo",
            display_name="Veo Text to Video",
            category="ERPK/Gemini/Veo",
            description="Generate video from a text prompt using Veo.",
            not_idempotent=True,
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Gemini API client from Gemini API Config node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings > GOOGLE_API_KEY (or env / config.ini)."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip=(
                        "Text description of the video to generate (max 2500 characters). "
                        "Supports audio cues: quote dialogue, describe sound effects and ambient noise."
                    ),
                ),
                IO.Image.Input(
                    "reference_images",
                    optional=True,
                    tooltip=(
                        "Up to 3 reference images (batched IMAGE) for style/content guidance. "
                        "Only supported on Veo 3.1 and Veo 3.1 Fast. Ignored on Lite, Veo 3, Veo 2."
                    ),
                ),
                IO.Combo.Input(
                    "model",
                    options=VEO_MODELS,
                    default="veo-3.1-generate-preview",
                    optional=True,
                    tooltip=(
                        "Veo model. Lite is cheapest (no 4k, no extension, no reference images). "
                        "Veo 3.1 / 3.1 Fast support reference images. Veo 2 has no resolution control."
                    ),
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=VEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Video aspect ratio (16:9 landscape, 9:16 portrait)",
                ),
                IO.Combo.Input(
                    "resolution",
                    options=VEO_RESOLUTIONS,
                    default="720p",
                    optional=True,
                    tooltip=(
                        "Output resolution. 4k is Veo 3.1 / Fast only. Lite caps at 1080p. "
                        "8s output requires 1080p (or 4k where supported) or reference_images. "
                        "Veo 2 ignores this parameter (always 720p)."
                    ),
                ),
                IO.Combo.Input(
                    "duration_seconds",
                    options=VEO_DURATIONS,
                    default="8",
                    optional=True,
                    tooltip=(
                        "Video duration. Veo 3.x (all variants): 4/6/8s. Veo 2: 5/6/8s. "
                        "8s output requires 1080p (or 4k where supported) or reference_images. "
                        "Mismatched values are auto-clamped to the nearest valid choice."
                    ),
                ),
                IO.Combo.Input(
                    "person_generation",
                    options=VEO_PERSON_GENERATION_OPTIONS,
                    default="allow_adult",
                    optional=True,
                    tooltip=(
                        "Person generation safety. EU/UK/CH/MENA: Veo 3.x limited to allow_adult. "
                        "Veo 3.x text-to-video only accepts allow_all."
                    ),
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xffffffff,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation. The Gemini Developer API does not "
                        "accept a seed for video generation (only Vertex/Enterprise mode does), so "
                        "this value is not forwarded — but changing it still forces a fresh run. "
                        "-1 for random."
                    ),
                ),
                IO.String.Input(
                    "output_directory",
                    default="",
                    optional=True,
                    tooltip="Directory to save video. Empty uses ComfyUI output folder.",
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
        reference_images = kwargs.get("reference_images")
        model = kwargs.get("model", "veo-3.1-generate-preview")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "720p")
        duration_seconds = int(kwargs.get("duration_seconds", 8))
        person_generation = kwargs.get("person_generation", "allow_adult")
        output_directory = kwargs.get("output_directory", "")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if len(prompt) > 2500:
            print(f"[Veo] Warning: Prompt exceeds 2500 characters, truncating")
            prompt = prompt[:2500]

        has_refs = reference_images is not None and model in _MODELS_WITH_REFERENCE_IMAGES
        duration_seconds, resolution, warnings = _validate_veo_config(
            model, duration_seconds, resolution, has_reference_images=has_refs
        )
        for w in warnings:
            print(f"[Veo] {w}")
        _validate_person_generation(model, person_generation, is_image_to_video=False)

        temp_paths_to_clean = []

        try:
            from google.genai import types

            print(f"[Veo] Generating video with model: {model}")
            print(f"[Veo] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[Veo] Aspect ratio: {aspect_ratio}, Duration: {duration_seconds}s, Resolution: {resolution or 'model-default'}")

            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }
            if resolution:
                config_params["resolution"] = resolution
            # Seed is preserved for ComfyUI cache invalidation via fingerprint_inputs but
            # not forwarded — the Gemini Developer API rejects seed; only Vertex/Enterprise
            # mode accepts it, which we don't use.

            if reference_images is not None:
                if model not in _MODELS_WITH_REFERENCE_IMAGES:
                    print(f"[Veo] Warning: {model} does not support reference_images; ignoring")
                else:
                    ref_list, ref_paths = _build_reference_images(reference_images, max_count=3)
                    temp_paths_to_clean.extend(ref_paths)
                    if ref_list:
                        config_params["reference_images"] = ref_list
                        print(f"[Veo] Using {len(ref_list)} reference image(s)")

            config = types.GenerateVideosConfig(**config_params)

            request_params = {
                "model": model,
                "prompt": prompt.strip(),
                "config": config,
            }

            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = await asyncio.to_thread(
                client.client.models.generate_videos, **request_params
            )

            operation = await _poll_until_done(operation, client)

            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated (likely safety filter — Veo does not charge for blocked generations)")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            output_path = _save_video(video, client, output_directory, prefix="veo")
            print(f"[Veo] Video saved successfully: {output_path}")
            return IO.NodeOutput(output_path)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)
        finally:
            for path in temp_paths_to_clean:
                try:
                    os.unlink(path)
                except Exception:
                    pass


class VeoImageToVideo(IO.ComfyNode):
    """Generates videos from an input image and optional text prompt.
    The image serves as the first frame; an optional last_frame_image enables
    first-to-last frame interpolation on Veo 3.x."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="VeoImageToVideo",
            display_name="Veo Image to Video",
            category="ERPK/Gemini/Veo",
            description="Generate video from an image (and optional last frame) using Veo.",
            not_idempotent=True,
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip=(
                        "Gemini API client from Gemini API Config node. "
                        "Optional: when unconnected, the key is resolved from "
                        "ComfyUI Settings > GOOGLE_API_KEY (or env / config.ini)."
                    ),
                ),
                IO.Image.Input(
                    "image",
                    tooltip="First frame of the video (required)",
                ),
                IO.Image.Input(
                    "last_frame_image",
                    optional=True,
                    tooltip=(
                        "Optional last frame for first-to-last interpolation. "
                        "Supported on all Veo 3.x models including Lite, and Veo 2. "
                        "REQUIRES duration_seconds=8 — the API rejects 4s/6s interpolation "
                        "with an opaque 'use case not supported' 400 after running generation."
                    ),
                ),
                IO.Image.Input(
                    "reference_images",
                    optional=True,
                    tooltip=(
                        "Up to 3 reference images (batched IMAGE) for style/content guidance. "
                        "Only supported on Veo 3.1 and Veo 3.1 Fast. "
                        "REQUIRES duration_seconds=8 and aspect_ratio=16:9. "
                        "Mutually exclusive with last_frame_image."
                    ),
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip=(
                        "Optional text description to guide the video. "
                        "Supports audio cues for Veo 3.x."
                    ),
                ),
                IO.Combo.Input(
                    "model",
                    options=VEO_MODELS,
                    default="veo-3.1-generate-preview",
                    optional=True,
                    tooltip=(
                        "Veo model. Lite is cheapest (no 4k, no reference images). "
                        "Veo 3.1 / 3.1 Fast support reference images. Veo 2 has no resolution control."
                    ),
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=VEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Video aspect ratio (16:9 landscape, 9:16 portrait)",
                ),
                IO.Combo.Input(
                    "resolution",
                    options=VEO_RESOLUTIONS,
                    default="720p",
                    optional=True,
                    tooltip=(
                        "Output resolution. 1080p and 4k require duration=8s. "
                        "Lite caps at 1080p. Veo 2 ignores this parameter."
                    ),
                ),
                IO.Combo.Input(
                    "duration_seconds",
                    options=VEO_DURATIONS,
                    default=8,
                    optional=True,
                    tooltip=(
                        "Video duration. Veo 3.x (all variants): 4/6/8s. Veo 2: 5/6/8s. "
                        "8s output requires 1080p (or 4k where supported) or reference_images. "
                        "Mismatched values are auto-clamped to the nearest valid choice."
                    ),
                ),
                IO.Combo.Input(
                    "person_generation",
                    options=VEO_PERSON_GENERATION_OPTIONS,
                    default="allow_adult",
                    optional=True,
                    tooltip=(
                        "Person generation safety. EU/UK/CH/MENA: Veo 3.x limited to allow_adult. "
                        "Veo 3.x image-to-video rejects allow_all; use allow_adult or dont_allow."
                    ),
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xffffffff,
                    optional=True,
                    control_after_generate="randomize",
                    tooltip=(
                        "Seed for ComfyUI cache invalidation. The Gemini Developer API does not "
                        "accept a seed for video generation (only Vertex/Enterprise mode does), so "
                        "this value is not forwarded — but changing it still forces a fresh run. "
                        "-1 for random."
                    ),
                ),
                IO.String.Input(
                    "output_directory",
                    default="",
                    optional=True,
                    tooltip="Directory to save video. Empty uses ComfyUI output folder.",
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
        from .gemini_api.utils import ImageConverter

        client = kwargs.get("client")
        if client is None:
            from .gemini_api.client import GeminiClient
            client = GeminiClient(api_key=None)
        image = kwargs.get("image")
        last_frame_image = kwargs.get("last_frame_image")
        reference_images = kwargs.get("reference_images")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "veo-3.1-generate-preview")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        resolution = kwargs.get("resolution", "720p")
        duration_seconds = int(kwargs.get("duration_seconds", 8))
        person_generation = kwargs.get("person_generation", "allow_adult")
        output_directory = kwargs.get("output_directory", "")

        has_refs = reference_images is not None and model in _MODELS_WITH_REFERENCE_IMAGES
        duration_seconds, resolution, warnings = _validate_veo_config(
            model, duration_seconds, resolution, has_reference_images=has_refs
        )
        for w in warnings:
            print(f"[Veo] {w}")
        _validate_person_generation(model, person_generation, is_image_to_video=True)
        _validate_interpolation_constraints(
            has_last_frame=last_frame_image is not None,
            has_reference_images=reference_images is not None and model in _MODELS_WITH_REFERENCE_IMAGES,
            duration=duration_seconds,
            aspect_ratio=aspect_ratio,
        )

        temp_paths_to_clean = []

        try:
            from google.genai import types

            pil_image = ImageConverter.tensor_to_pil(image)
            print(f"[Veo] Input image size: {pil_image.size}")

            genai_image, first_tmp = _pil_to_genai_image(pil_image)
            temp_paths_to_clean.append(first_tmp)

            print(f"[Veo] Generating video from image with model: {model}")
            if prompt and prompt.strip():
                print(f"[Veo] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[Veo] Aspect ratio: {aspect_ratio}, Duration: {duration_seconds}s, Resolution: {resolution or 'model-default'}")

            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }
            if resolution:
                config_params["resolution"] = resolution
            # Seed is preserved for ComfyUI cache invalidation via fingerprint_inputs but
            # not forwarded — the Gemini Developer API rejects seed; only Vertex/Enterprise
            # mode accepts it, which we don't use.

            if last_frame_image is not None:
                last_pil = ImageConverter.tensor_to_pil(last_frame_image)
                last_genai, last_tmp = _pil_to_genai_image(last_pil)
                temp_paths_to_clean.append(last_tmp)
                config_params["last_frame"] = last_genai
                print(f"[Veo] Using last_frame for first→last interpolation")

            if reference_images is not None:
                if model not in _MODELS_WITH_REFERENCE_IMAGES:
                    print(f"[Veo] Warning: {model} does not support reference_images; ignoring")
                else:
                    ref_list, ref_paths = _build_reference_images(reference_images, max_count=3)
                    temp_paths_to_clean.extend(ref_paths)
                    if ref_list:
                        config_params["reference_images"] = ref_list
                        print(f"[Veo] Using {len(ref_list)} reference image(s)")

            config = types.GenerateVideosConfig(**config_params)

            request_params = {
                "model": model,
                "image": genai_image,
                "config": config,
            }

            if prompt and prompt.strip():
                if len(prompt) > 2500:
                    print(f"[Veo] Warning: Prompt exceeds 2500 characters, truncating")
                    prompt = prompt[:2500]
                request_params["prompt"] = prompt.strip()

            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = await asyncio.to_thread(
                client.client.models.generate_videos, **request_params
            )

            operation = await _poll_until_done(operation, client)

            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated (likely safety filter — Veo does not charge for blocked generations)")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            output_path = _save_video(video, client, output_directory, prefix="veo_i2v")
            print(f"[Veo] Video saved successfully: {output_path}")
            return IO.NodeOutput(output_path)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)
        finally:
            for path in temp_paths_to_clean:
                try:
                    os.unlink(path)
                except Exception:
                    pass
