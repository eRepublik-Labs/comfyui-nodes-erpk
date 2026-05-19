# ABOUTME: ComfyUI V3 utility node that previews any input: text, markdown, URLs, images, video, audio.
# ABOUTME: Detects content type server-side and hands a typed payload to the frontend renderer.

import os
import re
import time
from urllib.parse import urlparse

from comfy_api.latest import IO


_STRIP_METADATA_TOOLTIP = (
    "Re-encode image URL inputs to strip EXIF / ICC / XMP metadata (GPS, "
    "camera info, timestamps) before download. Only applies to image URLs; "
    "IMAGE tensor inputs are already metadata-free. Text, video, audio, and "
    "non-image URLs are unaffected."
)


_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "avif"}
_GIF_EXTS = {"gif", "apng"}
_VIDEO_EXTS = {"mp4", "webm", "mov", "m4v", "mkv", "ogv"}
_AUDIO_EXTS = {"mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"}

_MARKDOWN_HINTS = re.compile(
    r"(^#{1,6}\s)|(^\s*[-*+]\s)|(^\s*\d+\.\s)|(```)|(^>\s)|(\*\*[^*]+\*\*)|(`[^`]+`)|(\[[^\]]+\]\([^)]+\))",
    re.MULTILINE,
)


class PreviewAnything(IO.ComfyNode):
    """Preview any ComfyUI value: text, markdown, URLs, images, video, audio."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ERPK_PreviewAnything",
            display_name="Preview Anything",
            category="ERPK/utils",
            description=(
                "Preview any input. Strings are inspected: URLs with image/video/audio "
                "extensions render as media; others render as text or markdown. IMAGE "
                "tensors and AUDIO dicts are saved to the temp folder and rendered. "
                "A download button saves the content to your computer."
            ),
            inputs=[
                IO.AnyType.Input(
                    "value",
                    tooltip="Any content. Strings, URLs, IMAGE tensors, AUDIO dicts, or any Python value.",
                ),
                IO.Combo.Input(
                    "display_type",
                    options=["auto", "text", "markdown", "image", "gif", "video", "audio"],
                    default="auto",
                    optional=True,
                    tooltip="How to render. 'auto' picks based on the input.",
                ),
                IO.String.Input(
                    "filename",
                    default="preview",
                    optional=True,
                    tooltip="Base filename used when downloading.",
                ),
                IO.Boolean.Input(
                    "strip_metadata",
                    default=False,
                    optional=True,
                    tooltip=_STRIP_METADATA_TOOLTIP,
                ),
            ],
            outputs=[],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, value=None, display_type="auto", filename="preview",
                strip_metadata=False, **kwargs) -> IO.NodeOutput:
        payload = _build_payload(value, display_type, filename, strip_metadata)
        return IO.NodeOutput(ui={"preview_anything": [payload]})


def _build_payload(value, display_type: str, filename: str, strip_metadata: bool = False) -> dict:
    if display_type and display_type != "auto":
        return _forced_payload(value, display_type, filename)

    if _is_image_tensor(value):
        # Batched IMAGE tensor (N > 1): emit a gallery payload so the frontend
        # can show all N images. Previously only the first image was saved.
        if _is_batched_image(value):
            urls = _save_image_tensor_batch(value, filename)
            if urls:
                return {"kind": "image_gallery", "urls": urls, "filename": filename}
        saved = _save_image_tensor(value, filename)
        if saved is not None:
            return {"kind": "image", "url": saved, "filename": filename}

    if _is_audio_dict(value):
        saved = _save_audio_dict(value, filename)
        if saved is not None:
            return {"kind": "audio", "url": saved, "filename": filename}

    if isinstance(value, str):
        return _payload_from_string(value, filename, strip_metadata)

    text = _stringify(value)
    return {"kind": "text", "text": text, "filename": filename}


def _forced_payload(value, display_type: str, filename: str) -> dict:
    if display_type in ("text", "markdown"):
        text = value if isinstance(value, str) else _stringify(value)
        return {"kind": display_type, "text": text, "filename": filename}

    if isinstance(value, str):
        return {"kind": display_type, "url": value, "filename": filename}

    if display_type == "image" and _is_image_tensor(value):
        saved = _save_image_tensor(value, filename)
        if saved is not None:
            return {"kind": "image", "url": saved, "filename": filename}

    if display_type == "audio" and _is_audio_dict(value):
        saved = _save_audio_dict(value, filename)
        if saved is not None:
            return {"kind": "audio", "url": saved, "filename": filename}

    return {"kind": "text", "text": _stringify(value), "filename": filename}


def _payload_from_string(value: str, filename: str, strip_metadata: bool = False) -> dict:
    # If the value is an absolute filesystem path to a file under one of
    # ComfyUI's served directories (output / temp / input), rewrite it to
    # the /view URL form so the browser can actually fetch the bytes.
    # Otherwise the absolute path passes _url_kind (scheme="" + startswith("/"))
    # but the browser then 404s on /Users/.../output/<file>.mp4.
    served = _local_path_to_view_url(value)
    if served is not None:
        value = served

    url_kind = _url_kind(value)
    if url_kind is not None:
        url = value
        # Image-only metadata stripping (EXIF/ICC/XMP). Re-encode server-side
        # so the Download button serves the clean copy. Non-image URL kinds
        # pass through untouched — stripping video/audio needs ffmpeg, which
        # is out of scope for this node.
        if strip_metadata and url_kind in ("image", "gif"):
            stripped = _reencode_image_url_without_metadata(url, filename)
            if stripped is not None:
                url = stripped
        return {"kind": url_kind, "url": url, "filename": filename}

    if _looks_like_markdown(value):
        return {"kind": "markdown", "text": value, "filename": filename}

    return {"kind": "text", "text": value, "filename": filename}


def _reencode_image_url_without_metadata(url: str, filename: str):
    """Fetch an image URL, re-encode with PIL to strip all metadata,
    save to ComfyUI's temp dir, return the /view URL for the clean copy.

    Returns None (caller falls back to original URL) on any error — fetch
    failure, unsupported format, or missing dependencies. Logs a warning
    so users can debug.
    """
    try:
        import io
        from PIL import Image
        import folder_paths
    except ImportError as e:
        print(f"[PreviewAnything] strip_metadata: missing dep ({e}); passing original URL")
        return None

    raw_bytes = _fetch_url_bytes(url)
    if raw_bytes is None:
        return None

    try:
        from .safe_fetch import safe_image_decode
        with safe_image_decode():
            original = Image.open(io.BytesIO(raw_bytes))
            original.load()  # force decode before creating clean copy
            # Create a fresh image containing ONLY pixel data. Paste drops
            # EXIF / ICC profile / XMP / all format-specific metadata.
            clean = Image.new(original.mode, original.size)
            clean.paste(original)
            fmt = original.format or "PNG"
    except Exception as e:
        print(f"[PreviewAnything] strip_metadata: PIL decode failed ({e}); passing original URL")
        return None

    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)
    ext = _EXT_BY_PIL_FORMAT.get(fmt.upper(), "png")
    name = f"{_safe(filename)}_stripped_{int(time.time() * 1000)}.{ext}"
    path = os.path.join(temp_dir, name)

    try:
        # Preserve source format but don't pass exif= / icc_profile= / xmp=
        if fmt.upper() in ("JPEG", "JPG"):
            clean.save(path, format="JPEG", quality=95)
        else:
            clean.save(path, format=fmt)
    except Exception as e:
        print(f"[PreviewAnything] strip_metadata: PIL save failed ({e}); passing original URL")
        return None

    return _view_url(name, "", "temp")


_EXT_BY_PIL_FORMAT = {
    "JPEG": "jpg",
    "JPG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
    "BMP": "bmp",
    "GIF": "gif",
    "TIFF": "tiff",
}


_IMAGE_MAX_BYTES = 100 * 1024 * 1024
_LOOPBACK_MAX_BYTES = 500 * 1024 * 1024


def _fetch_url_bytes(url: str, timeout_seconds: int = 30):
    """Fetch URL content as bytes. Handles http(s), data:, and local /view?
    paths (served by the same ComfyUI instance via loopback).

    Returns None on any fetch error; caller should log and fall back.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            from .safe_fetch import fetch_remote_bytes
            return fetch_remote_bytes(
                url,
                max_bytes=_IMAGE_MAX_BYTES,
                timeout=timeout_seconds,
                user_agent="ERPK-PreviewAnything/1.0",
            )
        if parsed.scheme == "data":
            # data:<mediatype>;base64,<payload>
            header, _, payload = url.partition(",")
            if "base64" in header:
                import base64
                return base64.b64decode(payload)
            from urllib.parse import unquote_to_bytes
            return unquote_to_bytes(payload)
        if parsed.scheme == "" and url.startswith("/"):
            # ComfyUI serves /view?filename=X&type=Y on its own loopback port;
            # this branch deliberately targets 127.0.0.1 and bypasses the IP
            # blocklist. Bounded by _LOOPBACK_MAX_BYTES to prevent OOM if
            # someone crafts a /view URL pointing at a huge served file.
            import urllib.request
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:8188{url}", timeout=timeout_seconds) as resp:
                    data = resp.read(_LOOPBACK_MAX_BYTES + 1)
                    if len(data) > _LOOPBACK_MAX_BYTES:
                        return None
                    return data
            except Exception:
                return None
        return None
    except Exception as e:
        print(f"[PreviewAnything] strip_metadata: URL fetch failed for {url!r} ({e})")
        return None


