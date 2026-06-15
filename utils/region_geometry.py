# ABOUTME: Pure geometry and predicate helpers over the typed Region/Box model.
# ABOUTME: Shared by prompt assembly, mask rendering, and image compositing.

from .region_contract import MIN_REGION_EXTENT


def box_2d(box):
    """Convert a normalized Box to Gemini's [ymin, xmin, ymax, xmax] on a 0-1000 grid."""
    return box.grid_2d()


def mask_pixel_box(box, width, height):
    """Integer pixel bounds (x0, y0, x1, y1) for a normalized Box, clamped to the
    frame and guaranteed to enclose at least one pixel."""
    return box.pixel_bounds(width, height)


def region_moved(region):
    """True when a region carries an origin box it has moved away from."""
    if region.source is None:
        return False
    src, box = region.source.box, region.box
    return (abs(src.x - box.x) > MIN_REGION_EXTENT
            or abs(src.y - box.y) > MIN_REGION_EXTENT
            or abs(src.w - box.w) > MIN_REGION_EXTENT
            or abs(src.h - box.h) > MIN_REGION_EXTENT)


def region_has_stored_mask(region):
    """True when the region carries a decodable box-relative segmentation mask."""
    return region.source is not None and region.source.mask is not None


def region_ref_image(region):
    """The reference-image number wired to this region at execute time, or None.

    ref_image is assigned from the wired ref_N sockets and is never serialized, so
    it lives as a runtime attribute on the region rather than a contract field.
    """
    return getattr(region, "ref_image", None)
