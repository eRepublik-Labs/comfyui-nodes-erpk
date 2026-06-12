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
# Each move is decomposed into erase + repaint: edit models execute the two
# primitive operations far more reliably than an abstract "move".
REPOSITION_HEADER = (
    "Make these edits to the image (areas are "
    '"box_2d = [ymin, xmin, ymax, xmax]" on a 0-1000 grid with top-left '
    "origin):"
)
ANCHORS_LINE = (
    "Every other element in the image stays exactly where it is — do not "
    "remove, add, or alter anything else."
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
        src = _parse_src_box(entry.get("src"))
        if src is not None:
            region["src"] = src
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


def _move_line(region):
    # Hybrid phrasing, same doctrine as placement lines: the verbal
    # destination drives the model, the coordinates pin it.
    src = region["src"]
    origin = box_2d(src["x"], src["y"], src["w"], src["h"])
    target = box_2d(region["x"], region["y"], region["w"], region["h"])
    placement = placement_phrase(region["x"], region["y"],
                                 region["w"], region["h"])
    where = placement.replace("at the", "to the", 1)
    subject = region["desc"] or "The element"
    return (
        f"{subject}: erase it from box_2d = {origin} and fill that area "
        f"with the scene's background, then paint it again {where}, "
        f"covering about {round(region['w'] * 100)}% of the image width "
        f"and {round(region['h'] * 100)}% of its height — box_2d = {target}"
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
    if moves or additions:
        lines.append(LAYOUT_FOOTER)
    return "\n".join(lines)


def regions_to_pixel_bboxes(regions, width, height):
    """Convert normalized regions into one frame of integer pixel boxes: [[box, ...]] or []."""
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
        masks = build_region_masks(regions, width, height)
        assembled = build_prompt(prompt, width, height, regions)
        bboxes = regions_to_pixel_bboxes(regions, width, height)
        return IO.NodeOutput(assembled, bboxes, width, height, image, image_refs, masks)
