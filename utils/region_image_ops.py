# ABOUTME: Bakes region edits into the image tensor: composite moves, inpaint origins and cut-outs.
# ABOUTME: This is the deterministic floor; the prompt still asks the edit model to rebuild those areas.

from .region_geometry import (
    mask_pixel_box,
    region_has_stored_mask,
    region_moved,
    region_ref_image,
)
from .region_masks import _cutout_mask, _move_origin_mask, _silhouette_at


def _boxes_overlap(a, b):
    """True when two integer pixel boxes (x0, y0, x1, y1) share any area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _reapply_occluders(image, result, regions, moved, width, height):
    """Re-stamp upper objects' original pixels over the moves they sit in front of.

    A pasted move lands flat on top of whatever was below it; this restores
    depth. For every scanned region (one with a stored silhouette) that sits
    above a moved region in the back-to-front order and overlaps it, the
    region's ORIGINAL pixels are copied from `image` onto `result` along its
    silhouette — so the move ends up behind it with no transparent hole for
    the edit model to fill with a second copy. Hand-drawn boxes carry no
    silhouette and are layout guides, not physical objects, so they never
    occlude. Mutates and returns `result`.
    """
    import numpy as np
    import torch

    moved_ids = {id(region) for region in moved}
    move_boxes = [(index, mask_pixel_box(region.box, width, height))
                  for index, region in enumerate(regions)
                  if id(region) in moved_ids]
    for index, region in enumerate(regions):
        if (id(region) in moved_ids or region.op == "cutout"
                or region.kind == "text" or region_moved(region)
                or not region_has_stored_mask(region)):
            continue
        obox = mask_pixel_box(region.box, width, height)
        if not any(j < index and _boxes_overlap(obox, mbox) for j, mbox in move_boxes):
            continue
        silhouette = _silhouette_at(region, region.box, width, height)
        sel = torch.from_numpy(np.asarray(silhouette) > 0).to(result.device)
        result[:, sel] = image[:, sel]
    return result


def composite_moved_regions(image, regions):
    """Paste each moved region's source pixels at its destination.

    The canvas previews moves with a masked cut-out; this makes the move real
    in the image tensor itself, so the edit model receives the relocation as
    fact and only has to remove the original and blend — operations it
    performs far more reliably than coordinate-addressed moves. A move that
    lands under a scanned region sitting above it in the depth order is
    re-covered by that region's original pixels, so it reads as moving behind
    the object. Returns the input unchanged when there is nothing to
    composite; never mutates it.
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
    return _reapply_occluders(image, result, regions, moved, width, height)


def crop_region_subject(image, region):
    """An RGB crop of a region's source subject, for use as a reference image.

    A model move clears its origin deterministically, so the edit model has no
    in-image copy of the subject to reproduce at the destination; this crops the
    subject from the source box and, when the region carries a segmentation mask,
    isolates it on white so the reference shows it cleanly. Returns None with no
    image; never mutates the input.
    """
    if image is None:
        return None
    import numpy as np
    import torch

    height, width = int(image.shape[1]), int(image.shape[2])
    box = region.source.box if region.source is not None else region.box
    x0, y0, x1, y1 = mask_pixel_box(box, width, height)
    crop = image[:, y0:y1, x0:x1, :].clone()
    if region_has_stored_mask(region):
        silhouette = _silhouette_at(region, box, width, height)[y0:y1, x0:x1]
        keep = torch.from_numpy(np.asarray(silhouette) > 0).to(crop.device)
        crop[:, ~keep, :] = 1.0
    return crop


