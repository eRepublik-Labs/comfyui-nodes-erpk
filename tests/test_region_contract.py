# ABOUTME: Tests for the pure region contract: v1/v2 parsing, serialization,
# ABOUTME: round-trips, edge-validation, ordering, binding, and geometry helpers.

import json

from utils.region_contract import (
    MIN_REGION_EXTENT,
    SCHEMA_VERSION,
    Box,
    Content,
    Mask,
    Region,
    Source,
    Ui,
    parse,
    serialize,
)


# A v1 document as the JS editor still emits it: a flat list with optional
# scan fields (mask/group/src) and layer fields (id/parent/hidden/cutout).
V1_HAND_DRAWN = [
    {"x": 0.04, "y": 0.62, "w": 0.30, "h": 0.25, "kind": "object",
     "desc": "a red vintage car", "text": ""},
    {"x": 0.30, "y": 0.03, "w": 0.40, "h": 0.14, "kind": "text",
     "desc": "glowing neon letters", "text": "OPEN LATE"},
]

V1_SCANNED = {
    "x": 0.10, "y": 0.10, "w": 0.20, "h": 0.20, "kind": "object",
    "desc": "a dog", "text": "",
    "mask": "iVBORw0KGgo=", "group": "animal", "id": "r_dog",
    "src": {"x": 0.50, "y": 0.50, "w": 0.20, "h": 0.20},
}


class TestParseV1:
    def test_parses_flat_list_into_regions(self):
        regions = parse(V1_HAND_DRAWN)
        assert len(regions) == 2
        first = regions[0]
        assert first.kind == "object"
        assert first.box == Box(0.04, 0.62, 0.30, 0.25)
        assert first.content == Content(desc="a red vintage car", text="")
        assert first.source is None
        assert first.op == "normal"
        assert first.bind_slot is None

    def test_parses_json_string(self):
        regions = parse(json.dumps(V1_HAND_DRAWN))
        assert [r.box for r in regions] == [
            Box(0.04, 0.62, 0.30, 0.25),
            Box(0.30, 0.03, 0.40, 0.14),
        ]

    def test_text_region_keeps_text_and_kind(self):
        region = parse(V1_HAND_DRAWN)[1]
        assert region.kind == "text"
        assert region.content.text == "OPEN LATE"
        assert region.content.desc == "glowing neon letters"

    def test_scanned_region_builds_source(self):
        region = parse([V1_SCANNED])[0]
        assert region.source is not None
        assert region.source.box == Box(0.50, 0.50, 0.20, 0.20)
        assert region.source.label == "animal"
        assert region.source.mask == Mask(data="iVBORw0KGgo=", enc="png-b64", w=0, h=0)

    def test_scanned_without_src_backfills_origin_to_box(self):
        entry = {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "mask": "AAAA"}
        region = parse([entry])[0]
        assert region.source is not None
        assert region.source.box == Box(0.1, 0.1, 0.2, 0.2)

    def test_cutout_maps_to_op(self):
        entry = dict(V1_HAND_DRAWN[0], cutout=True)
        assert parse([entry])[0].op == "cutout"

    def test_hidden_and_parent_land_in_ui(self):
        entry = dict(V1_HAND_DRAWN[0], id="child", parent="grp", hidden=True)
        region = parse([entry])[0]
        assert region.ui == Ui(parent="grp", hidden=True, collapsed=False)

    def test_idless_regions_get_stable_unique_ids(self):
        regions = parse(V1_HAND_DRAWN)
        ids = [r.id for r in regions]
        assert all(ids)
        assert len(set(ids)) == len(ids)


