# ABOUTME: Image helpers for the Grok provider — tensor→data-URI conversion for SDK image inputs.
# ABOUTME: xAI requires JSON bodies (not multipart), so images must be base64 data URIs or HTTPS URLs.

import base64
import io
from typing import List, Optional, Union

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

try:
    import torch
    import numpy as np
except ImportError:
    torch = None
    np = None


def tensor_to_pil(image) -> Optional["PILImage.Image"]:
    """Convert a ComfyUI IMAGE tensor (B,H,W,C float32 0-1) to a PIL Image.

    Returns the first image in the batch. Returns None if the tensor is None
    or PIL/torch aren't available (test environment).
    """
    if image is None:
        return None
    if PILImage is None or torch is None or np is None:
        return None
    if hasattr(image, "shape") and len(image.shape) == 4:
        arr = image[0].detach().cpu().numpy()
    elif hasattr(image, "shape") and len(image.shape) == 3:
        arr = image.detach().cpu().numpy() if hasattr(image, "detach") else image
    else:
        return None
    arr = (arr * 255.0).clip(0, 255).astype("uint8")
    return PILImage.fromarray(arr)


# xAI's image-edit endpoint goes through gRPC, which has a 4 MB
# (4_194_304-byte) default max message size. PNG + base64 blows past this for
# any reasonably-detailed source image (a 3 MB PNG becomes 4 MB+ after base64,
# plus the rest of the gRPC envelope). Encode as JPEG to stay well under, and
# cap the longest edge so high-res inputs don't slip through.
_JPEG_QUALITY = 90
_MAX_EDGE = 2048
# Leave headroom for the rest of the gRPC message (prompt, model, metadata).
_PAYLOAD_BUDGET_BYTES = 3_500_000


def image_to_data_uri(image) -> Optional[str]:
    """Convert a ComfyUI IMAGE tensor or PIL Image to a `data:image/jpeg;base64,...` URI.

    Used wherever xAI's image-edit / reference-to-video / video-edit APIs accept
    an image as base64 data URI alongside HTTPS URLs. Encoded as JPEG to stay
    under xAI's 4 MB gRPC message limit; quality is dropped progressively if the
    first encode exceeds the per-image payload budget.
    """
    if image is None:
        return None
    if PILImage is not None and isinstance(image, PILImage.Image):
        pil = image
    else:
        pil = tensor_to_pil(image)
    if pil is None:
        return None

    # Downscale if either dimension exceeds the cap. Preserves aspect ratio.
    if max(pil.size) > _MAX_EDGE:
        pil.thumbnail((_MAX_EDGE, _MAX_EDGE), PILImage.LANCZOS)

    # JPEG doesn't support RGBA; convert any alpha to RGB on white background.
    if pil.mode not in ("RGB", "L"):
        if pil.mode in ("RGBA", "LA"):
            bg = PILImage.new("RGB", pil.size, (255, 255, 255))
            bg.paste(pil, mask=pil.split()[-1])
            pil = bg
        else:
            pil = pil.convert("RGB")

    # Encode at the configured quality; if the result is still over budget,
    # step down quality before giving up. 4 MB is a hard wall; 60 quality is
    # the floor before visible artifacts get distracting for edit references.
    for quality in (_JPEG_QUALITY, 80, 70, 60):
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= _PAYLOAD_BUDGET_BYTES:
            break
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def images_to_data_uris(images, max_count: int = 3) -> List[str]:
    """Convert a batch IMAGE tensor or list of images to a list of data URIs.

    xAI multi-image edit accepts up to 3 source images. Caller is responsible
    for enforcing the count cap appropriate to its endpoint.
    """
    if images is None:
        return []
    out: List[str] = []
    # Batch tensor: iterate slices
    if hasattr(images, "shape") and len(images.shape) == 4 and torch is not None:
        n = min(images.shape[0], max_count)
        for i in range(n):
            uri = image_to_data_uri(images[i:i + 1])
            if uri:
                out.append(uri)
        return out
    # List of images / URLs / PIL
    if isinstance(images, (list, tuple)):
        for img in images[:max_count]:
            if isinstance(img, str):
                # Already a URL or data URI
                out.append(img)
            else:
                uri = image_to_data_uri(img)
                if uri:
                    out.append(uri)
        return out
    # Single image fallback
    uri = image_to_data_uri(images)
    return [uri] if uri else []
