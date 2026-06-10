# ABOUTME: Pure prompt-builder node that turns canvas-drawn regions into a layout-aware
# ABOUTME: Gemini image prompt plus interoperable pixel bounding boxes.

import json
import math

from comfy_api.latest import IO

REGION_KINDS = {"object", "text"}
MIN_REGION_EXTENT = 0.005

# "Bounding box" is detection-annotation vocabulary: models that know it from
# vision training will happily RENDER yellow boxes around the elements. The
# template calls them invisible placement areas and forbids drawing them.
LAYOUT_HEADER = (
    "Layout: place each element exactly where specified. Each position gives a "
    'verbal placement plus its placement area as "box_2d = [ymin, xmin, ymax, xmax]" '
    "on a 0-1000 grid with top-left origin."
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
    if region["kind"] == "text":
        if region["desc"]:
            return f'The text "{region["text"]}", {region["desc"]}: {geometry}'
        return f'The text "{region["text"]}": {geometry}'
    return f'{region["desc"] or "An element"}: {geometry}'


def build_prompt(scene_description, background, style, width, height, regions):
    """Assemble the hybrid scene + layout prompt for Gemini image generation."""
    lines = []
    scene = scene_description.strip()
    if scene:
        lines.append(scene)
        lines.append("")
    background = background.strip()
    if background:
        lines.append(f"Background: {background}")
    style = style.strip()
    if style:
        lines.append(f"Style: {style}")
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


class GeminiRegionalPromptBuilder(IO.ComfyNode):
    """Builds a layout-aware Gemini image prompt from canvas-drawn regions."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiRegionalPromptBuilder",
            display_name="Gemini Regional Prompt Builder",
            category="ERPK/Gemini",
            description="Draw regions on a canvas and emit a layout-aware prompt "
                        "for Gemini image generation, plus pixel bounding boxes.",
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
                    "scene_description",
                    multiline=True,
                    default="",
                    tooltip="Overall scene description",
                ),
                IO.String.Input(
                    "background",
                    multiline=False,
                    default="",
                    tooltip="Background description",
                ),
                IO.String.Input(
                    "style",
                    multiline=False,
                    default="",
                    tooltip="Style, medium, and lighting",
                ),
                IO.String.Input(
                    "regions_data",
                    multiline=True,
                    default="[]",
                    socketless=True,
                    tooltip="Managed by the canvas editor; JSON list of normalized regions.",
                ),
            ],
            outputs=[
                IO.String.Output("prompt"),
                IO.Custom("BOUNDING_BOX").Output("bboxes"),
                IO.Int.Output("width"),
                IO.Int.Output("height"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        scene_description = kwargs.get("scene_description", "")
        background = kwargs.get("background", "")
        style = kwargs.get("style", "")
        regions = parse_regions(kwargs.get("regions_data", "[]"))
        if not regions and not any(
                value.strip() for value in (scene_description, background, style)):
            raise ValueError("Describe the scene or add at least one region")
        prompt = build_prompt(scene_description, background, style,
                              width, height, regions)
        bboxes = regions_to_pixel_bboxes(regions, width, height)
        return IO.NodeOutput(prompt, bboxes, width, height)