class TestParseV2:
    def make_doc(self):
        return {
            "version": 2,
            "order": ["r_a", "r_b"],
            "regions": [
                {
                    "id": "r_a", "kind": "object",
                    "box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
                    "content": {"desc": "a cat", "text": ""},
                    "source": {
                        "box": {"x": 0.3, "y": 0.3, "w": 0.2, "h": 0.2},
                        "mask": {"enc": "png-b64", "w": 32, "h": 24, "data": "QQ=="},
                        "label": "animal",
                    },
                    "op": "normal",
                    "bind": {"slot": 3},
                    "ui": {"parent": None, "hidden": False, "collapsed": True},
                },
                {
                    "id": "r_b", "kind": "text",
                    "box": {"x": 0.5, "y": 0.5, "w": 0.3, "h": 0.1},
                    "content": {"desc": "", "text": "HELLO"},
                    "op": "cutout",
                    "bind": None,
                    "ui": {"parent": "r_a", "hidden": True, "collapsed": False},
                },
            ],
        }

    def test_parses_document(self):
        regions = parse(self.make_doc())
        assert [r.id for r in regions] == ["r_a", "r_b"]
        assert regions[0].box == Box(0.1, 0.1, 0.2, 0.2)
        assert regions[0].content == Content(desc="a cat", text="")
        assert regions[1].kind == "text"
        assert regions[1].op == "cutout"

    def test_parses_v2_source_with_sized_mask(self):
        region = parse(self.make_doc())[0]
        assert region.source == Source(
            box=Box(0.3, 0.3, 0.2, 0.2),
            mask=Mask(data="QQ==", enc="png-b64", w=32, h=24),
            label="animal",
        )

    def test_bind_slot_read_from_bind_object(self):
        regions = parse(self.make_doc())
        assert regions[0].bind_slot == 3
        assert regions[1].bind_slot is None

    def test_ui_collapsed_preserved(self):
        regions = parse(self.make_doc())
        assert regions[0].ui.collapsed is True
        assert regions[1].ui == Ui(parent="r_a", hidden=True, collapsed=False)

    def test_region_without_source_key_has_no_source(self):
        assert parse(self.make_doc())[1].source is None


class TestOrdering:
    def test_order_array_drives_depth_independent_of_array(self):
        doc = {
            "version": 2,
            "order": ["b", "a"],
            "regions": [
                {"id": "a", "box": {"x": 0, "y": 0, "w": 0.2, "h": 0.2}},
                {"id": "b", "box": {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2}},
            ],
        }
        assert [r.id for r in parse(doc)] == ["b", "a"]

    def test_regions_missing_from_order_are_appended(self):
        doc = {
            "version": 2,
            "order": ["a"],
            "regions": [
                {"id": "a", "box": {"x": 0, "y": 0, "w": 0.2, "h": 0.2}},
                {"id": "b", "box": {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2}},
            ],
        }
        assert [r.id for r in parse(doc)] == ["a", "b"]

    def test_bind_slot_follows_id_not_position(self):
        doc = {
            "version": 2,
            "order": ["b", "a"],
            "regions": [
                {"id": "a", "box": {"x": 0, "y": 0, "w": 0.2, "h": 0.2},
                 "bind": {"slot": 1}},
                {"id": "b", "box": {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2},
                 "bind": {"slot": 9}},
            ],
        }
        regions = parse(doc)
        assert regions[0].id == "b" and regions[0].bind_slot == 9
        assert regions[1].id == "a" and regions[1].bind_slot == 1


class TestSerialize:
    def test_serializes_to_v2_document(self):
        regions = parse(V1_HAND_DRAWN)
        doc = serialize(regions)
        assert doc["version"] == SCHEMA_VERSION
        assert doc["order"] == [r.id for r in regions]
        assert len(doc["regions"]) == 2
        first = doc["regions"][0]
        assert first["box"] == {"x": 0.04, "y": 0.62, "w": 0.30, "h": 0.25}
        assert first["content"] == {"desc": "a red vintage car", "text": ""}
        assert first["op"] == "normal"
        assert first["bind"] is None
        assert first["ui"] == {"parent": None, "hidden": False, "collapsed": False}
        assert "source" not in first

    def test_scanned_region_serializes_source(self):
        doc = serialize(parse([V1_SCANNED]))
        source = doc["regions"][0]["source"]
        assert source["box"] == {"x": 0.50, "y": 0.50, "w": 0.20, "h": 0.20}
        assert source["label"] == "animal"
        assert source["mask"] == {"enc": "png-b64", "w": 0, "h": 0, "data": "iVBORw0KGgo="}

    def test_serialized_document_is_json_dumpable(self):
        doc = serialize(parse([V1_SCANNED]))
        json.loads(json.dumps(doc))

    def test_bound_region_serializes_slot(self):
        region = Region(id="x", kind="object", box=Box(0.1, 0.1, 0.2, 0.2),
                        content=Content(desc="d"), bind_slot=4)
        assert serialize([region])["regions"][0]["bind"] == {"slot": 4}