def composite_ref_at_box(image, ref, box):
    """Composite a reference image's auto-keyed subject into `image` at `box`.

    The ref's near-uniform border color is sampled and treated as transparent, so
    a product/cutout PNG (e.g. an object on a white background) drops cleanly into
    the scene; the subject is fit inside the box with its aspect preserved and
    centered. This makes the box authoritative for an added object's placement —
    the edit model only blends it, never repositions it. Returns the input
    unchanged when either is missing; never mutates the inputs.
    """
    if image is None or ref is None:
        return image
    import numpy as np
    import torch

    result = image.clone()
    height, width = int(result.shape[1]), int(result.shape[2])
    x0, y0, x1, y1 = mask_pixel_box(box, width, height)
    box_w, box_h = x1 - x0, y1 - y0
    ref_h, ref_w = int(ref.shape[1]), int(ref.shape[2])
    scale = min(box_w / ref_w, box_h / ref_h)
    new_w, new_h = max(1, round(ref_w * scale)), max(1, round(ref_h * scale))
    patch = torch.nn.functional.interpolate(
        ref[:, :, :, :3].permute(0, 3, 1, 2), size=(new_h, new_w),
        mode="bilinear", align_corners=False,
    ).permute(0, 2, 3, 1)
    # Auto-key: the background is the patch's border color; pixels far from it are
    # the subject. Sampling the border (not a single corner) tolerates noise.
    arr = patch[0].cpu().numpy()
    border = np.concatenate([arr[0, :, :], arr[-1, :, :], arr[:, 0, :], arr[:, -1, :]])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    keep = torch.from_numpy((dist > 0.30).astype(np.float32)).to(result.device)
    # Center the fitted subject inside the box.
    ox, oy = x0 + (box_w - new_w) // 2, y0 + (box_h - new_h) // 2
    target = result[:, oy:oy + new_h, ox:ox + new_w, :]
    blend = keep.reshape(1, new_h, new_w, 1)
    result[:, oy:oy + new_h, ox:ox + new_w, :] = patch * blend + target * (1 - blend)
    return result


# Saturated, unnatural colors used as visual placement markers ("set-of-mark"
# prompting): an edit model ignores box_2d coordinates but reads pixels, so a
# marker of one of these at an element's box center gives it a target it can
# actually see. Red is omitted because elements are often red and the marker must
# contrast with the object it marks. Names are cited verbatim in the prompt, so
# they read as natural color words.
MARKER_COLORS = [
    ("magenta", (1.0, 0.0, 1.0)),
    ("cyan", (0.0, 1.0, 1.0)),
    ("lime green", (0.6, 1.0, 0.0)),
    ("orange", (1.0, 0.5, 0.0)),
    ("yellow", (1.0, 1.0, 0.0)),
    ("hot pink", (1.0, 0.1, 0.55)),
]


def _is_model_move(region):
    """True for a relocation the edit model performs (gets a from/to marker pair)."""
    return (region_moved(region) and region.edit_by == "model"
            and region.kind != "text" and region.op != "cutout")


def assign_markers(to_mark):
    """Give each region distinct marker color(s) and label letter(s).

    Two independent identifiers make a mark unmistakable: a color name (set on
    region.marker_color, skipping any color word already in the description so a
    magenta object never gets a magenta marker) and a sequential letter A, B, C…
    (region.marker_label) that the drawn glyph and the prompt's "marker A" both
    cite. A model move is a relocation, so it gets TWO markers — its ORIGIN
    (marker_origin_color/marker_origin_label, allocated first) and its DESTINATION
    — and the prompt reads "move it from marker A to marker B". A letter, not a
    number, avoids colliding with the prompt's own numbered element list. Pure (no
    image work); all are runtime attributes the prompt reads via getattr,
    mirroring ref_image.
    """
    used = set()
    counter = 0

    def take(desc):
        nonlocal counter
        choice = next(
            (name for name, _ in MARKER_COLORS
             if name not in used and name.split()[-1] not in desc),
            None,
        )
        if choice is None:
            choice = next((name for name, _ in MARKER_COLORS if name not in used),
                          MARKER_COLORS[0][0])
        used.add(choice)
        label = chr(ord("A") + counter) if counter < 26 else str(counter + 1)
        counter += 1
        return choice, label

    for region in to_mark:
        desc = (region.content.desc or "").lower()
        if _is_model_move(region):
            region.marker_origin_color, region.marker_origin_label = take(desc)
        region.marker_color, region.marker_label = take(desc)


