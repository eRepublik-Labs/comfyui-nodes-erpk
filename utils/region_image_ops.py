# ABOUTME: Bakes region edits into the image tensor: composite moves, inpaint origins and cut-outs.
# ABOUTME: Reports what was applied so the prompt can describe only the edits the model still owes.

from dataclasses import dataclass

from .region_geometry import (
    mask_pixel_box,
    region_has_stored_mask,
    region_moved,
    region_ref_image,
)
from .region_masks import _cutout_mask, _move_origin_mask


@dataclass
class PreprocessReport:
    """Counts the deterministic edits baked into the image before prompting.

    The prompt builder reads these to decide its wording: an inpainted origin or
    cut-out is already natural background, so the model is told to keep it rather
    than to remove a leftover that is no longer there.
    """

    pasted_moves: int = 0
    inpainted_origins: int = 0
    inpainted_cutouts: int = 0
    cv2_available: bool = False


def composite_moved_regions(image, regions):
    """Paste each moved region's source pixels at its destination.

    The canvas previews moves with a masked cut-out; this makes the move real
    in the image tensor itself, so the edit model receives the relocation as
    fact and only has to remove the original and blend — operations it
    performs far more reliably than coordinate-addressed moves. Returns the
    input unchanged when there is nothing to composite; never mutates it.
    Returns (image, PreprocessReport) where pasted_moves counts the pastes.
    """
    moved = [r for r in regions
             if region_moved(r) and r.kind != "text"
             and not region_ref_image(r) and r.op != "cutout"]
    if image is None or not moved:
        return image, PreprocessReport()
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
    return result, PreprocessReport(pasted_moves=len(moved))


def _inpaint_regions(image, mask):
    """Inpaint an image tensor's masked pixels from their surroundings.

    image is float [B,H,W,3]; mask is uint8 [H,W] (255 = fill). Returns
    (image, cv2_ran): the input unchanged when the mask is empty or OpenCV is
    missing (a ComfyUI core dependency, so absence is logged, not fatal) with
    cv2_ran False; never mutates the input.
    """
    import numpy as np
    import torch

    if image is None or mask is None or not mask.any():
        return image, False
    try:
        import cv2
    except ImportError:
        print("[ERPK] Warning: OpenCV unavailable; removed/moved areas left unfilled")
        return image, False
    result = image.clone()
    for frame in range(int(result.shape[0])):
        rgb = (result[frame, :, :, :3].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
        filled = cv2.inpaint(rgb, mask, 4, cv2.INPAINT_TELEA)
        result[frame, :, :, :3] = torch.from_numpy(filled.astype(np.float32) / 255.0)
    return result, True


def apply_cutouts(image, regions):
    """Remove each cut-out region by inpainting its masked area from the scene.

    A cut-out region (Shift+Delete in the editor) is erased: its masked
    silhouette — or its whole box when it has no stored mask — is filled in from
    the surrounding pixels (OpenCV), so the object is seamlessly gone while the
    output stays RGB. Returns the input unchanged when there are no cut-outs.
    Returns (image, PreprocessReport); inpainted_cutouts counts the cut-outs
    filled (0 when OpenCV is unavailable).
    """
    cuts = [r for r in regions if r.op == "cutout" and r.kind != "text"]
    if image is None or not cuts:
        return image, PreprocessReport()
    height, width = int(image.shape[1]), int(image.shape[2])
    result, cv2_ran = _inpaint_regions(image, _cutout_mask(regions, width, height))
    return result, PreprocessReport(
        inpainted_cutouts=len(cuts) if cv2_ran else 0, cv2_available=cv2_ran)


def apply_move_origin_cutouts(image, regions):
    """Inpaint the leftover origin of each moved region so it does not appear twice.

    composite_moved_regions pastes a moved object at its destination but leaves
    the original behind; this erases that original (silhouette minus destination)
    from the surrounding pixels, making the move's removal deterministic instead
    of relying on the edit model. Returns the input unchanged when nothing moved.
    Returns (image, PreprocessReport); inpainted_origins counts the origins filled
    (0 when OpenCV is unavailable).
    """
    moved = [r for r in regions if region_moved(r) and r.kind != "text"
             and not region_ref_image(r) and r.op != "cutout"]
    if image is None or not moved:
        return image, PreprocessReport()
    height, width = int(image.shape[1]), int(image.shape[2])
    result, cv2_ran = _inpaint_regions(image, _move_origin_mask(regions, width, height))
    return result, PreprocessReport(
        inpainted_origins=len(moved) if cv2_ran else 0, cv2_available=cv2_ran)
