# ABOUTME: Typed, pure region document model shared by the canvas editor and prompt builder.
# ABOUTME: Parses legacy v1 and v2 region documents into Regions and serializes them back to v2.

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

# Drawn regions smaller than this fraction of the frame in either axis carry no
# usable geometry and are dropped at the edge. Re-exported by the facade.
MIN_REGION_EXTENT = 0.005
REGION_KINDS = {"object", "text"}
SCHEMA_VERSION = 2


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


@dataclass
class Box:
    """A normalized 0..1 rectangle in frame space."""

    x: float
    y: float
    w: float
    h: float

    def grid_2d(self):
        """Convert to [ymin, xmin, ymax, xmax] integers on a 0-1000 grid (top-left origin)."""
        def to_grid(value):
            return _clamp(round(value * 1000), 0, 1000)
        return [to_grid(self.y), to_grid(self.x),
                to_grid(self.y + self.h), to_grid(self.x + self.w)]

    def pixel_bounds(self, width, height):
        """Integer (x0, y0, x1, y1) pixel bounds clamped to the frame.

        The far edge is rounded from the box's far coordinate rather than from
        its width, and floored to at least one pixel past the near edge, so the
        box always encloses at least one pixel even at low resolutions.
        """
        x0 = _clamp(round(self.x * width), 0, width - 1)
        y0 = _clamp(round(self.y * height), 0, height - 1)
        x1 = _clamp(round((self.x + self.w) * width), x0 + 1, width)
        y1 = _clamp(round((self.y + self.h) * height), y0 + 1, height)
        return (x0, y0, x1, y1)

    def as_dict(self):
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}


@dataclass
class Mask:
    """A box-relative segmentation mask carried by scanned regions."""

    data: str
    enc: str = "png-b64"
    w: int = 0
    h: int = 0

    def as_dict(self):
        return {"enc": self.enc, "w": self.w, "h": self.h, "data": self.data}


@dataclass
class Content:
    """A region's prompt payload: a description and literal text to render."""

    desc: str = ""
    text: str = ""


@dataclass
class Source:
    """A scanned region's origin: where it came from and what was detected there."""

    box: Box
    mask: Mask | None = None
    label: str = ""


@dataclass
class Ui:
    """Editor-only state that never influences the prompt, bboxes, or masks."""

    parent: str | None = None
    hidden: bool = False
    collapsed: bool = False


@dataclass
class Region:
    """One placement: its box, content, optional scan origin, op, binding, and UI state."""

    id: str
    kind: str
    box: Box
    content: Content
    source: Source | None = None
    op: str = "normal"
    bind_slot: int | None = None
    # Who performs this region's geometric edit (move/cut-out): "node" composites
    # and inpaints it deterministically; "model" leaves the pixels untouched and
    # asks the edit model to do it from the prompt. Irrelevant for static regions.
    edit_by: str = "node"
    ui: Ui = field(default_factory=Ui)


def parse(value):
    """Parse a v1 list or v2 document into a depth-ordered list of Regions.

    Validation happens here at the edge: JSON is decoded, coordinates are
    coerced to finite floats and clamped to the unit square, sub-extent boxes
    are dropped, and any malformed entry is skipped without failing its peers.
    """
    data = _load(value)
    if isinstance(data, list):
        regions = _parse_v1(data)
    elif isinstance(data, dict):
        regions = _parse_v2(data)
    else:
        return []
    _assign_missing_ids(regions)
    return regions


def serialize(regions):
    """Render a list of Regions into a v2 document ready for json.dumps."""
    return {
        "version": SCHEMA_VERSION,
        "order": [region.id for region in regions],
        "regions": [_region_to_dict(region) for region in regions],
    }


