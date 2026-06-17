# ABOUTME: Tests for RegionalPromptBuilder schema, region parsing, coordinate
# ABOUTME: conversions, prompt assembly, and pixel bounding-box outputs.

import ast
import inspect
import json

import pytest

from utils.region_contract import Box, Content, Region, Source, Mask, Ui
from utils.regional_prompt import (
    MARKER_HEADER,
    MODEL_REPOSITION_HEADER,
    REMOVAL_HEADER,
    REPOSITION_HEADER,
    RegionalPromptBuilder,
    _cutout_mask,
    _move_origin_mask,
    apply_cutouts,
    apply_move_origin_cutouts,
    aspect_ratio_string,
    assign_markers,
    box_2d,
    build_prompt,
    composite_moved_regions,
    composite_ref_at_box,
    crop_region_subject,
    build_region_masks,
    draw_placement_markers,
    marker_regions,
    mask_pixel_box,
    parse_regions,
    placement_phrase,
    region_has_stored_mask,
    region_moved,
    regions_to_pixel_bboxes,
)


def region(x=0.1, y=0.1, w=0.2, h=0.2, kind="object", desc="", text="",
           src=None, mask=None, cutout=False, parent=None, hidden=False,
           rid="", bind_slot=None, ref_image=None, edit_by="node", markers=True):
    """Build a Region the way the canvas/scan would, for concise fixtures.

    A src box or mask attaches a Source (scan origin); src defaults to the box
    itself when only a mask is given (a scanned-in-place region). ref_image is
    the runtime reference-image number execute() would assign. edit_by="model"
    hands the region's move/cut-out to the prompt instead of the node.
    """
    source = None
    if src is not None or mask is not None:
        sbox = Box(src["x"], src["y"], src["w"], src["h"]) if src else Box(x, y, w, h)
        source = Source(box=sbox, mask=Mask(data=mask) if mask else None, label="")
    built = Region(
        id=rid, kind=kind, box=Box(x, y, w, h),
        content=Content(desc=desc, text=text),
        source=source, op="cutout" if cutout else "normal",
        bind_slot=bind_slot, edit_by=edit_by, markers=markers,
        ui=Ui(parent=parent, hidden=hidden),
    )
    if ref_image is not None:
        built.ref_image = ref_image
    return built


# A v1 region document as the JS editor still emits it: a flat list of dicts.
# Kept as JSON source for the parse/execute paths; the typed expectations below
# describe what parse_regions yields.
CANONICAL_REGIONS = [
    {"x": 0.04, "y": 0.62, "w": 0.30, "h": 0.25, "kind": "object",
     "desc": "a red vintage car", "text": ""},
    {"x": 0.30, "y": 0.03, "w": 0.40, "h": 0.14, "kind": "text",
     "desc": "glowing neon letters", "text": "OPEN LATE"},
]

CANONICAL_PROMPT = (
    "A rainy neon city street at night, wet asphalt reflecting neon signs, "
    "cinematic photo\n"
    "\n"
    "Compose for a 1000x1000 frame (aspect ratio 1:1).\n"
    "\n"
    'Layout: place each element exactly where specified. Each position gives a '
    'verbal placement plus its placement area as "box_2d = [ymin, xmin, ymax, xmax]" '
    "on a 0-1000 grid with top-left origin. Elements are listed from back to "
    "front: where placement areas overlap, a later element appears in front of "
    "an earlier one.\n"
    "1. a red vintage car: at the bottom-left. box_2d = [620, 40, 870, 340]\n"
    '2. The text "OPEN LATE", glowing neon letters: at the top-center. '
    "box_2d = [30, 300, 170, 700]\n"
    "Every element must stay fully inside its placement area and fill most of it. "
    "Put each element exactly at its own box_2d and nowhere else, even if a "
    "different, similar-looking spot in the image seems more natural. "
    "Do not add other prominent subjects. The placement areas are invisible "
    "composition guides: never draw boxes, frames, outlines, coordinates, or any "
    "annotation overlays in the image."
)

CANONICAL_BBOXES = [[
    {"x": 40, "y": 620, "width": 300, "height": 250},
    {"x": 300, "y": 30, "width": 400, "height": 140},
]]


class TestSchema:
    def test_node_identity(self):
        schema = RegionalPromptBuilder.define_schema()
        assert schema.node_id == "RegionalPromptBuilder"
        assert schema.display_name == "Regional Prompt Builder"
        assert schema.category == "ERPK/utils"

    def test_input_ids_and_order(self):
        schema = RegionalPromptBuilder.define_schema()
        assert [i.id for i in schema.inputs] == [
            "width", "height", "prompt", "regions_data",
            "removal_fill", "chroma_color", "image",
            *[f"desc_{n}" for n in range(1, 11)],
            *[f"ref_{n}" for n in range(1, 11)],
            "regions",
        ]

    def test_regions_input_type_and_optional(self):
        schema = RegionalPromptBuilder.define_schema()
        regions_input = next(i for i in schema.inputs if i.id == "regions")
        assert regions_input.io_type == "ERPK_REGIONS"
        assert regions_input.optional is True

    def test_ref_inputs_are_images(self):
        schema = RegionalPromptBuilder.define_schema()
        for i in schema.inputs:
            if i.id.startswith("ref_"):
                assert i.io_type == "IMAGE", i.id

    def test_only_sockets_are_optional(self):
        schema = RegionalPromptBuilder.define_schema()
        optional = {i.id: bool(i.optional) for i in schema.inputs}
        required = ("width", "height", "prompt", "regions_data")
        for input_id, is_optional in optional.items():
            assert is_optional == (input_id not in required), input_id

    def test_desc_inputs_are_socket_only(self):
        schema = RegionalPromptBuilder.define_schema()
        for i in schema.inputs:
            if i.id.startswith("desc_"):
                assert i.force_input is True, i.id

    def test_dimension_widget_ranges(self):
        schema = RegionalPromptBuilder.define_schema()
        for input_id in ("width", "height"):
            widget = next(i for i in schema.inputs if i.id == input_id)
            assert widget.io_type == "INT"
            assert widget.default == 1024
            assert widget.min == 64
            assert widget.max == 8192
            assert widget.step == 8

    def test_prompt_widget_is_multiline(self):
        schema = RegionalPromptBuilder.define_schema()
        prompt_input = next(i for i in schema.inputs if i.id == "prompt")
        assert prompt_input.multiline is True

    def test_regions_data_default_and_socketless(self):
        schema = RegionalPromptBuilder.define_schema()
        regions_input = next(i for i in schema.inputs if i.id == "regions_data")
        assert regions_input.default == "[]"
        assert regions_input.socketless is True

    def test_output_ids_order_and_io_types(self):
        schema = RegionalPromptBuilder.define_schema()
        assert [o.id for o in schema.outputs] == [
            "prompt", "bboxes", "width", "height", "image", "image_refs", "masks",
        ]
        assert [o.io_type for o in schema.outputs] == [
            "STRING", "BOUNDING_BOX", "INT", "INT", "IMAGE", "ERPK_IMAGE_REFS",
            "MASK",
        ]

    def test_masks_output_is_appended_last(self):
        schema = RegionalPromptBuilder.define_schema()
        last = schema.outputs[-1]
        assert last.id == "masks"
        assert last.io_type == "MASK"

    def test_no_seed_input(self):
        schema = RegionalPromptBuilder.define_schema()
        assert not [i for i in schema.inputs if i.id == "seed"]

    def test_no_fingerprint_inputs(self):
        assert "fingerprint_inputs" not in RegionalPromptBuilder.__dict__

    def test_idempotent(self):
        schema = RegionalPromptBuilder.define_schema()
        assert not schema.not_idempotent

    def test_execute_is_not_async(self):
        assert not inspect.iscoroutinefunction(RegionalPromptBuilder.execute)

    def test_no_module_level_heavy_imports(self):
        # torch/numpy/PIL may be imported lazily inside build_region_masks, but
        # the module must import without the ComfyUI runtime present.
        module_path = inspect.getsourcefile(RegionalPromptBuilder)
        with open(module_path) as f:
            tree = ast.parse(f.read())
        forbidden = {"torch", "numpy", "PIL"}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden


class TestParseRegions:
    def test_valid_regions_pass_through(self):
        regions = parse_regions(json.dumps(CANONICAL_REGIONS))
        assert [(r.box, r.kind, r.content) for r in regions] == [
            (Box(0.04, 0.62, 0.30, 0.25), "object",
             Content("a red vintage car", "")),
            (Box(0.30, 0.03, 0.40, 0.14), "text",
             Content("glowing neon letters", "OPEN LATE")),
        ]

    def test_invalid_json_yields_no_regions(self):
        assert parse_regions("not json {") == []

    def test_non_list_json_yields_no_regions(self):
        assert parse_regions('{"x": 0.1}') == []
        assert parse_regions("42") == []

    def test_non_dict_entries_are_skipped(self):
        data = json.dumps([1, "box", CANONICAL_REGIONS[0], None])
        regions = parse_regions(data)
        assert len(regions) == 1
        assert regions[0].box == Box(0.04, 0.62, 0.30, 0.25)
        assert regions[0].content.desc == "a red vintage car"

    def test_position_clamped_to_unit_square(self):
        data = json.dumps([{"x": -0.5, "y": 0.5, "w": 2.0, "h": 0.2}])
        box = parse_regions(data)[0].box
        assert box.x == 0.0
        assert box.y == 0.5
        assert box.w == 1.0
        assert box.h == 0.2

    def test_size_clamped_to_remaining_extent(self):
        data = json.dumps([{"x": 0.8, "y": 0.7, "w": 0.5, "h": 0.6}])
        box = parse_regions(data)[0].box
        assert box.w == pytest.approx(0.2)
        assert box.h == pytest.approx(0.3)

    def test_degenerate_regions_are_skipped(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.005, "h": 0.5},
            {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.004},
            {"x": 0.1, "y": 0.1, "w": -0.5, "h": 0.5},
        ])
        assert parse_regions(data) == []

    def test_kind_defaults_to_object(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
            {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "kind": "banana"},
        ])
        regions = parse_regions(data)
        assert [r.kind for r in regions] == ["object", "object"]

    def test_missing_desc_and_text_default_to_empty(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}])
        content = parse_regions(data)[0].content
        assert content.desc == ""
        assert content.text == ""

    def test_non_numeric_coordinates_skip_the_entry(self):
        data = json.dumps([
            {"x": "wide", "y": 0.1, "w": 0.2, "h": 0.2},
            {"x": None, "y": 0.1, "w": 0.2, "h": 0.2},
        ])
        assert parse_regions(data) == []

    def test_unhashable_kind_defaults_to_object(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "kind": ["object"]},
            {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "kind": {}},
        ])
        regions = parse_regions(data)
        assert [r.kind for r in regions] == ["object", "object"]

    def test_non_finite_coordinates_skip_the_entry(self):
        data = '[{"x": 0.1, "y": 0.1, "w": NaN, "h": 0.5}, ' \
               '{"x": Infinity, "y": 0.1, "w": 0.2, "h": 0.2}, ' \
               '{"x": 0.1, "y": -Infinity, "w": 0.2, "h": 0.2}]'
        assert parse_regions(data) == []

    def test_scan_mask_and_group_are_preserved(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "kind": "object", "desc": "car", "text": "",
                            "mask": "iVBORw0K", "group": "car"}])
        source = parse_regions(data)[0].source
        assert source.mask.data == "iVBORw0K"
        assert source.label == "car"

    def test_hand_drawn_regions_carry_no_mask_or_group(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}])
        assert parse_regions(data)[0].source is None

    def test_blank_or_non_string_mask_and_group_are_dropped(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "mask": "", "group": 7},
                           {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "mask": 123, "group": ["car"]}])
        for parsed in parse_regions(data):
            assert parsed.source is None


