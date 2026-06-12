# ABOUTME: Tests for the pluggable scan engine's torch-free parse/clamp/rank helpers.
# ABOUTME: Covers detection parsing, depth ranking, and engine dispatch.

"""
Validates utils.scan_engine's pure helpers (parse_detection, strip_data_url,
parse_depth_order, apply_depth_ranks) and the engine dispatch indirection. The
Gemini engine itself hits the network and is exercised only via dispatch with an
injected fake coroutine, mirroring the torch/genai-free testing constraint.
"""

import asyncio
import json
import math

import pytest

from utils.scan_engine import (
    DEFAULT_ENGINE,
    DEPTH_SCHEMA,
    DETECTION_SCHEMA,
    MIN_REGION_EXTENT as ENGINE_MIN_REGION_EXTENT,
    apply_depth_ranks,
    detection_prompt,
    depth_prompt,
    depth_ranks,
    florence_to_objects,
    gemini_scan,
    local_scan,
    parse_depth_order,
    parse_detection,
    pixel_box_prompts,
    resolve_model,
    scan,
)
from utils.regional_prompt import MIN_REGION_EXTENT


class TestSchemas:
    """The structured-output schemas match the depth and detection contracts.

    The detection call asks for boxes, labels, and one-sentence descriptions
    with a response schema (Gemini supplies no masks here, so structured output
    is safe); parse_detection still validates defensively.
    """

    def test_depth_schema_shape(self):
        assert DEPTH_SCHEMA["type"] == "OBJECT"
        assert DEPTH_SCHEMA["properties"]["order"]["type"] == "ARRAY"
        assert DEPTH_SCHEMA["required"] == ["order"]

    def test_detection_schema_shape(self):
        assert DETECTION_SCHEMA["type"] == "ARRAY"
        item = DETECTION_SCHEMA["items"]
        assert item["type"] == "OBJECT"
        assert item["properties"]["box_2d"]["type"] == "ARRAY"
        assert item["properties"]["box_2d"]["items"]["type"] == "INTEGER"
        assert item["properties"]["label"]["type"] == "STRING"
        assert item["properties"]["description"]["type"] == "STRING"
        assert item["required"] == ["box_2d", "label", "description"]


class TestDetectionPrompt:
    """The detection request prompt names the box grid, label, description, cap."""

    def test_mentions_grid_label_description_and_cap(self):
        prompt = detection_prompt(20)
        assert "box_2d" in prompt
        assert "0-1000" in prompt
        assert "label" in prompt.lower()
        assert "description" in prompt.lower()
        assert "at most 20" in prompt