def _marker_font(size):
    """A bitmap font at the requested size, falling back for older Pillow."""
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _draw_marker(draw, cx, cy, r, rgb, label):
    """Draw a solid colored dot with its label letter centered inside.

    A dark halo disc sits under the colored fill so the mark stays high-contrast
    on any scene color; the label ink is black on a bright fill and white on a
    dark one (by luminance) so it reads against its own dot. Operates on a
    transparent ImageDraw surface.
    """
    draw.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=(0, 0, 0, 255))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb + (255,))
    if not label:
        return
    luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    ink = (0, 0, 0, 255) if luminance > 150 else (255, 255, 255, 255)
    font = _marker_font(max(11, int(r * 1.3)))
    # Faux-bold: a stroke in the ink color thickens the glyph so the letter reads
    # boldly on the dot (the default font has no bold weight), making the marker a
    # stronger signal the edit model is less likely to overlook.
    stroke = max(1, r // 10)
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font,
                                             stroke_width=stroke)
    tx = cx - (right - left) / 2 - left
    ty = cy - (bottom - top) / 2 - top
    draw.text((tx, ty), label, fill=ink, font=font,
              stroke_width=stroke, stroke_fill=ink)


def draw_placement_markers(image, regions):
    """Stamp a solid colored dot with a centered label letter for every region
    carrying a marker_color: at its box center, plus — for a model move — a second
    dot at its origin (marker_origin_color), so the pair reads as "from A to B".

    A bold filled dot (over a dark halo) reads on any background far better than a
    thin outline, and the letter inside gives the prompt a second referent. The
    mark sits under where the element should land, so a hit hides it and a miss
    leaves a visible dot — an honest signal. Each mark composites as a small tile
    so every non-marker pixel stays bit-exact. Returns the input unchanged with no
    image or nothing marked; never mutates it.
    """
    marked = [r for r in regions if getattr(r, "marker_color", None)]
    if image is None or not marked:
        return image
    import numpy as np
    import torch
    from PIL import Image, ImageDraw

    palette = {name: tuple(int(round(c * 255)) for c in rgb)
               for name, rgb in MARKER_COLORS}
    result = image.clone()
    height, width = int(result.shape[1]), int(result.shape[2])

    def stamp(frame, color_name, label, box):
        rgb = palette.get(color_name)
        if rgb is None:
            return
        x0, y0, x1, y1 = mask_pixel_box(box, width, height)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        r = int(min(max(min(x1 - x0, y1 - y0) * 0.18, 10), 30))
        pad = 3
        tx0, ty0 = max(0, cx - r - pad), max(0, cy - r - pad)
        tx1, ty1 = min(width, cx + r + pad), min(height, cy + r + pad)
        tw, th = tx1 - tx0, ty1 - ty0
        if tw <= 0 or th <= 0:
            return
        tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        _draw_marker(ImageDraw.Draw(tile), cx - tx0, cy - ty0, r, rgb, label)
        overlay = np.asarray(tile, dtype=np.float32) / 255.0
        alpha = overlay[:, :, 3:4]
        sub = result[frame, ty0:ty1, tx0:tx1, :].cpu().numpy()
        blended = overlay[:, :, :3] * alpha + sub * (1.0 - alpha)
        result[frame, ty0:ty1, tx0:tx1, :] = torch.from_numpy(blended).to(
            device=result.device, dtype=result.dtype)

    for frame in range(int(result.shape[0])):
        for region in marked:
            stamp(frame, region.marker_color,
                  getattr(region, "marker_label", None), region.box)
            origin_color = getattr(region, "marker_origin_color", None)
            if origin_color and region.source is not None:
                stamp(frame, origin_color,
                      getattr(region, "marker_origin_label", None),
                      region.source.box)
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

    For a node move, composite_moved_regions pastes the object at its destination
    and this erases the original (silhouette minus destination). For a model move
    nothing is composited, so the whole origin is erased — leaving it makes the
    edit model render a second copy at the destination. Cleared by inpaint, or a
    flat chroma key fill when chroma is set. Returns the input unchanged when
    nothing moved.
    """
    moved = [r for r in regions if region_moved(r) and r.kind != "text"
             and not region_ref_image(r) and r.op != "cutout"]
    if image is None or not moved:
        return image
    height, width = int(image.shape[1]), int(image.shape[2])
    return _clear_regions(image, _move_origin_mask(regions, width, height), chroma)
