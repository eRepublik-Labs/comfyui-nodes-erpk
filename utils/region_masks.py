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


def _silhouette_at(region, box, width, height):
    """Full-image uint8 mask (255) with the region's stored silhouette — or its
    whole box when maskless — rendered at `box`. Shared primitive for cut-out and
    move-origin geometry so they subtract real shapes, not bounding rectangles.
    """
    import base64
    from io import BytesIO

    import numpy as np
    from PIL import Image

    x0, y0, x1, y1 = mask_pixel_box(box, width, height)
    patch = np.full((y1 - y0, x1 - x0), 255, dtype=np.uint8)
    if region_has_stored_mask(region):
        try:
            glyph = Image.open(BytesIO(base64.b64decode(region.source.mask.data)))
            glyph = glyph.convert("L").resize((x1 - x0, y1 - y0))
            patch = ((np.asarray(glyph) > 127).astype(np.uint8)) * 255
        except Exception:
            pass
    full = np.zeros((height, width), dtype=np.uint8)
    full[y0:y1, x0:x1] = patch
    return full


def _cutout_mask(regions, width, height):
    """uint8 [height, width] mask, 255 where cut-out regions are to be filled.

    Each cut-out region contributes its stored segmentation silhouette, or its
    whole box when it has no mask; the union is returned. Cut-outs sit at the
    lowest depth, so the SILHOUETTE of any kept (non-cut-out) region overlapping
    a cut-out is spared — a cut-out clears the background behind it, never an
    element kept on top of it, whatever the layer order. Sparing the kept
    silhouette (not its box) leaves the background around a kept object fillable.
    All-zero when there are no cut-outs. numpy/PIL only, unit-testable without cv2.
    """
    import numpy as np

    kept = np.zeros((height, width), dtype=np.uint8)
    for other in regions:
        if other.op != "cutout":
            kept = np.maximum(kept, _silhouette_at(other, other.box, width, height))
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if region.op != "cutout" or region.kind == "text" or region.edit_by == "model":
            continue
        cut = _silhouette_at(region, region.box, width, height)
        mask = np.maximum(mask, cut & ~kept)
    return mask


def _move_origin_mask(regions, width, height):
    """uint8 [height, width] mask, 255 over each moved region's leftover origin.

    For each moved region the origin is its source silhouette (or src box when
    maskless) MINUS the destination silhouette — the area the pasted copy actually
    covers, not its bounding box — so the whole original is cleared except where
    the fresh paste truly lands (a box subtraction left ghost pixels behind on a
    short move). All-zero when nothing moved. numpy/PIL only, unit-testable.
    """
    import numpy as np

    from .region_geometry import region_ref_image

    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if (not region_moved(region) or region.kind == "text"
                or region_ref_image(region) or region.op == "cutout"
                or region.edit_by == "model"):
            continue
        origin = _silhouette_at(region, region.source.box, width, height)
        paste = _silhouette_at(region, region.box, width, height)
        mask = np.maximum(mask, origin & ~paste)
    return mask
