# ABOUTME: Tests for RegionalPromptBuilder schema, region parsing, coordinate
# ABOUTME: conversions, prompt assembly, and pixel bounding-box outputs.

import inspect
import json

import pytest

from utils.regional_prompt import (
    RegionalPromptBuilder,
    aspect_ratio_string,
    box_2d,
    build_prompt,
    parse_regions,
    placement_phrase,
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
            "desc_1", "desc_2", "desc_3", "desc_4", "desc_5", "desc_6",
            "ref_1", "ref_2", "ref_3", "ref_4", "ref_5", "ref_6",
        ]

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
            "prompt", "bboxes", "width", "height", "image", "image_refs",
        ]
        assert [o.io_type for o in schema.outputs] == [
            "STRING", "BOUNDING_BOX", "INT", "INT", "IMAGE", "ERPK_IMAGE_REFS",
        ]

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

    def test_no_heavy_imports(self):
        module_path = inspect.getsourcefile(RegionalPromptBuilder)
        with open(module_path) as f:
            source = f.read()
        for forbidden in ("torch", "numpy", "PIL"):
            assert forbidden not in source


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


class TestExecute:
    def test_canonical_node_output(self):
        out = RegionalPromptBuilder.execute(
            width=1000,
            height=1000,
            prompt="A rainy neon city street at night, wet asphalt reflecting "
                   "neon signs, cinematic photo",
            regions_data=json.dumps(CANONICAL_REGIONS),
        )
        assert out.args == (CANONICAL_PROMPT, CANONICAL_BBOXES, 1000, 1000, None, [])

    def test_scene_only_outputs_empty_bboxes(self):
        out = RegionalPromptBuilder.execute(
            width=1024, height=1024,
            prompt="A quiet forest", regions_data="[]",
        )
        prompt, bboxes, width, height, image, image_refs = out.args
        assert "A quiet forest" in prompt
        assert bboxes == []
        assert (width, height) == (1024, 1024)
        assert image is None
        assert image_refs == []

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
        assert "image 1 is the image being edited" not in without_refs
        assert "Reproduce each referenced item" not in without_refs

    def test_ref_beyond_region_count_is_ignored(self):
        out = RegionalPromptBuilder.execute(
            width=1000, height=1000, prompt="",
            regions_data=json.dumps(CANONICAL_REGIONS),
            ref_5=object(),
        )
        assert out.args[5] == []
        assert "taken from image" not in out.args[0]
        assert "styled as shown in" not in out.args[0]
