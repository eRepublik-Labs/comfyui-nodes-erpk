# ABOUTME: Saves a node's image output to ComfyUI's temp dir and builds the UI payload
# ABOUTME: consumed by the web/inline_preview.js frontend extension.

import os
import time

_INLINE_PREVIEW_KEY = "erpk_inline_preview"


def inline_preview_image(cls_or_name, tensor, slot=0, ui=None):
    """Save the first frame of an IMAGE tensor to temp and merge a preview entry into `ui`.

    Pass the result as `ui=` to `IO.NodeOutput(...)`. The frontend extension reads the
    `erpk_inline_preview` key from the executed message and sets `node.imgs = [img]`,
    which causes LiteGraph to create the canvas image preview widget.

    Returns a `ui` dict ready to forward; on any failure, returns the original `ui` unchanged.
    """
    node_name = cls_or_name.__name__ if hasattr(cls_or_name, "__name__") else str(cls_or_name)
    base = dict(ui) if ui else {}

    entry = _save_image_safe(tensor, node_name, slot)
    if entry is None:
        return base

    existing = list(base.get(_INLINE_PREVIEW_KEY, []))
    existing.append(entry)
    base[_INLINE_PREVIEW_KEY] = existing
    return base


def _save_image_safe(tensor, node_name, slot):
    try:
        import folder_paths
        import numpy as np
        from PIL import Image
    except ImportError:
        return None

    if not _looks_like_image_tensor(tensor):
        return None

    try:
        temp_dir = folder_paths.get_temp_directory()
        os.makedirs(temp_dir, exist_ok=True)

        frame = tensor[0]
        arr = frame.detach().cpu().numpy() if hasattr(frame, "detach") else (
            frame.cpu().numpy() if hasattr(frame, "cpu") else frame
        )
        arr = (arr * 255.0).clip(0, 255).astype(np.uint8)

        channels = arr.shape[-1] if arr.ndim == 3 else 1
        if channels == 1:
            img = Image.fromarray(arr.squeeze(-1) if arr.ndim == 3 else arr, mode="L")
        elif channels == 4:
            img = Image.fromarray(arr, mode="RGBA")
        else:
            img = Image.fromarray(arr, mode="RGB")

        ts = int(time.time() * 1000)
        filename = f"erpk_preview_{node_name}_{slot}_{ts}.png"
        img.save(os.path.join(temp_dir, filename), format="PNG", compress_level=4)

        return {
            "type": "image",
            "slot": slot,
            "filename": filename,
            "subfolder": "",
            "dir_type": "temp",
            "width": img.width,
            "height": img.height,
        }
    except Exception as exc:
        print(f"[ERPK inline_preview] image save failed for {node_name}: {exc}")
        return None


def _looks_like_image_tensor(value):
    shape = getattr(value, "shape", None)
    if shape is None:
        return False
    if len(shape) != 4:
        return False
    return shape[-1] in (1, 3, 4)