class TestRoundTrip:
    def test_v1_to_v2_to_v1_is_stable(self):
        once = parse(V1_HAND_DRAWN)
        twice = parse(serialize(once))
        assert once == twice

    def test_scanned_round_trip_preserves_source(self):
        once = parse([V1_SCANNED])
        twice = parse(serialize(once))
        assert once == twice

    def test_v2_round_trip_preserves_every_field(self):
        doc = TestParseV2().make_doc()
        once = parse(doc)
        twice = parse(serialize(once))
        assert once == twice

    def test_round_trip_through_json_string(self):
        once = parse(V1_HAND_DRAWN)
        twice = parse(json.dumps(serialize(once)))
        assert once == twice


class TestValidation:
    def test_invalid_json_yields_empty(self):
        assert parse("{not json") == []

    def test_non_collection_yields_empty(self):
        assert parse(42) == []
        assert parse(None) == []

    def test_non_dict_entries_skipped(self):
        regions = parse([V1_HAND_DRAWN[0], "garbage", 5, None, ["nested"]])
        assert len(regions) == 1

    def test_nan_box_dropped(self):
        entry = {"x": float("nan"), "y": 0.1, "w": 0.2, "h": 0.2}
        assert parse([entry]) == []

    def test_infinite_box_dropped(self):
        entry = {"x": 0.1, "y": 0.1, "w": float("inf"), "h": 0.2}
        assert parse([entry]) == []

    def test_non_numeric_box_dropped(self):
        entry = {"x": "left", "y": 0.1, "w": 0.2, "h": 0.2}
        assert parse([entry]) == []

    def test_negative_extent_dropped(self):
        entry = {"x": 0.1, "y": 0.1, "w": -0.5, "h": 0.2}
        assert parse([entry]) == []

    def test_tiny_box_dropped(self):
        entry = {"x": 0.1, "y": 0.1, "w": MIN_REGION_EXTENT, "h": 0.2}
        assert parse([entry]) == []

    def test_fully_out_of_range_box_dropped(self):
        # x clamps to 1.0, leaving no room for width -> sub-extent -> dropped.
        entry = {"x": 2.0, "y": 0.1, "w": 0.3, "h": 0.3}
        assert parse([entry]) == []

    def test_oversized_box_is_clamped_not_dropped(self):
        entry = {"x": 0.5, "y": 0.5, "w": 5.0, "h": 5.0}
        region = parse([entry])[0]
        assert region.box == Box(0.5, 0.5, 0.5, 0.5)

    def test_negative_origin_is_clamped(self):
        entry = {"x": -0.3, "y": -0.3, "w": 0.4, "h": 0.4}
        region = parse([entry])[0]
        assert region.box == Box(0.0, 0.0, 0.4, 0.4)

    def test_one_bad_region_does_not_sink_the_others(self):
        regions = parse([
            {"x": float("nan"), "y": 0, "w": 0.2, "h": 0.2},
            V1_HAND_DRAWN[0],
        ])
        assert len(regions) == 1
        assert regions[0].content.desc == "a red vintage car"

    def test_unknown_kind_defaults_to_object(self):
        entry = dict(V1_HAND_DRAWN[0], kind="sticker")
        assert parse([entry])[0].kind == "object"

    def test_invalid_src_box_drops_only_source_for_maskless_region(self):
        entry = {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2,
                 "src": {"x": "bad", "y": 0.1, "w": 0.2, "h": 0.2}}
        region = parse([entry])[0]
        assert region.source is None


