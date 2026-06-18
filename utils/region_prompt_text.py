# ABOUTME: Assembles the hybrid scene + layout image prompt from typed regions.
# ABOUTME: Pure text only — no torch, numpy, or comfy_api — so it stays unit-testable.

import math

from .region_geometry import (
    box_2d,
    region_has_stored_mask,
    region_moved,
    region_ref_image,
)

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
    "0-1000 grid with top-left origin). Where you remove a leftover, rebuild that "
    "area as natural background that continues the surrounding scene; do not "
    "place any object, subject, animal, plant, sign, or text there:"
)
# Model-applied moves are NOT composited into the image — the object still sits
# only at its origin, with nothing pasted at the destination — so the prompt asks
# the model to perform the relocation itself rather than to clean up a paste.
MODEL_REPOSITION_HEADER = (
    "Relocate the elements below — move each existing object, do not add a new "
    "one. There is exactly one of each: erase it completely from its current "
    "location (rebuild that area as natural background that continues the "
    "surrounding scene, leaving no copy or trace of it behind), then render that "
    'same object at the target location, blending naturally (areas are "box_2d = '
    '[ymin, xmin, ymax, xmax]" on a 0-1000 grid with top-left origin):'
)
ANCHORS_LINE = (
    "Every other element in the image stays exactly where it is — do not "
    "remove, add, or alter anything else."
)
# Cut-out regions are already content-aware-filled in the image the model
# receives (apply_cutouts), but an edit model repaints freely, so the prompt
# must tell it to rebuild those areas as plain background — without naming what
# was there, which would invite re-adding it.
REMOVAL_HEADER = (
    "Remove the contents of these areas: rebuild each as natural background that "
    "continues the surrounding scene (same surfaces, texture, lighting, and "
    "perspective). Do not place any object, subject, animal, plant, sign, or "
    "text in them. Any element described above that falls within one of these "
    "areas stays — clear only around it (areas are "
    '"box_2d = [ymin, xmin, ymax, xmax]" on a 0-1000 grid with top-left origin):'
)
LAYOUT_FOOTER = (
    "Every element must stay fully inside its placement area and fill most of it. "
    "Put each element exactly at its own box_2d and nowhere else, even if a "
    "different, similar-looking spot in the image seems more natural. "
    "Do not add other prominent subjects. The placement areas are invisible "
    "composition guides: never draw boxes, frames, outlines, coordinates, or any "
    "annotation overlays in the image."
)
# When an image is connected the node is editing a photo, not composing a scene.
# Leading with a strong preservation instruction (and dropping the "compose a
# frame" framing) keeps an edit model from re-rendering everything that is not an
# explicit edit.
EDIT_PREAMBLE = (
    "Edit the provided image. Keep it faithful to the original — the same "
    "subjects, textures, colors, lighting, framing, and composition — and apply "
    "ONLY the changes described below. Do not re-render, restyle, or regenerate "
    "any part of the image that is not an explicit edit. Keep the original "
    "orientation and framing exactly: do not flip, mirror, rotate, or crop the "
    "image."
)
# Inserted regions had their reference image composited into the scene at their
# box already, so the model must not move or re-place them — only integrate them.
INSERT_HEADER = (
    "The elements below were already placed into the image at their exact "
    "positions. Keep each exactly where it is — do not move, resize, or "
    'duplicate it — only blend it into the scene (areas are "box_2d = [ymin, '
    'xmin, ymax, xmax]" on a 0-1000 grid with top-left origin):'
)
# A small colored dot is drawn at each model-placed element's box center
# (region_image_ops.draw_placement_markers). The model ignores box_2d numbers but
# reads pixels, so the dot is a target it can actually see; it must be painted out
# so it never survives into the result.
MARKER_HEADER = (
    "Solid colored dots have been drawn on the image to mark placements — each is "
    "a filled dot in a unique color with a label letter inside it, and each "
    "element below names its marker(s) by letter and color. A newly added element "
    "has one dot: place it centered there. A move has two dots — one on the object "
    "at its current spot and one at its target — so move that object from the "
    "first dot onto the second. An object to be removed has one dot on it: delete "
    "that object and rebuild the background where it was. The dots are guides, not "
    "part of the scene: paint every dot out completely so none of it remains. Each "
    "dot is the exact, required location for its element — put the element on its "
    "dot even if a "
    "different spot in the scene looks more natural or more typical for it; never "
    "move it off its dot to a more likely place."
)


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
    box = region.box
    placement = placement_phrase(box.x, box.y, box.w, box.h)
    # The box_2d carries the extent; a spelled-out percent size on top of it reads
    # as a competing instruction and edit models place worse with it, so the line
    # states only where the element goes.
    geometry = f"{placement}. box_2d = {box_2d(box)}"
    # Referenced items use take-from-image phrasing: a trailing "as shown in"
    # aside is weak enough that models follow the words and drop the picture.
    ref = region_ref_image(region)
    if region.kind == "text":
        styled = f", styled as shown in image {ref}" if ref else ""
        if region.content.desc:
            return f'The text "{region.content.text}", {region.content.desc}{styled}: {geometry}'
        return f'The text "{region.content.text}"{styled}: {geometry}'
    if ref:
        subject = (
            f"{region.content.desc}, taken from image {ref} (reproduce that exact item)"
            if region.content.desc
            else f"The item shown in image {ref}, reproduced exactly"
        )
        return f"{subject}: {geometry}"
    return f'{region.content.desc or "An element"}: {geometry}'


