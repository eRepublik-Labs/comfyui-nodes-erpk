# ABOUTME: Pure prompt-builder node that turns canvas-drawn regions into a layout-aware
# ABOUTME: image-generation prompt plus interoperable pixel bounding boxes.

import json
import math

from comfy_api.latest import IO

REGION_KINDS = {"object", "text"}
MIN_REGION_EXTENT = 0.005
# Socket-only description overrides; desc_N feeds the region numbered N on
# the canvas (numbers are depth order, so reordering remaps the wires).
DESC_INPUT_COUNT = 10
# Per-region reference images; ref_N attaches to the region numbered N. The
# wired images flow out on image_refs in region order, and the prompt counts
# them from 2 because the edit node's base image occupies slot 1.
REF_INPUT_COUNT = 10

# "Bounding box" is detection-annotation vocabulary: models that know it from
# vision training will happily RENDER yellow boxes around the elements. The
# template calls them invisible placement areas and forbids drawing them.
LAYOUT_HEADER = (
    "Layout: place each element exactly where specified. Each position gives a "
    'verbal placement plus its placement area as "box_2d = [ymin, xmin, ymax, xmax]" '
    "on a 0-1000 grid with top-left origin. Elements are listed from back to "
    "front: where placement areas overlap, a later element appears in front of "
    "an earlier one."
)
REFS_HEADER = (
    "Numbered images accompany this request: image 1 is the image being "
    "edited, and elements below reference later images by number. Reproduce "
    "each referenced item faithfully (shape, colors, materials, markings), "
    "adapting it to the scene's lighting and perspective. Keep everything "
    "else in image 1 unchanged."
)
# Edits lead the prompt: buried inside a long placement list that mostly
# matches the existing image, move instructions lose to "reproduce the input".
# The move itself is already composited into the image the model receives
# (composite_moved_regions), so the prompt only asks for what edit models do
# reliably: remove the original and blend the pasted copy.
REPOSITION_HEADER = (
    "Elements in this image were repositioned by pasting them at their new "
    "locations, so each still has a leftover duplicate at its old position. "
    'Make these edits (areas are "box_2d = [ymin, xmin, ymax, xmax]" on a '
    "0-1000 grid with top-left origin):"
)
ANCHORS_LINE = (
    "Every other element in the image stays exactly where it is — do not "
    "remove, add, or alter anything else."
)
# Cut-out regions are already content-aware-filled in the image the model
# receives (apply_cutouts), but an edit model repaints freely, so the prompt
# must tell it to keep those areas as plain background — without naming what was
# there, which would invite re-adding it.
REMOVAL_HEADER = (
    "Remove the contents of these areas: rebuild each as natural background that "
    "continues the surrounding scene (same surfaces, texture, lighting, and "
    "perspective). Do not place any object, subject, animal, plant, sign, or "
    'text in them (areas are "box_2d = [ymin, xmin, ymax, xmax]" on a 0-1000 '
    "grid with top-left origin):"
)
LAYOUT_FOOTER = (
    "Every element must stay fully inside its placement area and fill most of it. "
    "Do not add other prominent subjects. The placement areas are invisible "
    "composition guides: never draw boxes, frames, outlines, coordinates, or any "
    "annotation overlays in the image."
)


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def parse_regions(regions_json):
    """Parse the canvas editor's JSON into clamped, validated region dicts."""
    try:
        raw = json.loads(regions_json)
    except (TypeError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    regions = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        try:
            x = float(entry.get("x", 0))
            y = float(entry.get("y", 0))
            w = float(entry.get("w", 0))
            h = float(entry.get("h", 0))
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in (x, y, w, h)):
            continue
        x = _clamp(x, 0.0, 1.0)
        y = _clamp(y, 0.0, 1.0)
        w = _clamp(w, 0.0, 1.0 - x)
        h = _clamp(h, 0.0, 1.0 - y)
        if w <= MIN_REGION_EXTENT or h <= MIN_REGION_EXTENT:
            continue
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind not in REGION_KINDS:
            kind = "object"
        desc = entry.get("desc", "")
        if not isinstance(desc, str):
            desc = ""
        text = entry.get("text", "")
        if not isinstance(text, str):
            text = ""
        region = {"x": x, "y": y, "w": w, "h": h,
                  "kind": kind, "desc": desc, "text": text}
        # Scan-produced regions carry a box-relative base64 PNG segmentation mask
        # and a class-label group; hand-drawn regions omit both and stay compact.
        mask = entry.get("mask")
        if isinstance(mask, str) and mask:
            region["mask"] = mask
        group = entry.get("group")
        if isinstance(group, str) and group:
            region["group"] = group
        # Layer-group links: a stable id and an optional parent id. Groups
        # are organizational only — prompt, bboxes, and masks stay flat.
        region_id = entry.get("id")
        if isinstance(region_id, str) and region_id:
            region["id"] = region_id
        parent = entry.get("parent")
        if isinstance(parent, str) and parent:
            region["parent"] = parent
        src = _parse_src_box(entry.get("src"))
        if src is not None:
            region["src"] = src
        # A cut-out region: removed from prompt/bboxes/masks, and its masked
        # pixels are erased to transparent in the image output (Shift+Delete).
        if entry.get("cutout"):
            region["cutout"] = True
        regions.append(region)
    return regions