def _url_kind(value: str):
    # Accept absolute URLs (http/https/file/data) AND server-relative paths
    # starting with "/" — ComfyUI serves temp files via /view?filename=X.ext
    # patterns, which urlparse reports with an empty scheme.
    parsed = urlparse(value)
    scheme_ok = parsed.scheme in ("http", "https", "file", "data")
    relative_ok = parsed.scheme == "" and value.startswith("/")
    if not (scheme_ok or relative_ok):
        return None

    # Path extension first; fall back to query-string `filename=X.ext`
    # (our own /view?filename= pattern doesn't put the extension in the path).
    ext = _ext_from_url(parsed.path) or _ext_from_query(parsed.query)
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _GIF_EXTS:
        return "gif"
    if ext in _VIDEO_EXTS:
        return "video"
    if ext in _AUDIO_EXTS:
        return "audio"
    return None


def _ext_from_url(path: str) -> str:
    base = os.path.basename(path)
    if "." not in base:
        return ""
    return base.rsplit(".", 1)[-1].lower()


def _ext_from_query(query: str) -> str:
    """Extract extension from a `filename=X.ext` query parameter, if present."""
    if not query:
        return ""
    from urllib.parse import parse_qs
    params = parse_qs(query)
    names = params.get("filename") or []
    if not names:
        return ""
    return _ext_from_url(names[0])