def _boxes_overlap(a, b):
    """Fraction of box b's area that box a covers (normalized Boxes)."""
    ix = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
    iy = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
    area = b.w * b.h
    return (ix * iy) / area if area > 0 else 0.0


# A node-composited move is a hard-edged paste of original pixels — it reads as a
# sticker until the model relights it and grounds it with a shadow. The edit
# preamble tells the model to leave untouched regions alone, so the kept copy must
# be named as an explicit harmonization target or it stays copy-paste. Identity is
# pinned ("keep its shape, colors, and details") so harmonizing never re-renders it.
BLEND_DIRECTIVE = (
    "blending it into the scene so it looks photographed in place, not pasted: "
    "relight it to match the scene's light direction, intensity, and color "
    "temperature; ground it with a contact shadow and soft ambient occlusion "
    "where it meets the surface; match the surrounding depth of field, focus, and "
    "film grain; and let nearby colors and reflections spill onto it — keep its "
    "shape, pose, colors, and identifying details unchanged."
)


def _move_line(region):
    # Hybrid phrasing, same doctrine as placement lines: the verbal
    # placement drives the model, the coordinates pin it.
    src = region.source.box
    dest = region.box
    origin = box_2d(src)
    target = box_2d(dest)
    placement = placement_phrase(dest.x, dest.y, dest.w, dest.h)
    subject = region.content.desc or "The element"
    # When the destination covers the origin, the paste hides the old copy:
    # there is no duplicate to remove, and asking for one invites cutting a
    # hole through the pasted object.
    if _boxes_overlap(dest, src) > 0.9:
        return (
            f"{subject}: keep the one {placement} (box_2d = {target}), "
            f"{BLEND_DIRECTIVE}"
        )
    # When the destination overlaps the origin, "remove the duplicate at
    # [src]" would also remove the kept copy — the instruction is
    # self-contradicting and models resolve it by doing nothing. Erasing
    # only what sticks out beyond the kept copy is geometrically truthful.
    if _boxes_overlap(src, dest) > 0.25:
        return (
            f"{subject}: the old, larger copy overlaps the kept one — "
            f"erase every part of it outside box_2d = {target} and fill "
            f"those areas with the scene's background. Keep the copy "
            f"{placement} (box_2d = {target}), {BLEND_DIRECTIVE}"
        )
    return (
        f"{subject}: remove the duplicate at box_2d = {origin} and fill "
        f"that area with the scene's background. Keep the one {placement} "
        f"(box_2d = {target}), {BLEND_DIRECTIVE}"
    )