class TestBox2d:
    def test_canonical_first_region(self):
        assert box_2d(Box(0.04, 0.62, 0.30, 0.25)) == [620, 40, 870, 340]

    def test_canonical_second_region(self):
        assert box_2d(Box(0.30, 0.03, 0.40, 0.14)) == [30, 300, 170, 700]

    def test_values_clamped_to_grid(self):
        assert box_2d(Box(-0.5, -0.5, 2.0, 2.0)) == [0, 0, 1000, 1000]


class TestPlacementPhrase:
    @pytest.mark.parametrize("x,y,expected", [
        (0.116, 0.116, "at the top-left"),
        (0.45, 0.116, "at the top-center"),
        (0.783, 0.116, "at the top-right"),
        (0.116, 0.45, "at the middle-left"),
        (0.45, 0.45, "at the center"),
        (0.783, 0.45, "at the middle-right"),
        (0.116, 0.783, "at the bottom-left"),
        (0.45, 0.783, "at the bottom-center"),
        (0.783, 0.783, "at the bottom-right"),
    ])
    def test_all_nine_grid_cells(self, x, y, expected):
        assert placement_phrase(x, y, 0.1, 0.1) == expected

    @pytest.mark.parametrize("x,y,w,h,expected", [
        (0.0, 0.05, 2 / 3, 0.1, "at the top-center"),
        (1 / 3, 0.05, 2 / 3, 0.1, "at the top-right"),
        (0.05, 0.0, 0.1, 2 / 3, "at the middle-left"),
        (0.05, 1 / 3, 0.1, 2 / 3, "at the bottom-left"),
    ])
    def test_thirds_boundaries_use_strict_less_than(self, x, y, w, h, expected):
        assert placement_phrase(x, y, w, h) == expected


class TestAspectRatioString:
    @pytest.mark.parametrize("width,height,expected", [
        (1024, 1024, "1:1"),
        (1920, 1080, "16:9"),
        (1024, 768, "4:3"),
        (1000, 500, "2:1"),
        (853, 480, "853:480"),
    ])
    def test_reduces_by_gcd(self, width, height, expected):
        assert aspect_ratio_string(width, height) == expected


class TestBuildPrompt:
    def test_canonical_full_prompt(self):
        prompt = build_prompt(
            "A rainy neon city street at night, wet asphalt reflecting neon "
            "signs, cinematic photo",
            1000, 1000,
            parse_regions(json.dumps(CANONICAL_REGIONS)),
        )
        assert prompt == CANONICAL_PROMPT

    def test_scene_only(self):
        prompt = build_prompt("A quiet forest", 1024, 1024, [])
        assert prompt == (
            "A quiet forest\n"
            "\n"
            "Compose for a 1024x1024 frame (aspect ratio 1:1)."
        )

    def test_empty_prompt_has_no_leading_blank_line(self):
        prompt = build_prompt("", 1920, 1080, [])
        assert prompt == "Compose for a 1920x1080 frame (aspect ratio 16:9)."

    def test_edit_mode_leads_with_preservation(self):
        # An image is connected: the prompt edits the photo, it does not compose
        # a fresh scene, so the model keeps the input instead of re-rendering it.
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a cat")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=True)
        assert prompt.startswith("Edit the provided image")
        assert "do not re-render" in prompt.lower()
        assert "Compose for a" not in prompt

    def test_edit_mode_forbids_flipping(self):
        # Heavy regeneration (model-applied moves) can mirror or rotate the whole
        # frame; the preamble locks orientation against that.
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a cat")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=True)
        assert "do not flip, mirror, rotate, or crop" in prompt.lower()

    def test_generate_mode_composes_and_omits_edit_preamble(self):
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a cat")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=False)
        assert "Compose for a 1000x1000 frame" in prompt
        assert "Edit the provided image" not in prompt

    def test_chroma_note_describes_the_key_color_when_set(self):
        # When cleared areas are chroma-filled (not inpainted), the prompt names
        # the key color so a downstream model treats it as empty to rebuild.
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, cutout=True)]
        prompt = build_prompt("a zoo", 1000, 1000, regions, chroma="#00B140")
        assert "chroma" in prompt.lower()
        assert "#00B140" in prompt

    def test_no_chroma_note_without_chroma(self):
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, cutout=True)]
        prompt = build_prompt("a zoo", 1000, 1000, regions)
        assert "chroma" not in prompt.lower()

    def test_chroma_note_fires_for_model_move(self):
        # A model move now clears its origin too, so a chroma fill there needs the
        # key-color note even with no node move or cut-out present.
        regions = [region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                          src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
                          edit_by="model")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, chroma="#00B140")
        assert "#00B140" in prompt

    def test_edit_mode_states_image_pixel_dimensions(self):
        # box_2d is normalized 0-1000, but stating the frame's actual pixel size
        # removes ambiguity about the grid the coordinates map onto. The compose
        # framing stays out — only the dimensions are stated, not a target frame.
        regions = [region(x=0.4, y=0.3, w=0.1, h=0.16, desc="a red ball")]
        prompt = build_prompt("a zoo", 1365, 768, regions, edit_mode=True)
        assert "1365x768 pixels" in prompt
        assert "Compose for a" not in prompt

    def test_edit_mode_addition_gets_blend_directive(self):
        # An added object dropped onto an existing photo needs relighting and a
        # contact shadow or it reads as a sticker, the same as a move.
        regions = [region(x=0.4, y=0.4, w=0.2, h=0.2, desc="a red hat")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=True)
        assert "photographed in place" in prompt
        assert "contact shadow" in prompt

    def test_compose_mode_addition_omits_blend_directive(self):
        # Compose renders the whole frame at once: there is nothing to blend into.
        regions = [region(x=0.4, y=0.4, w=0.2, h=0.2, desc="a red hat")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=False)
        assert "photographed in place" not in prompt

    def test_edit_mode_text_addition_omits_blend_directive(self):
        regions = [region(x=0.4, y=0.4, w=0.2, h=0.2, kind="text", text="SALE")]
        prompt = build_prompt("a zoo", 1000, 1000, regions, edit_mode=True)
        assert "photographed in place" not in prompt

    def test_object_region_without_desc_uses_an_element(self):
        regions = [region(x=0.4, y=0.4, w=0.2, h=0.2)]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "1. An element: at the center. box_2d = [400, 400, 600, 600]" in prompt

    def test_text_region_without_desc_omits_desc_clause(self):
        regions = [region(x=0.4, y=0.4, w=0.2, h=0.2, kind="text", text="SALE")]
        prompt = build_prompt("", 1000, 1000, regions)
        assert '1. The text "SALE": at the center. box_2d =' in prompt

    def test_layout_forbids_drawing_annotations(self):
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a cat")]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "never draw boxes" in prompt
        assert "bounding box" not in prompt

    def test_layout_declares_back_to_front_depth_order(self):
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a cat")]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "listed from back to front" in prompt
        assert "appears in front of an earlier one" in prompt

    def test_layout_anchors_each_element_to_its_box(self):
        # Inserted objects otherwise drift to a "more natural" lookalike spot —
        # a ball drawn over one hand gets rendered in the other. The footer pins
        # each element to its own box and forbids the relocation.
        regions = [region(x=0.1, y=0.1, w=0.2, h=0.2, desc="a red ball")]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "nowhere else" in prompt
        assert "similar-looking spot" in prompt

    def test_unicode_and_long_desc_round_trip(self):
        long_desc = "ornate baroque detail, " * 200
        regions = [
            region(x=0.1, y=0.1, w=0.3, h=0.3, kind="text",
                   desc="霓虹灯 sign with sparkles", text="营业中 OPEN"),
            region(x=0.5, y=0.5, w=0.3, h=0.3, desc=long_desc),
        ]
        prompt = build_prompt("scene", 1024, 1024, regions)
        assert 'The text "营业中 OPEN", 霓虹灯 sign with sparkles:' in prompt
        assert long_desc in prompt


class TestRegionsToPixelBboxes:
    def test_canonical_pixel_boxes(self):
        regions = parse_regions(json.dumps(CANONICAL_REGIONS))
        assert regions_to_pixel_bboxes(regions, 1000, 1000) == CANONICAL_BBOXES

    def test_no_regions_yields_empty_list(self):
        assert regions_to_pixel_bboxes([], 1024, 1024) == []

    def test_boxes_scale_with_frame_size(self):
        regions = [region(x=0.5, y=0.25, w=0.25, h=0.5)]
        assert regions_to_pixel_bboxes(regions, 1920, 1080) == [[
            {"x": 960, "y": 270, "width": 480, "height": 540},
        ]]


class TestMaskPixelBox:
    def test_canonical_region_pixel_bounds(self):
        assert mask_pixel_box(Box(0.04, 0.62, 0.30, 0.25), 1000, 1000) == (40, 620, 340, 870)

    def test_bounds_scale_with_frame_size(self):
        assert mask_pixel_box(Box(0.5, 0.25, 0.25, 0.5), 1920, 1080) == (960, 270, 1440, 810)

    def test_bounds_clamped_to_frame(self):
        assert mask_pixel_box(Box(0.95, 0.95, 0.2, 0.2), 100, 100) == (95, 95, 100, 100)

    def test_sub_pixel_region_still_encloses_a_pixel(self):
        x0, y0, x1, y1 = mask_pixel_box(Box(0.0, 0.0, 0.006, 0.006), 64, 64)
        assert x1 > x0
        assert y1 > y0


class TestRegionHasStoredMask:
    def test_region_with_stored_mask_is_true(self):
        assert region_has_stored_mask(region(mask="iVBORw0K")) is True

    def test_region_without_source_is_not_stored(self):
        assert region_has_stored_mask(region()) is False

    def test_scanned_region_without_mask_is_not_stored(self):
        # A scanned-in-place region carries a Source but no segmentation mask.
        assert region_has_stored_mask(
            region(src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})) is False


