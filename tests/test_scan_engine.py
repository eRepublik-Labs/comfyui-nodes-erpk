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
from utils import scan_engine
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
            assert getattr(parsed[0].box, key) == pytest.approx(obj["box"][key])

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
        async def fake_engine(image, max_objects, model, segmenter=None):
            return [{"name": "stub", "max_objects": max_objects, "model": model}]

        result = asyncio.run(scan("IMG", max_objects=7, model="m", engine=fake_engine))
        assert result[0]["name"] == "stub"
        assert result[0]["max_objects"] == 7
        assert result[0]["model"] == "m"

    def test_default_engine_used_when_unset(self, monkeypatch):
        async def fake_default(image, max_objects, model, segmenter=None):
            return [{"name": "default", "max_objects": max_objects}]

        monkeypatch.setattr("utils.scan_engine.DEFAULT_ENGINE", fake_default)
        result = asyncio.run(scan("IMG"))
        assert result[0]["name"] == "default"
        assert result[0]["max_objects"] == 20

    def test_segmenter_is_forwarded_to_engine(self):
        seen = {}

        async def fake_engine(image, max_objects, model, segmenter=None):
            seen["segmenter"] = segmenter
            return []

        asyncio.run(scan("IMG", engine=fake_engine, segmenter="facebook/sam-vit-large"))
        assert seen["segmenter"] == "facebook/sam-vit-large"


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
            assert getattr(parsed[0].box, key) == pytest.approx(obj["box"][key])


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


