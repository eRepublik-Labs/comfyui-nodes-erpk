# ABOUTME: Tests for RegionalPromptBuilder schema, region parsing, coordinate
# ABOUTME: conversions, prompt assembly, and pixel bounding-box outputs.

import ast
import inspect
import json

import pytest

from utils.regional_prompt import (
    RegionalPromptBuilder,
    aspect_ratio_string,
    box_2d,
    build_prompt,
    composite_moved_regions,
    build_region_masks,
    mask_pixel_box,
    parse_regions,
    placement_phrase,
    region_has_stored_mask,
    region_moved,
    regions_to_pixel_bboxes,
)


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
    "1. a red vintage car: at the bottom-left, covering about 30% of the image "
    "width and 25% of its height. box_2d = [620, 40, 870, 340]\n"
    '2. The text "OPEN LATE", glowing neon letters: at the top-center, covering '
    "about 40% of the image width and 14% of its height. box_2d = [30, 300, 170, 700]\n"
    "Every element must stay fully inside its placement area and fill most of it. "
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
            "width", "height", "prompt", "regions_data", "image",
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
        assert regions == CANONICAL_REGIONS

    def test_invalid_json_yields_no_regions(self):
        assert parse_regions("not json {") == []

    def test_non_list_json_yields_no_regions(self):
        assert parse_regions('{"x": 0.1}') == []
        assert parse_regions("42") == []

    def test_non_dict_entries_are_skipped(self):
        data = json.dumps([1, "box", CANONICAL_REGIONS[0], None])
        assert parse_regions(data) == [CANONICAL_REGIONS[0]]

    def test_position_clamped_to_unit_square(self):
        data = json.dumps([{"x": -0.5, "y": 0.5, "w": 2.0, "h": 0.2}])
        region = parse_regions(data)[0]
        assert region["x"] == 0.0
        assert region["y"] == 0.5
        assert region["w"] == 1.0
        assert region["h"] == 0.2

    def test_size_clamped_to_remaining_extent(self):
        data = json.dumps([{"x": 0.8, "y": 0.7, "w": 0.5, "h": 0.6}])
        region = parse_regions(data)[0]
        assert region["w"] == pytest.approx(0.2)
        assert region["h"] == pytest.approx(0.3)

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
        assert [r["kind"] for r in regions] == ["object", "object"]

    def test_missing_desc_and_text_default_to_empty(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}])
        region = parse_regions(data)[0]
        assert region["desc"] == ""
        assert region["text"] == ""

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
        assert [r["kind"] for r in regions] == ["object", "object"]

    def test_non_finite_coordinates_skip_the_entry(self):
        data = '[{"x": 0.1, "y": 0.1, "w": NaN, "h": 0.5}, ' \
               '{"x": Infinity, "y": 0.1, "w": 0.2, "h": 0.2}, ' \
               '{"x": 0.1, "y": -Infinity, "w": 0.2, "h": 0.2}]'
        assert parse_regions(data) == []

    def test_scan_mask_and_group_are_preserved(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "kind": "object", "desc": "car", "text": "",
                            "mask": "iVBORw0K", "group": "car"}])
        region = parse_regions(data)[0]
        assert region["mask"] == "iVBORw0K"
        assert region["group"] == "car"

    def test_hand_drawn_regions_carry_no_mask_or_group(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}])
        region = parse_regions(data)[0]
        assert "mask" not in region
        assert "group" not in region

    def test_blank_or_non_string_mask_and_group_are_dropped(self):
        data = json.dumps([{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "mask": "", "group": 7},
                           {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                            "mask": 123, "group": ["car"]}])
        for region in parse_regions(data):
            assert "mask" not in region
            assert "group" not in region