def _join_names(names):
    """Join names as prose: "a", "a and b", or "a, b, and c"."""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def _occluder_regions(region, regions):
    """The scanned objects that sit in front of `region` and cover it.

    An object later in `regions` and overlapping the move is in front of it
    (back-to-front order). It occludes in pixels either because it is static and
    re-stamped (region_image_ops._reapply_occluders) or because it is a node move
    whose paste lands on top in that same order. A model-move occluder is never
    composited, so it cannot occlude and is excluded; a hand-drawn box carries no
    silhouette and is a layout guide. Returned in depth order, back-to-front.
    """
    index = next((i for i, other in enumerate(regions) if other is region), None)
    if index is None:
        return []
    found = []
    for other in regions[index + 1:]:
        if (other.op == "cutout" or other.kind == "text"
                or (region_moved(other) and other.edit_by == "model")
                or not region_has_stored_mask(other)):
            continue
        if _boxes_overlap(other.box, region.box) > 0:
            found.append(other)
    return found


def _occluder_names(region, regions):
    """Descriptions of the occluders in front of `region`, in depth order."""
    return [other.content.desc or "the object in front"
            for other in _occluder_regions(region, regions)]


def _occlusion_clause(subject, names):
    """A trailing clause keeping a move's occluded part hidden.

    Framed from the occluder's side ("X in front of it"), which edit models honor
    better than a subject-side "it is behind X" — foreground-covers-background is
    how they reason. For node moves the composited pixels already back this up; on
    a model move it is the only signal and stays best-effort.
    """
    occ = _join_names(names)
    return (
        f" With {occ} in front of it, {subject} is partly hidden: render only "
        f"the part of it not covered by {occ}, and do not redraw the covered part."
    )


def _grounded_occlusion_clause(subject, occluders):
    """Occluder-framed occlusion clause carrying each occluder's box_2d.

    For a model move there are no composited pixels to imply the layering, so the
    occluder's coordinates are stated next to the move's own box — bounding-box
    grounding for both objects is the strongest lever an edit model honors for
    depth. Best-effort: it raises the odds, it does not guarantee occlusion.
    """
    refs = _join_names([
        f"{other.content.desc or 'the object in front'} (box_2d = {box_2d(other.box)})"
        for other in occluders
    ])
    plain = _join_names([other.content.desc or "the object in front"
                         for other in occluders])
    return (
        f" With {refs} in front of it, {subject} is partly hidden: render only "
        f"the visible part of it and do not redraw the part covered by {plain}."
    )


def _box_center(box):
    return (box.x + box.w / 2, box.y + box.h / 2)


_DIRECTIONS = ("to the left of", "to the right of", "above", "below")


def _direction(dest, other_box):
    """The directional placement of `dest` relative to a separated `other_box`."""
    dcx, dcy = _box_center(dest)
    ocx, ocy = _box_center(other_box)
    if abs(ocx - dcx) >= abs(ocy - dcy):
        return "to the left of" if ocx > dcx else "to the right of"
    return "above" if ocy > dcy else "below"


def _depth_relation(region, other, regions):
    """"in front of" / "behind" from back-to-front order, or "" if unresolved.

    Later in `regions` = nearer the camera, the same rule the occlusion composite
    follows, so a model-move's stated depth matches what a node-move would paint.
    """
    ri = next((i for i, r in enumerate(regions) if r is region), None)
    oi = next((i for i, r in enumerate(regions) if r is other), None)
    if ri is None or oi is None or ri == oi:
        return ""
    return "in front of" if ri > oi else "behind"


def _anchor_relation(region, other, regions):
    """How `region`'s destination relates to a landmark: depth when they overlap
    (front/behind is what's visible there), direction when they are separated."""
    if _boxes_overlap(region.box, other.box) > 0:
        depth = _depth_relation(region, other, regions)
        if depth:
            return depth
    return _direction(region.box, other.box)


