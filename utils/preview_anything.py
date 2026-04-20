# ABOUTME: ComfyUI V3 utility node that previews any input: text, markdown, URLs, images, video, audio.
# ABOUTME: Detects content type server-side and hands a typed payload to the frontend renderer.

import os
import re
import time
from urllib.parse import urlparse

from comfy_api.latest import IO


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
            ],
            outputs=[],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, value=None, display_type="auto", filename="preview", **kwargs) -> IO.NodeOutput:
        payload = _build_payload(value, display_type, filename)
        return IO.NodeOutput(ui={"preview_anything": [payload]})


def _build_payload(value, display_type: str, filename: str) -> dict:
    if display_type and display_type != "auto":
        return _forced_payload(value, display_type, filename)

    if _is_image_tensor(value):
        saved = _save_image_tensor(value, filename)
        if saved is not None:
            return {"kind": "image", "url": saved, "filename": filename}

    if _is_audio_dict(value):
        saved = _save_audio_dict(value, filename)
        if saved is not None:
            return {"kind": "audio", "url": saved, "filename": filename}

    if isinstance(value, str):
        return _payload_from_string(value, filename)

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


def _payload_from_string(value: str, filename: str) -> dict:
    url_kind = _url_kind(value)
    if url_kind is not None:
        return {"kind": url_kind, "url": value, "filename": filename}

    if _looks_like_markdown(value):
        return {"kind": "markdown", "text": value, "filename": filename}

    return {"kind": "text", "text": value, "filename": filename}


def _url_kind(value: str):
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https", "file", "data"):
        return None
    ext = _ext_from_url(parsed.path)
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


def _save_audio_dict(audio, filename: str):
    try:
        import torchaudio
        import folder_paths
    except ImportError:
        return None

    waveform = audio["waveform"]
    sample_rate = int(audio["sample_rate"])
    if waveform.ndim == 3:
        waveform = waveform[0]

    temp_dir = folder_paths.get_temp_directory()
    os.makedirs(temp_dir, exist_ok=True)
    name = f"{_safe(filename)}_{int(time.time() * 1000)}.wav"
    path = os.path.join(temp_dir, name)
    torchaudio.save(path, waveform.detach().cpu(), sample_rate)
    return _view_url(name, "", "temp")


def _view_url(filename: str, subfolder: str, folder_type: str) -> str:
    from urllib.parse import quote
    parts = [f"filename={quote(filename)}"]
    if subfolder:
        parts.append(f"subfolder={quote(subfolder)}")
    parts.append(f"type={folder_type}")
    return "/view?" + "&".join(parts)


def _safe(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", name or "preview")
    return cleaned[:64] or "preview"
