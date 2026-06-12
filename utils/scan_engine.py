# ABOUTME: Pluggable vision-scan engine: a PIL image becomes ranked scan objects with masks.
# ABOUTME: Default local pipeline (Florence-2/SAM/Depth-Anything) plus a Gemini engine; parse helpers stay torch/genai-free.

import asyncio
import json
import math

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
        objects.append({
            "name": name,
            "box": {"x": x, "y": y, "w": w, "h": h},
            "mask": strip_data_url(entry.get("mask")),
            "group": name,
        })
    return objects[:max_objects]


FLORENCE_DETECTION_TASK = "<OD>"


def florence_to_objects(od_result, width, height, max_objects):
    """Convert a Florence-2 <OD> result into normalized scan-object dicts.

    Input is post_process_generation's {"<OD>": {"bboxes": [[x0,y0,x1,y1]...],
    "labels": [...]}} where boxes are absolute pixels (top-left/bottom-right).
    Output dicts are {name, box:{x,y,w,h}, mask:None, group}; masks come from the
    SAM stage and depth_rank is added later. Boxes are clamped to the frame,
    degenerate ones (w or h <= MIN_REGION_EXTENT) are dropped, and the result is
    capped at max_objects. <OD> is class-agnostic and can return very few,
    nested boxes, so callers must tolerate small counts.
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


SEGMENTER_MODEL_ID = "facebook/sam-vit-base"
_segmenter = {}


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


def segment_objects(image, objects):
    """Fill each object's mask with a locally-computed segmentation.

    The detector (Florence-2 locally, Gemini in the cloud) supplies boxes and
    labels; masks always come from this box-prompted segmentation model (one
    image embedding, one prompt per box) because vision-LLM mask output is too
    unreliable to ship (omitted fields, truncated multi-object responses).
    Masks are stored box-relative base64 PNGs per the regions contract. Any
    failure leaves masks None — the scan survives, downstream falls back to
    rectangles, and the log says why.
    """
    try:
        import base64
        from io import BytesIO

        import numpy as np
        import torch
        from PIL import Image
        from transformers import SamModel, SamProcessor

        if not _segmenter:
            # CPU on purpose: the segmentation pipeline materializes float64
            # tensors, which MPS rejects; the model is small enough that CPU
            # stays interactive.
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _segmenter["processor"] = SamProcessor.from_pretrained(SEGMENTER_MODEL_ID)
            _segmenter["model"] = SamModel.from_pretrained(SEGMENTER_MODEL_ID).to(device)
            _segmenter["device"] = device
            print(f"[ERPK scan] segmenter loaded on {device}")
        processor = _segmenter["processor"]
        model = _segmenter["model"]
        device = _segmenter["device"]

        rgb = image.convert("RGB")
        prompts = pixel_box_prompts(objects, rgb.width, rgb.height)
        inputs = processor(rgb, input_boxes=[prompts], return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs, multimask_output=False)
        masks = processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
            inputs["reshaped_input_sizes"].cpu(),
        )[0]
        for obj, prompt, mask in zip(objects, prompts, masks):
            x0, y0, x1, y1 = prompt
            crop = mask[0, y0:y1, x0:x1].numpy().astype(np.uint8) * 255
            buf = BytesIO()
            Image.fromarray(crop, mode="L").save(buf, format="PNG")
            obj["mask"] = base64.b64encode(buf.getvalue()).decode()
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

    # No response_schema here: forcing structured output suppresses Gemini's
    # segmentation-mask generation (masks come back omitted or the result is
    # empty). The prompt specifies the JSON shape; parsing is defensive.
    segmentation = await client.generate_content(
        segmentation_prompt(max_objects),
        images=[image],
        temperature=0.0,
        model=model_to_use,
        response_mime_type="application/json",
    )
    if segmentation.get("blocked"):
        raise RuntimeError(
            segmentation.get("error") or "Gemini segmentation request was blocked"
        )
    raw_text = segmentation.get("text", "")
    objects = parse_segmentation(raw_text, max_objects)
    if not objects:
        print(f"[ERPK scan] 0 objects; raw response head: {raw_text[:400]!r}")
        return []
    segment_objects(image, objects)
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
    # A blocked/empty depth call degrades to the segmentation order rather than
    # failing the whole scan.
    depth_text = "" if depth.get("blocked") else depth.get("text", "")
    rank_map = parse_depth_order(depth_text, labels)
    return apply_depth_ranks(objects, rank_map)


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


def _local_scan_sync(image, max_objects):
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

    segment_objects(image, objects)
    masked = sum(1 for obj in objects if obj.get("mask"))
    print(f"[ERPK scan] {len(objects)} objects, {masked} with masks")

    try:
        medians = _mask_region_medians(objects, _depth_map(image))
    except Exception as e:
        print(f"[ERPK scan] Warning: depth ordering unavailable ({e}); "
              "keeping Florence detection order")
        medians = [None] * len(objects)
    return depth_ranks(objects, medians)


async def local_scan(image, max_objects, model):
    """Local engine: Florence-2 detection, SAM masks, Depth-Anything ordering.

    The model param is ignored: model selection is a cloud-provider concept
    (Gemini's MODELS list). The local pipeline's models are pinned by revision,
    so there is nothing to choose. It stays in the signature for engine-contract
    parity. The blocking torch work runs in a thread so it never stalls the
    event loop when two scans share it.
    """
    return await asyncio.to_thread(_local_scan_sync, image, max_objects)


# The single indirection point a future Moondream engine plugs into: any
# coroutine (PIL.Image, max_objects:int, model:str|None) -> list[scan-object].
# The scan button defaults to the local pipeline; Gemini stays opt-in per scan.
DEFAULT_ENGINE = local_scan


async def scan(image, max_objects=DEFAULT_MAX_OBJECTS, model=None, engine=None):
    """Run the active scan engine over the image, returning ranked scan objects."""
    return await (engine or DEFAULT_ENGINE)(image, max_objects, model)
