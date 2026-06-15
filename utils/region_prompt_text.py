# ABOUTME: Assembles the hybrid scene + layout image prompt from typed regions.
# ABOUTME: Pure text only — no torch, numpy, or comfy_api — so it stays unit-testable.

import math

from .region_geometry import box_2d, region_moved, region_ref_image

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
    'text in them (areas are "box_2d = [ymin, xmin, ymax, xmax]" on a 0-1000 '
    "grid with top-left origin):"
)
LAYOUT_FOOTER = (
    "Every element must stay fully inside its placement area and fill most of it. "
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
    "any part of the image that is not an explicit edit."
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
    geometry = (
        f"{placement}, covering about {round(box.w * 100)}% of the image "
        f"width and {round(box.h * 100)}% of its height. box_2d = {box_2d(box)}"
    )
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
            f"{subject}: blend the one {placement} (box_2d = {target}) "
            f"naturally into the scene — match lighting, shadows, and "
            f"perspective."
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
        if region.op == "cutout":
            continue
        plain = region.kind != "text" and not region_ref_image(region)
        if plain and region_moved(region):
            moves.append(region)
        elif plain and region.source is not None:
            anchors.append(region)
        else:
            additions.append(region)
    return moves, anchors, additions


def build_prompt(prompt, width, height, regions, edit_mode=False):
    """Assemble the hybrid scene + layout prompt for image generation.

    edit_mode is set when an image is connected: the prompt then leads with a
    preservation instruction and drops the "compose a frame" framing, so an edit
    model edits the supplied photo instead of re-rendering the whole scene.

    Move origins and cut-outs are deterministically inpainted before the image
    reaches the model, but an edit model regenerates freely, so the prompt always
    tells it to remove the leftover at the origin and rebuild those areas as
    natural background. The OpenCV fill is only the floor for the no-edit-model
    path; relying on it alone lets the model re-add what was there.
    """
    lines = []
    scene = prompt.strip()
    if edit_mode:
        lines.append(EDIT_PREAMBLE)
        if scene:
            lines.append("")
            lines.append(scene)
    else:
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
        if any(region_ref_image(region) for region in additions):
            header += " " + REFS_HEADER
        lines.append(header)
        for index, region in enumerate(additions, start=1):
            lines.append(f"{index}. {_element_line(region)}")
        if anchors and not moves:
            lines.append(ANCHORS_LINE)
    removals = [r for r in regions if r.op == "cutout" and r.kind != "text"]
    if removals:
        lines.append("")
        lines.append(REMOVAL_HEADER)
        for index, region in enumerate(removals, start=1):
            lines.append(f"{index}. box_2d = {box_2d(region.box)}")
    if moves or additions:
        lines.append(LAYOUT_FOOTER)
    return "\n".join(lines)