class TestDownscaleMask:
    """Box-relative masks are capped on their longer side before encoding, then
    still decode and composite at the target box size."""

    def test_large_mask_is_capped(self):
        np = pytest.importorskip("numpy")
        pytest.importorskip("PIL")
        from utils.scan_engine import downscale_mask, MASK_ENCODE_MAX_SIDE
        out = downscale_mask(np.full((1000, 800), 255, dtype=np.uint8))
        assert max(out.shape) == MASK_ENCODE_MAX_SIDE  # longer side capped
        assert out.shape[0] == MASK_ENCODE_MAX_SIDE
        assert out.shape[1] < out.shape[0]             # aspect preserved

    def test_small_mask_is_not_upscaled(self):
        np = pytest.importorskip("numpy")
        pytest.importorskip("PIL")
        from utils.scan_engine import downscale_mask
        out = downscale_mask(np.full((100, 50), 255, dtype=np.uint8))
        assert out.shape == (100, 50)

    def test_downscaled_mask_encodes_smaller(self):
        np = pytest.importorskip("numpy")
        Image = pytest.importorskip("PIL.Image")
        import base64
        import io
        from utils.scan_engine import downscale_mask

        def encode(arr):
            buf = io.BytesIO()
            Image.fromarray(np.asarray(arr, dtype=np.uint8), mode="L").save(
                buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

        # A filled-disk silhouette, like a real segmentation: its encoded size
        # scales with the boundary, so capping the long side shrinks the PNG.
        yy, xx = np.ogrid[:1000, :1000]
        mask = (((yy - 500) ** 2 + (xx - 500) ** 2) < 400 ** 2).astype(np.uint8) * 255
        assert len(encode(downscale_mask(mask))) < len(encode(mask))

    def test_downscaled_mask_decodes_and_composites_at_box_size(self):
        np = pytest.importorskip("numpy")
        Image = pytest.importorskip("PIL.Image")
        pytest.importorskip("torch")
        import base64
        import io
        from utils.scan_engine import downscale_mask, MASK_ENCODE_MAX_SIDE
        from utils.region_contract import Box, Content, Mask, Region, Source
        from utils.regional_prompt import build_region_masks

        # A 900px silhouette, left half opaque. Capping shrinks it below 900px,
        # but the decoder resizes it back to the 30px box and keeps the split.
        glyph = np.zeros((900, 900), dtype=np.uint8)
        glyph[:, :450] = 255
        small = downscale_mask(glyph)
        assert max(small.shape) <= MASK_ENCODE_MAX_SIDE
        buf = io.BytesIO()
        Image.fromarray(small, mode="L").save(buf, format="PNG")
        data = base64.b64encode(buf.getvalue()).decode()
        scanned = Region(id="r", kind="object", box=Box(0.0, 0.0, 1.0, 1.0),
                         content=Content(),
                         source=Source(box=Box(0.0, 0.0, 1.0, 1.0),
                                       mask=Mask(data=data)))
        masks = build_region_masks([scanned], 30, 30)
        assert masks.shape == (1, 30, 30)
        assert float(masks[0, 15, 5]) == 1.0    # left half -> set
        assert float(masks[0, 15, 25]) == 0.0   # right half -> clear


class TestBuildCost:
    """build_cost sums per-call token usage and prices it for the scan response."""

    def test_sums_tokens_and_counts_calls(self):
        from utils.scan_engine import build_cost
        usages = [
            {"input_tokens": 1200, "output_tokens": 1500, "total_tokens": 2700},
            {"input_tokens": 1100, "output_tokens": 50, "total_tokens": 1150},
        ]
        cost = build_cost(usages, "gemini-2.5-flash")
        assert cost["input_tokens"] == 2300
        assert cost["output_tokens"] == 1550
        assert cost["calls"] == 2
        assert cost["model"] == "gemini-2.5-flash"
        # 2300/1e6*0.30 + 1550/1e6*2.50
        assert cost["usd"] == pytest.approx(2300 / 1e6 * 0.30 + 1550 / 1e6 * 2.5)

    def test_single_unreported_usage_is_unknown(self):
        from utils.scan_engine import build_cost
        # A call happened but reported no usage -> the total is unknown, so the
        # whole cost is None rather than billing that call as zero tokens.
        assert build_cost([None], "gemini-2.5-flash") is None

    def test_any_unreported_usage_is_unknown(self):
        from utils.scan_engine import build_cost
        # One reported call plus one unreported call still reads as unknown: the
        # reported tokens alone would undercount the scan.
        assert build_cost([{"input_tokens": 100, "output_tokens": 0,
                            "total_tokens": 100}, None], "gemini-2.5-flash") is None

    def test_all_unreported_usage_is_unknown(self):
        from utils.scan_engine import build_cost
        assert build_cost([None, None], "gemini-2.5-flash") is None

    def test_unknown_model_reports_tokens_but_no_usd(self):
        from utils.scan_engine import build_cost
        cost = build_cost([{"input_tokens": 500, "output_tokens": 500,
                            "total_tokens": 1000}], "totally-bogus-model")
        assert cost["usd"] is None
        assert cost["input_tokens"] == 500 and cost["output_tokens"] == 500


class TestBestMaskIndex:
    """best_mask_index picks the highest predicted-IoU hypothesis."""

    def test_picks_argmax(self):
        from utils.scan_engine import best_mask_index
        assert best_mask_index([0.1, 0.9, 0.5]) == 1

    def test_first_on_tie(self):
        from utils.scan_engine import best_mask_index
        assert best_mask_index([0.5, 0.5, 0.5]) == 0

    def test_empty_is_zero(self):
        from utils.scan_engine import best_mask_index
        assert best_mask_index([]) == 0


class TestIsSmallObject:
    """is_small_object flags boxes that benefit from a crop re-encode."""

    def test_small_box_is_small(self):
        from utils.scan_engine import is_small_object
        assert is_small_object({"x": 0.1, "y": 0.1, "w": 0.05, "h": 0.05})

    def test_large_box_is_not_small(self):
        from utils.scan_engine import is_small_object
        assert not is_small_object({"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.4})

    def test_threshold_is_strict(self):
        from utils.scan_engine import is_small_object, SMALL_OBJECT_MAX_EXTENT
        # A box whose larger side is exactly the threshold is not "small".
        box = {"x": 0.0, "y": 0.0, "w": SMALL_OBJECT_MAX_EXTENT, "h": 0.01}
        assert not is_small_object(box)

    def test_tall_thin_object_is_small_by_max_extent(self):
        from utils.scan_engine import is_small_object
        # Both sides small -> small, even if aspect is extreme.
        assert is_small_object({"x": 0.0, "y": 0.0, "w": 0.02, "h": 0.12})


class TestCleanMask:
    """clean_mask keeps the largest blob, fills holes, and softens edges."""

    def test_keeps_largest_component_and_fills_holes(self):
        np = pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        from utils.scan_engine import clean_mask
        mask = np.zeros((40, 40), dtype=np.uint8)
        mask[5:35, 5:35] = 1      # the object blob
        mask[18:22, 18:22] = 0    # a hole punched in it
        mask[0:2, 0:2] = 1        # a stray speckle in the corner
        out = clean_mask(mask, feather_sigma=0)
        assert out.dtype == np.uint8
        assert out[0, 0] == 0     # speckle dropped
        assert out[20, 20] == 255  # hole filled
        assert out[20, 6] == 255   # blob retained

    def test_all_zero_stays_zero(self):
        np = pytest.importorskip("numpy")
        from utils.scan_engine import clean_mask
        out = clean_mask(np.zeros((10, 10), dtype=np.uint8))
        assert out.max() == 0

    def test_feather_introduces_soft_edge_values(self):
        np = pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        from utils.scan_engine import clean_mask
        mask = np.zeros((40, 40), dtype=np.uint8)
        mask[10:30, 10:30] = 1
        out = clean_mask(mask, feather_sigma=1.5)
        # Feathering yields intermediate alpha, not a pure 0/255 mask.
        assert ((out > 0) & (out < 255)).any()

    def test_degrades_without_scipy(self, monkeypatch):
        np = pytest.importorskip("numpy")
        from utils import scan_engine
        # Simulate scipy being absent: clean_mask must still return a binary
        # mask rather than raise, so the scan survives on a bare-numpy host.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "scipy" or name.startswith("scipy."):
                raise ImportError("no scipy")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        mask = np.zeros((20, 20), dtype=np.uint8)
        mask[5:15, 5:15] = 1
        out = scan_engine.clean_mask(mask, feather_sigma=1.0)
        assert out.max() == 255 and out.min() == 0


class TestSegmenterRegistry:
    """The SEGMENTERS registry lists selectable backbones; vit-base is default."""

    def test_default_is_vit_base(self):
        from utils.scan_engine import DEFAULT_SEGMENTER
        assert DEFAULT_SEGMENTER == "facebook/sam-vit-base"

    def test_default_is_first_entry(self):
        from utils.scan_engine import SEGMENTERS, DEFAULT_SEGMENTER
        assert SEGMENTERS[0]["id"] == DEFAULT_SEGMENTER

    def test_registry_covers_three_families(self):
        from utils.scan_engine import SEGMENTERS
        assert {s["family"] for s in SEGMENTERS} == {"sam1", "samhq", "sam2"}

    def test_entries_have_required_fields(self):
        from utils.scan_engine import SEGMENTERS
        for spec in SEGMENTERS:
            assert {"id", "label", "family"} <= set(spec)
            assert spec["family"] in ("sam1", "samhq", "sam2")


class TestResolveSegmenter:
    """resolve_segmenter falls back to the default for unknown/blank ids."""

    def test_known_passes_through(self):
        from utils.scan_engine import resolve_segmenter
        assert resolve_segmenter("facebook/sam-vit-large") == "facebook/sam-vit-large"

    def test_unknown_falls_back(self):
        from utils.scan_engine import resolve_segmenter, DEFAULT_SEGMENTER
        assert resolve_segmenter("bogus/model") == DEFAULT_SEGMENTER

    def test_none_and_blank_fall_back(self):
        from utils.scan_engine import resolve_segmenter, DEFAULT_SEGMENTER
        assert resolve_segmenter(None) == DEFAULT_SEGMENTER
        assert resolve_segmenter("  ") == DEFAULT_SEGMENTER


class TestAvailableSegmenters:
    """available_segmenters keeps only families whose transformers classes import."""

    def _fake_tf(self, names):
        import types as _t
        ns = _t.SimpleNamespace()
        for n in names:
            setattr(ns, n, object)
        return ns

    def test_sam1_only_when_only_sam_classes(self):
        from utils.scan_engine import available_segmenters
        tf = self._fake_tf(["SamModel", "SamProcessor"])
        fams = {s["family"] for s in available_segmenters(tf=tf)}
        assert fams == {"sam1"}

    def test_all_families_when_all_classes_present(self):
        from utils.scan_engine import available_segmenters
        tf = self._fake_tf([
            "SamModel", "SamProcessor", "SamHQModel", "SamHQProcessor",
            "Sam2Model", "Sam2Processor",
        ])
        fams = {s["family"] for s in available_segmenters(tf=tf)}
        assert fams == {"sam1", "samhq", "sam2"}

    def test_entries_flag_downloaded(self):
        from utils.scan_engine import available_segmenters
        tf = self._fake_tf(["SamModel", "SamProcessor"])
        for s in available_segmenters(tf=tf):
            assert "downloaded" in s and isinstance(s["downloaded"], bool)

    def test_no_transformers_yields_empty(self, monkeypatch):
        from utils import scan_engine
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "transformers":
                raise ImportError("no transformers")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert scan_engine.available_segmenters() == []


class TestFlorenceMalformedLabels:
    """A malformed labels array keeps the boxes, mirroring parse_segmentation."""

    def test_missing_labels_keep_boxes_with_blank_names(self):
        od = {"<OD>": {"bboxes": [[10, 10, 200, 200], [300, 300, 500, 500]],
                       "labels": "not a list"}}
        objects = florence_to_objects(od, 1000, 1000, 20)
        assert len(objects) == 2
        assert all(obj["name"] == "" for obj in objects)


class TestGeminiScanOffloadsSegmentation:
    """The SAM stage runs off the event-loop thread so it never stalls aiohttp.

    gemini_scan does a relative `..gemini` import, so it is driven through the
    synthetic `erpk` package (conftest) where that import resolves, mirroring how
    the Gemini-touching modules are exercised elsewhere.
    """

    class _FakeClient:
        MODELS = ["gemini-2.5-flash"]
        DEFAULT_MODEL = "gemini-2.5-flash"

        def __init__(self, api_key=None):
            self._calls = 0

        async def generate_content(self, prompt, images=None, **kwargs):
            self._calls += 1
            if self._calls == 1:
                text = json.dumps([{"box_2d": [100, 200, 500, 600],
                                    "label": "cat", "description": "a cat"}])
            else:
                text = json.dumps({"order": ["cat"]})
            return {"text": text,
                    "usage": {"input_tokens": 1, "output_tokens": 1,
                              "total_tokens": 2}}

    def test_segment_objects_runs_on_worker_thread(self, monkeypatch):
        import threading
        import erpk.gemini.gemini_api.client as gemini_client_module
        from erpk.utils import scan_engine as erpk_scan_engine

        monkeypatch.setattr(gemini_client_module, "GeminiClient", self._FakeClient)

        recorded = {}

        def fake_segment(image, objects, segmenter=None):
            recorded["on_main"] = (threading.current_thread()
                                   is threading.main_thread())

        monkeypatch.setattr(erpk_scan_engine, "segment_objects", fake_segment)

        asyncio.run(erpk_scan_engine.gemini_scan("IMG", 5, "gemini-2.5-flash"))
        assert recorded["on_main"] is False


class TestCacheInitLock:
    """Concurrent first loads of a cache load the backbone exactly once.

    Each loader is replaced with a counting stub that sleeps to widen the race
    window; without the per-cache lock every thread would see the empty cache and
    load, so a count of one proves the lock serializes the check-then-populate.
    """

    def _hammer(self, target):
        import threading

        barrier = threading.Barrier(8)

        def run():
            barrier.wait()
            target()

        threads = [threading.Thread(target=run) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def test_segmenter_loads_once(self, monkeypatch):
        import time

        scan_engine._segmenter.clear()
        calls = []

        def fake_load(model_id, family, torch):
            calls.append(model_id)
            time.sleep(0.02)
            return {"processor": object(), "model": object(),
                    "device": "cpu", "family": family}

        monkeypatch.setattr(scan_engine, "_load_segmenter", fake_load)
        try:
            self._hammer(lambda: scan_engine._get_segmenter("id", "sam1", None))
            assert len(calls) == 1
        finally:
            scan_engine._segmenter.clear()

    def test_florence_loads_once(self, monkeypatch):
        import time

        scan_engine._florence.clear()
        calls = []

        def fake_load():
            calls.append(1)
            time.sleep(0.02)
            return {"processor": object(), "model": object(), "device": "cpu"}

        monkeypatch.setattr(scan_engine, "_load_florence", fake_load)
        try:
            self._hammer(scan_engine._florence_models)
            assert len(calls) == 1
        finally:
            scan_engine._florence.clear()

    def test_depth_loads_once(self, monkeypatch):
        import time

        scan_engine._depth.clear()
        calls = []

        def fake_load():
            calls.append(1)
            time.sleep(0.02)
            return {"processor": object(), "model": object(), "device": "cpu"}

        monkeypatch.setattr(scan_engine, "_load_depth", fake_load)
        try:
            self._hammer(scan_engine._depth_models)
            assert len(calls) == 1
        finally:
            scan_engine._depth.clear()
