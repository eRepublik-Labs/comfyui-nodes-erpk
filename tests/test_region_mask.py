# ABOUTME: Tests for the Region Mask node that picks one region's mask from the
# ABOUTME: builder's masks batch by canvas region number.

"""
Validates RegionMask: V3 structure, schema IO (MASK in, INT region, MASK out),
and the clamp_region_index helper that maps a 1-based canvas region number onto
a safe 0-based batch index. Execute is exercised with plain sequences since it
only slices.
"""

import inspect

import pytest

IO = pytest.importorskip("comfy_api.latest").IO

from utils.region_mask import RegionMask, clamp_region_index


class TestStructure:
    def test_inherits_comfy_node(self):
        assert issubclass(RegionMask, IO.ComfyNode)

    def test_schema_identity(self):
        schema = RegionMask.define_schema()
        assert schema.node_id == "RegionMask"
        assert schema.category == "ERPK/utils"

    def test_registered_in_utils_nodes(self):
        from utils import NODES
        assert RegionMask in NODES


class TestSchemaIO:
    def test_inputs(self):
        schema = RegionMask.define_schema()
        ids = [i.id for i in schema.inputs]
        assert ids == ["masks", "region"]
        assert schema.inputs[0].io_type == "MASK"
        assert schema.inputs[1].io_type == "INT"

    def test_single_mask_output(self):
        schema = RegionMask.define_schema()
        assert len(schema.outputs) == 1
        assert schema.outputs[0].io_type == "MASK"

    def test_no_fingerprint_inputs(self):
        # Pure slicing node: must stay cacheable like other config nodes.
        assert "fingerprint_inputs" not in vars(RegionMask)


class TestClampRegionIndex:
    def test_first_region(self):
        assert clamp_region_index(5, 1) == 0

    def test_last_region(self):
        assert clamp_region_index(5, 5) == 4

    def test_above_count_clamps_to_last(self):
        assert clamp_region_index(3, 9) == 2

    def test_below_one_clamps_to_first(self):
        assert clamp_region_index(3, 0) == 0
        assert clamp_region_index(3, -2) == 0

    def test_empty_batch_yields_first(self):
        assert clamp_region_index(0, 1) == 0


class TestExecute:
    def test_slices_the_numbered_region(self):
        result = RegionMask.execute(masks=["m1", "m2", "m3"], region=2)
        assert result.args[0] == ["m2"]

    def test_out_of_range_clamps(self):
        result = RegionMask.execute(masks=["m1", "m2"], region=99)
        assert result.args[0] == ["m2"]
