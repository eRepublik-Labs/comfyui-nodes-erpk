# ABOUTME: Decodes box-relative segmentation masks and renders per-region mask tensors.
# ABOUTME: numpy/PIL/torch are imported lazily so the module loads without the ComfyUI runtime.

from .region_geometry import mask_pixel_box, region_has_stored_mask, region_moved


def build_region_masks(regions, width, height):
    """Render one [height, width] mask per region into an [N, height, width] tensor.

    Regions with a stored segmentation mask are decoded, thresholded at 127, and
    placed at their box offset; regions without one (or whose mask fails to
    decode) fall back to a filled rectangle so a scan never fails the build. With
    no regions, returns a single all-zero mask as a ComfyUI-friendly placeholder.
    """
    # Imported lazily so the module stays importable without the ComfyUI runtime;
    # this is the only torch/numpy/PIL touch in the function.
    import base64
    from io import BytesIO

    import numpy as np
    import torch
    from PIL import Image

    # Cut-out regions are removed entirely (they erase to transparent in the
    # image output instead of contributing a mask slot).
    regions = [r for r in regions if r.op != "cutout"]
    if not regions:
        return torch.zeros((1, height, width))
    frames = []
    for region in regions:
        frame = np.zeros((height, width), dtype=np.float32)
        x0, y0, x1, y1 = mask_pixel_box(region.box, width, height)
        rendered = False
        if region_has_stored_mask(region):
            try:
                raw = base64.b64decode(region.source.mask.data)
                glyph = Image.open(BytesIO(raw)).convert("L")
                glyph = glyph.resize((x1 - x0, y1 - y0))
                probs = np.asarray(glyph, dtype=np.float32)
                frame[y0:y1, x0:x1] = (probs > 127).astype(np.float32)
                rendered = True
            except Exception:
                rendered = False
        if not rendered:
            frame[y0:y1, x0:x1] = 1.0
        frames.append(frame)
    return torch.from_numpy(np.stack(frames)).float()


def _cutout_mask(regions, width, height):
    """uint8 [height, width] mask, 255 where cut-out regions are to be filled.

    Each cut-out region contributes its stored segmentation silhouette, or its
    whole box when it has no mask; the union is returned. Cut-outs sit at the
    lowest depth, so the area covered by ANY kept (non-cut-out) region overlapping
    a cut-out is spared — a cut-out clears the background behind it, never an
    element kept on top of it, whatever the layer order. All-zero when there are
    no cut-outs. numpy/PIL only, so the fill geometry is unit-testable without cv2.
    """
    import base64
    from io import BytesIO

    import numpy as np
    from PIL import Image

    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if region.op != "cutout" or region.kind == "text":
            continue
        if region.edit_by == "model":
            continue  # the edit model removes this one; leave the pixels
        x0, y0, x1, y1 = mask_pixel_box(region.box, width, height)
        bw, bh = x1 - x0, y1 - y0
        patch = np.full((bh, bw), 255, dtype=np.uint8)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region.source.mask.data)))
                glyph = glyph.convert("L").resize((bw, bh))
                patch = ((np.asarray(glyph) > 127).astype(np.uint8)) * 255
            except Exception:
                pass
        # Zero the part of this cut-out covered by any kept region so an element
        # kept on top is never erased (cut-outs are the lowest depth).
        for other in regions:
            if other.op == "cutout":
                continue
            fx0, fy0, fx1, fy1 = mask_pixel_box(other.box, width, height)
            ix0, iy0 = max(x0, fx0), max(y0, fy0)
            ix1, iy1 = min(x1, fx1), min(y1, fy1)
            if ix1 > ix0 and iy1 > iy0:
                patch[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = 0
        mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], patch)
    return mask


def _move_origin_mask(regions, width, height):
    """uint8 [height, width] mask, 255 over each moved region's leftover origin.

    For each moved region the origin is its source silhouette (or src box when
    maskless) MINUS the destination box — so a move-in-place or scale that covers
    its own origin erases only the part sticking out, never the fresh paste.
    All-zero when nothing moved. numpy/PIL only (cv2-free, so unit-testable).
    """
    import base64
    from io import BytesIO

    import numpy as np
    from PIL import Image

    from .region_geometry import region_ref_image

    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if (not region_moved(region) or region.kind == "text"
                or region_ref_image(region) or region.op == "cutout"
                or region.edit_by == "model"):
            continue
        sx0, sy0, sx1, sy1 = mask_pixel_box(region.source.box, width, height)
        bw, bh = sx1 - sx0, sy1 - sy0
        patch = np.full((bh, bw), 255, dtype=np.uint8)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region.source.mask.data)))
                glyph = glyph.convert("L").resize((bw, bh))
                patch = ((np.asarray(glyph) > 127).astype(np.uint8)) * 255
            except Exception:
                pass
        # Zero the part of this origin covered by the destination box so the
        # freshly pasted copy is never erased.
        dx0, dy0, dx1, dy1 = mask_pixel_box(region.box, width, height)
        ix0, iy0 = max(sx0, dx0), max(sy0, dy0)
        ix1, iy1 = min(sx1, dx1), min(sy1, dy1)
        if ix1 > ix0 and iy1 > iy0:
            patch[iy0 - sy0:iy1 - sy0, ix0 - sx0:ix1 - sx0] = 0
        mask[sy0:sy1, sx0:sx1] = np.maximum(mask[sy0:sy1, sx0:sx1], patch)
    return mask
