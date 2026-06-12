# ABOUTME: Pluggable vision-scan engine: a PIL image becomes ranked scan objects with masks.
# ABOUTME: Ships a Gemini segmentation + depth-ranking implementation; parse helpers stay torch/genai-free.

import json
import math

# Degenerate-box floor for detections, mirroring utils/regional_prompt's
# MIN_REGION_EXTENT (the regions contract). It is duplicated rather than imported
# to keep this module free of comfy_api/torch/genai so the pure helpers stay
# unit-testable; test_scan_engine asserts the two stay in sync.
MIN_REGION_EXTENT = 0.005

DEFAULT_MAX_OBJECTS = 20
MAX_OBJECTS_CEILING = 100

# Structured-output schema for segmentation: each entry carries box_2d on the
# 0-1000 grid, a label, and a base64 PNG mask. "mask" is intentionally NOT
# required so a model that omits it still validates (rectangle fallback later).
SEGMENTATION_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "box_2d": {"type": "ARRAY", "items": {"type": "INTEGER"}},
            "label": {"type": "STRING"},
            "mask": {"type": "STRING"},
        },
        "required": ["box_2d", "label"],
    },
}

# Structured-output schema for depth ranking: the found labels reordered
# background-to-foreground.
DEPTH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "order": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["order"],
}


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def strip_data_url(value):
    """Return prefix-free base64 from a possible data URL; non-str/empty -> None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("data:"):
        comma = text.find(",")
        if comma == -1:
            return None
        text = text[comma + 1:].strip()
    return text or None


def segmentation_prompt(max_objects):
    """Build the segmentation request prompt for the vision model."""
    return (
        "Segment the prominent objects in the image. For each instance, return "
        "its 2D bounding box as box_2d = [ymin, xmin, ymax, xmax] on a 0-1000 "
        "grid with the origin at the top-left, a short label naming the object, "
        "and a base64-encoded PNG segmentation mask whose pixels are relative to "
        "the bounding box (the mask covers only the box, not the full image). "
        f"Segment at most {max_objects} instances total."
    )


def parse_segmentation(text, max_objects):
    """Convert the model's segmentation JSON into normalized scan-object dicts.

    Input is a list of {box_2d, label, mask?} where box_2d is
    [ymin, xmin, ymax, xmax] on a 0-1000 grid (top-left origin). Output dicts are
    {name, box:{x,y,w,h}, mask:str|None, group}; depth_rank is added later.
    Malformed or non-list JSON yields [] (the scan must never fail on parse).
    """
    try:
        raw = json.loads(text)
    except (TypeError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    objects = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        box = entry.get("box_2d")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        try:
            values = [float(value) for value in box]
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in values):
            continue
        ymin, xmin, ymax, xmax = (value / 1000.0 for value in values)
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin
        xmin = _clamp(xmin, 0.0, 1.0)
        xmax = _clamp(xmax, 0.0, 1.0)
        ymin = _clamp(ymin, 0.0, 1.0)
        ymax = _clamp(ymax, 0.0, 1.0)
        x, y, w, h = xmin, ymin, xmax - xmin, ymax - ymin
        if w <= MIN_REGION_EXTENT or h <= MIN_REGION_EXTENT:
            continue
        label = entry.get("label")
        name = label.strip() if isinstance(label, str) else ""
        objects.append({
            "name": name,
            "box": {"x": x, "y": y, "w": w, "h": h},
            "mask": strip_data_url(entry.get("mask")),
            "group": name,
        })
    return objects[:max_objects]


def depth_prompt(labels):
    """Build the depth-ranking request prompt for the found labels."""
    listed = ", ".join(labels)
    return (
        "Looking at this image, order these object labels from background "
        "(farthest from the camera) to foreground (nearest the camera) as they "
        f"appear in the scene: {listed}. Return them in that order."
    )


def resolve_model(model, known_models, default):
    """Pick the requested model when it is a known name, else the default.

    The route forwards a browser-supplied string; anything outside the known
    model set falls back to the default rather than reaching the API.
    """
    if isinstance(model, str) and model in known_models:
        return model
    return default


def parse_depth_order(text, labels):
    """Map each label to a back-to-front rank from the model's order list.

    Labels the model omitted are appended after the ranked ones (stable in the
    input order) so unknowns sort frontmost. Unknown labels in the model's order
    are ignored. Malformed JSON falls back to the input label order.
    """
    order = []
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        data = None
    if isinstance(data, dict):
        raw_order = data.get("order")
        if isinstance(raw_order, list):
            order = [item for item in raw_order if isinstance(item, str)]
    label_set = set(labels)
    rank_map = {}
    rank = 0
    for label in order:
        if label in label_set and label not in rank_map:
            rank_map[label] = rank
            rank += 1
    for label in labels:
        if label not in rank_map:
            rank_map[label] = rank
            rank += 1
    return rank_map


def apply_depth_ranks(objects, rank_map):
    """Tag each object with its group's depth_rank and stably sort back-to-front."""
    for obj in objects:
        obj["depth_rank"] = rank_map.get(obj.get("group"), 0)
    return sorted(objects, key=lambda obj: obj["depth_rank"])


async def gemini_scan(image, max_objects, model):
    """Gemini engine: one segmentation call plus one depth-ranking call.

    GeminiClient is imported lazily so this module stays genai-free at import
    time (the test harness never reaches this code). The key resolves through the
    standard 3-tier chain via GeminiClient(api_key=None).
    """
    from ..gemini.gemini_api.client import GeminiClient

    client = GeminiClient(api_key=None)
    model_to_use = resolve_model(model, GeminiClient.MODELS,
                                 GeminiClient.DEFAULT_MODEL)

    segmentation = await client.generate_content(
        segmentation_prompt(max_objects),
        images=[image],
        temperature=0.0,
        model=model_to_use,
        response_mime_type="application/json",
        response_schema=SEGMENTATION_SCHEMA,
    )
    if segmentation.get("blocked"):
        raise RuntimeError(
            segmentation.get("error") or "Gemini segmentation request was blocked"
        )
    objects = parse_segmentation(segmentation.get("text", ""), max_objects)
    if not objects:
        return []

    labels = []
    seen = set()
    for obj in objects:
        group = obj["group"]
        if group not in seen:
            seen.add(group)
            labels.append(group)

    # The image goes along so the ranking reflects the actual scene, not the
    # labels' usual semantics.
    depth = await client.generate_content(
        depth_prompt(labels),
        images=[image],
        temperature=0.0,
        model=model_to_use,
        response_mime_type="application/json",
        response_schema=DEPTH_SCHEMA,
    )
    # A blocked/empty depth call degrades to the segmentation order rather than
    # failing the whole scan.
    depth_text = "" if depth.get("blocked") else depth.get("text", "")
    rank_map = parse_depth_order(depth_text, labels)
    return apply_depth_ranks(objects, rank_map)


# The single indirection point a future Moondream engine plugs into: any
# coroutine (PIL.Image, max_objects:int, model:str|None) -> list[scan-object].
DEFAULT_ENGINE = gemini_scan


async def scan(image, max_objects=DEFAULT_MAX_OBJECTS, model=None, engine=None):
    """Run the active scan engine over the image, returning ranked scan objects."""
    return await (engine or DEFAULT_ENGINE)(image, max_objects, model)
