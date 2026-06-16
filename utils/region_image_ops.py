# ABOUTME: Bakes region edits into the image tensor: composite moves, inpaint origins and cut-outs.
# ABOUTME: This is the deterministic floor; the prompt still asks the edit model to rebuild those areas.

from .region_geometry import (
    mask_pixel_box,
    region_has_stored_mask,
    region_moved,
    region_ref_image,
)
from .region_masks import _cutout_mask, _move_origin_mask


def composite_moved_regions(image, regions):
    """Paste each moved region's source pixels at its destination.

    The canvas previews moves with a masked cut-out; this makes the move real
    in the image tensor itself, so the edit model receives the relocation as
    fact and only has to remove the original and blend — operations it
    performs far more reliably than coordinate-addressed moves. Returns the
    input unchanged when there is nothing to composite; never mutates it.
    """
    moved = [r for r in regions
             if region_moved(r) and r.kind != "text"
             and not region_ref_image(r) and r.op != "cutout"
             and r.edit_by != "model"]
    if image is None or not moved:
        return image
    # Imported lazily, mirroring build_region_masks: the only torch touch.
    import base64
    from io import BytesIO

    import numpy as np
    import torch
    from PIL import Image

    result = image.clone()
    height, width = int(result.shape[1]), int(result.shape[2])
    for region in moved:
        sx0, sy0, sx1, sy1 = mask_pixel_box(region.source.box, width, height)
        dx0, dy0, dx1, dy1 = mask_pixel_box(region.box, width, height)
        dw, dh = dx1 - dx0, dy1 - dy0
        patch = image[:, sy0:sy1, sx0:sx1, :].permute(0, 3, 1, 2)
        patch = torch.nn.functional.interpolate(
            patch, size=(dh, dw), mode="bilinear", align_corners=False,
        ).permute(0, 2, 3, 1)
        alpha = torch.ones((dh, dw), device=result.device, dtype=result.dtype)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region.source.mask.data)))
                glyph = glyph.convert("L").resize((dw, dh))
                probs = np.asarray(glyph, dtype=np.float32) / 255.0
                alpha = torch.from_numpy((probs > 0.5).astype(np.float32)).to(
                    device=result.device, dtype=result.dtype)
            except Exception:
                pass
        blend = alpha.reshape(1, dh, dw, 1)
        target = result[:, dy0:dy1, dx0:dx1, :]
        result[:, dy0:dy1, dx0:dx1, :] = patch * blend + target * (1 - blend)
    return result


def _inpaint_regions(image, mask):
    """Inpaint an image tensor's masked pixels from their surroundings.

    image is float [B,H,W,3]; mask is uint8 [H,W] (255 = fill). Returns the
    input unchanged when the mask is empty or OpenCV is missing (a ComfyUI core
    dependency, so absence is logged, not fatal); never mutates the input.
    """
    import numpy as np
    import torch

    if image is None or mask is None or not mask.any():
        return image
    try:
        import cv2
    except ImportError:
        print("[ERPK] Warning: OpenCV unavailable; removed/moved areas left unfilled")
        return image
    result = image.clone()
    for frame in range(int(result.shape[0])):
        rgb = (result[frame, :, :, :3].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        filled = cv2.inpaint(rgb, mask, 4, cv2.INPAINT_TELEA)
        result[frame, :, :, :3] = torch.from_numpy(filled.astype(np.float32) / 255.0)
    return result


def _hex_to_rgb01(value):
    """Parse "#rrggbb" into an (r, g, b) tuple of 0..1 floats.

    Falls back to chroma green on anything unparseable, so a malformed widget
    value never breaks the fill.
    """
    default = (0.0, 0.690, 0.251)  # chroma green #00B140
    if not isinstance(value, str):
        return default
    text = value.lstrip("#")
    if len(text) != 6:
        return default
    try:
        return tuple(int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return default


def _fill_regions(image, mask, color):
    """Paint an image tensor's masked pixels a flat color (chroma key fill).

    image is float [B,H,W,3]; mask is uint8 [H,W] (255 = fill); color is an
    (r,g,b) 0..1 tuple. A flat fill is the clean alternative to inpaint for the
    no-model path — a downstream chroma keyer can remove it. Never mutates input.
    """
    import numpy as np
    import torch

    if image is None or mask is None or not mask.any():
        return image
    result = image.clone()
    sel = torch.from_numpy(np.asarray(mask) > 0).to(result.device)
    for channel in range(3):
        result[:, :, :, channel][:, sel] = float(color[channel])
    return result


def _clear_regions(image, mask, chroma):
    """Clear masked pixels: flat chroma key when chroma is a hex color, else inpaint."""
    if chroma:
        return _fill_regions(image, mask, _hex_to_rgb01(chroma))
    return _inpaint_regions(image, mask)


def apply_cutouts(image, regions, chroma=None):
    """Remove each cut-out region from the scene's masked area.

    A cut-out region (Shift+Delete in the editor) is erased: its masked
    silhouette — or its whole box when it has no stored mask — is filled from the
    surrounding pixels (OpenCV inpaint), or flat-filled with a chroma key color
    when chroma is a hex string. Returns the input unchanged with no cut-outs.
    """
    cuts = [r for r in regions if r.op == "cutout" and r.kind != "text"
            and r.edit_by != "model"]
    if image is None or not cuts:
        return image
    height, width = int(image.shape[1]), int(image.shape[2])
    return _clear_regions(image, _cutout_mask(regions, width, height), chroma)


def apply_move_origin_cutouts(image, regions, chroma=None):
    """Clear the leftover origin of each moved region so it does not appear twice.

    composite_moved_regions pastes a moved object at its destination but leaves
    the original behind; this erases that original (silhouette minus destination)
    by inpaint, or a flat chroma key fill when chroma is set, making the move's
    removal deterministic. Returns the input unchanged when nothing moved.
    """
    moved = [r for r in regions if region_moved(r) and r.kind != "text"
             and not region_ref_image(r) and r.op != "cutout"
             and r.edit_by != "model"]
    if image is None or not moved:
        return image
    height, width = int(image.shape[1]), int(image.shape[2])
    return _clear_regions(image, _move_origin_mask(regions, width, height), chroma)