def _flanked_between(dest, first, second):
    """The "between A and B" phrase when two landmarks straddle `dest`, else "".

    A straddle means the two landmark centers sit on opposite sides of the
    destination on either axis; the names are ordered along that axis (top→bottom
    or left→right) so the prose matches the layout.
    """
    dcx, dcy = _box_center(dest)
    fx, fy = _box_center(first.box)
    sx, sy = _box_center(second.box)
    if (fy - dcy) * (sy - dcy) < 0:
        top, bottom = (first, second) if fy < sy else (second, first)
        return f"between {top.content.desc} and {bottom.content.desc}"
    if (fx - dcx) * (sx - dcx) < 0:
        left, right = (first, second) if fx < sx else (second, first)
        return f"between {left.content.desc} and {right.content.desc}"
    return ""


def _placement_anchors(region, regions):
    """Describe a placement's destination relative to nearby grounded landmarks.

    Edit models place objects by landmarks far more reliably than by box_2d
    coordinates, so the destination is pinned to the nearest named objects that
    are actually in the image at a known position: a scanned region (has a
    source) or a node move (composited at its box). A model move or a not-yet-
    placed addition has no known position and is skipped, as are cut-outs, text,
    hidden, and unnamed regions. Used for both model moves and hand-drawn
    additions, neither of which the model places well from coordinates alone.

    Two separated landmarks that straddle the spot read as "between A and B"
    (the strongest triangulation); otherwise each landmark gets a relation that
    is a depth cue when it overlaps the move and a direction when it does not.
    Returns a trailing sentence (" Place it ...."), or "" when nothing anchors it.
    """
    dest = region.box
    dcx, dcy = _box_center(dest)
    landmarks = []
    for other in regions:
        if (other is region or other.op == "cutout" or other.kind != "object"
                or other.ui.hidden or not other.content.desc
                or other.source is None
                or (region_moved(other) and other.edit_by == "model")):
            continue
        ocx, ocy = _box_center(other.box)
        landmarks.append(((ocx - dcx) ** 2 + (ocy - dcy) ** 2, other))
    if not landmarks:
        return ""
    landmarks.sort(key=lambda item: item[0])
    first = landmarks[0][1]
    rel_first = _anchor_relation(region, first, regions)
    if len(landmarks) > 1:
        second = landmarks[1][1]
        rel_second = _anchor_relation(region, second, regions)
        if rel_first in _DIRECTIONS and rel_second in _DIRECTIONS:
            between = _flanked_between(dest, first, second)
            if between:
                return f" Place it {between}."
        place = (f"{rel_first} {first.content.desc} and "
                 f"{rel_second} {second.content.desc}")
    else:
        place = f"{rel_first} {first.content.desc}"
    return f" Place it {place}."


def _model_move_line(region, regions):
    # No composite happened — the object is still visible at its origin — so the
    # prompt asks the model to relocate the object it can see. Lead with the
    # destination (the action the model must perform) and name the origin second
    # (the cleanup); models weight the first instruction, and one box per clause
    # keeps the two coordinate sets from being conflated. The box_2d pins the
    # target extent; a spelled-out percent/pixel size on top of it competes with
    # the box and places worse, so size rides on the box plus a no-resize cue. The
    # caller appends the marker clause, which names the from/to dots the model
    # actually follows.
    src = region.source.box
    dest = region.box
    placement = placement_phrase(dest.x, dest.y, dest.w, dest.h)
    subject = region.content.desc or "The element"
    return (
        f"{subject}: its new position is {placement}, exactly filling box_2d = "
        f"{box_2d(dest)}. Keep it at the size of that box; do not enlarge or "
        f"shrink it.{_placement_anchors(region, regions)} It is currently at "
        f"box_2d = {box_2d(src)}; erase it there completely — leave no copy of it "
        f"behind — and rebuild that area as natural background. Render the same "
        f"object at the new position, matching lighting, shadows, and perspective."
    )


def _classify_regions(regions):
    """Split regions into inserts, moves, anchors, and additions for the prompt.

    An inserted region is one whose reference image was composited into the scene
    at its box (region.inserted) — it is already placed, so it only needs a blend
    directive. A scanned region (one with an origin box) that has not moved
    describes pixels already in the image — giving it a placement line invites the
    model to re-render the scene instead of editing it, so it becomes a silent
    anchor. Reference-image and text regions always render as additions regardless
    of origin.
    """
    inserts, moves, anchors, additions = [], [], [], []
    for region in regions:
        # Cut-out regions are removed from the scene; they never get a line.
        if region.op == "cutout":
            continue
        if getattr(region, "inserted", False):
            inserts.append(region)
            continue
        plain = region.kind != "text" and not region_ref_image(region)
        if plain and region_moved(region):
            moves.append(region)
        elif plain and region.source is not None:
            anchors.append(region)
        else:
            additions.append(region)
    return inserts, moves, anchors, additions