def _load(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _parse_v1(entries):
    regions = []
    for entry in entries:
        region = _parse_v1_entry(entry)
        if region is not None:
            regions.append(region)
    return regions


def _parse_v1_entry(entry):
    if not isinstance(entry, dict):
        return None
    box = _coerce_box(entry)
    if box is None:
        return None
    content = Content(_coerce_str(entry.get("desc")), _coerce_str(entry.get("text")))
    op = "cutout" if entry.get("cutout") is True else "normal"
    ui = Ui(parent=_coerce_optional_str(entry.get("parent")),
            hidden=entry.get("hidden") is True,
            collapsed=False)
    return Region(
        id=_coerce_optional_str(entry.get("id")) or "",
        kind=_coerce_kind(entry.get("kind")),
        box=box,
        content=content,
        source=_parse_v1_source(entry, box),
        op=op,
        bind_slot=None,
        ui=ui,
    )


def _parse_v1_source(entry, box):
    """Build a Source from a v1 entry's flat scan fields, or None when hand-drawn."""
    mask = _parse_v1_mask(entry.get("mask"))
    label = _coerce_str(entry.get("group"))
    src_box = _coerce_box(entry.get("src"))
    if mask is None and not label and src_box is None:
        return None
    # A scanned region with no recorded origin has not moved: its current box
    # is its origin, so the move geometry stays comparable.
    if src_box is None:
        src_box = Box(box.x, box.y, box.w, box.h)
    return Source(box=src_box, mask=mask, label=label)


def _parse_v1_mask(value):
    if isinstance(value, str) and value:
        return Mask(data=value)
    return None


def _parse_v2(doc):
    raw = doc.get("regions")
    if not isinstance(raw, list):
        return []
    parsed = []
    by_id = {}
    for entry in raw:
        region = _parse_v2_entry(entry)
        if region is None:
            continue
        parsed.append(region)
        if region.id:
            by_id.setdefault(region.id, region)
    order = doc.get("order")
    if not isinstance(order, list):
        return parsed
    # order[] carries depth back-to-front, decoupled from the regions array.
    ordered = []
    seen = set()
    for rid in order:
        region = by_id.get(rid)
        if region is not None and id(region) not in seen:
            ordered.append(region)
            seen.add(id(region))
    for region in parsed:
        if id(region) not in seen:
            ordered.append(region)
            seen.add(id(region))
    return ordered


def _parse_v2_entry(entry):
    if not isinstance(entry, dict):
        return None
    box = _coerce_box(entry.get("box"))
    if box is None:
        return None
    raw_content = entry.get("content")
    if isinstance(raw_content, dict):
        content = Content(_coerce_str(raw_content.get("desc")),
                          _coerce_str(raw_content.get("text")))
    else:
        content = Content()
    op = "cutout" if entry.get("op") == "cutout" else "normal"
    return Region(
        id=_coerce_optional_str(entry.get("id")) or "",
        kind=_coerce_kind(entry.get("kind")),
        box=box,
        content=content,
        source=_parse_v2_source(entry.get("source"), box),
        op=op,
        bind_slot=_parse_bind(entry.get("bind")),
        edit_by=_coerce_edit_by(entry.get("edit_by")),
        ui=_parse_v2_ui(entry.get("ui")),
    )


def _parse_v2_source(value, box):
    if not isinstance(value, dict):
        return None
    src_box = _coerce_box(value.get("box"))
    if src_box is None:
        src_box = Box(box.x, box.y, box.w, box.h)
    return Source(box=src_box,
                  mask=_parse_v2_mask(value.get("mask")),
                  label=_coerce_str(value.get("label")))


def _parse_v2_mask(value):
    if not isinstance(value, dict):
        return None
    data = value.get("data")
    if not isinstance(data, str) or not data:
        return None
    enc = value.get("enc")
    enc = enc if isinstance(enc, str) and enc else "png-b64"
    return Mask(data=data, enc=enc, w=_coerce_int(value.get("w")), h=_coerce_int(value.get("h")))


def _parse_v2_ui(value):
    if not isinstance(value, dict):
        return Ui()
    return Ui(parent=_coerce_optional_str(value.get("parent")),
              hidden=value.get("hidden") is True,
              collapsed=value.get("collapsed") is True)


def _parse_bind(value):
    if not isinstance(value, dict):
        return None
    slot = value.get("slot")
    if isinstance(slot, bool):
        return None
    try:
        return int(slot)
    except (TypeError, ValueError):
        return None


def _coerce_box(value):
    """Parse and clamp a normalized box mapping, or None if unusable or sub-extent."""
    if not isinstance(value, dict):
        return None
    try:
        x = float(value.get("x", 0))
        y = float(value.get("y", 0))
        w = float(value.get("w", 0))
        h = float(value.get("h", 0))
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
    return Box(x, y, w, h)


def _coerce_str(value):
    return value if isinstance(value, str) else ""


def _coerce_optional_str(value):
    return value if isinstance(value, str) and value else None


def _coerce_kind(value):
    return value if isinstance(value, str) and value in REGION_KINDS else "object"


def _coerce_edit_by(value):
    return "model" if value == "model" else "node"


def _coerce_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _assign_missing_ids(regions):
    """Give every id-less region a stable id unique within the document."""
    used = {region.id for region in regions if region.id}
    counter = 0
    for region in regions:
        if region.id:
            continue
        candidate = f"r{counter}"
        while candidate in used:
            counter += 1
            candidate = f"r{counter}"
        region.id = candidate
        used.add(candidate)
        counter += 1


def _region_to_dict(region):
    out = {
        "id": region.id,
        "kind": region.kind,
        "box": region.box.as_dict(),
        "content": {"desc": region.content.desc, "text": region.content.text},
    }
    if region.source is not None:
        out["source"] = {
            "box": region.source.box.as_dict(),
            "mask": region.source.mask.as_dict() if region.source.mask else None,
            "label": region.source.label,
        }
    out["op"] = region.op
    # Default stays out of the document so node-applied regions serialize as before.
    if region.edit_by != "node":
        out["edit_by"] = region.edit_by
    out["bind"] = {"slot": region.bind_slot} if region.bind_slot is not None else None
    out["ui"] = {
        "parent": region.ui.parent,
        "hidden": region.ui.hidden,
        "collapsed": region.ui.collapsed,
    }
    return out