def _png_base64(array):
    import base64
    import io

    import numpy as np
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(np.asarray(array, dtype="uint8"), mode="L").save(
        buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class TestCutouts:
    """A cut-out region is removed from prompt/bboxes/masks and erased to
    transparent in the image output (Shift+Delete in the editor)."""

    def _cut(self, **over):
        params = dict(x=0.5, y=0.5, w=0.3, h=0.3, desc="a dog", cutout=True)
        params.update(over)
        return region(**params)

    def test_parse_preserves_cutout(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3,
                            "kind": "object", "cutout": True}])
        assert parse_regions(data)[0].op == "cutout"

    def test_parse_omits_cutout_when_absent_or_false(self):
        assert parse_regions(
            json.dumps([{"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3}]))[0].op == "normal"
        assert parse_regions(
            json.dumps([{"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3,
                         "cutout": False}]))[0].op == "normal"

    def test_cutout_excluded_from_prompt(self):
        keep = region(x=0.1, y=0.1, w=0.3, h=0.3, desc="a cat")
        out = build_prompt("scene", 1000, 1000, [keep, self._cut()])
        assert "a cat" in out and "a dog" not in out

    def test_cutout_adds_removal_directive_without_naming_it(self):
        keep = region(x=0.1, y=0.1, w=0.3, h=0.3, desc="a cat")
        out = build_prompt("scene", 1000, 1000, [keep, self._cut()])
        assert REMOVAL_HEADER in out
        # A box_2d for the removed area follows the header...
        assert "box_2d" in out.split(REMOVAL_HEADER, 1)[1]
        # ...but the removed object is never named (naming it invites re-adding).
        assert "a dog" not in out

    def test_cutout_excluded_from_bboxes(self):
        keep = region(x=0.1, y=0.1, w=0.3, h=0.3, desc="a")
        boxes = regions_to_pixel_bboxes([keep, self._cut()], 1000, 1000)
        assert len(boxes[0]) == 1

    def test_cutout_excluded_from_masks(self):
        pytest.importorskip("torch")
        keep = region(x=0.1, y=0.1, w=0.3, h=0.3)
        masks = build_region_masks([keep, self._cut()], 50, 50)
        assert masks.shape[0] == 1

    def test_cutout_mask_spares_kept_region(self):
        # A kept region overlapping a cut-out is never erased — the cut-out clears
        # only the background around it.
        cut = region(x=0.1, y=0.1, w=0.4, h=0.4, cutout=True)
        kept = region(x=0.3, y=0.3, w=0.4, h=0.4, desc="a man")
        mask = _cutout_mask([cut, kept], 100, 100)
        assert mask[15, 15] == 255   # cut-out only -> filled
        assert mask[35, 35] == 0     # overlap with the kept region -> spared

    def test_cutout_mask_spares_kept_region_regardless_of_order(self):
        # Cut-outs sit at the lowest depth, so a kept region is spared even when
        # it is listed before the cut-out in the regions array.
        kept = region(x=0.3, y=0.3, w=0.4, h=0.4, desc="a man")
        cut = region(x=0.1, y=0.1, w=0.4, h=0.4, cutout=True)
        mask = _cutout_mask([kept, cut], 100, 100)
        assert mask[35, 35] == 0

    def test_removal_directive_keeps_overlapping_kept_element(self):
        out = build_prompt("scene", 1000, 1000, [self._cut()])
        assert "clear only around it" in out

    def test_all_cutouts_yield_one_zero_mask(self):
        pytest.importorskip("torch")
        masks = build_region_masks([self._cut()], 40, 40)
        assert masks.shape == (1, 40, 40)
        assert float(masks.sum()) == 0.0

    def test_hex_to_rgb01_parses_and_falls_back(self):
        from utils.region_image_ops import _hex_to_rgb01
        assert _hex_to_rgb01("#00FF00") == (0.0, 1.0, 0.0)
        assert _hex_to_rgb01("nope") == (0.0, 0.690, 0.251)  # chroma-green default

    def test_apply_cutouts_chroma_fills_flat_color(self):
        torch = pytest.importorskip("torch")
        img = torch.zeros((1, 20, 20, 3))
        cut = region(x=0.25, y=0.25, w=0.5, h=0.5, cutout=True)
        out = apply_cutouts(img, [cut], chroma="#00FF00")
        px = out[0, 10, 10, :]  # center of the cut-out box -> pure green
        assert float(px[0]) == 0.0 and float(px[1]) == 1.0 and float(px[2]) == 0.0

    def test_apply_cutouts_no_cutouts_returns_input_unchanged(self):
        torch = pytest.importorskip("torch")
        img = torch.rand((1, 8, 8, 3))
        keep = region(x=0.0, y=0.0, w=0.5, h=0.5)
        out = apply_cutouts(img, [keep])
        assert out is img

    def test_cutout_mask_marks_the_box(self):
        np = pytest.importorskip("numpy")
        mask = _cutout_mask([region(x=0.0, y=0.0, w=0.5, h=0.5, cutout=True)], 20, 20)
        assert mask.shape == (20, 20) and mask.dtype == np.uint8
        assert mask[2, 2] == 255    # inside the cut box -> fill
        assert mask[18, 18] == 0    # outside -> keep

    def test_cutout_mask_follows_silhouette(self):
        np = pytest.importorskip("numpy")
        glyph = np.zeros((10, 10), dtype="uint8")
        glyph[:, :5] = 255          # left half opaque
        cut = region(x=0.0, y=0.0, w=1.0, h=1.0, cutout=True, mask=_png_base64(glyph))
        mask = _cutout_mask([cut], 20, 20)
        assert mask[10, 3] == 255    # masked (left) -> fill
        assert mask[10, 17] == 0     # unmasked (right) -> keep

    def test_cutout_mask_empty_without_cutouts(self):
        pytest.importorskip("numpy")
        keep = region(x=0.0, y=0.0, w=0.5, h=0.5)
        assert _cutout_mask([keep], 16, 16).max() == 0

    def test_apply_cutouts_fills_masked_area(self):
        pytest.importorskip("numpy")
        torch = pytest.importorskip("torch")
        pytest.importorskip("cv2")
        # A red field with a blue patch in the cut box; inpaint fills the patch
        # from the surrounding red, so it goes red and the output stays RGB.
        img = torch.zeros((1, 20, 20, 3))
        img[..., 0] = 1.0                       # all red
        img[0, 5:15, 5:15, 0] = 0.0             # blue patch where the cut box is
        img[0, 5:15, 5:15, 2] = 1.0
        cut = region(x=0.25, y=0.25, w=0.5, h=0.5, cutout=True)
        out = apply_cutouts(img, [cut])
        assert out.shape == (1, 20, 20, 3)      # stays RGB, no alpha
        assert float(out[0, 10, 10, 0]) > float(out[0, 10, 10, 2])  # filled red
        assert float(out[0, 0, 0, 0]) == 1.0    # outside untouched


class TestBuildRegionMasks:
    def test_empty_regions_yield_one_zero_mask(self):
        torch = pytest.importorskip("torch")
        masks = build_region_masks([], 1024, 768)
        assert masks.shape == (1, 768, 1024)
        assert float(masks.sum()) == 0.0

    def test_maskless_region_fills_its_rectangle(self):
        pytest.importorskip("torch")
        masks = build_region_masks([region(x=0.25, y=0.25, w=0.5, h=0.5)], 100, 100)
        assert masks.shape == (1, 100, 100)
        assert float(masks[0, 50, 50]) == 1.0
        assert float(masks[0, 0, 0]) == 0.0
        assert float(masks[0, 90, 90]) == 0.0

    def test_stored_mask_is_decoded_box_relative(self):
        import numpy as np
        pytest.importorskip("torch")
        glyph = np.zeros((10, 10), dtype="uint8")
        glyph[:, :5] = 255  # left half opaque, right half transparent
        masks = build_region_masks(
            [region(x=0.0, y=0.0, w=1.0, h=1.0, mask=_png_base64(glyph))], 20, 20)
        assert float(masks[0, 10, 2]) == 1.0
        assert float(masks[0, 10, 18]) == 0.0

    def test_malformed_mask_falls_back_to_rectangle(self):
        pytest.importorskip("torch")
        masks = build_region_masks(
            [region(x=0.25, y=0.25, w=0.5, h=0.5, mask="@@@not-a-png@@@")], 100, 100)
        assert float(masks[0, 50, 50]) == 1.0
        assert float(masks[0, 0, 0]) == 0.0

    def test_one_mask_per_region_in_order(self):
        pytest.importorskip("torch")
        regions = [
            region(x=0.0, y=0.0, w=0.3, h=0.3),
            region(x=0.5, y=0.5, w=0.4, h=0.4),
        ]
        masks = build_region_masks(regions, 100, 100)
        assert masks.shape == (2, 100, 100)
        assert float(masks[0, 10, 10]) == 1.0
        assert float(masks[0, 70, 70]) == 0.0
        assert float(masks[1, 70, 70]) == 1.0
        assert float(masks[1, 10, 10]) == 0.0


class TestExecute:
    def test_canonical_node_output(self):
        out = RegionalPromptBuilder.execute(
            width=1000,
            height=1000,
            prompt="A rainy neon city street at night, wet asphalt reflecting "
                   "neon signs, cinematic photo",
            regions_data=json.dumps(CANONICAL_REGIONS),
        )
        assert out.args[:6] == (CANONICAL_PROMPT, CANONICAL_BBOXES, 1000, 1000, None, [])
        assert out.args[6].shape == (2, 1000, 1000)

    def test_scene_only_outputs_empty_bboxes(self):
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="A quiet forest", regions_data="[]",
        )
        prompt, bboxes, width, height, image, image_refs, masks = out.args
        assert "A quiet forest" in prompt
        assert bboxes == []
        assert (width, height) == (1024, 1024)
        assert image is None
        assert image_refs == []
        # No regions: one all-zero placeholder mask keeps the batch ComfyUI-friendly.
        assert masks.shape == (1, 1024, 1024)
        assert float(masks.sum()) == 0.0

    def test_regions_only_is_valid(self):
        regions = [{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "a cat", "text": ""}]
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="", regions_data=json.dumps(regions),
        )
        assert "a cat" in out.args[0]

    def test_all_empty_raises_value_error(self):
        with pytest.raises(ValueError,
                           match="Describe the scene or add at least one region"):
            RegionalPromptBuilder.execute(
                width=1024, height=1024,
                prompt="  \n", regions_data="[]",
            )

    def test_invalid_regions_json_with_scene_still_builds(self):
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="A quiet forest", regions_data="not json",
        )
        assert out.args[1] == []
        assert "Layout:" not in out.args[0]

    def test_reference_image_passes_through(self):
        torch = pytest.importorskip("torch")
        sentinel = torch.zeros((1, 8, 8, 3))
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="A quiet forest", regions_data="[]",
            image=sentinel,
        )
        assert out.args[4] is sentinel

    def test_missing_reference_image_passes_none(self):
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="A quiet forest", regions_data="[]",
        )
        assert out.args[4] is None

    def test_masks_match_connected_image_resolution(self):
        # The masks must overlay the passed-through image, so when an image is
        # connected they follow its H x W, not the width/height widgets.
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 768, 512, 3))  # differs from the widgets
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            image=image,
        )
        masks = out.args[6]
        assert masks.shape == (2, 768, 512)

    def test_bboxes_and_dims_follow_connected_image_resolution(self):
        # bboxes and the width/height outputs must match the connected image too,
        # not the widgets — otherwise a 2K (or any non-widget-sized) image yields
        # bboxes/dims that disagree with the masks and the passed-through image.
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 768, 512, 3))  # H x W differs from the widgets
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            image=image,
        )
        bboxes, width, height = out.args[1], out.args[2], out.args[3]
        assert (width, height) == (512, 768)              # image size, not widgets
        assert bboxes[0][0]["width"] == round(0.30 * 512)  # scaled to image width

    def test_dims_fall_back_to_widgets_without_image(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=800, prompt="a forest",
            regions_data=json.dumps(CANONICAL_REGIONS),
        )
        assert (out.args[2], out.args[3]) == (1000, 800)

    def test_desc_input_overrides_region_description(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            desc_1="a battered taxi cab",
        )
        assert "a battered taxi cab: at the bottom-left" in out.args[0]
        assert "a red vintage car" not in out.args[0]

    def test_desc_override_applies_to_text_region_clause(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            desc_2="flickering tube letters",
        )
        assert 'The text "OPEN LATE", flickering tube letters:' in out.args[0]

    def test_blank_desc_override_is_ignored(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            desc_1="   \n",
        )
        assert "a red vintage car: at the bottom-left" in out.args[0]

    def test_desc_override_beyond_region_count_is_ignored(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            desc_5="nothing to attach to",
        )
        assert "nothing to attach to" not in out.args[0]