class TestBox2d:
    def test_canonical_first_region(self):
        assert box_2d(0.04, 0.62, 0.30, 0.25) == [620, 40, 870, 340]

    def test_canonical_second_region(self):
        assert box_2d(0.30, 0.03, 0.40, 0.14) == [30, 300, 170, 700]

    def test_values_clamped_to_grid(self):
        assert box_2d(-0.5, -0.5, 2.0, 2.0) == [0, 0, 1000, 1000]


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

    def test_object_region_without_desc_uses_an_element(self):
        regions = [{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "", "text": ""}]
        prompt = build_prompt("", 1000, 1000, regions)
        assert ("1. An element: at the center, covering about 20% of the image "
                "width and 20% of its height. box_2d = [400, 400, 600, 600]") in prompt

    def test_text_region_without_desc_omits_desc_clause(self):
        regions = [{"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2,
                    "kind": "text", "desc": "", "text": "SALE"}]
        prompt = build_prompt("", 1000, 1000, regions)
        assert '1. The text "SALE": at the center, covering about 20%' in prompt

    def test_layout_forbids_drawing_annotations(self):
        regions = [{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "a cat", "text": ""}]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "never draw boxes" in prompt
        assert "bounding box" not in prompt

    def test_layout_declares_back_to_front_depth_order(self):
        regions = [{"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                    "kind": "object", "desc": "a cat", "text": ""}]
        prompt = build_prompt("", 1000, 1000, regions)
        assert "listed from back to front" in prompt
        assert "appears in front of an earlier one" in prompt


    def test_unicode_and_long_desc_round_trip(self):
        long_desc = "ornate baroque detail, " * 200
        regions = [
            {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3,
             "kind": "text", "desc": "霓虹灯 sign with sparkles", "text": "营业中 OPEN"},
            {"x": 0.5, "y": 0.5, "w": 0.3, "h": 0.3,
             "kind": "object", "desc": long_desc, "text": ""},
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
        regions = [{"x": 0.5, "y": 0.25, "w": 0.25, "h": 0.5,
                    "kind": "object", "desc": "", "text": ""}]
        assert regions_to_pixel_bboxes(regions, 1920, 1080) == [[
            {"x": 960, "y": 270, "width": 480, "height": 540},
        ]]


class TestMaskPixelBox:
    def test_canonical_region_pixel_bounds(self):
        region = {"x": 0.04, "y": 0.62, "w": 0.30, "h": 0.25}
        assert mask_pixel_box(region, 1000, 1000) == (40, 620, 340, 870)

    def test_bounds_scale_with_frame_size(self):
        region = {"x": 0.5, "y": 0.25, "w": 0.25, "h": 0.5}
        assert mask_pixel_box(region, 1920, 1080) == (960, 270, 1440, 810)

    def test_bounds_clamped_to_frame(self):
        region = {"x": 0.95, "y": 0.95, "w": 0.2, "h": 0.2}
        assert mask_pixel_box(region, 100, 100) == (95, 95, 100, 100)

    def test_sub_pixel_region_still_encloses_a_pixel(self):
        region = {"x": 0.0, "y": 0.0, "w": 0.006, "h": 0.006}
        x0, y0, x1, y1 = mask_pixel_box(region, 64, 64)
        assert x1 > x0
        assert y1 > y0


class TestRegionHasStoredMask:
    def test_non_empty_string_is_stored(self):
        assert region_has_stored_mask({"mask": "iVBORw0K"}) is True

    @pytest.mark.parametrize("region", [
        {},
        {"mask": ""},
        {"mask": None},
        {"mask": 123},
        {"mask": ["iVBORw0K"]},
    ])
    def test_missing_blank_or_non_string_is_not_stored(self, region):
        assert region_has_stored_mask(region) is False


def _png_base64(array):
    import base64
    import io

    import numpy as np
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(np.asarray(array, dtype="uint8"), mode="L").save(
        buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class TestBuildRegionMasks:
    def test_empty_regions_yield_one_zero_mask(self):
        torch = pytest.importorskip("torch")
        masks = build_region_masks([], 1024, 768)
        assert masks.shape == (1, 768, 1024)
        assert float(masks.sum()) == 0.0

    def test_maskless_region_fills_its_rectangle(self):
        pytest.importorskip("torch")
        region = {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5}
        masks = build_region_masks([region], 100, 100)
        assert masks.shape == (1, 100, 100)
        assert float(masks[0, 50, 50]) == 1.0
        assert float(masks[0, 0, 0]) == 0.0
        assert float(masks[0, 90, 90]) == 0.0

    def test_stored_mask_is_decoded_box_relative(self):
        import numpy as np
        pytest.importorskip("torch")
        glyph = np.zeros((10, 10), dtype="uint8")
        glyph[:, :5] = 255  # left half opaque, right half transparent
        region = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0,
                  "mask": _png_base64(glyph)}
        masks = build_region_masks([region], 20, 20)
        assert float(masks[0, 10, 2]) == 1.0
        assert float(masks[0, 10, 18]) == 0.0

    def test_malformed_mask_falls_back_to_rectangle(self):
        pytest.importorskip("torch")
        region = {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5,
                  "mask": "@@@not-a-png@@@"}
        masks = build_region_masks([region], 100, 100)
        assert float(masks[0, 50, 50]) == 1.0
        assert float(masks[0, 0, 0]) == 0.0

    def test_one_mask_per_region_in_order(self):
        pytest.importorskip("torch")
        regions = [
            {"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3},
            {"x": 0.5, "y": 0.5, "w": 0.4, "h": 0.4},
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
        sentinel = object()
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


class TestMovedRegions:
    """Scanned regions carry their origin box; moving one switches the prompt
    line to relocation language and raises the reposition header."""

    @staticmethod
    def _moved_region():
        return {"x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2, "kind": "object",
                "desc": "a hippo", "text": "",
                "src": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}}

    def test_parse_preserves_valid_src(self):
        regions = parse_regions(json.dumps([self._moved_region()]))
        assert regions[0]["src"] == {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}

    def test_parse_clamps_src(self):
        entry = self._moved_region()
        entry["src"] = {"x": -0.5, "y": 0.0, "w": 2.0, "h": 0.5}
        regions = parse_regions(json.dumps([entry]))
        assert regions[0]["src"] == {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.5}

    def test_parse_drops_malformed_src_keeps_region(self):
        for bad in ("nope", {"x": 0.1}, {"x": "a", "y": 0, "w": 1, "h": 1},
                    {"x": 0.1, "y": 0.1, "w": 0.001, "h": 0.001}):
            entry = self._moved_region()
            entry["src"] = bad
            regions = parse_regions(json.dumps([entry]))
            assert len(regions) == 1
            assert "src" not in regions[0]

    def test_region_moved_true_when_geometry_differs(self):
        assert region_moved(self._moved_region())

    def test_region_moved_false_in_place(self):
        region = self._moved_region()
        region["src"] = {"x": 0.6, "y": 0.6, "w": 0.2, "h": 0.2}
        assert not region_moved(region)

    def test_region_moved_false_without_src(self):
        assert not region_moved(
            {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
             "kind": "object", "desc": "", "text": ""})

    @staticmethod
    def _anchor_region(desc="a sleeping otter"):
        # Scanned and unmoved: the object already sits where its box says.
        return {"x": 0.1, "y": 0.7, "w": 0.2, "h": 0.2, "kind": "object",
                "desc": desc, "text": "",
                "src": {"x": 0.1, "y": 0.7, "w": 0.2, "h": 0.2}}

    def test_move_block_asks_for_duplicate_removal(self):
        # The move is already composited into the image; the model only cleans up.
        prompt = build_prompt("", 1000, 1000, [self._moved_region()])
        assert "Make these edits" in prompt
        assert "a hippo: remove the duplicate at box_2d = [100, 100, 300, 300]" in prompt
        assert "Keep the one" in prompt
        assert "blending it naturally" in prompt
        assert "box_2d = [600, 600, 800, 800]" in prompt
        assert "background" in prompt.lower()

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
        hand_drawn = {"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2, "kind": "object",
                      "desc": "a brass lantern", "text": ""}
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
        region = self._moved_region()
        region["ref_image"] = 2
        prompt = build_prompt("", 1000, 1000, [region])
        assert "taken from image 2" in prompt
        assert "Make these edits" not in prompt


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
    def _moved(extra=None):
        region = {"x": 0.5, "y": 0.5, "w": 0.25, "h": 0.25, "kind": "object",
                  "desc": "patch", "text": "",
                  "src": {"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25}}
        region.update(extra or {})
        return region

    def test_identity_without_moves(self):
        torch = pytest.importorskip("torch")
        image = self._image(torch)
        anchor = self._moved({"x": 0.0, "y": 0.0})
        assert composite_moved_regions(image, [anchor]) is image

    def test_none_image_passes_through(self):
        assert composite_moved_regions(None, [self._moved()]) is None

    def test_maskless_move_pastes_the_source_rectangle(self):
        torch = pytest.importorskip("torch")
        out = composite_moved_regions(self._image(torch), [self._moved()])
        assert float(out[0, 12, 12, 0]) == 1.0   # pasted at destination
        assert float(out[0, 2, 2, 0]) == 1.0     # source pixels untouched
        assert float(out[0, 12, 2, 0]) == 0.0    # elsewhere unchanged

    def test_move_scales_the_patch_to_the_destination(self):
        torch = pytest.importorskip("torch")
        big = self._moved({"w": 0.5, "h": 0.5, "x": 0.5, "y": 0.5})
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
        region = self._moved({"mask": base64.b64encode(buf.getvalue()).decode()})
        out = composite_moved_regions(self._image(torch), [region])
        assert float(out[0, 12, 10, 0]) == 1.0   # inside the opaque half
        assert float(out[0, 12, 14, 0]) == 0.0   # masked-out half untouched

    def test_input_tensor_is_not_mutated(self):
        torch = pytest.importorskip("torch")
        image = self._image(torch)
        composite_moved_regions(image, [self._moved()])
        assert float(image[0, 12, 12, 0]) == 0.0


class TestOverlappingMoves:
    """A destination overlapping its origin needs erase-outside phrasing:
    "remove the duplicate at [src]" would also remove the kept copy."""

    @staticmethod
    def _overlapping_move():
        # Destination sits inside the origin, like shrinking a subject in place.
        return {"x": 0.35, "y": 0.35, "w": 0.2, "h": 0.2, "kind": "object",
                "desc": "a safari guide", "text": "",
                "src": {"x": 0.2, "y": 0.1, "w": 0.5, "h": 0.8}}

    def test_overlapping_move_erases_outside_the_kept_copy(self):
        prompt = build_prompt("", 1000, 1000, [self._overlapping_move()])
        assert "erase every part of it outside box_2d = [350, 350, 550, 550]" in prompt
        assert "remove the duplicate at" not in prompt

    def test_disjoint_move_keeps_remove_duplicate_phrasing(self):
        region = self._overlapping_move()
        region["src"] = {"x": 0.0, "y": 0.0, "w": 0.2, "h": 0.2}
        prompt = build_prompt("", 1000, 1000, [region])
        assert "remove the duplicate at box_2d = [0, 0, 200, 200]" in prompt
        assert "erase every part" not in prompt

    def test_growing_in_place_asks_only_for_blending(self):
        # Destination covers the origin: the paste hides the old copy, so
        # there is no duplicate to remove.
        region = {"x": 0.1, "y": 0.1, "w": 0.6, "h": 0.6, "kind": "object",
                  "desc": "a safari guide", "text": "",
                  "src": {"x": 0.3, "y": 0.3, "w": 0.2, "h": 0.2}}
        prompt = build_prompt("", 1000, 1000, [region])
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
        assert regions[0]["id"] == "abc123"
        assert "parent" not in regions[0]
        assert regions[1]["parent"] == "abc123"

    def test_non_string_id_and_parent_dropped(self):
        data = json.dumps([
            {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "id": 7, "parent": []},
        ])
        regions = parse_regions(data)
        assert "id" not in regions[0]
        assert "parent" not in regions[0]

    def test_groups_do_not_change_prompt_or_bboxes(self):
        flat = [{"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "kind": "object",
                 "desc": "a man", "text": ""}]
        grouped = [dict(flat[0], id="a1"),
                   {"x": 0.15, "y": 0.12, "w": 0.1, "h": 0.1,
                    "kind": "object", "desc": "a hat", "text": "",
                    "id": "b2", "parent": "a1"}]
        prompt = build_prompt("", 1000, 1000, grouped)
        assert "a man" in prompt and "a hat" in prompt
        assert len(regions_to_pixel_bboxes(grouped, 100, 100)[0]) == 2
