# ABOUTME: Pluggable vision-scan engine: a PIL image becomes ranked scan objects with masks.
# ABOUTME: Default local pipeline (Florence-2/SAM/Depth-Anything) plus a Gemini engine; parse helpers stay torch/genai-free.

import asyncio
import json
import math

from . import scan_cost

# Degenerate-box floor for detections, mirroring utils/regional_prompt's
# MIN_REGION_EXTENT (the regions contract). It is duplicated rather than imported
# to keep this module free of comfy_api/torch/genai so the pure helpers stay
# unit-testable; test_scan_engine asserts the two stay in sync.
MIN_REGION_EXTENT = 0.005

DEFAULT_MAX_OBJECTS = 20
MAX_OBJECTS_CEILING = 100

# Structured-output schema for depth ranking: the found labels reordered
# background-to-foreground.
DEPTH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "order": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["order"],
}

# Structured-output schema for detection: one entry per prominent object with a
# 0-1000 box, a short label, and a one-sentence description. Gemini supplies no
# masks here (the SAM stage does), so structured output is safe.
DETECTION_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "box_2d": {"type": "ARRAY", "items": {"type": "INTEGER"}},
            "label": {"type": "STRING"},
            "description": {"type": "STRING"},
        },
        "required": ["box_2d", "label", "description"],
    },
}


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def detection_prompt(max_objects):
    """Build the detection request prompt for the vision model."""
    return (
        "Detect the prominent objects in the image. For each instance, return "
        "its 2D bounding box as box_2d = [ymin, xmin, ymax, xmax] on a 0-1000 "
        "grid with the origin at the top-left, a short label naming the object, "
        "and a one-sentence description of what is visible inside that box. "
        f"Return at most {max_objects} instances total."
    )


def parse_detection(text, max_objects):
    """Convert the model's detection JSON into normalized scan-object dicts.

    Input is a list of {box_2d, label, description} where box_2d is
    [ymin, xmin, ymax, xmax] on a 0-1000 grid (top-left origin). Output dicts are
    {name, box:{x,y,w,h}, mask:None, group, caption}; masks come from the SAM
    stage and depth_rank is added later. caption is the stripped description (""
    when missing/non-string). Malformed or non-list JSON yields [] (the scan must
    never fail on parse).
    """
    if isinstance(text, str):
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip()[:-3]
            text = stripped
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
        description = entry.get("description")
        caption = description.strip() if isinstance(description, str) else ""
        objects.append({
            "name": name,
            "box": {"x": x, "y": y, "w": w, "h": h},
            "mask": None,
            "group": name,
            "caption": caption,
        })
    return objects[:max_objects]


FLORENCE_DETECTION_TASK = "<OD>"