class TestImageRefs:
    def test_refs_collect_in_region_order(self):
        first, second = object(), object()
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_1=first, ref_2=second,
        )
        assert out.args[5] == [first, second]

    def test_region_line_references_its_image_number(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_1=object(), ref_2=object(),
        )
        prompt = out.args[0]
        assert ("a red vintage car, taken from image 2 (reproduce that exact "
                "item): at the bottom-left") in prompt
        assert ('The text "OPEN LATE", glowing neon letters, styled as shown '
                "in image 3: at the top-center") in prompt

    def test_ref_without_desc_makes_the_image_the_subject(self):
        regions = [{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "", "text": ""}]
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(regions),
            ref_1=object(),
        )
        assert ("1. The item shown in image 2, reproduced exactly: "
                "at the center") in out.args[0]

    def test_unwired_regions_skip_numbering(self):
        sentinel = object()
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_2=sentinel,
        )
        prompt, image_refs = out.args[0], out.args[5]
        assert image_refs == [sentinel]
        assert "a red vintage car: at the bottom-left" in prompt
        assert "styled as shown in image 2: at the top-center" in prompt

    def test_header_explains_numbering_only_when_refs_exist(self):
        with_refs = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_1=object(),
        ).args[0]
        without_refs = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
        ).args[0]
        assert "image 1 is the image being edited" in with_refs
        assert "Reproduce each referenced item faithfully" in with_refs
        assert "Keep everything else in image 1 unchanged" in with_refs
        assert "image 1 is the image being edited" not in without_refs
        assert "Reproduce each referenced item" not in without_refs
        assert "Keep everything else" not in without_refs

    def test_ref_beyond_region_count_is_ignored(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_5=object(),
        )
        assert out.args[5] == []
        assert "taken from image" not in out.args[0]
        assert "styled as shown in" not in out.args[0]


WIRED_REGION = {"x": 0.7, "y": 0.7, "w": 0.2, "h": 0.2,
                "kind": "object", "desc": "a barking dog", "text": ""}


class TestWiredRegions:
    def test_wired_regions_append_after_canvas(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            regions=json.dumps([WIRED_REGION]),
        )
        prompt, bboxes = out.args[0], out.args[1]
        assert "1. a red vintage car" in prompt
        assert '2. The text "OPEN LATE"' in prompt
        assert "3. a barking dog" in prompt
        assert len(bboxes[0]) == 3

    def test_desc_override_binds_canvas_only(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            regions=json.dumps([WIRED_REGION]),
            desc_3="should not apply",
        )
        prompt = out.args[0]
        assert "3. a barking dog" in prompt
        assert "should not apply" not in prompt

    def test_ref_override_binds_canvas_only(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            regions=json.dumps([WIRED_REGION]),
            ref_3=object(),
        )
        prompt, image_refs = out.args[0], out.args[5]
        assert image_refs == []
        assert "3. a barking dog: at the bottom-right" in prompt
        assert "taken from image" not in prompt

    def test_wired_regions_go_through_parse_regions(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="A scene",
            regions_data="[]",
            regions=json.dumps([
                {"x": -0.5, "y": 0.5, "w": 2.0, "h": 0.2,
                 "kind": "object", "desc": "clamped", "text": ""},
                {"x": 0.1, "y": 0.1, "w": 0.004, "h": 0.5,
                 "kind": "object", "desc": "degenerate", "text": ""},
            ]),
        )
        bboxes = out.args[1]
        assert len(bboxes[0]) == 1
        assert bboxes[0][0] == {"x": 0, "y": 500, "width": 1000, "height": 200}
        assert "degenerate" not in out.args[0]

    def test_malformed_wired_regions_are_ignored(self):
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024, prompt="A scene",
            regions_data="[]",
            regions="not json {",
        )
        assert out.args[1] == []
        assert "Layout:" not in out.args[0]

    def test_wired_regions_satisfy_all_empty_guard(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data="[]",
            regions=json.dumps([WIRED_REGION]),
        )
        assert "a barking dog" in out.args[0]
        assert len(out.args[1][0]) == 1


def _v2_entry(rid, *, x=0.1, y=0.1, w=0.2, h=0.2, kind="object",
              desc="", text="", bind_slot=None):
    """A single v2 region entry the contract parses; bind_slot wires its slot."""
    return {
        "id": rid, "kind": kind,
        "box": {"x": x, "y": y, "w": w, "h": h},
        "content": {"desc": desc, "text": text},
        "op": "normal",
        "bind": {"slot": bind_slot} if bind_slot is not None else None,
        "ui": {"parent": None, "hidden": False, "collapsed": False},
    }


def _v2_document(entries):
    """A v2 regions document whose order[] is the entries' depth order."""
    return json.dumps({
        "version": 2,
        "order": [entry["id"] for entry in entries],
        "regions": entries,
    })


class TestBindSlotBinding:
    """desc_N/ref_N bind by a region's stable bind_slot, so reordering the
    canvas does not remap wires. Regions without a bind_slot fall back to their
    depth position, preserving the legacy positional behavior."""

    def test_desc_follows_bind_slot_not_position(self):
        # Depth order is [alpha, beta] but their bind slots are reversed: alpha
        # binds slot 2, beta binds slot 1.
        doc = _v2_document([
            _v2_entry("a", x=0.1, desc="alpha", bind_slot=2),
            _v2_entry("b", x=0.5, desc="beta", bind_slot=1),
        ])
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=doc, desc_1="one", desc_2="two",
        )
        prompt = out.args[0]
        # alpha is element 1 (depth 0) but bound to slot 2 -> desc_2 = "two";
        # beta is element 2 (depth 1) but bound to slot 1 -> desc_1 = "one".
        assert "1. two:" in prompt
        assert "2. one:" in prompt
        assert "alpha" not in prompt
        assert "beta" not in prompt

    def test_desc_falls_back_to_position_without_bind_slot(self):
        doc = _v2_document([
            _v2_entry("a", x=0.1, desc="alpha"),
            _v2_entry("b", x=0.5, desc="beta"),
        ])
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=doc, desc_1="one", desc_2="two",
        )
        prompt = out.args[0]
        # No bind_slot: desc_1 -> depth 0, desc_2 -> depth 1 (positional).
        assert "1. one:" in prompt
        assert "2. two:" in prompt

    def test_ref_follows_bind_slot_keeping_region_order(self):
        first, second = object(), object()
        doc = _v2_document([
            _v2_entry("a", x=0.1, desc="alpha", bind_slot=2),
            _v2_entry("b", x=0.5, desc="beta", bind_slot=1),
        ])
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=doc, ref_1=first, ref_2=second,
        )
        prompt, image_refs = out.args[0], out.args[5]
        # image_refs stays in region (depth) order: alpha's ref_2 then beta's
        # ref_1; the cited image numbers follow that list (offset by the base).
        assert image_refs == [second, first]
        assert "alpha, taken from image 2" in prompt
        assert "beta, taken from image 3" in prompt


