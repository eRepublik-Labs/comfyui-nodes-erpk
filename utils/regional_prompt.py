# ABOUTME: Pure prompt-builder node that turns canvas-drawn regions into a layout-aware
# ABOUTME: image-generation prompt plus interoperable pixel bounding boxes.

from comfy_api.latest import IO

from . import region_contract
from .region_contract import MIN_REGION_EXTENT, REGION_KINDS
from .region_geometry import (
    box_2d,
    mask_pixel_box,
    region_has_stored_mask,
    region_moved,
    region_ref_image,
)
from .region_image_ops import (
    apply_cutouts,
    apply_move_origin_cutouts,
    composite_moved_regions,
)
from .region_masks import _cutout_mask, _move_origin_mask, build_region_masks
from .region_outputs import regions_to_pixel_bboxes
from .region_prompt_text import (
    ANCHORS_LINE,
    LAYOUT_FOOTER,
    LAYOUT_HEADER,
    REFS_HEADER,
    REMOVAL_HEADER,
    REPOSITION_HEADER,
    aspect_ratio_string,
    build_prompt,
    placement_phrase,
)

# The node module is the public surface: the helpers live in region_* modules and
# are re-exported here so callers and tests import them from one place.
__all__ = [
    "RegionalPromptBuilder",
    "parse_regions",
    "DESC_INPUT_COUNT",
    "REF_INPUT_COUNT",
    "MIN_REGION_EXTENT",
    "REGION_KINDS",
    "box_2d",
    "mask_pixel_box",
    "region_has_stored_mask",
    "region_moved",
    "region_ref_image",
    "apply_cutouts",
    "apply_move_origin_cutouts",
    "composite_moved_regions",
    "_cutout_mask",
    "_move_origin_mask",
    "build_region_masks",
    "regions_to_pixel_bboxes",
    "ANCHORS_LINE",
    "LAYOUT_FOOTER",
    "LAYOUT_HEADER",
    "REFS_HEADER",
    "REMOVAL_HEADER",
    "REPOSITION_HEADER",
    "aspect_ratio_string",
    "build_prompt",
    "placement_phrase",
]

# Socket-only description overrides; desc_N feeds the region bound to slot N.
# A region binds to its stable bind_slot when it has one, and otherwise falls
# back to its depth position, so reordering the canvas does not remap wires.
DESC_INPUT_COUNT = 10
# Per-region reference images; ref_N attaches to the region bound to slot N. The
# wired images flow out on image_refs in region order, and the prompt counts
# them from 2 because the edit node's base image occupies slot 1.
REF_INPUT_COUNT = 10


def _binding_slot(index, region):
    """The socket slot a region binds to: its stable bind_slot, or its depth
    position (1-based) when it carries none (wired detections, legacy v1)."""
    return region.bind_slot if region.bind_slot is not None else index + 1


def parse_regions(regions_json):
    """Parse the canvas editor's JSON (v1 list or v2 document) into typed Regions."""
    return region_contract.parse(regions_json)


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
                *[
                    IO.Image.Input(
                        f"ref_{n}",
                        optional=True,
                        tooltip=f"Reference image for region {n}: forwarded on "
                                "image_refs, and the region's prompt line cites "
                                "its image number (regions numbered as on the "
                                "canvas).",
                    )
                    for n in range(1, REF_INPUT_COUNT + 1)
                ],
                IO.Custom("ERPK_REGIONS").Input(
                    "regions",
                    optional=True,
                    tooltip="Detected regions (JSON) appended after the canvas "
                            "regions at execute time. The canvas is unchanged, "
                            "and desc_N/ref_N bind canvas regions only.",
                ),
            ],
            outputs=[
                IO.String.Output("prompt"),
                IO.Custom("BOUNDING_BOX").Output("bboxes"),
                IO.Int.Output("width"),
                IO.Int.Output("height"),
                IO.Image.Output("image"),
                IO.Custom("ERPK_IMAGE_REFS").Output(
                    "image_refs",
                    tooltip="Per-region reference images in region order; "
                            "connect to an image edit node's image_refs input.",
                ),
                IO.Mask.Output(
                    "masks",
                    tooltip="One mask per region in region order [N, height, "
                            "width]; regions without a stored segmentation get a "
                            "filled-rectangle mask.",
                ),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        prompt = kwargs.get("prompt", "")
        image = kwargs.get("image")
        regions = parse_regions(kwargs.get("regions_data", "[]"))
        for index, region in enumerate(regions):
            slot = _binding_slot(index, region)
            if not 1 <= slot <= DESC_INPUT_COUNT:
                continue
            override = kwargs.get(f"desc_{slot}")
            if isinstance(override, str) and override.strip():
                region.content.desc = override.strip()
        # image_refs collects in region (depth) order so the output list stays
        # in region order; each region cites its 1-based position in that list,
        # offset by the base image in slot 1.
        image_refs = []
        for index, region in enumerate(regions):
            slot = _binding_slot(index, region)
            if not 1 <= slot <= REF_INPUT_COUNT:
                continue
            ref = kwargs.get(f"ref_{slot}")
            if ref is not None:
                image_refs.append(ref)
                region.ref_image = len(image_refs) + 1
        # Appended after the override loops so desc_N/ref_N bind canvas regions
        # only; wired detections always land past the canvas indices.
        regions += parse_regions(kwargs.get("regions"))
        if not regions and not prompt.strip():
            raise ValueError("Describe the scene or add at least one region")
        image = composite_moved_regions(image, regions)
        image = apply_move_origin_cutouts(image, regions)
        image = apply_cutouts(image, regions)
        # Masks overlay the passed-through image, so they render at the
        # connected image's H x W; with no image they fall back to the widgets.
        mask_width, mask_height = width, height
        if image is not None:
            mask_height, mask_width = int(image.shape[1]), int(image.shape[2])
        masks = build_region_masks(regions, mask_width, mask_height)
        assembled = build_prompt(prompt, width, height, regions)
        bboxes = regions_to_pixel_bboxes(regions, width, height)
        return IO.NodeOutput(assembled, bboxes, width, height, image, image_refs, masks)