def _looks_like_markdown(text: str) -> bool:
    return bool(_MARKDOWN_HINTS.search(text))


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        try:
            import json
            return json.dumps(value, indent=2, default=str)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _is_image_tensor(value) -> bool:
    try:
        import torch
        return isinstance(value, torch.Tensor) and value.ndim in (3, 4)
    except ImportError:
        return False


def _is_batched_image(value) -> bool:
    """True if value is a ComfyUI IMAGE tensor with a batch size > 1."""
    try:
        import torch
        return (
            isinstance(value, torch.Tensor)
            and value.ndim == 4
            and value.shape[0] > 1
        )
    except ImportError:
        return False


def _is_audio_dict(value) -> bool:
    return (
        isinstance(value, dict)
        and "waveform" in value
        and "sample_rate" in value
    )


def _save_image_tensor(tensor, filename: str):
    try:
        import numpy as np
        from PIL import Image
        import folder_paths
    except ImportError:
        return None

    if tensor.ndim == 4:
        tensor = tensor[0]
    array = tensor.detach().cpu().numpy()
    if array.dtype != np.uint8:
        array = (array.clip(0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

    img = Image.fromarray(array)
    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)
    name = f"{_safe(filename)}_{int(time.time() * 1000)}.png"
    path = os.path.join(temp_dir, name)
    img.save(path)
    return _view_url(name, "", "temp")


def _save_image_tensor_batch(tensor, filename: str):
    """Save each image in a [N,H,W,C] batch tensor to ComfyUI's temp dir.

    Returns a list of /view URLs in batch order, or None on any error.
    """
    try:
        import numpy as np
        from PIL import Image
        import folder_paths
    except ImportError:
        return None

    if tensor.ndim != 4 or tensor.shape[0] < 1:
        return None

    array_all = tensor.detach().cpu().numpy()
    if array_all.dtype != np.uint8:
        array_all = (array_all.clip(0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)
    stem = _safe(filename)
    ts = int(time.time() * 1000)

    urls = []
    for i in range(array_all.shape[0]):
        img = Image.fromarray(array_all[i])
        name = f"{stem}_{ts}_{i + 1}.png"
        path = os.path.join(temp_dir, name)
        img.save(path)
        urls.append(_view_url(name, "", "temp"))
    return urls


def _save_audio_dict(audio, filename: str):
    try:
        import folder_paths
    except ImportError:
        return None

    waveform = audio["waveform"]
    sample_rate = int(audio["sample_rate"])
    if waveform.ndim == 3:
        waveform = waveform[0]
    waveform = waveform.detach().cpu()

    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)
    name = f"{_safe(filename)}_{int(time.time() * 1000)}.wav"
    path = os.path.join(temp_dir, name)

    try:
        import torchaudio
        torchaudio.save(path, waveform, sample_rate)
    except ImportError:
        # torchaudio.save in 2.x delegates to torchcodec; if torchcodec is not
        # installed, fall back to a stdlib WAV writer. 16-bit PCM is the WAV
        # default and matches torchaudio's default for float inputs.
        _write_wav_pcm16(path, waveform, sample_rate)
    return _view_url(name, "", "temp")


def _write_wav_pcm16(path: str, waveform, sample_rate: int) -> None:
    import wave
    import numpy as np
    array = waveform.numpy()
    if array.ndim == 1:
        array = array[None, :]
    channels, samples = array.shape
    interleaved = array.T.reshape(-1)
    interleaved = np.clip(interleaved, -1.0, 1.0)
    pcm16 = (interleaved * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())


def _view_url(filename: str, subfolder: str, folder_type: str) -> str:
    from urllib.parse import quote
    parts = [f"filename={quote(filename)}"]
    if subfolder:
        parts.append(f"subfolder={quote(subfolder)}")
    parts.append(f"type={folder_type}")
    return "/view?" + "&".join(parts)


def _local_path_to_view_url(value: str):
    """Convert an absolute filesystem path under ComfyUI's served directories
    into the /view URL form the frontend can fetch. Returns None if the value
    isn't an absolute path, doesn't exist, or sits outside output/temp/input.
    """
    if not value or not os.path.isabs(value):
        return None
    try:
        if not os.path.isfile(value):
            return None
        import folder_paths
    except Exception:
        return None

    real = os.path.realpath(value)
    dir_map = (
        ("output", folder_paths.get_output_directory()),
        ("temp", folder_paths.get_temp_directory()),
        ("input", folder_paths.get_input_directory()),
    )
    for folder_type, base in dir_map:
        if not base:
            continue
        try:
            base_real = os.path.realpath(base)
        except Exception:
            continue
        rel = os.path.relpath(real, base_real)
        if rel.startswith("..") or os.path.isabs(rel):
            continue
        # rel is something like "veo_i2v_1234.mp4" or "subdir/clip.mp4"
        subfolder, fname = os.path.split(rel)
        return _view_url(fname, subfolder, folder_type)
    return None


def _safe(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", name or "preview")
    return cleaned[:64] or "preview"