class TestGeometry:
    def test_grid_2d_matches_box_2d_convention(self):
        assert Box(0.04, 0.62, 0.30, 0.25).grid_2d() == [620, 40, 870, 340]
        assert Box(0.30, 0.03, 0.40, 0.14).grid_2d() == [30, 300, 170, 700]

    def test_grid_2d_clamps_to_zero_thousand(self):
        assert Box(0.0, 0.0, 1.0, 1.0).grid_2d() == [0, 0, 1000, 1000]

    def test_pixel_bounds_high_res(self):
        assert Box(0.04, 0.62, 0.30, 0.25).pixel_bounds(1000, 1000) == (40, 620, 340, 870)

    def test_pixel_bounds_never_zero_width_at_low_res(self):
        x0, y0, x1, y1 = Box(0.0, 0.0, 0.006, 0.006).pixel_bounds(10, 10)
        assert x1 > x0 and y1 > y0

    def test_pixel_bounds_zero_extent_box_still_encloses_a_pixel(self):
        x0, y0, x1, y1 = Box(0.5, 0.5, 0.0, 0.0).pixel_bounds(8, 8)
        assert x1 == x0 + 1 and y1 == y0 + 1

    def test_pixel_bounds_at_right_edge_stays_in_frame(self):
        x0, y0, x1, y1 = Box(0.99, 0.0, 0.006, 0.5).pixel_bounds(10, 10)
        assert x0 < x1 <= 10 and y0 < y1 <= 10


class TestEditBy:
    def base_v2(self, **over):
        entry = {
            "id": "r_a", "kind": "object",
            "box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
            "content": {"desc": "a cat", "text": ""},
        }
        entry.update(over)
        return {"version": 2, "order": ["r_a"], "regions": [entry]}

    def test_defaults_to_node_in_v1(self):
        assert parse(V1_HAND_DRAWN)[0].edit_by == "node"

    def test_defaults_to_node_in_v2_when_absent(self):
        assert parse(self.base_v2())[0].edit_by == "node"

    def test_model_value_parsed(self):
        assert parse(self.base_v2(edit_by="model"))[0].edit_by == "model"

    def test_unknown_value_falls_back_to_node(self):
        assert parse(self.base_v2(edit_by="banana"))[0].edit_by == "node"

    def test_node_region_omits_edit_by(self):
        # Default stays out of the document so existing regions serialize byte-identically.
        out = serialize([parse(self.base_v2())[0]])
        assert "edit_by" not in out["regions"][0]

    def test_model_region_serializes_edit_by(self):
        out = serialize([parse(self.base_v2(edit_by="model"))[0]])
        assert out["regions"][0]["edit_by"] == "model"


class TestMarkers:
    def base_v2(self, **over):
        entry = {
            "id": "r_a", "kind": "object",
            "box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
            "content": {"desc": "a cat", "text": ""},
        }
        entry.update(over)
        return {"version": 2, "order": ["r_a"], "regions": [entry]}

    def test_defaults_on_in_v1(self):
        assert parse(V1_HAND_DRAWN)[0].markers is True

    def test_defaults_on_in_v2_when_absent(self):
        assert parse(self.base_v2())[0].markers is True

    def test_false_value_parsed(self):
        assert parse(self.base_v2(markers=False))[0].markers is False

    def test_on_region_omits_markers(self):
        # Default stays out so existing regions serialize byte-identically.
        out = serialize([parse(self.base_v2())[0]])
        assert "markers" not in out["regions"][0]

    def test_off_region_serializes_markers(self):
        out = serialize([parse(self.base_v2(markers=False))[0]])
        assert out["regions"][0]["markers"] is False

    def test_model_round_trips(self):
        once = parse(self.base_v2(edit_by="model"))
        twice = parse(serialize(once))
        assert twice[0].edit_by == "model"