class TestParseDetection:
    """parse_detection normalizes, clamps, drops degenerate, captions, and caps."""

    def test_single_object(self):
        payload = ('[{"box_2d":[100,200,500,600],"label":"red car",'
                   '"description":"a red car parked on the street"}]')
        objects = parse_detection(payload, 20)
        assert len(objects) == 1
        obj = objects[0]
        assert obj["name"] == "red car"
        assert obj["group"] == "red car"
        assert obj["mask"] is None
        assert obj["caption"] == "a red car parked on the street"
        assert obj["box"]["x"] == pytest.approx(0.2)
        assert obj["box"]["y"] == pytest.approx(0.1)
        assert obj["box"]["w"] == pytest.approx(0.4)
        assert obj["box"]["h"] == pytest.approx(0.4)

    def test_mask_is_always_none(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x","description":"thing"}]'
        assert parse_detection(payload, 20)[0]["mask"] is None

    def test_markdown_fenced_json_is_unwrapped(self):
        payload = ('```json\n'
                   '[{"box_2d":[100,200,500,600],"label":"red car",'
                   '"description":"a red car"}]\n'
                   '```')
        objects = parse_detection(payload, 20)
        assert len(objects) == 1
        assert objects[0]["name"] == "red car"

    def test_missing_description_is_blank_caption(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x"}]'
        assert parse_detection(payload, 20)[0]["caption"] == ""

    def test_nonstring_description_is_blank_caption(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x","description":7}]'
        assert parse_detection(payload, 20)[0]["caption"] == ""

    def test_caption_is_stripped(self):
        payload = ('[{"box_2d":[0,0,400,400],"label":"x",'
                   '"description":"  a cat  "}]')
        assert parse_detection(payload, 20)[0]["caption"] == "a cat"

    def test_clamp_and_swap(self):
        payload = '[{"box_2d":[-50,1100,2000,-10],"label":"thing","description":"d"}]'
        for obj in parse_detection(payload, 20):
            box = obj["box"]
            for key in ("x", "y", "w", "h"):
                assert 0.0 <= box[key] <= 1.0
            assert box["x"] + box["w"] <= 1.0 + 1e-9
            assert box["y"] + box["h"] <= 1.0 + 1e-9

    def test_drop_degenerate_height(self):
        payload = '[{"box_2d":[100,100,101,800],"label":"sliver","description":"d"}]'
        assert parse_detection(payload, 20) == []

    def test_drop_zero_width(self):
        payload = '[{"box_2d":[100,300,500,300],"label":"line","description":"d"}]'
        assert parse_detection(payload, 20) == []

    def test_max_objects_cap(self):
        boxes = [{"box_2d": [0, 0, 500, 500], "label": f"o{i}", "description": "d"}
                 for i in range(5)]
        assert len(parse_detection(json.dumps(boxes), 3)) == 3

    def test_empty_list(self):
        assert parse_detection("[]", 20) == []

    def test_malformed_json_returns_empty(self):
        assert parse_detection("not json", 20) == []

    def test_non_list_returns_empty(self):
        assert parse_detection('{"box_2d":[0,0,500,500]}', 20) == []

    def test_missing_label_is_blank(self):
        payload = ('[{"box_2d":[100,200,500,600]},'
                   '{"box_2d":[0,0,400,400],"label":7}]')
        objects = parse_detection(payload, 20)
        assert all(obj["name"] == "" and obj["group"] == "" for obj in objects)

    def test_box_round_trips_through_parse_regions(self):
        from utils.regional_prompt import parse_regions

        payload = ('[{"box_2d":[100,200,500,600],"label":"cat",'
                   '"description":"a cat"}]')
        obj = parse_detection(payload, 20)[0]
        region = {"kind": "object", "desc": obj["caption"], **obj["box"]}
        parsed = parse_regions(json.dumps([region]))
        assert len(parsed) == 1
        for key in ("x", "y", "w", "h"):
            assert parsed[0][key] == pytest.approx(obj["box"][key])

    def test_min_region_extent_is_contract_value(self):
        assert ENGINE_MIN_REGION_EXTENT == MIN_REGION_EXTENT == 0.005


class TestDepthPrompt:
    """depth_prompt lists the labels and frames the back-to-front ordering."""

    def test_lists_labels_and_direction(self):
        prompt = depth_prompt(["car", "tree"])
        assert "car" in prompt and "tree" in prompt
        assert "background" in prompt.lower()
        assert "foreground" in prompt.lower()

    def test_references_the_image(self):
        # The ranking call sends the image; the prompt must anchor the
        # ordering to the depicted scene, not label semantics.
        assert "image" in depth_prompt(["car"]).lower()


class TestResolveModel:
    """resolve_model falls back to the default for unknown or missing names."""

    def test_none_uses_default(self):
        assert resolve_model(None, {"a", "b"}, "a") == "a"

    def test_known_model_passes_through(self):
        assert resolve_model("b", {"a", "b"}, "a") == "b"

    def test_unknown_model_uses_default(self):
        assert resolve_model("totally-bogus-model", {"a", "b"}, "a") == "a"

    def test_real_client_models_accept_their_default(self):
        from gemini.gemini_api.client import GeminiClient
        assert (resolve_model(GeminiClient.DEFAULT_MODEL, GeminiClient.MODELS,
                              GeminiClient.DEFAULT_MODEL)
                == GeminiClient.DEFAULT_MODEL)


class TestParseDepthOrder:
    """parse_depth_order maps labels to back-to-front ranks."""

    def test_basic_order(self):
        rank_map = parse_depth_order('{"order":["sky","tree","car"]}', ["car", "tree", "sky"])
        assert rank_map["sky"] == 0
        assert rank_map["tree"] == 1
        assert rank_map["car"] == 2

    def test_missing_labels_appended_after_known(self):
        # "car" omitted by the model -> sorts after ranked labels (frontmost).
        rank_map = parse_depth_order('{"order":["sky","tree"]}', ["car", "tree", "sky"])
        assert rank_map["sky"] == 0
        assert rank_map["tree"] == 1
        assert rank_map["car"] == 2

    def test_unknown_labels_in_order_ignored(self):
        rank_map = parse_depth_order('{"order":["ghost","car"]}', ["car"])
        assert rank_map == {"car": 0}

    def test_malformed_returns_input_order(self):
        rank_map = parse_depth_order("oops", ["a", "b"])
        assert rank_map == {"a": 0, "b": 1}

    def test_missing_order_key(self):
        rank_map = parse_depth_order('{"nope":[]}', ["a", "b"])
        assert rank_map == {"a": 0, "b": 1}


class TestApplyDepthRanks:
    """apply_depth_ranks tags objects and stably sorts back-to-front."""

    def test_sets_rank_and_sorts(self):
        objects = [
            {"name": "a", "group": "car", "box": {}},
            {"name": "b", "group": "sky", "box": {}},
        ]
        rank_map = {"sky": 0, "car": 1}
        result = apply_depth_ranks(objects, rank_map)
        assert [o["name"] for o in result] == ["b", "a"]
        assert result[0]["depth_rank"] == 0
        assert result[1]["depth_rank"] == 1

    def test_same_group_keeps_input_order(self):
        objects = [
            {"name": "a", "group": "car", "box": {}},
            {"name": "b", "group": "car", "box": {}},
        ]
        result = apply_depth_ranks(objects, {"car": 0})
        assert [o["name"] for o in result] == ["a", "b"]

    def test_unranked_group_defaults_to_zero(self):
        objects = [{"name": "a", "group": "mystery", "box": {}}]
        result = apply_depth_ranks(objects, {})
        assert result[0]["depth_rank"] == 0


class TestScanDispatch:
    """scan() routes to the injected engine (the Moondream plug-in point)."""

    def test_engine_argument_is_called(self):
        async def fake_engine(image, max_objects, model):
            return [{"name": "stub", "max_objects": max_objects, "model": model}]

        result = asyncio.run(scan("IMG", max_objects=7, model="m", engine=fake_engine))
        assert result[0]["name"] == "stub"
        assert result[0]["max_objects"] == 7
        assert result[0]["model"] == "m"

    def test_default_engine_used_when_unset(self, monkeypatch):
        async def fake_default(image, max_objects, model):
            return [{"name": "default", "max_objects": max_objects}]

        monkeypatch.setattr("utils.scan_engine.DEFAULT_ENGINE", fake_default)
        result = asyncio.run(scan("IMG"))
        assert result[0]["name"] == "default"
        assert result[0]["max_objects"] == 20


class TestFlorenceToObjects:
    """florence_to_objects normalizes Florence-2 <OD> pixel boxes into scan dicts."""

    def _od(self, bboxes, labels):
        return {"<OD>": {"bboxes": bboxes, "labels": labels}}

    def test_single_object(self):
        result = self._od([[100, 200, 500, 600]], ["red car"])
        objects = florence_to_objects(result, 1000, 1000, 20)
        assert len(objects) == 1
        obj = objects[0]
        assert obj["name"] == "red car"
        assert obj["group"] == "red car"
        assert obj["mask"] is None
        assert obj["caption"] == ""
        assert obj["box"]["x"] == pytest.approx(0.1)
        assert obj["box"]["y"] == pytest.approx(0.2)
        assert obj["box"]["w"] == pytest.approx(0.4)
        assert obj["box"]["h"] == pytest.approx(0.4)

    def test_real_spike_boxes(self):
        # The live <OD> result on /tmp/erpk_scan_1k.jpg (688x1024).
        result = self._od(
            [[345.72, 398.85, 498.46, 622.08], [115.24, 355.84, 531.48, 1022.46]],
            ["human face", "man"],
        )
        objects = florence_to_objects(result, 688, 1024, 20)
        assert [o["name"] for o in objects] == ["human face", "man"]
        for obj in objects:
            box = obj["box"]
            assert 0.0 <= box["x"] <= 1.0 and 0.0 <= box["y"] <= 1.0
            assert box["w"] > MIN_REGION_EXTENT and box["h"] > MIN_REGION_EXTENT

    def test_clamps_out_of_frame(self):
        result = self._od([[-50, -50, 2000, 2000]], ["thing"])
        box = florence_to_objects(result, 1000, 1000, 20)[0]["box"]
        for key in ("x", "y", "w", "h"):
            assert 0.0 <= box[key] <= 1.0
        assert box["x"] + box["w"] <= 1.0 + 1e-9
        assert box["y"] + box["h"] <= 1.0 + 1e-9

    def test_swaps_inverted_corners(self):
        result = self._od([[500, 600, 100, 200]], ["thing"])
        box = florence_to_objects(result, 1000, 1000, 20)[0]["box"]
        assert box["x"] == pytest.approx(0.1)
        assert box["y"] == pytest.approx(0.2)
        assert box["w"] == pytest.approx(0.4)
        assert box["h"] == pytest.approx(0.4)

    def test_drops_degenerate_box(self):
        result = self._od([[100, 100, 101, 800]], ["sliver"])
        assert florence_to_objects(result, 1000, 1000, 20) == []

    def test_caps_max_objects(self):
        bboxes = [[0, 0, 500, 500] for _ in range(5)]
        labels = [f"o{i}" for i in range(5)]
        assert len(florence_to_objects(self._od(bboxes, labels), 1000, 1000, 3)) == 3

    def test_non_numeric_box_skipped(self):
        result = self._od([["x", 0, 500, 500], [0, 0, 500, 500]], ["bad", "good"])
        objects = florence_to_objects(result, 1000, 1000, 20)
        assert [o["name"] for o in objects] == ["good"]

    def test_non_finite_box_skipped(self):
        result = self._od([[0, 0, float("inf"), 500]], ["bad"])
        assert florence_to_objects(result, 1000, 1000, 20) == []

    def test_non_string_label_is_blank(self):
        result = self._od([[0, 0, 500, 500]], [7])
        obj = florence_to_objects(result, 1000, 1000, 20)[0]
        assert obj["name"] == "" and obj["group"] == ""

    def test_missing_od_key_returns_empty(self):
        assert florence_to_objects({}, 1000, 1000, 20) == []

    def test_empty_detection_returns_empty(self):
        assert florence_to_objects(self._od([], []), 1000, 1000, 20) == []

    def test_box_round_trips_through_parse_regions(self):
        from utils.regional_prompt import parse_regions

        obj = florence_to_objects(self._od([[100, 200, 500, 600]], ["cat"]),
                                  1000, 1000, 20)[0]
        region = {"kind": "object", "desc": obj["name"], **obj["box"]}
        parsed = parse_regions(json.dumps([region]))
        assert len(parsed) == 1
        for key in ("x", "y", "w", "h"):
            assert parsed[0][key] == pytest.approx(obj["box"][key])


class TestDepthRanks:
    """depth_ranks ranks by measured median (larger = nearer, rank 0 = farthest)."""

    def _objs(self, names):
        return [{"name": n, "group": n, "box": {}} for n in names]

    def test_orders_smallest_median_first(self):
        objects = self._objs(["a", "b", "c"])
        result = depth_ranks(objects, [4.0, 0.0, 2.0])
        assert [o["name"] for o in result] == ["b", "c", "a"]
        assert [o["depth_rank"] for o in result] == [0, 1, 2]

    def test_none_median_sorts_as_farthest(self):
        objects = self._objs(["a", "b"])
        result = depth_ranks(objects, [None, 3.0])
        assert [o["name"] for o in result] == ["a", "b"]
        assert result[0]["depth_rank"] == 0

    def test_multiple_none_preserve_input_order(self):
        objects = self._objs(["a", "b", "c"])
        result = depth_ranks(objects, [None, 5.0, None])
        assert [o["name"] for o in result] == ["a", "c", "b"]

    def test_equal_medians_keep_input_order(self):
        objects = self._objs(["a", "b"])
        result = depth_ranks(objects, [2.0, 2.0])
        assert [o["name"] for o in result] == ["a", "b"]

    def test_empty(self):
        assert depth_ranks([], []) == []


class TestDefaultEngine:
    """The default engine is Gemini-first; the local pipeline stays opt-in."""

    def test_default_engine_is_gemini(self):
        assert DEFAULT_ENGINE is gemini_scan


class TestPixelBoxPrompts:
    """Normalized scan boxes become integer pixel prompts for the segmenter."""

    def test_converts_and_rounds(self):
        objects = [{"name": "car", "group": "car", "mask": None,
                    "box": {"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.25}}]
        assert pixel_box_prompts(objects, 1000, 800) == [[100, 160, 600, 360]]

    def test_clamps_to_frame(self):
        objects = [{"name": "x", "group": "x", "mask": None,
                    "box": {"x": 0.9, "y": 0.9, "w": 0.1, "h": 0.1}}]
        assert pixel_box_prompts(objects, 100, 100) == [[90, 90, 100, 100]]

    def test_degenerate_box_keeps_one_pixel(self):
        objects = [{"name": "x", "group": "x", "mask": None,
                    "box": {"x": 0.5, "y": 0.5, "w": 0.001, "h": 0.001}}]
        x0, y0, x1, y1 = pixel_box_prompts(objects, 100, 100)[0]
        assert x1 > x0 and y1 > y0


class TestFlorenceMalformedLabels:
    """A malformed labels array keeps the boxes, mirroring parse_segmentation."""

    def test_missing_labels_keep_boxes_with_blank_names(self):
        od = {"<OD>": {"bboxes": [[10, 10, 200, 200], [300, 300, 500, 500]],
                       "labels": "not a list"}}
        objects = florence_to_objects(od, 1000, 1000, 20)
        assert len(objects) == 2
        assert all(obj["name"] == "" for obj in objects)