def _parse_src_box(value):
    """Validate and clamp a region's origin box; None when unusable."""
    if not isinstance(value, dict):
        return None
    try:
        x = float(value.get("x"))
        y = float(value.get("y"))
        w = float(value.get("w"))
        h = float(value.get("h"))
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in (x, y, w, h)):
        return None
    x = _clamp(x, 0.0, 1.0)
    y = _clamp(y, 0.0, 1.0)
    w = _clamp(w, 0.0, 1.0 - x)
    h = _clamp(h, 0.0, 1.0 - y)
    if w <= MIN_REGION_EXTENT or h <= MIN_REGION_EXTENT:
        return None
    return {"x": x, "y": y, "w": w, "h": h}


def region_moved(region):
    """True when a region carries an origin box it has moved away from."""
    src = region.get("src")
    if not isinstance(src, dict):
        return False
    return any(abs(src[k] - region[k]) > MIN_REGION_EXTENT
               for k in ("x", "y", "w", "h"))


def box_2d(x, y, w, h):
    """Convert a normalized region to Gemini's [ymin, xmin, ymax, xmax] on a 0-1000 grid."""
    def to_grid(value):
        return _clamp(round(value * 1000), 0, 1000)
    return [to_grid(y), to_grid(x), to_grid(y + h), to_grid(x + w)]


def placement_phrase(x, y, w, h):
    """Describe where a region's center falls on a 3x3 grid, e.g. "at the bottom-left"."""
    cx = x + w / 2
    cy = y + h / 2
    horizontal = "left" if cx < 1 / 3 else "center" if cx < 2 / 3 else "right"
    vertical = "top" if cy < 1 / 3 else "middle" if cy < 2 / 3 else "bottom"
    if vertical == "middle" and horizontal == "center":
        return "at the center"
    return f"at the {vertical}-{horizontal}"


def aspect_ratio_string(width, height):
    """Reduce width:height by their greatest common divisor, e.g. 1920x1080 -> "16:9"."""
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def _element_line(region):
    placement = placement_phrase(region["x"], region["y"], region["w"], region["h"])
    box = box_2d(region["x"], region["y"], region["w"], region["h"])
    geometry = (
        f"{placement}, covering about {round(region['w'] * 100)}% of the image "
        f"width and {round(region['h'] * 100)}% of its height. box_2d = {box}"
    )
    # Referenced items use take-from-image phrasing: a trailing "as shown in"
    # aside is weak enough that models follow the words and drop the picture.
    ref = region.get("ref_image")
    if region["kind"] == "text":
        styled = f", styled as shown in image {ref}" if ref else ""
        if region["desc"]:
            return f'The text "{region["text"]}", {region["desc"]}{styled}: {geometry}'
        return f'The text "{region["text"]}"{styled}: {geometry}'
    if ref:
        subject = (
            f"{region['desc']}, taken from image {ref} (reproduce that exact item)"
            if region["desc"]
            else f"The item shown in image {ref}, reproduced exactly"
        )
        return f"{subject}: {geometry}"
    return f'{region["desc"] or "An element"}: {geometry}'