def marker_regions(regions):
    """The regions that get a visual marker: the ones the edit model acts on by
    reading pixels — additions and model-applied moves (placement) and model
    cut-outs (removal) — with markers left on. Node-composited moves/cut-outs and
    inserted refs already have their pixels done, so they never do, and a region
    with markers off opts out.
    """
    _, moves, _, additions = _classify_regions(regions)
    model_moves = [region for region in moves if region.edit_by == "model"]
    model_cutouts = [region for region in regions
                     if region.op == "cutout" and region.kind != "text"
                     and region.edit_by == "model"]
    return [region for region in model_moves + additions + model_cutouts
            if getattr(region, "markers", True)]


def _marker_clause(region):
    """A trailing clause pointing an element at its drawn marker(s), or "" if
    unmarked. A model move carries two markers and reads as a from/to move; an
    addition carries one and is centered on its dot."""
    color = getattr(region, "marker_color", None)
    if not color:
        return ""
    label = getattr(region, "marker_label", None)
    dest = f"marker {label} (the {color} dot)" if label else f"the {color} dot"
    origin_color = getattr(region, "marker_origin_color", None)
    if origin_color:
        origin_label = getattr(region, "marker_origin_label", None)
        origin = (f"marker {origin_label} (the {origin_color} dot it sits on now)"
                  if origin_label else f"the {origin_color} dot it sits on now")
        spot = f"marker {origin_label}" if origin_label else "that dot"
        return (f" Move it from {origin} to {dest}: there is only one of it — "
                f"erase it completely from {spot} so no copy remains, then paint "
                f"out both dots.")
    return f" Center it on {dest}."


def _chroma_note(color):
    # When cleared areas are chroma-filled instead of inpainted, name the key
    # color so a downstream model treats those flat patches as empty to rebuild.
    return (
        f"Cleared areas — removed objects and the old positions of moved ones — "
        f"are filled with a flat chroma key color ({color}). Treat any patch of "
        f"that exact color as empty space and rebuild it as natural background "
        f"that continues the scene; never leave the color visible."
    )