class TestMovedRegions:
    """Scanned regions carry their origin box; moving one switches the prompt
    line to relocation language and raises the reposition header."""

    @staticmethod
    def _moved_region():
        return region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                      src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})

    def test_parse_preserves_valid_src(self):
        regions = parse_regions(json.dumps([{
            "x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2, "kind": "object",
            "desc": "a hippo", "text": "",
            "src": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}}]))
        assert regions[0].source.box == Box(0.1, 0.1, 0.2, 0.2)

    def test_parse_clamps_src(self):
        regions = parse_regions(json.dumps([{
            "x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2, "kind": "object",
            "desc": "a hippo", "text": "",
            "src": {"x": -0.5, "y": 0.0, "w": 2.0, "h": 0.5}}]))
        assert regions[0].source.box == Box(0.0, 0.0, 1.0, 0.5)

    def test_parse_drops_malformed_src_keeps_region(self):
        for bad in ("nope", {"x": 0.1}, {"x": "a", "y": 0, "w": 1, "h": 1},
                    {"x": 0.1, "y": 0.1, "w": 0.001, "h": 0.001}):
            regions = parse_regions(json.dumps([{
                "x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2, "kind": "object",
                "desc": "a hippo", "text": "", "src": bad}]))
            assert len(regions) == 1
            assert regions[0].source is None

    def test_region_moved_true_when_geometry_differs(self):
        assert region_moved(self._moved_region())

    def test_region_moved_false_in_place(self):
        in_place = region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                          src={"x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2})
        assert not region_moved(in_place)

    def test_region_moved_false_without_src(self):
        assert not region_moved(region(x=0.1, y=0.1, w=0.2, h=0.2))

    @staticmethod
    def _anchor_region(desc="a sleeping otter"):
        # Scanned and unmoved: the object already sits where its box says.
        return region(x=0.1, y=0.7, w=0.2, h=0.2, desc=desc,
                      src={"x": 0.1, "y": 0.7, "w": 0.2, "h": 0.2})

    def test_move_block_asks_for_duplicate_removal(self):
        # The move is already composited into the image; the model only cleans up.
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "Make these edits" in prompt
        assert "a hippo: remove the duplicate at box_2d = [100, 100, 300, 300]" in prompt
        assert "Keep the one" in prompt
        assert "blending it into the scene" in prompt
        assert "box_2d = [600, 600, 800, 800]" in prompt
        assert "background" in prompt.lower()

    def test_move_asks_for_relight_and_contact_shadow(self):
        # A composited paste looks like a sticker until the model relights it and
        # casts a shadow; the directive makes that an explicit edit, not optional.
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "relight it" in prompt
        assert "contact shadow" in prompt
        assert "not pasted" in prompt
        assert "keep its shape, pose, colors, and identifying details unchanged" in prompt

    def test_move_blend_names_photographic_cues(self):
        # "Looks fake/pasted" is the failure; the directive must name the cues a
        # composite misses — depth of field, grain, and ambient color spill — so
        # the model integrates the patch instead of leaving a sticker.
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "depth of field" in prompt
        assert "film grain" in prompt
        assert "photographed in place" in prompt

    def test_move_destination_keeps_verbal_placement(self):
        # The hybrid doctrine: words drive the model, coordinates pin it.
        # No size phrasing — the composited paste already fixes the size.
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "at the bottom-right" in prompt
        assert "box_2d = [600, 600, 800, 800]" in prompt

    def test_anchor_sentence_forbids_removal(self):
        prompt = build_prompt("", 1000, 1000,
                              [self._anchor_region(), self._moved_region()])
        assert "do not remove" in prompt.lower()

    def test_moves_lead_the_layout_section(self):
        hand_drawn = region(x=0.4, y=0.4, w=0.2, h=0.2, desc="a brass lantern")
        prompt = build_prompt("", 1000, 1000,
                              [hand_drawn, self._moved_region()])
        assert prompt.index("Make these edits") < prompt.index("Layout:")
        assert "a brass lantern" in prompt

    def test_anchor_regions_emit_no_element_line(self):
        # An unmoved scanned region describes existing pixels - re-stating it
        # invites the model to re-render instead of edit.
        prompt = build_prompt("", 1000, 1000,
                              [self._anchor_region(), self._moved_region()])
        assert "a sleeping otter" not in prompt
        assert "stays exactly where it is" in prompt

    def test_anchors_only_yields_no_layout_section(self):
        prompt = build_prompt("a zoo scene", 1000, 1000,
                              [self._anchor_region()])
        assert "Layout:" not in prompt
        assert "Make these edits" not in prompt
        assert "a sleeping otter" not in prompt
        assert "a zoo scene" in prompt

    def test_no_anchor_sentence_without_anchors(self):
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "stays exactly where it is" not in prompt

    def test_ref_image_wins_over_move_phrasing(self):
        moved = self._moved_region()
        moved.ref_image = 2
        prompt = build_prompt("", 1000, 1000, [moved])
        assert "taken from image 2" in prompt
        assert "Make these edits" not in prompt


class TestOcclusionPrompt:
    """When a node-composited move lands behind a scanned region above it, the
    move's line names the occluder and tells the model to keep the covered part
    hidden — the pixels are already occluded, but the blend directive ('keep its
    shape unchanged') would otherwise invite the model to redraw the whole object."""

    @staticmethod
    def _lemur():
        # Moves from the top-left into the man's area below.
        return region(x=0.5, y=0.5, w=0.25, h=0.25, desc="a lemur",
                      src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25})

    @staticmethod
    def _man(mask=True, moved=False, edit_by="node"):
        import numpy as np
        solid = _png_base64(np.full((10, 10), 255, dtype="uint8")) if mask else None
        # A moved occluder comes from elsewhere; a static one sits at its box.
        src = ({"x": 0.2, "y": 0.15, "w": 0.2, "h": 0.3} if moved
               else {"x": 0.55, "y": 0.5, "w": 0.2, "h": 0.3})
        return region(x=0.55, y=0.5, w=0.2, h=0.3, desc="the man",
                      src=src, mask=solid, edit_by=edit_by)

    def test_occluded_move_frames_the_occluder_in_front(self):
        pytest.importorskip("numpy")
        prompt = build_prompt("", 1000, 1000, [self._lemur(), self._man()])
        assert "With the man in front of it" in prompt
        assert "a lemur is partly hidden" in prompt

    def test_occluded_move_keeps_the_covered_part_hidden(self):
        pytest.importorskip("numpy")
        prompt = build_prompt("", 1000, 1000, [self._lemur(), self._man()])
        assert "not covered by the man" in prompt
        assert "do not redraw the covered part" in prompt

    def test_node_moved_occluder_still_occludes(self):
        # The occluder can itself be a node move — its paste lands on top in
        # depth order — so it must still trigger the clause.
        pytest.importorskip("numpy")
        prompt = build_prompt("", 1000, 1000, [self._lemur(), self._man(moved=True)])
        assert "With the man in front of it" in prompt

    def test_model_moved_occluder_is_not_an_occluder(self):
        # A model-move occluder is never composited, so it cannot occlude.
        pytest.importorskip("numpy")
        man = self._man(moved=True, edit_by="model")
        prompt = build_prompt("", 1000, 1000, [self._lemur(), man])
        assert "partly hidden" not in prompt

    def test_occluder_below_the_move_adds_no_clause(self):
        pytest.importorskip("numpy")
        # Man first (behind), lemur second (in front): the lemur is on top.
        prompt = build_prompt("", 1000, 1000, [self._man(), self._lemur()])
        assert "partly hidden" not in prompt

    def test_maskless_region_adds_no_clause(self):
        # A hand-drawn box above the move is a layout guide, not an occluder.
        prompt = build_prompt("", 1000, 1000, [self._lemur(), self._man(mask=False)])
        assert "partly hidden" not in prompt


class TestAdditionAnchors:
    """Hand-drawn additions get the same landmark anchoring as model moves, so a
    new element is placed relative to objects already in the scene rather than by
    bare coordinates the edit model ignores."""

    @staticmethod
    def _man():
        return region(x=0.6, y=0.4, w=0.2, h=0.4, desc="the man",
                      src={"x": 0.6, "y": 0.4, "w": 0.2, "h": 0.4})

    def test_object_addition_anchors_to_landmark(self):
        hat = region(x=0.45, y=0.45, w=0.08, h=0.1, desc="a red hat")
        prompt = build_prompt("", 1000, 1000, [self._man(), hat])
        assert "to the left of the man" in prompt

    def test_text_addition_gets_no_anchor(self):
        sign = region(x=0.3, y=0.05, w=0.4, h=0.1, kind="text",
                      text="OPEN", desc="neon letters")
        prompt = build_prompt("", 1000, 1000, [self._man(), sign])
        assert "Place it" not in prompt

    def test_inserted_region_gets_blend_line_not_placement(self):
        # A composited ref (region.inserted) is already at its box, so it gets a
        # blend directive — never a "Place it" anchor or a Layout placement line.
        hat = region(x=0.45, y=0.45, w=0.1, h=0.13, desc="a wizard hat")
        hat.inserted = True
        prompt = build_prompt("", 1000, 1000, [hat])
        assert "a wizard hat: at the center" in prompt
        assert "at at" not in prompt          # placement_phrase already says "at the …"
        assert "blending it into the scene" in prompt
        assert "Place it" not in prompt
        assert "Layout:" not in prompt

    def test_addition_does_not_anchor_to_another_addition(self):
        # A second hand-drawn addition is not yet placed (no source), so it is not
        # a valid landmark — only grounded (scanned/node-moved) objects are.
        hat = region(x=0.45, y=0.45, w=0.08, h=0.1, desc="a red hat")
        scarf = region(x=0.5, y=0.5, w=0.08, h=0.1, desc="a blue scarf")
        prompt = build_prompt("", 1000, 1000, [hat, scarf])
        assert "Place it" not in prompt


class TestRemovalWording:
    """A move always tells the edit model to remove the leftover at the origin and
    a cut-out always asks for removal. OpenCV deterministically fills both before
    the image is handed off, but an edit model regenerates the scene, so relying
    on the fill alone lets it re-add what was there; the prompt must still ask.
    The removed object is never named (naming it invites re-adding)."""

    @staticmethod
    def _moved():
        return region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                      src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})

    @staticmethod
    def _cut():
        return region(x=0.5, y=0.5, w=0.3, h=0.3, desc="a dog", cutout=True)

    def test_move_asks_origin_removal(self):
        prompt = build_prompt("", 1000, 1000, [self._moved()])
        assert REPOSITION_HEADER in prompt
        assert "remove the duplicate at box_2d = [100, 100, 300, 300]" in prompt

    def test_move_origin_forbids_new_objects(self):
        # The cleared origin must be rebuilt as plain background, not refilled
        # with a new subject — over a large emptied area the edit model otherwise
        # hallucinates one (a giant spider in the man's vacated center).
        prompt = build_prompt("", 1000, 1000, [self._moved()])
        assert "do not place any" in prompt.lower()

    def test_cutout_asks_removal(self):
        prompt = build_prompt("scene", 1000, 1000, [self._cut()])
        assert REMOVAL_HEADER in prompt
        assert "a dog" not in prompt


class TestCompositeMovedRegions:
    """Moved regions paste their source pixels at the destination so the
    edit model receives the move as fact and only cleans up."""

    @staticmethod
    def _image(torch):
        # 20x20 black frame with a solid white 5x5 patch at the top-left.
        image = torch.zeros((1, 20, 20, 3))
        image[:, 0:5, 0:5, :] = 1.0
        return image

    @staticmethod
    def _moved(**over):
        params = dict(x=0.5, y=0.5, w=0.25, h=0.25, desc="patch",
                      src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25})
        params.update(over)
        return region(**params)

    def test_identity_without_moves(self):
        torch = pytest.importorskip("torch")
        image = self._image(torch)
        anchor = self._moved(x=0.0, y=0.0)
        out = composite_moved_regions(image, [anchor])
        assert out is image

    def test_none_image_passes_through(self):
        out = composite_moved_regions(None, [self._moved()])
        assert out is None

    def test_maskless_move_pastes_the_source_rectangle(self):
        torch = pytest.importorskip("torch")
        out = composite_moved_regions(self._image(torch), [self._moved()])
        assert float(out[0, 12, 12, 0]) == 1.0   # pasted at destination
        assert float(out[0, 2, 2, 0]) == 1.0     # source pixels untouched
        assert float(out[0, 12, 2, 0]) == 0.0    # elsewhere unchanged

    def test_move_scales_the_patch_to_the_destination(self):
        torch = pytest.importorskip("torch")
        big = self._moved(w=0.5, h=0.5, x=0.5, y=0.5)
        out = composite_moved_regions(self._image(torch), [big])
        assert float(out[0, 18, 18, 0]) == 1.0   # 5x5 grew to fill 10x10

    def test_mask_gates_the_paste(self):
        torch = pytest.importorskip("torch")
        Image = pytest.importorskip("PIL.Image")
        import base64
        from io import BytesIO
        # Left half of the mask is opaque, right half empty.
        mask = Image.new("L", (5, 5), 0)
        for yy in range(5):
            for xx in range(2):
                mask.putpixel((xx, yy), 255)
        buf = BytesIO()
        mask.save(buf, format="PNG")
        moved = self._moved(mask=base64.b64encode(buf.getvalue()).decode())
        out = composite_moved_regions(self._image(torch), [moved])
        assert float(out[0, 12, 10, 0]) == 1.0   # inside the opaque half
        assert float(out[0, 12, 14, 0]) == 0.0   # masked-out half untouched

    def test_input_tensor_is_not_mutated(self):
        torch = pytest.importorskip("torch")
        image = self._image(torch)
        composite_moved_regions(image, [self._moved()])
        assert float(image[0, 12, 12, 0]) == 0.0

    def test_blend_preserves_dtype_and_shape(self):
        # The blend tensors are built on the destination patch's device and
        # dtype, so the moved patch lands without changing the output's dtype
        # or shape.
        torch = pytest.importorskip("torch")
        image = self._image(torch)
        out = composite_moved_regions(image, [self._moved()])
        assert out.dtype == image.dtype
        assert out.shape == image.shape
        assert float(out[0, 12, 12, 0]) == 1.0   # patch landed at destination