def _boxes_overlap(a, b):
    """Fraction of box b's area that box a covers (normalized region dicts)."""
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    area = b["w"] * b["h"]
    return (ix * iy) / area if area > 0 else 0.0


def _move_line(region):
    # Hybrid phrasing, same doctrine as placement lines: the verbal
    # placement drives the model, the coordinates pin it.
    src = region["src"]
    origin = box_2d(src["x"], src["y"], src["w"], src["h"])
    target = box_2d(region["x"], region["y"], region["w"], region["h"])
    placement = placement_phrase(region["x"], region["y"],
                                 region["w"], region["h"])
    subject = region["desc"] or "The element"
    # When the destination covers the origin, the paste hides the old copy:
    # there is no duplicate to remove, and asking for one invites cutting a
    # hole through the pasted object.
    if _boxes_overlap(region, src) > 0.9:
        return (
            f"{subject}: blend the one {placement} (box_2d = {target}) "
            f"naturally into the scene — match lighting, shadows, and "
            f"perspective."
        )
    # When the destination overlaps the origin, "remove the duplicate at
    # [src]" would also remove the kept copy — the instruction is
    # self-contradicting and models resolve it by doing nothing. Erasing
    # only what sticks out beyond the kept copy is geometrically truthful.
    if _boxes_overlap(src, region) > 0.25:
        return (
            f"{subject}: the old, larger copy overlaps the kept one — "
            f"erase every part of it outside box_2d = {target} and fill "
            f"those areas with the scene's background. Keep the copy "
            f"{placement} (box_2d = {target}), blending it naturally into "
            f"the scene — match lighting, shadows, and perspective."
        )
    return (
        f"{subject}: remove the duplicate at box_2d = {origin} and fill "
        f"that area with the scene's background. Keep the one {placement} "
        f"(box_2d = {target}), blending it naturally into the scene — "
        f"match lighting, shadows, and perspective."
    )


def _classify_regions(regions):
    """Split regions into moves, anchors, and additions for the prompt.

    A scanned region (one with an origin box) that has not moved describes
    pixels already in the image — giving it a placement line invites the
    model to re-render the scene instead of editing it, so it becomes a
    silent anchor. Reference-image and text regions always render as
    additions regardless of origin.
    """
    moves, anchors, additions = [], [], []
    for region in regions:
        # Cut-out regions are removed from the scene; they never get a line.
        if region.get("cutout"):
            continue
        plain = region["kind"] != "text" and not region.get("ref_image")
        if plain and region_moved(region):
            moves.append(region)
        elif plain and isinstance(region.get("src"), dict):
            anchors.append(region)
        else:
            additions.append(region)
    return moves, anchors, additions


def build_prompt(prompt, width, height, regions):
    """Assemble the hybrid scene + layout prompt for image generation."""
    lines = []
    scene = prompt.strip()
    if scene:
        lines.append(scene)
        lines.append("")
    ratio = aspect_ratio_string(width, height)
    lines.append(f"Compose for a {width}x{height} frame (aspect ratio {ratio}).")
    moves, anchors, additions = _classify_regions(regions)
    if moves:
        lines.append("")
        lines.append(REPOSITION_HEADER)
        for index, region in enumerate(moves, start=1):
            lines.append(f"{index}. {_move_line(region)}")
        if anchors:
            lines.append(ANCHORS_LINE)
    if additions:
        lines.append("")
        header = LAYOUT_HEADER
        if any(region.get("ref_image") for region in additions):
            header += " " + REFS_HEADER
        lines.append(header)
        for index, region in enumerate(additions, start=1):
            lines.append(f"{index}. {_element_line(region)}")
        if anchors and not moves:
            lines.append(ANCHORS_LINE)
    removals = [r for r in regions
                if r.get("cutout") and r.get("kind") != "text"]
    if removals:
        lines.append("")
        lines.append(REMOVAL_HEADER)
        for index, region in enumerate(removals, start=1):
            box = box_2d(region["x"], region["y"], region["w"], region["h"])
            lines.append(f"{index}. box_2d = {box}")
    if moves or additions:
        lines.append(LAYOUT_FOOTER)
    return "\n".join(lines)


