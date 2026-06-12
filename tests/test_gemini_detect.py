# ABOUTME: Tests for the GeminiDetect node and its pure detections_to_regions parser.
# ABOUTME: Covers schema/structure, seed fingerprint, clamping/drop math, and the ERPK_REGIONS contract.

"""
Validates GeminiDetect: V3 structural compliance, the ERPK_REGIONS output
contract, seed-gated cache busting, and the torch-free detections_to_regions
helper (parse, clamp, swap, drop-degenerate, cap). The parser is tested with
real JSON payloads and round-tripped through utils.regional_prompt.parse_regions
to prove the emitted dicts are exactly what the builder accepts.
"""

import inspect
import json
import math

import pytest

IO = pytest.importorskip("comfy_api.latest").IO

from gemini.nodes import GeminiDetect, detection_prompt, detections_to_regions
from gemini.nodes import MIN_REGION_EXTENT as DETECT_MIN_REGION_EXTENT
from gemini.gemini_api.client import GeminiClient
from utils.regional_prompt import MIN_REGION_EXTENT, parse_regions


class TestGeminiDetectStructure:
    """GeminiDetect complies with the V3 node API."""

    def test_inherits_comfy_node(self):
        assert issubclass(GeminiDetect, IO.ComfyNode)

    def test_schema_identity(self):
        schema = GeminiDetect.define_schema()
        assert schema.node_id == "GeminiDetect"
        assert schema.display_name == "Gemini Detect"
        assert schema.category == "ERPK/Gemini"
        assert schema.not_idempotent is True
        assert schema.is_output_node is False

    def test_execute_is_classmethod_coroutine(self):
        assert isinstance(inspect.getattr_static(GeminiDetect, "execute"), classmethod)
        assert inspect.iscoroutinefunction(GeminiDetect.execute.__func__)


class TestGeminiDetectSchemaIO:
    """Schema inputs and the single ERPK_REGIONS output match the contract."""

    def test_single_regions_output(self):
        schema = GeminiDetect.define_schema()
        assert len(schema.outputs) == 1
        out = schema.outputs[0]
        assert out.io_type == "ERPK_REGIONS"
        assert out.id == "regions"

    def test_required_image_input(self):
        schema = GeminiDetect.define_schema()
        image = next(i for i in schema.inputs if i.id == "image")
        assert image.io_type == "IMAGE"
        assert not image.optional

    def test_required_objects_input(self):
        schema = GeminiDetect.define_schema()
        objects = next(i for i in schema.inputs if i.id == "objects")
        assert objects.io_type == "STRING"
        assert objects.multiline is True
        assert not objects.optional

    def test_optional_client_input(self):
        schema = GeminiDetect.define_schema()
        client = next(i for i in schema.inputs if i.id == "client")
        assert client.io_type == "GEMINI_API_CLIENT"
        assert client.optional is True

    def test_model_combo_options(self):
        schema = GeminiDetect.define_schema()
        model = next(i for i in schema.inputs if i.id == "model")
        assert set(model.options) == set(GeminiClient.MODELS.keys())
        assert model.default == GeminiClient.DEFAULT_MODEL

    def test_max_objects_and_seed(self):
        schema = GeminiDetect.define_schema()
        max_objects = next(i for i in schema.inputs if i.id == "max_objects")
        assert max_objects.io_type == "INT"
        seed = next(i for i in schema.inputs if i.id == "seed")
        assert seed.io_type == "INT"
        assert seed.control_after_generate is not None


class TestGeminiDetectFingerprint:
    """Seed-gated fingerprint busts cache on randomize, caches on fixed seed."""

    def test_random_seed_is_nan(self):
        result = GeminiDetect.fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result)

    def test_fixed_seed_returns_seed(self):
        assert GeminiDetect.fingerprint_inputs(seed=42) == 42


