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


# xAI's image endpoints go through gRPC; xai-sdk 1.20 caps a sent message at
# 20 MiB (grpc.max_send_message_length in xai_sdk/client.py). PNG + base64 is
# far too large for multi-image requests, so images are encoded as JPEG with
# the longest edge capped.
_JPEG_QUALITY = 90
_MAX_EDGE = 2048
# Per-image raw JPEG budget.
_PAYLOAD_BUDGET_BYTES = 3_500_000
# Raw JPEG budget shared by all images in one request. Base64 adds 4/3, so
# 14.5 MB raw is about 18.4 MiB on the wire, leaving room for the prompt and
# envelope under the 20 MiB cap. Five 2048px edit sources need this split.
_REQUEST_BUDGET_BYTES = 14_500_000
# Below this edge a reference stops being useful; fail instead of sending mush.
_MIN_EDGE = 256


def image_to_data_uri(image, budget_bytes: int = _PAYLOAD_BUDGET_BYTES) -> Optional[str]:
    """Convert a ComfyUI IMAGE tensor or PIL Image to a `data:image/jpeg;base64,...` URI.

    Used wherever xAI's image-edit / reference-to-video / video-edit APIs accept
    an image as base64 data URI alongside HTTPS URLs. JPEG quality is dropped
    progressively, then the image is downscaled, until the encode fits
    `budget_bytes`. Raises ValueError if it cannot fit above _MIN_EDGE.
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

    # Step quality down first (60 is the floor before artifacts get distracting
    # for edit references), then shrink the image and try again.
    while True:
        for quality in (_JPEG_QUALITY, 80, 70, 60):
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= budget_bytes:
                break
        if len(data) <= budget_bytes:
            break
        smaller = (int(pil.size[0] * 0.8), int(pil.size[1] * 0.8))
        if min(smaller) < _MIN_EDGE:
            raise ValueError(
                f"Image does not fit the {budget_bytes}-byte request budget even at "
                f"{pil.size[0]}x{pil.size[1]}, JPEG quality 60."
            )
        pil = pil.resize(smaller, PILImage.LANCZOS)
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def images_to_data_uris(images, max_count: int = 3) -> List[str]:
    """Convert a batch IMAGE tensor or list of images to a list of data URIs.

    The caller passes the count cap for its endpoint (GrokClient.MAX_EDIT_IMAGES
    or MAX_REFERENCE_IMAGES). All images share _REQUEST_BUDGET_BYTES so the
    request stays under the SDK's 20 MiB gRPC send limit.
    """
    if images is None:
        return []
    out: List[str] = []
    # Batch tensor: iterate slices
    if hasattr(images, "shape") and len(images.shape) == 4 and torch is not None:
        n = min(images.shape[0], max_count)
        budget = min(_PAYLOAD_BUDGET_BYTES, _REQUEST_BUDGET_BYTES // max(n, 1))
        for i in range(n):
            uri = image_to_data_uri(images[i:i + 1], budget)
            if uri:
                out.append(uri)
        return out
    # List of images / URLs / PIL
    if isinstance(images, (list, tuple)):
        selected = images[:max_count]
        budget = min(_PAYLOAD_BUDGET_BYTES, _REQUEST_BUDGET_BYTES // max(len(selected), 1))
        for img in selected:
            if isinstance(img, str):
                # Already a URL or data URI
                out.append(img)
            else:
                uri = image_to_data_uri(img, budget)
                if uri:
                    out.append(uri)
        return out
    # Single image fallback
    uri = image_to_data_uri(images)
    return [uri] if uri else []