def build_prompt(prompt, width, height, regions, edit_mode=False, chroma=None):
    """Assemble the hybrid scene + layout prompt for image generation.

    edit_mode is set when an image is connected: the prompt then leads with a
    preservation instruction and drops the "compose a frame" framing, so an edit
    model edits the supplied photo instead of re-rendering the whole scene.

    Move origins and cut-outs are deterministically filled before the image
    reaches the model — inpainted, or (when chroma is a hex color) flat-keyed.
    An edit model regenerates freely, so the prompt always tells it to rebuild
    those areas as natural background, and when chroma is set it names the key
    color so the model treats those patches as empty. The fill is only the floor
    for the no-edit-model path; relying on it alone lets the model re-add content.
    """
    lines = []
    scene = prompt.strip()
    if edit_mode:
        lines.append(EDIT_PREAMBLE)
        if scene:
            lines.append("")
            lines.append(scene)
        # box_2d is normalized 0-1000, but the model maps that grid onto the
        # frame's real extent; stating the pixel size pins the grid to the image
        # it is editing. No "compose" framing — this only states dimensions.
        lines.append("")
        lines.append(f"The image is {width}x{height} pixels.")
    else:
        if scene:
            lines.append(scene)
            lines.append("")
        ratio = aspect_ratio_string(width, height)
        lines.append(f"Compose for a {width}x{height} frame (aspect ratio {ratio}).")
    inserts, moves, anchors, additions = _classify_regions(regions)
    # Node-applied moves are already composited (clean up the paste); model-applied
    # moves are untouched in the image (relocate them from the prompt).
    node_moves = [region for region in moves if region.edit_by != "model"]
    model_moves = [region for region in moves if region.edit_by == "model"]
    # The chroma key fill touches every move's origin (node and model both clear
    # it) plus node cut-outs; name the key color once up front when any exist.
    node_removals = [r for r in regions if r.op == "cutout" and r.kind != "text"
                     and r.edit_by != "model"]
    if chroma and (moves or node_removals):
        lines.append("")
        lines.append(_chroma_note(chroma))
    # One legend for every numbered reference — wired ref images on additions and
    # the crops attached to model moves alike — so each "image N" is explained.
    if any(region_ref_image(r) or getattr(r, "move_ref_image", None)
           for r in regions):
        lines.append("")
        lines.append(REFS_HEADER)
    # The dots are drawn before any placement section so the model knows what the
    # colors mean when it reaches each element's marker clause.
    if any(getattr(r, "marker_color", None) for r in regions):
        lines.append("")
        lines.append(MARKER_HEADER)
    if node_moves:
        lines.append("")
        lines.append(REPOSITION_HEADER)
        for index, region in enumerate(node_moves, start=1):
            line = _move_line(region)
            occluders = _occluder_names(region, regions)
            if occluders:
                line += _occlusion_clause(region.content.desc or "the element",
                                          occluders)
            lines.append(f"{index}. {line}")
    if model_moves:
        lines.append("")
        lines.append(MODEL_REPOSITION_HEADER)
        for index, region in enumerate(model_moves, start=1):
            line = _model_move_line(region, regions)
            occluders = _occluder_regions(region, regions)
            if occluders:
                line += _grounded_occlusion_clause(
                    region.content.desc or "the element", occluders)
            line += _marker_clause(region)
            lines.append(f"{index}. {line}")
    if moves and anchors:
        lines.append(ANCHORS_LINE)
    if inserts:
        lines.append("")
        lines.append(INSERT_HEADER)
        for index, region in enumerate(inserts, start=1):
            subject = region.content.desc or "the element"
            placement = placement_phrase(region.box.x, region.box.y,
                                         region.box.w, region.box.h)
            lines.append(f"{index}. {subject}: {placement} (box_2d = "
                         f"{box_2d(region.box)}), {BLEND_DIRECTIVE}")
    if additions:
        lines.append("")
        lines.append(LAYOUT_HEADER)
        for index, region in enumerate(additions, start=1):
            line = _element_line(region)
            # Hand-drawn additions are placed by coordinates the model ignores;
            # anchoring them to grounded objects nudges them to a plausible spot.
            if region.kind != "text":
                line += _placement_anchors(region, regions)
            line += _marker_clause(region)
            # When editing a photo, an added object is dropped onto an existing
            # scene and reads as a sticker without relighting; ask for the same
            # integration a move gets. Compose mode renders the whole frame at
            # once, so there is nothing to blend into and the directive is skipped.
            if edit_mode and region.kind != "text":
                line += f" {BLEND_DIRECTIVE[0].upper()}{BLEND_DIRECTIVE[1:]}"
            lines.append(f"{index}. {line}")
        if anchors and not moves:
            lines.append(ANCHORS_LINE)
    removals = [r for r in regions if r.op == "cutout" and r.kind != "text"]
    if removals:
        lines.append("")
        lines.append(REMOVAL_HEADER)
        for index, region in enumerate(removals, start=1):
            # A model cut-out still has its object in the image; a marker on it
            # tells the model which object to delete (pixels, not coordinates). A
            # node cut-out is already cleared, so only its area is named.
            color = getattr(region, "marker_color", None)
            if color and region.edit_by == "model":
                label = getattr(region, "marker_label", None)
                mark = (f"marker {label} (the {color} dot)" if label
                        else f"the {color} dot")
                lines.append(f"{index}. The object at {mark}, box_2d = "
                             f"{box_2d(region.box)}: remove it and rebuild that "
                             f"area as natural background, then paint the dot out.")
            else:
                lines.append(f"{index}. box_2d = {box_2d(region.box)}")
    if moves or additions or inserts:
        lines.append(LAYOUT_FOOTER)
    return "\n".join(lines)