class TestDetectionPrompt:
    """Prompt assembly for the detection request."""

    def test_named_objects_restrict_to_the_list(self):
        prompt = detection_prompt("wizard hat\nsunglasses", 20)
        assert "Detect the following objects in the image: wizard hat, sunglasses." in prompt
        assert "Only include objects from the list" in prompt
        assert "at most 20 instances" in prompt

    def test_empty_objects_detect_everything_without_list_restriction(self):
        prompt = detection_prompt("", 15)
        assert "Detect all prominent objects in the image." in prompt
        assert "from the list" not in prompt
        assert "at most 15 instances" in prompt

    def test_blank_lines_are_ignored(self):
        prompt = detection_prompt("\n  \n", 20)
        assert "Detect all prominent objects in the image." in prompt
        assert "from the list" not in prompt


class TestDetectionsToRegions:
    """The pure parser converts box_2d detections into normalized region dicts."""

    def test_single_box(self):
        payload = '[{"box_2d":[100,200,500,600],"label":"cat"}]'
        regions = detections_to_regions(payload, 20)
        assert len(regions) == 1
        region = regions[0]
        assert region["x"] == pytest.approx(0.2)
        assert region["y"] == pytest.approx(0.1)
        assert region["w"] == pytest.approx(0.4)
        assert region["h"] == pytest.approx(0.4)
        assert region["kind"] == "object"
        assert region["desc"] == "cat"
        assert region["text"] == ""

    def test_clamp_and_swap(self):
        # Out-of-range and reversed endpoints: clamp into [0,1] and reorder.
        payload = '[{"box_2d":[-50,1100,2000,-10],"label":"thing"}]'
        regions = detections_to_regions(payload, 20)
        for region in regions:
            for key in ("x", "y", "w", "h"):
                assert 0.0 <= region[key] <= 1.0
            assert region["x"] + region["w"] <= 1.0 + 1e-9
            assert region["y"] + region["h"] <= 1.0 + 1e-9

    def test_drop_degenerate_height(self):
        # Height 0.001 <= MIN_REGION_EXTENT -> dropped.
        payload = '[{"box_2d":[100,100,101,800],"label":"sliver"}]'
        assert detections_to_regions(payload, 20) == []

    def test_drop_zero_width(self):
        payload = '[{"box_2d":[100,300,500,300],"label":"line"}]'
        assert detections_to_regions(payload, 20) == []

    def test_max_objects_cap(self):
        boxes = [{"box_2d": [0, 0, 500, 500], "label": f"o{i}"} for i in range(5)]
        regions = detections_to_regions(json.dumps(boxes), 3)
        assert len(regions) == 3

    def test_empty_list_is_valid(self):
        assert detections_to_regions("[]", 20) == []

    def test_malformed_json_raises(self):
        with pytest.raises(ValueError):
            detections_to_regions("oops not json", 20)

    def test_non_list_json_raises(self):
        with pytest.raises(ValueError):
            detections_to_regions('{"box_2d":[0,0,500,500]}', 20)

    def test_label_missing_or_nonstring(self):
        payload = '[{"box_2d":[100,200,500,600]},{"box_2d":[0,0,400,400],"label":7}]'
        regions = detections_to_regions(payload, 20)
        assert all(r["desc"] == "" for r in regions)

    def test_min_region_extent_is_contract_value(self):
        # The detector's local floor must stay in sync with the regions contract.
        assert DETECT_MIN_REGION_EXTENT == MIN_REGION_EXTENT == 0.005


class TestContractRoundTrip:
    """detections_to_regions output round-trips through the builder's parse_regions."""

    def test_round_trip_count_and_geometry(self):
        payload = json.dumps([
            {"box_2d": [100, 200, 500, 600], "label": "cat"},
            {"box_2d": [0, 0, 300, 900], "label": "sky"},
        ])
        produced = detections_to_regions(payload, 20)
        serialized = json.dumps(produced)
        parsed = parse_regions(serialized)
        assert len(parsed) == len(produced)
        for emitted, accepted in zip(produced, parsed):
            for key in ("x", "y", "w", "h"):
                assert emitted[key] == pytest.approx(accepted[key])
            assert accepted["kind"] == "object"