def regions_to_pixel_bboxes(regions, width, height):
    """Convert normalized regions into one frame of integer pixel boxes: [[box, ...]] or []."""
    regions = [r for r in regions if not r.get("cutout")]
    if not regions:
        return []
    boxes = [{"x": round(region["x"] * width),
              "y": round(region["y"] * height),
              "width": round(region["w"] * width),
              "height": round(region["h"] * height)}
             for region in regions]
    return [boxes]


def mask_pixel_box(region, width, height):
    """Integer pixel bounds (x0, y0, x1, y1) for a normalized region, clamped to
    the frame and guaranteed to enclose at least one pixel."""
    x0 = _clamp(round(region["x"] * width), 0, width - 1)
    y0 = _clamp(round(region["y"] * height), 0, height - 1)
    x1 = _clamp(round((region["x"] + region["w"]) * width), x0 + 1, width)
    y1 = _clamp(round((region["y"] + region["h"]) * height), y0 + 1, height)
    return (x0, y0, x1, y1)


def region_has_stored_mask(region):
    """True when the region carries a non-empty base64 segmentation mask."""
    mask = region.get("mask")
    return isinstance(mask, str) and bool(mask)


def composite_moved_regions(image, regions):
    """Paste each moved region's source pixels at its destination.

    The canvas previews moves with a masked cut-out; this makes the move real
    in the image tensor itself, so the edit model receives the relocation as
    fact and only has to remove the original and blend — operations it
    performs far more reliably than coordinate-addressed moves. Returns the
    input unchanged when there is nothing to composite; never mutates it.
    """
    moved = [r for r in regions
             if region_moved(r) and r["kind"] != "text"
             and not r.get("ref_image") and not r.get("cutout")]
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
        sx0, sy0, sx1, sy1 = mask_pixel_box(region["src"], width, height)
        dx0, dy0, dx1, dy1 = mask_pixel_box(region, width, height)
        dw, dh = dx1 - dx0, dy1 - dy0
        patch = image[:, sy0:sy1, sx0:sx1, :].permute(0, 3, 1, 2)
        patch = torch.nn.functional.interpolate(
            patch, size=(dh, dw), mode="bilinear", align_corners=False,
        ).permute(0, 2, 3, 1)
        alpha = torch.ones((dh, dw), device=result.device, dtype=result.dtype)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region["mask"])))
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


def _cutout_mask(regions, width, height):
    """uint8 [height, width] mask, 255 where cut-out regions are to be filled.

    Each cut-out region contributes its stored segmentation silhouette, or its
    whole box when it has no mask; the union is returned. All-zero when there are
    no cut-outs. numpy/PIL only, so the fill geometry is unit-testable without cv2.
    """
    import base64
    from io import BytesIO

    import numpy as np
    from PIL import Image

    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if not region.get("cutout") or region.get("kind") == "text":
            continue
        x0, y0, x1, y1 = mask_pixel_box(region, width, height)
        bw, bh = x1 - x0, y1 - y0
        patch = np.full((bh, bw), 255, dtype=np.uint8)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region["mask"])))
                glyph = glyph.convert("L").resize((bw, bh))
                patch = ((np.asarray(glyph) > 127).astype(np.uint8)) * 255
            except Exception:
                pass
        mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], patch)
    return mask