class TestCropRegionSubject:
    """A model move's origin is cleared, so a crop of the original subject is
    attached as a reference image the edit model can reproduce."""

    def test_none_image_returns_none(self):
        assert crop_region_subject(None, region()) is None

    def test_crops_the_source_box(self):
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 20, 20, 3))
        image[:, 0:5, 0:5, :] = 1.0
        mv = region(x=0.5, y=0.5, w=0.25, h=0.25, desc="x",
                    src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25}, edit_by="model")
        crop = crop_region_subject(image, mv)
        assert crop.shape == (1, 5, 5, 3)
        assert float(crop[0, 2, 2, 0]) == 1.0    # source pixels carried over

    def test_mask_isolates_subject_on_white(self):
        torch = pytest.importorskip("torch")
        Image = pytest.importorskip("PIL.Image")
        import base64
        from io import BytesIO
        glyph = Image.new("L", (5, 5), 0)
        for yy in range(5):
            for xx in range(2):
                glyph.putpixel((xx, yy), 255)   # left two columns opaque
        buf = BytesIO()
        glyph.save(buf, format="PNG")
        image = torch.full((1, 20, 20, 3), 0.5)
        mv = region(x=0.5, y=0.5, w=0.25, h=0.25, desc="x",
                    src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25},
                    mask=base64.b64encode(buf.getvalue()).decode(), edit_by="model")
        crop = crop_region_subject(image, mv)
        assert float(crop[0, 2, 0, 0]) == 0.5   # inside the silhouette: kept
        assert float(crop[0, 2, 4, 0]) == 1.0   # outside it: white


class TestCompositeRefAtBox:
    """A wired reference image is composited into the scene at its region's box,
    with its near-uniform background auto-keyed out, so an added object lands
    pixel-exact where the box is drawn."""

    def test_none_inputs_return_image(self):
        assert composite_ref_at_box(None, "x", Box(0.1, 0.1, 0.2, 0.2)) is None

    def test_keys_background_and_pastes_subject(self):
        torch = pytest.importorskip("torch")
        base = torch.zeros((1, 20, 20, 3))           # black scene
        ref = torch.ones((1, 4, 4, 3))               # white background
        ref[:, 1:3, 1:3, 2] = 1.0                     # blue subject (R,G=0, B=1)
        ref[:, 1:3, 1:3, 0] = 0.0
        ref[:, 1:3, 1:3, 1] = 0.0
        out = composite_ref_at_box(base, ref, Box(0.4, 0.4, 0.2, 0.2))  # px 8..12
        # The blue subject lands inside the box…
        assert float(out[0, 10, 10, 2]) == 1.0
        assert float(out[0, 10, 10, 0]) == 0.0
        # …and the white border is keyed out, leaving the black scene.
        assert float(out[0, 8, 8, 0]) == 0.0

    def test_input_not_mutated(self):
        torch = pytest.importorskip("torch")
        base = torch.zeros((1, 20, 20, 3))
        ref = torch.ones((1, 4, 4, 3))
        ref[:, 1:3, 1:3, :] = 0.0
        composite_ref_at_box(base, ref, Box(0.4, 0.4, 0.2, 0.2))
        assert float(base[0, 10, 10, 0]) == 0.0


class TestModelMoveReferenceCrop:
    """execute() attaches the crop to image_refs and the prompt cites it."""

    @staticmethod
    def _doc():
        return json.dumps({
            "version": 2, "order": ["r0"],
            "regions": [{
                "id": "r0", "kind": "object",
                "box": {"x": 0.5, "y": 0.5, "w": 0.25, "h": 0.25},
                "content": {"desc": "a lemur", "text": ""},
                "source": {"box": {"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25},
                           "mask": None, "label": ""},
                "op": "normal", "edit_by": "model", "bind": None,
                "ui": {"parent": None, "hidden": False, "collapsed": False},
            }],
        })

    def test_crop_appended_and_cited(self):
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 40, 40, 3))
        image[:, 0:10, 0:10, :] = 1.0
        out = RegionalPromptBuilder.execute(
            width=40, height=40, prompt="",
            regions_data=self._doc(), image=image,
        )
        prompt, image_refs = out.args[0], out.args[5]
        assert len(image_refs) == 1
        assert float(image_refs[0][0, 2, 2, 0]) == 1.0   # the source subject
        assert "Reproduce it exactly from image 2" in prompt


class TestNodeRefInsertion:
    """A node-mode ref addition with an image connected is composited into the
    scene at its box (not sent to the edit model), and the prompt blends it."""

    def test_ref_addition_composited_not_sent(self):
        torch = pytest.importorskip("torch")
        base = torch.zeros((1, 40, 40, 3))            # black scene
        ref = torch.ones((1, 8, 8, 3))                # white background
        ref[:, 2:6, 2:6, 0] = 0.0                      # blue subject (R,G=0, B=1)
        ref[:, 2:6, 2:6, 1] = 0.0
        regions = [{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "a hat", "text": ""}]
        out = RegionalPromptBuilder.execute(
            width=40, height=40, prompt="",
            regions_data=json.dumps(regions), image=base, ref_1=ref,
        )
        prompt, image, image_refs = out.args[0], out.args[4], out.args[5]
        assert image_refs == []                        # composited, not sent
        assert "blending it into the scene" in prompt  # insert blend line
        assert "image 2" not in prompt                 # not "reproduce from image 2"
        assert float(image[0, 20, 20, 2]) == 1.0       # subject landed at the box
        assert float(image[0, 20, 20, 0]) == 0.0

    def test_ref_addition_sent_to_model_without_image(self):
        # No image to composite into → the ref still goes to the edit model.
        sentinel = object()
        out = RegionalPromptBuilder.execute(
            width=40, height=40, prompt="",
            regions_data=json.dumps([{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                                      "kind": "object", "desc": "a hat", "text": ""}]),
            ref_1=sentinel,
        )
        assert out.args[5] == [sentinel]


class TestOcclusion:
    """A moved region pasted under a scanned region that sits above it in the
    depth order is partially hidden: the upper region's original pixels are
    re-stamped on top, so the move can land behind an object in the photo."""

    @staticmethod
    def _scene(torch):
        # 20x20 black frame. A white 5x5 patch top-left is the movable object;
        # a green vertical band (cols 12..16, rows 8..18) is the standing object
        # that other things can move behind.
        image = torch.zeros((1, 20, 20, 3))
        image[:, 0:5, 0:5, :] = 1.0          # white source patch (the lemur)
        image[:, 8:18, 12:16, 1] = 0.5       # green band (the man), red stays 0
        return image

    @staticmethod
    def _lemur(**over):
        params = dict(x=0.5, y=0.5, w=0.25, h=0.25, desc="lemur",
                      src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25})
        params.update(over)
        return region(**params)

    @staticmethod
    def _man():
        import numpy as np
        # A scanned region needs a stored mask to act as an occluder; a solid
        # mask means its silhouette is its whole box (cols 12..16, rows 8..18).
        solid = _png_base64(np.full((10, 4), 255, dtype="uint8"))
        return region(x=0.6, y=0.4, w=0.2, h=0.5, desc="man", mask=solid)

    def test_upper_region_re_covers_the_move(self):
        torch = pytest.importorskip("torch")
        pytest.importorskip("PIL.Image")
        # Depth order back-to-front: lemur first (behind), man second (in front).
        out = composite_moved_regions(self._scene(torch), [self._lemur(), self._man()])
        assert float(out[0, 12, 11, 0]) == 1.0   # lemur shows where the man is absent
        assert float(out[0, 12, 13, 0]) == 0.0   # under the man: lemur is hidden
        assert float(out[0, 12, 13, 1]) == 0.5   # the man's own pixels show through

    def test_lower_region_does_not_occlude(self):
        torch = pytest.importorskip("torch")
        pytest.importorskip("PIL.Image")
        # Man first (behind), lemur second (in front): the move stays on top.
        out = composite_moved_regions(self._scene(torch), [self._man(), self._lemur()])
        assert float(out[0, 12, 13, 0]) == 1.0   # lemur covers the man, not vice versa

    def test_maskless_region_does_not_occlude(self):
        torch = pytest.importorskip("torch")
        # A hand-drawn box (no scan, no mask) is a layout guide, not a physical
        # object, so it never re-covers a move even when drawn above it.
        guide = region(x=0.6, y=0.4, w=0.2, h=0.5, desc="area")
        out = composite_moved_regions(self._scene(torch), [self._lemur(), guide])
        assert float(out[0, 12, 13, 0]) == 1.0   # the lemur is not occluded


