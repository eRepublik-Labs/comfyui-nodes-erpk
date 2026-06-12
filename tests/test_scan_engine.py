# ABOUTME: Tests for the pluggable scan engine's torch-free parse/clamp/rank helpers.
# ABOUTME: Covers segmentation parsing, mask data-URL stripping, depth ranking, and engine dispatch.

"""
Validates utils.scan_engine's pure helpers (parse_segmentation, strip_data_url,
parse_depth_order, apply_depth_ranks) and the engine dispatch indirection. The
Gemini engine itself hits the network and is exercised only via dispatch with an
injected fake coroutine, mirroring the torch/genai-free testing constraint.
"""

import asyncio
import json
import math

import pytest

from utils.scan_engine import (
    DEPTH_SCHEMA,
    MIN_REGION_EXTENT as ENGINE_MIN_REGION_EXTENT,
    SEGMENTATION_SCHEMA,
    apply_depth_ranks,
    depth_prompt,
    parse_depth_order,
    parse_segmentation,
    resolve_model,
    scan,
    segmentation_prompt,
    strip_data_url,
)
from utils.regional_prompt import MIN_REGION_EXTENT


class TestSchemas:
    """The structured-output schemas match the segmentation/depth contract."""

    def test_segmentation_schema_shape(self):
        assert SEGMENTATION_SCHEMA["type"] == "ARRAY"
        props = SEGMENTATION_SCHEMA["items"]["properties"]
        assert set(props) == {"box_2d", "label", "mask"}
        # mask is tolerated-missing so models that omit it still validate.
        assert SEGMENTATION_SCHEMA["items"]["required"] == ["box_2d", "label"]

    def test_depth_schema_shape(self):
        assert DEPTH_SCHEMA["type"] == "OBJECT"
        assert DEPTH_SCHEMA["properties"]["order"]["type"] == "ARRAY"
        assert DEPTH_SCHEMA["required"] == ["order"]


class TestStripDataUrl:
    """strip_data_url returns prefix-free base64 or None."""

    def test_plain_base64_passthrough(self):
        assert strip_data_url("iVBORw0K") == "iVBORw0K"

    def test_strips_data_url_prefix(self):
        assert strip_data_url("data:image/png;base64,iVBORw0K") == "iVBORw0K"

    def test_strips_arbitrary_image_mime(self):
        assert strip_data_url("data:image/webp;base64,QUJD") == "QUJD"

    def test_none_for_non_string(self):
        assert strip_data_url(None) is None
        assert strip_data_url(123) is None

    def test_none_for_empty(self):
        assert strip_data_url("") is None
        assert strip_data_url("   ") is None

    def test_none_for_prefix_without_comma(self):
        assert strip_data_url("data:image/png;base64") is None


class TestSegmentationPrompt:
    """The segmentation request prompt names the box grid, label, mask, and cap."""

    def test_mentions_grid_label_mask_and_cap(self):
        prompt = segmentation_prompt(20)
        assert "box_2d" in prompt
        assert "0-1000" in prompt
        assert "mask" in prompt.lower()
        assert "at most 20" in prompt


class TestParseSegmentation:
    """parse_segmentation normalizes, clamps, drops degenerate, and caps."""

    def test_single_object(self):
        payload = '[{"box_2d":[100,200,500,600],"label":"red car","mask":"QUJD"}]'
        objects = parse_segmentation(payload, 20)
        assert len(objects) == 1
        obj = objects[0]
        assert obj["name"] == "red car"
        assert obj["group"] == "red car"
        assert obj["mask"] == "QUJD"
        assert obj["box"]["x"] == pytest.approx(0.2)
        assert obj["box"]["y"] == pytest.approx(0.1)
        assert obj["box"]["w"] == pytest.approx(0.4)
        assert obj["box"]["h"] == pytest.approx(0.4)

    def test_mask_data_url_is_stripped(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x","mask":"data:image/png;base64,QUJD"}]'
        assert parse_segmentation(payload, 20)[0]["mask"] == "QUJD"

    def test_missing_mask_is_none(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x"}]'
        assert parse_segmentation(payload, 20)[0]["mask"] is None

    def test_nonstring_mask_is_none(self):
        payload = '[{"box_2d":[0,0,400,400],"label":"x","mask":7}]'
        assert parse_segmentation(payload, 20)[0]["mask"] is None

    def test_clamp_and_swap(self):
        payload = '[{"box_2d":[-50,1100,2000,-10],"label":"thing"}]'
        for obj in parse_segmentation(payload, 20):
            box = obj["box"]
            for key in ("x", "y", "w", "h"):
                assert 0.0 <= box[key] <= 1.0
            assert box["x"] + box["w"] <= 1.0 + 1e-9
            assert box["y"] + box["h"] <= 1.0 + 1e-9

    def test_drop_degenerate_height(self):
        payload = '[{"box_2d":[100,100,101,800],"label":"sliver"}]'
        assert parse_segmentation(payload, 20) == []

    def test_drop_zero_width(self):
        payload = '[{"box_2d":[100,300,500,300],"label":"line"}]'
        assert parse_segmentation(payload, 20) == []

    def test_max_objects_cap(self):
        boxes = [{"box_2d": [0, 0, 500, 500], "label": f"o{i}"} for i in range(5)]
        assert len(parse_segmentation(json.dumps(boxes), 3)) == 3

    def test_empty_list(self):
        assert parse_segmentation("[]", 20) == []

    def test_malformed_json_returns_empty(self):
        assert parse_segmentation("not json", 20) == []

    def test_non_list_returns_empty(self):
        assert parse_segmentation('{"box_2d":[0,0,500,500]}', 20) == []

    def test_missing_label_is_blank(self):
        payload = '[{"box_2d":[100,200,500,600]},{"box_2d":[0,0,400,400],"label":7}]'
        objects = parse_segmentation(payload, 20)
        assert all(obj["name"] == "" and obj["group"] == "" for obj in objects)

    def test_box_round_trips_through_parse_regions(self):
        from utils.regional_prompt import parse_regions

        payload = '[{"box_2d":[100,200,500,600],"label":"cat","mask":"QUJD"}]'
        obj = parse_segmentation(payload, 20)[0]
        region = {"kind": "object", "desc": obj["name"], **obj["box"]}
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
