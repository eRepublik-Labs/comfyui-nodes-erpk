# ABOUTME: V3 structural and behavioral tests for all BGRemoval provider nodes.
# ABOUTME: Validates V3 compliance, image/mask types, and provider export.

"""
V3 tests for BGRemoval provider nodes (6 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- IMAGE and MASK types in schemas
- not_idempotent and is_output_node flags match V1 behavior
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the bgremoval package."""
    import importlib
    mod = importlib.import_module(f"bgremoval.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 6 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
BGREMOVAL_NODES = [
    ("rembg_node", "RembgRemoveBackground", "RembgRemoveBackground",
     "Remove Background (rembg)", "ERPK/Background Removal", False, False),
    ("inspyrenet_node", "InSPyReNetRemoveBackground", "InSPyReNetRemoveBackground",
     "Remove Background (InSPyReNet)", "ERPK/Background Removal", False, False),
    ("birefnet_node", "BiRefNetRemoveBackground", "BiRefNetRemoveBackground",
     "Remove Background (BiRefNet)", "ERPK/Background Removal", False, False),
    ("birefnet_node", "BiRefNetGetMask", "BiRefNetGetMask",
     "Get Mask (BiRefNet)", "ERPK/Background Removal", False, False),
    ("blur_fusion_node", "BlurFusionForegroundEstimation", "BlurFusionForegroundEstimation",
     "Foreground Refinement (BlurFusion)", "ERPK/Background Removal", False, False),
    ("ben2_node", "BEN2RemoveBackground", "BEN2RemoveBackground",
     "Remove Background (BEN2)", "ERPK/Background Removal", False, False),
]


@pytest.fixture(params=BGREMOVAL_NODES, ids=[n[2] for n in BGREMOVAL_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestBGRemovalV3Compliance:
    """All BGRemoval nodes comply with V3 API requirements."""

    def test_inherits_comfy_node(self, node_spec):
        cls, *_ = node_spec
        assert issubclass(cls, IO.ComfyNode), f"{cls.__name__} must inherit IO.ComfyNode"

    def test_has_define_schema(self, node_spec):
        cls, *_ = node_spec
        assert hasattr(cls, "define_schema")
        assert callable(cls.define_schema)

    def test_has_execute(self, node_spec):
        cls, *_ = node_spec
        assert hasattr(cls, "execute")
        assert callable(cls.execute)

    def test_execute_is_classmethod(self, node_spec):
        cls, *_ = node_spec
        assert isinstance(inspect.getattr_static(cls, "execute"), classmethod), \
            f"{cls.__name__}.execute must be a @classmethod"

    def test_schema_node_id(self, node_spec):
        cls, node_id, *_ = node_spec
        schema = cls.define_schema()
        assert schema.node_id == node_id

    def test_schema_display_name(self, node_spec):
        cls, _, display_name, *_ = node_spec
        schema = cls.define_schema()
        assert schema.display_name == display_name

    def test_schema_category(self, node_spec):
        cls, _, _, category, *_ = node_spec
        schema = cls.define_schema()
        assert schema.category == category

    def test_schema_not_idempotent(self, node_spec):
        cls, _, _, _, not_idempotent, _ = node_spec
        schema = cls.define_schema()
        assert schema.not_idempotent == not_idempotent, \
            f"{cls.__name__}: expected not_idempotent={not_idempotent}"

    def test_schema_is_output_node(self, node_spec):
        cls, _, _, _, _, is_output_node = node_spec
        schema = cls.define_schema()
        assert schema.is_output_node == is_output_node, \
            f"{cls.__name__}: expected is_output_node={is_output_node}"

    def test_schema_has_inputs(self, node_spec):
        cls, *_ = node_spec
        schema = cls.define_schema()
        assert len(schema.inputs) > 0, f"{cls.__name__} schema must have inputs"

    def test_schema_has_outputs(self, node_spec):
        cls, *_ = node_spec
        schema = cls.define_schema()
        assert len(schema.outputs) > 0, f"{cls.__name__} schema must have outputs"


class TestBGRemovalImageTypes:
    """IMAGE and MASK types appear correctly in schemas."""

    def test_rembg_accepts_image_outputs_image_and_mask(self):
        cls = _import_node("rembg_node", "RembgRemoveBackground")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "IMAGE" in output_types
        assert "MASK" in output_types

    def test_inspyrenet_accepts_image_outputs_image_and_mask(self):
        cls = _import_node("inspyrenet_node", "InSPyReNetRemoveBackground")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "IMAGE" in output_types
        assert "MASK" in output_types

    def test_birefnet_accepts_image_outputs_image_and_mask(self):
        cls = _import_node("birefnet_node", "BiRefNetRemoveBackground")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "IMAGE" in output_types
        assert "MASK" in output_types

    def test_birefnet_get_mask_accepts_image_outputs_mask_only(self):
        cls = _import_node("birefnet_node", "BiRefNetGetMask")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert output_types == ["MASK"], "BiRefNetGetMask should only output MASK"

    def test_blur_fusion_accepts_image_and_mask_outputs_image_and_mask(self):
        cls = _import_node("blur_fusion_node", "BlurFusionForegroundEstimation")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "MASK" in input_types, "BlurFusion requires MASK input"
        assert "IMAGE" in output_types
        assert "MASK" in output_types

    def test_ben2_accepts_image_outputs_image_and_mask(self):
        cls = _import_node("ben2_node", "BEN2RemoveBackground")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in input_types
        assert "IMAGE" in output_types
        assert "MASK" in output_types

    def test_rembg_has_model_combo(self):
        cls = _import_node("rembg_node", "RembgRemoveBackground")
        schema = cls.define_schema()
        model_inputs = [i for i in schema.inputs if i.id == "model"]
        assert len(model_inputs) == 1
        assert hasattr(model_inputs[0], "options")
        assert "u2net" in model_inputs[0].options

    def test_birefnet_has_variant_combo(self):
        cls = _import_node("birefnet_node", "BiRefNetRemoveBackground")
        schema = cls.define_schema()
        variant_inputs = [i for i in schema.inputs if i.id == "variant"]
        assert len(variant_inputs) == 1
        assert hasattr(variant_inputs[0], "options")
        assert "ZhengPeng7/BiRefNet" in variant_inputs[0].options


class TestBGRemovalNoDuplicateIds:
    """No duplicate node_ids across all BGRemoval nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in BGREMOVAL_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestBGRemovalProviderExport:
    """bgremoval/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("bgremoval")
        assert hasattr(mod, "NODES"), "bgremoval package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("bgremoval")
        assert len(mod.NODES) == 6, f"Expected 6 BGRemoval nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("bgremoval")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"
