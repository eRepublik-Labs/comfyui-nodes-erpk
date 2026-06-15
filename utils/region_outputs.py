# ABOUTME: Converts typed regions into the node's interoperable pixel bounding-box output.
# ABOUTME: Pure integer math over the Region model — no torch or comfy_api.


def regions_to_pixel_bboxes(regions, width, height):
    """Convert normalized regions into one frame of integer pixel boxes: [[box, ...]] or []."""
    regions = [r for r in regions if r.op != "cutout"]
    if not regions:
        return []
    boxes = [{"x": round(region.box.x * width),
              "y": round(region.box.y * height),
              "width": round(region.box.w * width),
              "height": round(region.box.h * height)}
             for region in regions]
    return [boxes]