def florence_to_objects(od_result, width, height, max_objects):
    """Convert a Florence-2 <OD> result into normalized scan-object dicts.

    Input is post_process_generation's {"<OD>": {"bboxes": [[x0,y0,x1,y1]...],
    "labels": [...]}} where boxes are absolute pixels (top-left/bottom-right).
    Output dicts are {name, box:{x,y,w,h}, mask:None, group, caption}; masks come
    from the SAM stage and depth_rank is added later. caption is left "" because
    Florence-2 emits no per-object description, keeping the scan-object contract
    uniform with the Gemini engine. Boxes are clamped to the frame, degenerate
    ones (w or h <= MIN_REGION_EXTENT) are dropped, and the result is capped at
    max_objects. <OD> is class-agnostic and can return very few, nested boxes, so
    callers must tolerate small counts.
    """
    detection = {}
    if isinstance(od_result, dict):
        detection = od_result.get(FLORENCE_DETECTION_TASK) or {}
    bboxes = detection.get("bboxes") if isinstance(detection, dict) else None
    labels = detection.get("labels") if isinstance(detection, dict) else None
    if not isinstance(bboxes, (list, tuple)):
        return []
    if not isinstance(labels, (list, tuple)):
        labels = [""] * len(bboxes)
    objects = []
    for box, label in zip(bboxes, labels):
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        try:
            values = [float(value) for value in box]
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in values):
            continue
        x0, y0, x1, y1 = values
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        x0 = _clamp(x0 / width, 0.0, 1.0)
        x1 = _clamp(x1 / width, 0.0, 1.0)
        y0 = _clamp(y0 / height, 0.0, 1.0)
        y1 = _clamp(y1 / height, 0.0, 1.0)
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
        if w <= MIN_REGION_EXTENT or h <= MIN_REGION_EXTENT:
            continue
        name = label.strip() if isinstance(label, str) else ""
        objects.append({
            "name": name,
            "box": {"x": x, "y": y, "w": w, "h": h},
            "mask": None,
            "group": name,
            "caption": "",
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


# Selectable segmentation backbones. vit-base is the default — clean, tight masks
# at low CPU cost; the rest are opt-in via the editor's options window. Each family
# needs a different call, handled per-family in segment_objects.
DEFAULT_SEGMENTER = "facebook/sam-vit-base"
SEGMENTERS = [
    {"id": "facebook/sam-vit-base", "label": "SAM ViT-Base (default, fast)", "family": "sam1"},
    {"id": "facebook/sam-vit-large", "label": "SAM ViT-Large", "family": "sam1"},
    {"id": "facebook/sam-vit-huge", "label": "SAM ViT-Huge", "family": "sam1"},
    {"id": "syscv-community/sam-hq-vit-base", "label": "SAM-HQ ViT-Base (fine edges)", "family": "samhq"},
    {"id": "syscv-community/sam-hq-vit-large", "label": "SAM-HQ ViT-Large", "family": "samhq"},
    {"id": "facebook/sam2.1-hiera-small", "label": "SAM 2.1 Hiera-Small", "family": "sam2"},
    {"id": "facebook/sam2.1-hiera-base-plus", "label": "SAM 2.1 Hiera-Base+", "family": "sam2"},
    {"id": "facebook/sam2.1-hiera-large", "label": "SAM 2.1 Hiera-Large", "family": "sam2"},
]

# transformers classes each family needs — used to detect what this install runs.
SEGMENTER_FAMILY_CLASSES = {
    "sam1": ("SamModel", "SamProcessor"),
    "samhq": ("SamHQModel", "SamHQProcessor"),
    "sam2": ("Sam2Model", "Sam2Processor"),
}

# Back-compat alias for the default; segment_objects resolves the per-scan choice.
SEGMENTER_MODEL_ID = DEFAULT_SEGMENTER

# Loaded segmenters cached per model id: {id: {processor, model, device, family}}.
_segmenter = {}


def resolve_segmenter(model_id):
    """Return the requested segmenter when it is a known id, else the default.

    The editor forwards a browser-supplied string; anything outside the registry
    (or blank/None) falls back to vit-base rather than trying to load a bogus id.
    """
    if isinstance(model_id, str) and model_id.strip():
        for spec in SEGMENTERS:
            if spec["id"] == model_id:
                return model_id
    return DEFAULT_SEGMENTER


def _segmenter_family(model_id):
    """Family key for a segmenter id (defaults to sam1 for unknown ids)."""
    for spec in SEGMENTERS:
        if spec["id"] == model_id:
            return spec["family"]
    return "sam1"


def _is_cached(model_id):
    """True when a model's weights are already in the local HF hub cache.

    Best-effort UI hint — a False only means "first use downloads". Honors
    HF_HUB_CACHE / HF_HOME, defaulting to ~/.cache/huggingface/hub.
    """
    import os
    cache = os.environ.get("HF_HUB_CACHE")
    if not cache:
        home = os.environ.get(
            "HF_HOME", os.path.join(os.path.expanduser("~"), ".cache", "huggingface"))
        cache = os.path.join(home, "hub")
    folder = "models--" + model_id.replace("/", "--")
    return os.path.isdir(os.path.join(cache, folder))


def available_segmenters(tf=None):
    """Registry entries whose transformers classes import on this install.

    Each kept entry is annotated with `downloaded`. tf is injectable for tests; in
    production it lazily imports transformers — if transformers is missing it
    returns [] so the editor simply shows no picker rather than erroring.
    """
    if tf is None:
        try:
            import transformers as tf
        except ImportError:
            return []
    result = []
    for spec in SEGMENTERS:
        classes = SEGMENTER_FAMILY_CLASSES.get(spec["family"], ())
        if classes and all(hasattr(tf, name) for name in classes):
            result.append({**spec, "downloaded": _is_cached(spec["id"])})
    return result

# A box whose larger normalized side is below this is "small": at the frame's
# fixed encoder resolution it gets few mask pixels and inherently rough edges,
# so it earns a crop re-encode (an extra image embedding) for full resolution.
# Larger objects keep the single shared whole-image embedding.
SMALL_OBJECT_MAX_EXTENT = 0.15

# Padding around a small object's box when cropping it for the re-encode, as a
# fraction of the box size, so the segmenter sees a little context on each side.
CROP_PADDING_FRAC = 0.25


def best_mask_index(scores):
    """Index of the highest predicted-IoU mask among SAM's hypotheses.

    SAM with multimask_output=True returns several mask candidates plus a
    predicted IoU per candidate; the best-scoring one is usually the cleanest for
    an ambiguous box. Empty scores fall back to 0 (the only/first mask).
    """
    if scores is None or len(scores) == 0:
        return 0
    best = 0
    for index in range(1, len(scores)):
        if scores[index] > scores[best]:
            best = index
    return best


def is_small_object(box, threshold=SMALL_OBJECT_MAX_EXTENT):
    """True when both of the box's sides are below threshold (normalized 0-1).

    Uses the larger side: an object is small only when it is small in both
    dimensions, so a long thin region (a wide horizon, a tall pole) is not
    re-encoded just for being narrow on one axis.
    """
    return max(float(box.get("w", 0.0)), float(box.get("h", 0.0))) < threshold


def clean_mask(mask, feather_sigma=1.0):
    """Tidy a raw segmentation mask, returning a 2D uint8 array (0..255).

    Keeps the largest connected blob (drops stray islands), fills interior holes,
    and lightly feathers the edge so cut-outs composite without a hard stair-step.
    numpy/scipy are imported lazily; if scipy is unavailable the mask degrades to
    a clean binary one rather than raising, so the scan survives on a bare host.
    """
    import numpy as np

    binary = np.asarray(mask) > 0
    if not binary.any():
        return binary.astype(np.uint8) * 255
    try:
        from scipy import ndimage

        labels, count = ndimage.label(binary)
        if count > 1:
            sizes = ndimage.sum(binary, labels, range(1, count + 1))
            binary = labels == (1 + int(np.argmax(sizes)))
        binary = ndimage.binary_fill_holes(binary)
        if feather_sigma and feather_sigma > 0:
            alpha = ndimage.gaussian_filter(binary.astype(np.float32), feather_sigma)
            return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    except ImportError:
        pass
    return binary.astype(np.uint8) * 255


def pixel_box_prompts(objects, width, height):
    """Convert normalized scan boxes into integer [x0, y0, x1, y1] pixel
    prompts, clamped to the frame with at least one pixel of extent."""
    prompts = []
    for obj in objects:
        box = obj["box"]
        x0 = _clamp(round(box["x"] * width), 0, width - 1)
        y0 = _clamp(round(box["y"] * height), 0, height - 1)
        x1 = _clamp(round((box["x"] + box["w"]) * width), x0 + 1, width)
        y1 = _clamp(round((box["y"] + box["h"]) * height), y0 + 1, height)
        prompts.append([x0, y0, x1, y1])
    return prompts


def _load_segmenter(model_id, family, torch):
    """Load a segmenter's processor+model for its family, onto CPU/CUDA.

    CPU on purpose: the SAM pipeline materializes float64 tensors that MPS
    rejects; these models are small enough that CPU stays interactive. Each
    family has its own transformers classes (imported lazily here).
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if family == "samhq":
        from transformers import SamHQModel, SamHQProcessor
        processor = SamHQProcessor.from_pretrained(model_id)
        model = SamHQModel.from_pretrained(model_id).to(device)
    elif family == "sam2":
        from transformers import Sam2Model, Sam2Processor
        processor = Sam2Processor.from_pretrained(model_id)
        model = Sam2Model.from_pretrained(model_id).to(device)
    else:
        from transformers import SamModel, SamProcessor
        processor = SamProcessor.from_pretrained(model_id)
        model = SamModel.from_pretrained(model_id).to(device)
    return {"processor": processor, "model": model, "device": device, "family": family}


def segment_objects(image, objects, segmenter=None):
    """Fill each object's mask with a locally-computed segmentation.

    The detector (Florence-2 locally, Gemini in the cloud) supplies boxes and
    labels; masks always come from a box-prompted segmentation model because
    vision-LLM mask output is too unreliable to ship (omitted fields, truncated
    multi-object responses). The backbone is the resolved `segmenter` (defaults
    to vit-base); each SAM family is invoked correctly by segment_masks (SAM1:
    multimask + best-IoU; SAM-HQ: single HQ mask; SAM 2.1: its own processor).
    One shared image embedding masks every box at once; small objects are
    re-encoded from a padded crop so they get the encoder's full resolution
    instead of a few pixels. Each mask is tidied (largest blob, holes filled,
    edge feathered) and stored as a box-relative base64 PNG per the regions
    contract. Any failure leaves masks None — the scan survives, downstream falls
    back to rectangles, and the log says why.
    """
    try:
        import base64
        from io import BytesIO

        import numpy as np
        import torch
        from PIL import Image

        model_id = resolve_segmenter(segmenter)
        family = _segmenter_family(model_id)
        if model_id not in _segmenter:
            _segmenter[model_id] = _load_segmenter(model_id, family, torch)
            print(f"[ERPK scan] segmenter '{model_id}' ({family}) loaded on "
                  f"{_segmenter[model_id]['device']}")
        entry = _segmenter[model_id]
        processor, model, device = entry["processor"], entry["model"], entry["device"]

        rgb = image.convert("RGB")

        def encode_png(mask_array):
            """Box-relative uint8 mask -> base64 PNG, per the regions contract."""
            buf = BytesIO()
            Image.fromarray(mask_array, mode="L").save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

        def segment_masks(pil, prompts):
            """Best masks for a batch of boxes, each a full-frame bool array sized
            to `pil`. SAM1 picks the highest predicted-IoU of its hypotheses;
            SAM-HQ returns its single HQ mask; SAM 2.1 uses its own processor and
            output layout. Shared by the whole-image pass and the small-crop pass.
            """
            if family in ("sam1", "samhq"):
                inputs = processor(pil, input_boxes=[prompts],
                                   return_tensors="pt").to(device)
                kwargs = ({"multimask_output": True} if family == "sam1"
                          else {"multimask_output": False, "hq_token_only": True})
                with torch.no_grad():
                    out = model(**inputs, **kwargs)
                masks = processor.image_processor.post_process_masks(
                    out.pred_masks.cpu(), inputs["original_sizes"].cpu(),
                    inputs["reshaped_input_sizes"].cpu())[0]
                result = []
                for i in range(len(prompts)):
                    idx = (best_mask_index(out.iou_scores[0, i].tolist())
                           if family == "sam1" else 0)
                    result.append(masks[i, idx].numpy().astype(bool))
                return result
            # SAM 2.1: separate processor; normalize the per-box output dims.
            inputs = processor(images=pil, input_boxes=[prompts],
                               return_tensors="pt").to(device)
            with torch.no_grad():
                out = model(**inputs, multimask_output=True)
            masks = processor.post_process_masks(
                out.pred_masks.cpu(), inputs["original_sizes"])[0]
            arr = np.asarray(masks.numpy() if hasattr(masks, "numpy") else masks)
            scores = np.asarray(out.iou_scores.cpu().numpy()).reshape(len(prompts), -1)
            result = []
            for i in range(len(prompts)):
                per_box = arr[i]
                if per_box.ndim == 3:
                    idx = int(np.argmax(scores[i])) if scores[i].size else 0
                    result.append(per_box[idx].astype(bool))
                else:
                    result.append(np.squeeze(per_box).astype(bool))
            return result

        def segment_small(box_px):
            """Re-encode a small object from a padded crop for full-resolution edges.

            Returns a full-frame mask with the crop's result pasted back, so the
            caller crops it to the box just like a shared-pass mask.
            """
            x0, y0, x1, y1 = box_px
            pad_x = int(round((x1 - x0) * CROP_PADDING_FRAC))
            pad_y = int(round((y1 - y0) * CROP_PADDING_FRAC))
            cx0, cy0 = max(0, x0 - pad_x), max(0, y0 - pad_y)
            cx1, cy1 = min(rgb.width, x1 + pad_x), min(rgb.height, y1 + pad_y)
            crop_mask = segment_masks(rgb.crop((cx0, cy0, cx1, cy1)),
                                      [[x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0]])[0]
            full = np.zeros((rgb.height, rgb.width), dtype=bool)
            full[cy0:cy1, cx0:cx1] = np.asarray(crop_mask) > 0
            return full

        # One shared image embedding masks every box; small objects are then
        # refined with their own higher-resolution crop pass.
        prompts = pixel_box_prompts(objects, rgb.width, rgb.height)
        shared = segment_masks(rgb, prompts)

        for index, (obj, prompt) in enumerate(zip(objects, prompts)):
            x0, y0, x1, y1 = prompt
            full = segment_small(prompt) if is_small_object(obj["box"]) else shared[index]
            obj["mask"] = encode_png(clean_mask(full[y0:y1, x0:x1]))
    except Exception as e:
        print(f"[ERPK scan] Warning: local segmentation unavailable ({e}); "
              "masks fall back to rectangles")


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


def depth_ranks(objects, medians):
    """Tag objects with a measured depth_rank and sort them back-to-front.

    medians is parallel to objects: the median inverse-depth (disparity) sampled
    inside each object. Depth-Anything-V2 emits disparity where LARGER = NEARER,
    so depth_rank 0 = smallest median = farthest. None medians (no samples) sort
    as farthest and preserve input order among themselves; equal medians keep
    input order too (stable).
    """
    indexed = list(enumerate(zip(objects, medians)))

    def sort_key(item):
        index, (_obj, median) = item
        if median is None:
            return (0, 0.0, index)
        return (1, median, index)

    ordered = sorted(indexed, key=sort_key)
    result = []
    for rank, (_index, (obj, _median)) in enumerate(ordered):
        obj["depth_rank"] = rank
        result.append(obj)
    return result


def build_cost(usages, model):
    """Assemble the scan's cost from each API call's token usage.

    usages is one entry per Gemini call (None when a call reported no usage).
    Returns {usd, input_tokens, output_tokens, calls, model}: tokens are summed
    across calls and usd is the priced estimate, or None when the model has no
    rate on file (the UI then shows "cost unavailable" rather than implying free).
    """
    input_tokens = sum(usage["input_tokens"] for usage in usages if usage)
    output_tokens = sum(usage["output_tokens"] for usage in usages if usage)
    calls = sum(1 for usage in usages if usage)
    return {
        "usd": scan_cost.price(model, input_tokens, output_tokens),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "calls": calls,
        "model": model,
    }


async def gemini_scan(image, max_objects, model, segmenter=None):
    """Gemini engine: one detection call, SAM masks, one depth-ranking call.

    Gemini supplies boxes, labels, and per-object captions; the SAM stage fills
    masks (vision-LLM mask output is too unreliable to ship). GeminiClient is
    imported lazily so this module stays genai-free at import time (the test
    harness never reaches this code). The key resolves through the standard
    3-tier chain via GeminiClient(api_key=None).

    Returns {"objects": [...], "cost": {...}}: cost sums the token usage of both
    billable calls (detection + depth) and prices it. The detection call is
    billed even when it finds nothing, so a zero-object scan still reports cost.
    """
    from ..gemini.gemini_api.client import GeminiClient

    client = GeminiClient(api_key=None)
    model_to_use = resolve_model(model, GeminiClient.MODELS,
                                 GeminiClient.DEFAULT_MODEL)

    # response_schema is safe here: Gemini is not asked for masks (the SAM stage
    # produces them), so structured output does not suppress anything.
    detection = await client.generate_content(
        detection_prompt(max_objects),
        images=[image],
        temperature=0.0,
        model=model_to_use,
        response_mime_type="application/json",
        response_schema=DETECTION_SCHEMA,
    )
    if detection.get("blocked"):
        raise RuntimeError(
            detection.get("error") or "Gemini detection request was blocked"
        )
    raw_text = detection.get("text", "")
    objects = parse_detection(raw_text, max_objects)
    if not objects:
        print(f"[ERPK scan] 0 objects; raw response head: {raw_text[:400]!r}")
        return {"objects": [],
                "cost": build_cost([detection.get("usage")], model_to_use)}
    segment_objects(image, objects, segmenter)
    masked = sum(1 for obj in objects if obj.get("mask"))
    print(f"[ERPK scan] {len(objects)} objects, {masked} with masks")

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
    # A blocked/empty depth call degrades to the detection order rather than
    # failing the whole scan.
    depth_text = "" if depth.get("blocked") else depth.get("text", "")
    rank_map = parse_depth_order(depth_text, labels)
    ranked = apply_depth_ranks(objects, rank_map)
    cost = build_cost([detection.get("usage"), depth.get("usage")], model_to_use)
    return {"objects": ranked, "cost": cost}


# Pinned revisions are the security mitigation for Florence-2's trust_remote_code
# download: the revision is passed to BOTH from_pretrained calls. Depth-Anything
# is native transformers and needs no remote code.
FLORENCE_MODEL_ID = "microsoft/Florence-2-large-ft"
FLORENCE_REVISION = "4a12a2b54b7016a48a22037fbd62da90cd566f2a"
DEPTH_MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
DEPTH_REVISION = "5426e4f0f36572d16453bbda7a8389317b1bef99"
_florence = {}
_depth = {}


def _detect_florence(image):
    """Run Florence-2 open-vocabulary detection, returning post_process output.

    Loaded on CPU: MPS is ~2.5x slower here because use_cache=False (mandatory
    under transformers 4.56.1 with this pinned revision) recomputes the whole
    sequence per decode step and MPS launch overhead dominates that pattern.
    attn_implementation='eager' is also mandatory or the model fails to load.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoProcessor

    if not _florence:
        device = "cpu"
        processor = AutoProcessor.from_pretrained(
            FLORENCE_MODEL_ID, revision=FLORENCE_REVISION, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            FLORENCE_MODEL_ID, revision=FLORENCE_REVISION, trust_remote_code=True,
            attn_implementation="eager").to(device)
        _florence["processor"] = processor
        _florence["model"] = model
        _florence["device"] = device
        print(f"[ERPK scan] Florence-2 loaded on {device}")
    processor = _florence["processor"]
    model = _florence["model"]
    device = _florence["device"]

    rgb = image.convert("RGB")
    inputs = processor(text=FLORENCE_DETECTION_TASK, images=rgb, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}
    inputs["pixel_values"] = inputs["pixel_values"].to(model.dtype)
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False,
            use_cache=False,
        )
    text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    return processor.post_process_generation(
        text, task=FLORENCE_DETECTION_TASK, image_size=(rgb.width, rgb.height))


def _depth_map(image):
    """Return an (H, W) numpy disparity map (larger = nearer) for the image.

    Depth-Anything snaps the image to multiples of 14, so predicted_depth does
    not match (H, W); it is interpolated back to the original size before the
    SAM masks sample it, or the coordinates would not line up.
    """
    import numpy as np
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation

    if not _depth:
        device = "cpu"
        processor = AutoImageProcessor.from_pretrained(
            DEPTH_MODEL_ID, revision=DEPTH_REVISION)
        model = AutoModelForDepthEstimation.from_pretrained(
            DEPTH_MODEL_ID, revision=DEPTH_REVISION).to(device)
        _depth["processor"] = processor
        _depth["model"] = model
        _depth["device"] = device
        print(f"[ERPK scan] Depth-Anything loaded on {device}")
    processor = _depth["processor"]
    model = _depth["model"]
    device = _depth["device"]

    rgb = image.convert("RGB")
    inputs = processor(images=rgb, return_tensors="pt").to(device)
    with torch.no_grad():
        predicted = model(**inputs).predicted_depth
    resized = torch.nn.functional.interpolate(
        predicted.unsqueeze(1),
        size=(rgb.height, rgb.width),
        mode="bicubic",
        align_corners=False,
    )[0, 0]
    return resized.cpu().numpy()


def _mask_region_medians(objects, depth_map):
    """Median disparity inside each object: through its SAM mask, else its box.

    The stored mask is box-relative (segment_objects crops it to the same pixel
    box), so it is placed at the object's pixel box to select the matching depth
    region. Objects with no usable samples get a None median (sort as farthest).
    """
    import base64
    from io import BytesIO

    import numpy as np
    from PIL import Image

    height, width = depth_map.shape
    prompts = pixel_box_prompts(objects, width, height)
    medians = []
    for obj, (x0, y0, x1, y1) in zip(objects, prompts):
        region = depth_map[y0:y1, x0:x1]
        values = None
        mask_b64 = obj.get("mask")
        if mask_b64:
            try:
                raw = base64.b64decode(mask_b64)
                mask = np.array(Image.open(BytesIO(raw)).convert("L"))
                if mask.shape == region.shape:
                    selected = region[mask > 127]
                    if selected.size:
                        values = selected
            except Exception:
                values = None
        if values is None and region.size:
            values = region.reshape(-1)
        medians.append(float(np.median(values)) if values is not None and values.size
                       else None)
    return medians


def _local_scan_sync(image, max_objects, segmenter=None):
    """Blocking local pipeline: Florence detect -> SAM masks -> depth ordering."""
    try:
        detection = _detect_florence(image)
    except Exception as e:
        # No boxes means no scan; surface as a hard failure (the route maps it
        # to 502) rather than returning a silently empty result.
        raise RuntimeError(f"Florence-2 detection failed: {e}") from e

    rgb = image.convert("RGB")
    objects = florence_to_objects(detection, rgb.width, rgb.height, max_objects)
    if not objects:
        print("[ERPK scan] 0 objects detected")
        return []

    segment_objects(image, objects, segmenter)
    masked = sum(1 for obj in objects if obj.get("mask"))
    print(f"[ERPK scan] {len(objects)} objects, {masked} with masks")

    try:
        medians = _mask_region_medians(objects, _depth_map(image))
    except Exception as e:
        print(f"[ERPK scan] Warning: depth ordering unavailable ({e}); "
              "keeping Florence detection order")
        medians = [None] * len(objects)
    return depth_ranks(objects, medians)


async def local_scan(image, max_objects, model, segmenter=None):
    """Local engine: Florence-2 detection, SAM masks, Depth-Anything ordering.

    The model param is ignored: model selection is a cloud-provider concept
    (Gemini's MODELS list). The local pipeline's models are pinned by revision,
    so there is nothing to choose. It stays in the signature for engine-contract
    parity. The blocking torch work runs in a thread so it never stalls the
    event loop when two scans share it.

    Returns {"objects": [...], "cost": None}: the local pipeline makes no API
    calls, so there is no cost to report (None reads as "not applicable").
    """
    objects = await asyncio.to_thread(_local_scan_sync, image, max_objects, segmenter)
    return {"objects": objects, "cost": None}


# The single indirection point a future Moondream engine plugs into: any
# coroutine (PIL.Image, max_objects:int, model:str|None) -> {"objects": [...],
# "cost": {...}|None}. The scan button defaults to Gemini; the local pipeline
# stays opt-in per scan.
DEFAULT_ENGINE = gemini_scan


async def scan(image, max_objects=DEFAULT_MAX_OBJECTS, model=None, engine=None,
               segmenter=None):
    """Run the active scan engine over the image, returning ranked scan objects."""
    return await (engine or DEFAULT_ENGINE)(image, max_objects, model, segmenter)