class TestMoveOriginCutouts:
    """A moved region's origin is inpainted away (silhouette minus destination),
    so the object does not appear at both its old and new positions."""

    def test_disjoint_origin_is_marked(self):
        pytest.importorskip("numpy")
        moved = region(x=0.5, y=0.5, w=0.25, h=0.25, desc="x",
                       src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25})
        mask = _move_origin_mask([moved], 20, 20)
        assert mask[2, 2] == 255      # the origin gets filled
        assert mask[12, 12] == 0      # the destination is left alone
        assert mask[8, 8] == 0        # untouched elsewhere

    def test_overlap_excludes_the_destination(self):
        pytest.importorskip("numpy")
        # Destination sits inside the origin (scale/move-in-place).
        moved = region(x=0.2, y=0.2, w=0.2, h=0.2, desc="x",
                       src={"x": 0.0, "y": 0.0, "w": 0.6, "h": 0.6})
        mask = _move_origin_mask([moved], 20, 20)
        assert mask[1, 1] == 255       # origin, outside the destination -> fill
        assert mask[6, 6] == 0         # inside the destination -> kept (fresh paste)

    def test_unmoved_and_srcless_regions_are_ignored(self):
        pytest.importorskip("numpy")
        anchor = region(x=0.1, y=0.1, w=0.2, h=0.2, desc="x",
                        src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})
        hand_drawn = region(x=0.5, y=0.5, w=0.2, h=0.2, desc="x")
        assert _move_origin_mask([anchor, hand_drawn], 20, 20).max() == 0

    def test_origin_clear_spares_another_moves_destination(self):
        pytest.importorskip("numpy")
        # B's origin lands exactly on A's pasted destination; clearing B must not
        # wipe A's fresh copy, and A's own origin still clears.
        a = region(x=0.5, y=0.0, w=0.3, h=0.3, desc="A",
                   src={"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3})   # moved right
        b = region(x=0.0, y=0.5, w=0.3, h=0.3, desc="B",
                   src={"x": 0.5, "y": 0.0, "w": 0.3, "h": 0.3})   # origin == A's dest
        mask = _move_origin_mask([a, b], 100, 100)
        assert mask[10, 65] == 0      # A's destination is spared
        assert mask[10, 10] == 255    # A's own origin still cleared

    def test_origin_clear_spares_static_object(self):
        pytest.importorskip("numpy")
        # A moved region's origin overlaps a static scanned object; clearing must
        # not erase the static object that sits there.
        static = region(x=0.4, y=0.4, w=0.3, h=0.3, desc="tree",
                        src={"x": 0.4, "y": 0.4, "w": 0.3, "h": 0.3})  # unmoved
        moved = region(x=0.0, y=0.0, w=0.5, h=0.5, desc="x",
                       src={"x": 0.3, "y": 0.3, "w": 0.5, "h": 0.5})   # origin overlaps static
        mask = _move_origin_mask([static, moved], 100, 100)
        assert mask[50, 50] == 0      # the static object's area is spared

    def test_apply_fills_the_origin(self):
        pytest.importorskip("numpy")
        torch = pytest.importorskip("torch")
        pytest.importorskip("cv2")
        # Red field with a blue patch where the origin is; after the move the
        # origin is inpainted back to red, RGB preserved.
        img = torch.zeros((1, 20, 20, 3))
        img[..., 0] = 1.0
        img[0, 0:5, 0:5, 0] = 0.0      # blue origin patch
        img[0, 0:5, 0:5, 2] = 1.0
        moved = region(x=0.5, y=0.5, w=0.25, h=0.25, desc="x",
                       src={"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25})
        out = apply_move_origin_cutouts(img, [moved])
        assert out.shape == (1, 20, 20, 3)
        assert float(out[0, 2, 2, 0]) > float(out[0, 2, 2, 2])  # origin -> red

    def test_apply_no_move_returns_input(self):
        torch = pytest.importorskip("torch")
        img = torch.rand((1, 8, 8, 3))
        anchor = region(x=0.1, y=0.1, w=0.2, h=0.2, desc="x",
                        src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})
        out = apply_move_origin_cutouts(img, [anchor])
        assert out is img


class TestOverlappingMoves:
    """A destination overlapping its origin needs erase-outside phrasing:
    "remove the duplicate at [src]" would also remove the kept copy."""

    @staticmethod
    def _overlapping_move():
        # Destination sits inside the origin, like shrinking a subject in place.
        return region(x=0.35, y=0.35, w=0.2, h=0.2, desc="a safari guide",
                      src={"x": 0.2, "y": 0.1, "w": 0.5, "h": 0.8})

    def test_overlapping_move_erases_outside_the_kept_copy(self):
        prompt = build_prompt("", 1000, 1000, [self._overlapping_move()])
        assert "erase every part of it outside box_2d = [350, 350, 550, 550]" in prompt
        assert "remove the duplicate at" not in prompt

    def test_disjoint_move_keeps_remove_duplicate_phrasing(self):
        moved = region(x=0.35, y=0.35, w=0.2, h=0.2, desc="a safari guide",
                       src={"x": 0.0, "y": 0.0, "w": 0.2, "h": 0.2})
        prompt = build_prompt("", 1000, 1000, [moved])
        assert "remove the duplicate at box_2d = [0, 0, 200, 200]" in prompt
        assert "erase every part" not in prompt

    def test_growing_in_place_asks_only_for_blending(self):
        # Destination covers the origin: the paste hides the old copy, so
        # there is no duplicate to remove.
        moved = region(x=0.1, y=0.1, w=0.6, h=0.6, desc="a safari guide",
                       src={"x": 0.3, "y": 0.3, "w": 0.2, "h": 0.2})
        prompt = build_prompt("", 1000, 1000, [moved])
        assert "blend" in prompt.lower()
        assert "remove the duplicate" not in prompt
        assert "erase every part" not in prompt


class TestRegionGroups:
    """Regions carry optional stable ids and parent links for layer groups.
    Groups are organizational: prompt, bboxes, and masks stay flat."""

    def test_parse_preserves_id_and_parent(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "id": "abc123"},
            {"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1, "id": "def456",
             "parent": "abc123"},
        ])
        regions = parse_regions(data)
        assert regions[0].id == "abc123"
        assert regions[0].ui.parent is None
        assert regions[1].ui.parent == "abc123"

    def test_non_string_id_and_parent_dropped(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "id": 7, "parent": []},
        ])
        # A non-string id is not kept; the contract assigns a stable one instead.
        region_out = parse_regions(data)[0]
        assert region_out.id != 7
        assert region_out.ui.parent is None

    def test_groups_do_not_change_prompt_or_bboxes(self):
        grouped = [
            region(x=0.1, y=0.1, w=0.5, h=0.5, desc="a man", rid="a1"),
            region(x=0.15, y=0.12, w=0.1, h=0.1, desc="a hat",
                   rid="b2", parent="a1"),
        ]
        prompt = build_prompt("", 1000, 1000, grouped)
        assert "a man" in prompt and "a hat" in prompt
        assert len(regions_to_pixel_bboxes(grouped, 100, 100)[0]) == 2


class TestModelEditMoves:
    """A moved region flagged edit_by='model' is NOT composited by the node, so
    its prompt line tells the model to relocate it rather than to clean up an
    already-pasted copy."""

    @staticmethod
    def _model_move():
        return region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                      src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
                      edit_by="model")

    @staticmethod
    def _node_move():
        return region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                      src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})

    def test_model_move_uses_relocation_language(self):
        prompt = build_prompt("", 1000, 1000, [self._model_move()])
        assert MODEL_REPOSITION_HEADER in prompt
        assert "currently at box_2d = [100, 100, 300, 300]" in prompt
        assert "its new position is" in prompt
        # No double preposition from the placement phrase ("at the ...").
        assert "to at the" not in prompt

    def test_model_move_omits_paste_cleanup_language(self):
        # The node did not composite it, so there is no leftover duplicate.
        prompt = build_prompt("", 1000, 1000, [self._model_move()])
        assert "remove the duplicate" not in prompt
        assert "repositioned by pasting" not in prompt

    def test_model_move_pins_size_to_box(self):
        # The box_2d carries the extent; the line states no percent/pixel size and
        # leans on the box with an explicit no-resize directive instead.
        prompt = build_prompt("", 1000, 1000, [self._model_move()])
        assert "of the image width and" not in prompt
        assert "px)" not in prompt
        assert "Keep it at the size of that box; do not enlarge or shrink it" in prompt

    def test_node_move_keeps_composite_language(self):
        prompt = build_prompt("", 1000, 1000, [self._node_move()])
        assert REPOSITION_HEADER in prompt
        assert MODEL_REPOSITION_HEADER not in prompt

    def test_mixed_moves_emit_both_blocks(self):
        prompt = build_prompt("", 1000, 1000,
                              [self._node_move(), self._model_move()])
        assert REPOSITION_HEADER in prompt
        assert MODEL_REPOSITION_HEADER in prompt

    @staticmethod
    def _lemur(x=0.6, y=0.6, w=0.1, h=0.1):
        return region(x=x, y=y, w=w, h=h, desc="a lemur",
                      src={"x": 0.02, "y": 0.02, "w": w, "h": h}, edit_by="model")

    def test_model_move_anchors_to_nearest_landmark(self):
        # Edit models honor landmarks far better than coordinates, so the
        # destination is described relative to the nearest stable named region.
        man = region(x=0.75, y=0.55, w=0.15, h=0.3, desc="the man",
                     src={"x": 0.75, "y": 0.55, "w": 0.15, "h": 0.3})
        prompt = build_prompt("", 1000, 1000, [self._lemur(), man])
        assert "to the left of the man" in prompt

    def test_model_move_between_separated_flanking_landmarks(self):
        # Two landmarks straddling the destination triangulate it far better than
        # one fuzzy "next to": the placement becomes "between A and B".
        lemur = self._lemur(x=0.45, y=0.45)            # center (0.5, 0.5)
        cub = region(x=0.15, y=0.4, w=0.2, h=0.2, desc="a tiger cub",
                     src={"x": 0.15, "y": 0.4, "w": 0.2, "h": 0.2})  # left
        man = region(x=0.7, y=0.4, w=0.2, h=0.2, desc="the man",
                     src={"x": 0.7, "y": 0.4, "w": 0.2, "h": 0.2})   # right
        prompt = build_prompt("", 1000, 1000, [lemur, cub, man])
        assert "between a tiger cub and the man" in prompt

    def test_model_move_states_depth_in_front_when_overlapping(self):
        # An overlapping landmark is described by depth, not direction, and the
        # back-to-front order decides which: the later region is in front.
        cub = region(x=0.4, y=0.4, w=0.3, h=0.3, desc="a tiger cub",
                     src={"x": 0.4, "y": 0.4, "w": 0.3, "h": 0.3})
        lemur = self._lemur(x=0.45, y=0.45, w=0.15, h=0.15)
        prompt = build_prompt("", 1000, 1000, [cub, lemur])  # lemur drawn in front
        assert "in front of a tiger cub" in prompt

    def test_model_move_states_depth_behind_when_lower_layer(self):
        cub = region(x=0.4, y=0.4, w=0.3, h=0.3, desc="a tiger cub",
                     src={"x": 0.4, "y": 0.4, "w": 0.3, "h": 0.3})
        lemur = self._lemur(x=0.45, y=0.45, w=0.15, h=0.15)
        prompt = build_prompt("", 1000, 1000, [lemur, cub])  # lemur drawn behind
        assert "behind a tiger cub" in prompt

    def test_model_move_relates_to_two_overlapping_anchors_by_depth(self):
        # The lemur's case: it overlaps both the man and the cub, so it is placed
        # by depth against each — behind the man, in front of the cub.
        lemur = self._lemur(x=0.42, y=0.42, w=0.16, h=0.16)   # center (0.5, 0.5)
        man = region(x=0.3, y=0.1, w=0.4, h=0.45, desc="the man",
                     src={"x": 0.3, "y": 0.1, "w": 0.4, "h": 0.45})   # overlaps from above
        cub = region(x=0.35, y=0.5, w=0.3, h=0.4, desc="a tiger cub",
                     src={"x": 0.35, "y": 0.5, "w": 0.3, "h": 0.4})   # overlaps from below
        prompt = build_prompt("", 1000, 1000, [cub, lemur, man])  # cub back, lemur, man front
        assert "behind the man and in front of a tiger cub" in prompt

    def test_model_move_ignores_unstable_model_landmarks(self):
        # Another model-move has no known final position, so it is not an anchor.
        parrot = region(x=0.75, y=0.55, w=0.15, h=0.2, desc="a parrot",
                        src={"x": 0.2, "y": 0.2, "w": 0.15, "h": 0.2},
                        edit_by="model")
        prompt = build_prompt("", 1000, 1000, [self._lemur(), parrot])
        assert "Place it" not in prompt

    def test_model_move_without_landmarks_has_no_anchor(self):
        prompt = build_prompt("", 1000, 1000, [self._model_move()])
        assert "Place it" not in prompt

    def test_model_move_cites_reference_crop(self):
        # The node clears the origin, so the model has no in-image reference; a
        # crop is attached and the line tells the model to reproduce it from it.
        lemur = self._lemur(x=0.5, y=0.5, w=0.1, h=0.1)
        lemur.move_ref_image = 2
        prompt = build_prompt("", 1000, 1000, [lemur])
        assert "Reproduce it exactly from image 2" in prompt
        assert "image 1 is the image being edited" in prompt  # legend present

    def test_model_move_without_crop_omits_reference(self):
        prompt = build_prompt("", 1000, 1000, [self._model_move()])
        assert "Reproduce it exactly from image" not in prompt
        assert "image 1 is the image being edited" not in prompt

    def test_model_move_gets_best_effort_occlusion_clause(self):
        # Model mode can't bake occlusion, but the prompt still asks for it when a
        # masked object sits in front of and overlaps the move.
        import numpy as np
        solid = _png_base64(np.full((10, 10), 255, dtype="uint8"))
        lemur = self._lemur(x=0.42, y=0.42, w=0.16, h=0.16)
        man = region(x=0.3, y=0.3, w=0.4, h=0.4, desc="the man", mask=solid)
        prompt = build_prompt("", 1000, 1000, [lemur, man])
        assert "partly hidden" in prompt
        assert "covered by the man" in prompt

    def test_model_move_occlusion_grounds_the_occluder_box(self):
        # Bounding-box grounding: with no pixels to lean on, the occluder's box_2d
        # is stated next to the move's own box (Gemini honors coords for both).
        import numpy as np
        solid = _png_base64(np.full((10, 10), 255, dtype="uint8"))
        lemur = self._lemur(x=0.42, y=0.42, w=0.16, h=0.16)
        man = region(x=0.3, y=0.3, w=0.4, h=0.4, desc="the man", mask=solid)
        prompt = build_prompt("", 1000, 1000, [lemur, man])
        assert "the man (box_2d = [300, 300, 700, 700])" in prompt

    def test_node_move_occlusion_clause_omits_box(self):
        # Node moves bake occlusion into pixels, so the clause stays box-free —
        # the coordinates would be redundant noise.
        import numpy as np
        solid = _png_base64(np.full((10, 10), 255, dtype="uint8"))
        node_lemur = region(x=0.42, y=0.42, w=0.16, h=0.16, desc="a lemur",
                            src={"x": 0.02, "y": 0.02, "w": 0.16, "h": 0.16})
        man = region(x=0.3, y=0.3, w=0.4, h=0.4, desc="the man", mask=solid)
        prompt = build_prompt("", 1000, 1000, [node_lemur, man])
        assert "in front of it" in prompt
        assert "the man (box_2d" not in prompt