def _inpaint_regions(image, mask):
    """Inpaint an image tensor's masked pixels from their surroundings.

    image is float [B,H,W,3]; mask is uint8 [H,W] (255 = fill). Returns the input
    unchanged when the mask is empty or OpenCV is missing (a ComfyUI core
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


def apply_cutouts(image, regions):
    """Remove each cut-out region by inpainting its masked area from the scene.

    A cut-out region (Shift+Delete in the editor) is erased: its masked
    silhouette — or its whole box when it has no stored mask — is filled in from
    the surrounding pixels (OpenCV), so the object is seamlessly gone while the
    output stays RGB. Returns the input unchanged when there are no cut-outs.
    """
    cuts = [r for r in regions if r.get("cutout") and r["kind"] != "text"]
    if image is None or not cuts:
        return image
    height, width = int(image.shape[1]), int(image.shape[2])
    return _inpaint_regions(image, _cutout_mask(regions, width, height))


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

    mask = np.zeros((height, width), dtype=np.uint8)
    for region in regions:
        if (not region_moved(region) or region.get("kind") == "text"
                or region.get("ref_image") or region.get("cutout")):
            continue
        sx0, sy0, sx1, sy1 = mask_pixel_box(region["src"], width, height)
        bw, bh = sx1 - sx0, sy1 - sy0
        patch = np.full((bh, bw), 255, dtype=np.uint8)
        if region_has_stored_mask(region):
            try:
                glyph = Image.open(BytesIO(base64.b64decode(region["mask"])))
                glyph = glyph.convert("L").resize((bw, bh))
                patch = ((np.asarray(glyph) > 127).astype(np.uint8)) * 255
            except Exception:
                pass
        # Zero the part of this origin covered by the destination box so the
        # freshly pasted copy is never erased.
        dx0, dy0, dx1, dy1 = mask_pixel_box(region, width, height)
        ix0, iy0 = max(sx0, dx0), max(sy0, dy0)
        ix1, iy1 = min(sx1, dx1), min(sy1, dy1)
        if ix1 > ix0 and iy1 > iy0:
            patch[iy0 - sy0:iy1 - sy0, ix0 - sx0:ix1 - sx0] = 0
        mask[sy0:sy1, sx0:sx1] = np.maximum(mask[sy0:sy1, sx0:sx1], patch)
    return mask


def apply_move_origin_cutouts(image, regions):
    """Inpaint the leftover origin of each moved region so it does not appear twice.

    composite_moved_regions pastes a moved object at its destination but leaves
    the original behind; this erases that original (silhouette minus destination)
    from the surrounding pixels, making the move's removal deterministic instead
    of relying on the edit model. Returns the input unchanged when nothing moved.
    """
    moved = [r for r in regions if region_moved(r) and r.get("kind") != "text"
             and not r.get("ref_image") and not r.get("cutout")]
    if image is None or not moved:
        return image
    height, width = int(image.shape[1]), int(image.shape[2])
    return _inpaint_regions(image, _move_origin_mask(regions, width, height))


def build_region_masks(regions, width, height):
    """Render one [height, width] mask per region into an [N, height, width] tensor.

    Regions with a stored segmentation mask are decoded, thresholded at 127, and
    placed at their box offset; regions without one (or whose mask fails to
    decode) fall back to a filled rectangle so a scan never fails the build. With
    no regions, returns a single all-zero mask as a ComfyUI-friendly placeholder.
    """
    # Imported lazily so the module stays importable without the ComfyUI runtime;
    # this is the only torch/numpy/PIL touch in the file.
    import base64
    from io import BytesIO

    import numpy as np
    import torch
    from PIL import Image

    # Cut-out regions are removed entirely (they erase to transparent in the
    # image output instead of contributing a mask slot).
    regions = [r for r in regions if not r.get("cutout")]
    if not regions:
        return torch.zeros((1, height, width))
    frames = []
    for region in regions:
        frame = np.zeros((height, width), dtype=np.float32)
        x0, y0, x1, y1 = mask_pixel_box(region, width, height)
        rendered = False
        if region_has_stored_mask(region):
            try:
                raw = base64.b64decode(region["mask"])
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


class RegionalPromptBuilder(IO.ComfyNode):
    """Builds a layout-aware image prompt from canvas-drawn regions."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="RegionalPromptBuilder",
            display_name="Regional Prompt Builder",
            category="ERPK/utils",
            description="Draw regions on a canvas and emit a layout-aware prompt "
                        "for image generation models, plus pixel bounding boxes.",
            inputs=[
                IO.Int.Input(
                    "width",
                    default=1024,
                    min=64,
                    max=8192,
                    step=8,
                    tooltip="Target frame width in pixels",
                ),
                IO.Int.Input(
                    "height",
                    default=1024,
                    min=64,
                    max=8192,
                    step=8,
                    tooltip="Target frame height in pixels",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Scene description: subject, setting, background, "
                            "and style. Elements drawn on the canvas are placed "
                            "on top of this scene.",
                ),
                IO.String.Input(
                    "regions_data",
                    multiline=True,
                    default="[]",
                    socketless=True,
                    tooltip="Managed by the canvas editor; JSON list of normalized regions.",
                ),
                IO.Image.Input(
                    "image",
                    optional=True,
                    tooltip="Optional reference image shown under the canvas "
                            "regions and passed through unchanged, so the "
                            "builder can sit inline in an image-edit chain.",
                ),
                *[
                    IO.String.Input(
                        f"desc_{n}",
                        optional=True,
                        force_input=True,
                        tooltip=f"Overrides region {n}'s description when "
                                "connected (regions numbered as on the canvas).",
                    )
                    for n in range(1, DESC_INPUT_COUNT + 1)
                ],
                *[
                    IO.Image.Input(
                        f"ref_{n}",
                        optional=True,
                        tooltip=f"Reference image for region {n}: forwarded on "
                                "image_refs, and the region's prompt line cites "
                                "its image number (regions numbered as on the "
                                "canvas).",
                    )
                    for n in range(1, REF_INPUT_COUNT + 1)
                ],
                IO.Custom("ERPK_REGIONS").Input(
                    "regions",
                    optional=True,
                    tooltip="Detected regions (JSON) appended after the canvas "
                            "regions at execute time. The canvas is unchanged, "
                            "and desc_N/ref_N bind canvas regions only.",
                ),
            ],
            outputs=[
                IO.String.Output("prompt"),
                IO.Custom("BOUNDING_BOX").Output("bboxes"),
                IO.Int.Output("width"),
                IO.Int.Output("height"),
                IO.Image.Output("image"),
                IO.Custom("ERPK_IMAGE_REFS").Output(
                    "image_refs",
                    tooltip="Per-region reference images in region order; "
                            "connect to an image edit node's image_refs input.",
                ),
                IO.Mask.Output(
                    "masks",
                    tooltip="One mask per region in region order [N, height, "
                            "width]; regions without a stored segmentation get a "
                            "filled-rectangle mask.",
                ),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image")
        regions = parse_regions(kwargs.get("regions_data", "[]"))
        for index, region in enumerate(regions[:DESC_INPUT_COUNT]):
            override = kwargs.get(f"desc_{index + 1}")
            if isinstance(override, str) and override.strip():
                region["desc"] = override.strip()
        image_refs = []
        for index, region in enumerate(regions[:REF_INPUT_COUNT]):
            ref = kwargs.get(f"ref_{index + 1}")
            if ref is not None:
                image_refs.append(ref)
                region["ref_image"] = len(image_refs) + 1
        # Appended after the override loops so desc_N/ref_N bind canvas regions
        # only; wired detections always land past the canvas indices.
        regions += parse_regions(kwargs.get("regions"))
        if not regions and not prompt.strip():
            raise ValueError("Describe the scene or add at least one region")
        image = composite_moved_regions(image, regions)
        image = apply_move_origin_cutouts(image, regions)
        image = apply_cutouts(image, regions)
        # Masks overlay the passed-through image, so they render at the
        # connected image's H x W; with no image they fall back to the widgets.
        mask_width, mask_height = width, height
        if image is not None:
            mask_height, mask_width = int(image.shape[1]), int(image.shape[2])
        masks = build_region_masks(regions, mask_width, mask_height)
        assembled = build_prompt(prompt, width, height, regions)
        bboxes = regions_to_pixel_bboxes(regions, width, height)
        return IO.NodeOutput(assembled, bboxes, width, height, image, image_refs, masks)
