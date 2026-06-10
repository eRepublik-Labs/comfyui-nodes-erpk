# ABOUTME: Pure prompt-builder node that turns canvas-drawn regions into a layout-aware
# ABOUTME: image-generation prompt plus interoperable pixel bounding boxes.

import json
import math

from comfy_api.latest import IO

REGION_KINDS = {"object", "text"}
MIN_REGION_EXTENT = 0.005
# Socket-only description overrides; desc_N feeds the region numbered N on
# the canvas (numbers are depth order, so reordering remaps the wires).
DESC_INPUT_COUNT = 6

# Detection-annotation cues make vision models RENDER boxes around the
# elements: both the words ("bounding box") and the format - Gemini draws
# colored rectangles at coordinates given as its native box_2d detection
# arrays. The template calls them invisible placement areas, states geometry
# as plain percent spans, and forbids drawing them.
LAYOUT_HEADER = (
    "Layout: place each element exactly where specified. Each position gives "
    "a verbal placement plus the exact span it occupies as percentages of "
    "the frame width and height, measured from the top-left corner. Elements "
    "are listed from back to front: where placement areas overlap, a later "
    "element appears in front of an earlier one."
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
        regions.append({"x": x, "y": y, "w": w, "h": h,
                        "kind": kind, "desc": desc, "text": text})
    return regions


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


# Tenth-of-a-percent resolution matches the 0-1000 grid of detection-style
# coordinates; whole numbers drop the decimal so typical spans read clean.
def _pct(value):
    text = f"{value * 100:.1f}".rstrip("0").rstrip(".")
    return text or "0"


def _span(start, extent):
    return f"{_pct(start)}% to {_pct(start + extent)}%"


def _element_line(region):
    placement = placement_phrase(region["x"], region["y"], region["w"], region["h"])
    geometry = (
        f"{placement}, spanning {_span(region['x'], region['w'])} of the frame "
        f"width and {_span(region['y'], region['h'])} of its height"
    )
    if region["kind"] == "text":
        if region["desc"]:
            return f'The text "{region["text"]}", {region["desc"]}: {geometry}'
        return f'The text "{region["text"]}": {geometry}'
    return f'{region["desc"] or "An element"}: {geometry}'


def build_prompt(prompt, width, height, regions):
    """Assemble the hybrid scene + layout prompt for image generation."""
    lines = []
    scene = prompt.strip()
    if scene:
        lines.append(scene)
        lines.append("")
    ratio = aspect_ratio_string(width, height)
    lines.append(f"Compose for a {width}x{height} frame (aspect ratio {ratio}).")
    if regions:
        lines.append("")
        lines.append(LAYOUT_HEADER)
        for index, region in enumerate(regions, start=1):
            lines.append(f"{index}. {_element_line(region)}")
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
            ],
            outputs=[
                IO.String.Output("prompt"),
                IO.Custom("BOUNDING_BOX").Output("bboxes"),
                IO.Int.Output("width"),
                IO.Int.Output("height"),
                IO.Image.Output("image"),
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
        if not regions and not prompt.strip():
            raise ValueError("Describe the scene or add at least one region")
        assembled = build_prompt(prompt, width, height, regions)
        bboxes = regions_to_pixel_bboxes(regions, width, height)
        return IO.NodeOutput(assembled, bboxes, width, height, image)