class TestModelEditSkipsNodeFill:
    """A model cut-out leaves its pixels for the model to remove. A model MOVE,
    however, still has its origin cleared by the node: leaving the original in
    place makes the edit model render a second copy at the destination."""

    def test_model_cutout_not_filled_by_node(self):
        cut = region(x=0.1, y=0.1, w=0.4, h=0.4, cutout=True, edit_by="model")
        mask = _cutout_mask([cut], 100, 100)
        assert mask[20, 20] == 0  # model removes it; node leaves the pixels

    def test_node_cutout_still_filled(self):
        cut = region(x=0.1, y=0.1, w=0.4, h=0.4, cutout=True)
        mask = _cutout_mask([cut], 100, 100)
        assert mask[20, 20] == 255

    def test_model_move_origin_is_cleared(self):
        # Leaving the origin makes the model render a SECOND copy; the node clears
        # it so only the destination render remains.
        mv = region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                    src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}, edit_by="model")
        mask = _move_origin_mask([mv], 100, 100)
        assert mask[15, 15] == 255   # origin (px 10-30) is cleared
        assert int(mask.sum()) > 0

    def test_model_move_clears_whole_origin_no_paste_to_spare(self):
        # A node move spares where its paste lands; a model move composites no
        # paste, so the entire origin silhouette is cleared even when the
        # destination overlaps it.
        mv = region(x=0.2, y=0.2, w=0.2, h=0.2, desc="a hippo",   # dest overlaps origin
                    src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}, edit_by="model")
        mask = _move_origin_mask([mv], 100, 100)
        assert mask[25, 25] == 255   # inside the dest box, still cleared

    def test_node_move_origin_still_erased(self):
        mv = region(x=0.6, y=0.6, w=0.2, h=0.2, desc="a hippo",
                    src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})
        mask = _move_origin_mask([mv], 100, 100)
        assert int(mask.sum()) > 0


class TestMoveOriginSilhouette:
    """A moved region's leftover origin is cleared everywhere the pasted copy
    does NOT actually cover — subtracting the paste silhouette, not its box."""

    @staticmethod
    def _half_mask_b64():
        np = pytest.importorskip("numpy")
        pytest.importorskip("PIL")
        import base64
        from io import BytesIO
        from PIL import Image
        arr = np.zeros((20, 20), dtype=np.uint8)
        arr[:, 10:] = 255  # white on the RIGHT half of the box
        buf = BytesIO()
        Image.fromarray(arr, "L").save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def test_origin_filled_where_paste_silhouette_misses(self):
        # Origin's right-half silhouette sits inside the dest BOX but outside the
        # dest paste silhouette, so it must be filled (box subtraction zeroed it).
        moved = region(x=0.25, y=0.0, w=0.5, h=0.5,
                       src={"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
                       mask=self._half_mask_b64())
        mask = _move_origin_mask([moved], 100, 100)
        assert mask[25, 30] == 255


class TestMarkerRegions:
    """marker_regions selects only the elements the edit model places itself —
    additions and model-applied moves — never node-composited or inserted ones."""

    def test_addition_is_marked(self):
        add = region(desc="a red hat")
        assert marker_regions([add]) == [add]

    def test_model_move_is_marked(self):
        mv = region(x=0.6, y=0.6, desc="a lemur",
                    src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}, edit_by="model")
        assert marker_regions([mv]) == [mv]

    def test_node_move_is_not_marked(self):
        mv = region(x=0.6, y=0.6, desc="a lemur",
                    src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})
        assert marker_regions([mv]) == []

    def test_unmoved_scan_anchor_is_not_marked(self):
        anchor = region(desc="a tree", src={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2})
        assert marker_regions([anchor]) == []

    def test_cutout_is_not_marked(self):
        cut = region(desc="a sign", cutout=True)
        assert marker_regions([cut]) == []

    def test_markers_off_opts_out(self):
        add = region(desc="a red hat", markers=False)
        assert marker_regions([add]) == []


class TestAssignMarkers:
    """Each placed region gets a distinct marker color and a sequential label
    letter; the color skips any color word already in the description."""

    def test_distinct_colors_and_labels(self):
        a, b = region(desc="a hat"), region(desc="a ball")
        assign_markers([a, b])
        assert a.marker_color and b.marker_color
        assert a.marker_color != b.marker_color
        assert a.marker_label == "A" and b.marker_label == "B"

    def test_avoids_color_named_in_description(self):
        # The default first palette color is magenta; a magenta object must not
        # get a magenta marker.
        r = region(desc="a magenta balloon")
        assign_markers([r])
        assert "magenta" not in r.marker_color


class TestMarkerPrompt:
    """When a region carries a marker, the prompt explains the targets and cites
    each element's marker by letter and color; without it, neither appears."""

    def test_header_and_marker_cited(self):
        add = region(desc="a red hat")
        assign_markers([add])
        out = build_prompt("", 686, 386, [add], edit_mode=True)
        assert MARKER_HEADER in out
        assert f"marker {add.marker_label}" in out
        assert f"{add.marker_color} dot" in out

    def test_no_marker_no_header(self):
        add = region(desc="a red hat")
        out = build_prompt("", 686, 386, [add], edit_mode=True)
        assert MARKER_HEADER not in out
        assert "Center it on marker" not in out


class TestDrawPlacementMarkers:
    """A colored reticle is stamped at each marked region's box center."""

    def test_none_image_returns_none(self):
        add = region(desc="a hat")
        assign_markers([add])
        assert draw_placement_markers(None, [add]) is None

    def test_unmarked_region_leaves_image_untouched(self):
        torch = pytest.importorskip("torch")
        pytest.importorskip("PIL")
        base = torch.zeros((1, 40, 40, 3))
        out = draw_placement_markers(base, [region(desc="a hat")])  # no marker_color
        assert float(out[0, 20, 20, 0]) == 0.0

    def test_dot_fill_is_marker_color(self):
        torch = pytest.importorskip("torch")
        pytest.importorskip("PIL")
        base = torch.zeros((1, 100, 100, 3))
        add = region(x=0.4, y=0.4, w=0.2, h=0.2, desc="a hat")  # center px (50,50)
        assign_markers([add])
        from utils.region_image_ops import MARKER_COLORS
        rgb = dict(MARKER_COLORS)[add.marker_color]
        out = draw_placement_markers(base, [add])
        # Sample the dot's left edge (inside the fill, off the centered glyph).
        assert float(out[0, 50, 41, 0]) == rgb[0]
        assert float(out[0, 50, 41, 1]) == rgb[1]
        assert float(out[0, 50, 41, 2]) == rgb[2]
        # A corner well outside the dot stays the original scene.
        assert float(out[0, 5, 5, 0]) == 0.0

    def test_input_not_mutated(self):
        torch = pytest.importorskip("torch")
        pytest.importorskip("PIL")
        base = torch.zeros((1, 100, 100, 3))
        add = region(x=0.4, y=0.4, w=0.2, h=0.2, desc="a hat")
        assign_markers([add])
        draw_placement_markers(base, [add])
        assert float(base[0, 50, 50, 0]) == 0.0


class TestExecuteMarkers:
    """execute() draws a region's marker and explains it by default, and draws
    nothing for a region that opts out with markers=false."""

    @staticmethod
    def _doc(markers=None):
        region = {
            "id": "r0", "kind": "object",
            "box": {"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2},
            "content": {"desc": "a red hat", "text": ""},
            "op": "normal", "bind": None,
            "ui": {"parent": None, "hidden": False, "collapsed": False},
        }
        if markers is not None:
            region["markers"] = markers
        return json.dumps({"version": 2, "order": ["r0"], "regions": [region]})

    def test_marker_drawn_and_prompt_explains(self):
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 100, 100, 3))
        out = RegionalPromptBuilder.execute(
            width=100, height=100, prompt="",
            regions_data=self._doc(), image=image,
        )
        prompt, image_out = out.args[0], out.args[4]
        assert MARKER_HEADER in prompt
        assert float(image_out.sum()) > 0   # a dot was stamped

    def test_markers_off_draws_nothing(self):
        torch = pytest.importorskip("torch")
        image = torch.zeros((1, 100, 100, 3))
        out = RegionalPromptBuilder.execute(
            width=100, height=100, prompt="",
            regions_data=self._doc(markers=False), image=image,
        )
        prompt, image_out = out.args[0], out.args[4]
        assert MARKER_HEADER not in prompt
        assert float(image_out.sum()) == 0.0
