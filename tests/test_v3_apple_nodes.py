# ABOUTME: V3 structural and behavioral tests for all Apple SHARP provider nodes.
# ABOUTME: Validates V3 compliance, custom types, input constraints, and provider export.

"""
V3 tests for Apple SHARP provider nodes (3 nodes total).

Validates:
- All classes inherit from IO.ComfyNode
- define_schema returns correct Schema with expected fields
- execute is a @classmethod
- Custom type (SHARP_GAUSSIANS) in correct schemas
- not_idempotent and is_output_node flags match V1 behavior
- force_input on ply_path inputs
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO


def _import_node(module_name, class_name):
    """Import a node class from the apple package."""
    import importlib
    mod = importlib.import_module(f"apple.{module_name}")
    return getattr(mod, class_name)


# --- Parametrized structural data for all 3 nodes ---
# (module, class_name, node_id, display_name, category, not_idempotent, is_output_node)
APPLE_NODES = [
    ("sharp_nodes", "SHARPPredict", "SHARPPredict",
     "SHARP Predict (Image to 3D Gaussian)", "ERPK/Apple/SHARP", False, False),
    ("sharp_nodes", "SHARPRenderViews", "SHARPRenderViews",
     "SHARP Render Views", "ERPK/Apple/SHARP", False, False),
    ("sharp_nodes", "SHARPRenderVideo", "SHARPRenderVideo",
     "SHARP Render Video", "ERPK/Apple/SHARP", False, False),
]


@pytest.fixture(params=APPLE_NODES, ids=[n[2] for n in APPLE_NODES])
def node_spec(request):
    """Yield (cls, node_id, display_name, category, not_idempotent, is_output_node)."""
    module, class_name, node_id, display_name, category, not_idempotent, is_output_node = request.param
    cls = _import_node(module, class_name)
    return cls, node_id, display_name, category, not_idempotent, is_output_node


class TestAppleV3Compliance:
    """All Apple SHARP nodes comply with V3 API requirements."""

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


class TestAppleCustomTypes:
    """Custom types and IO types appear correctly in schemas."""

    def test_predict_outputs_gaussians(self):
        cls = _import_node("sharp_nodes", "SHARPPredict")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "SHARP_GAUSSIANS" in output_types

    def test_predict_outputs_string(self):
        cls = _import_node("sharp_nodes", "SHARPPredict")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "STRING" in output_types

    def test_predict_accepts_image(self):
        cls = _import_node("sharp_nodes", "SHARPPredict")
        schema = cls.define_schema()
        input_types = [i.io_type for i in schema.inputs]
        assert "IMAGE" in input_types

    def test_predict_has_device_combo(self):
        cls = _import_node("sharp_nodes", "SHARPPredict")
        schema = cls.define_schema()
        device_inputs = [i for i in schema.inputs if i.id == "device"]
        assert len(device_inputs) == 1
        assert set(device_inputs[0].options) == {"auto", "cuda", "mps", "cpu"}

    def test_render_views_ply_path_force_input(self):
        cls = _import_node("sharp_nodes", "SHARPRenderViews")
        schema = cls.define_schema()
        ply_inputs = [i for i in schema.inputs if i.id == "ply_path"]
        assert len(ply_inputs) == 1
        assert ply_inputs[0].force_input is True

    def test_render_views_outputs_image(self):
        cls = _import_node("sharp_nodes", "SHARPRenderViews")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "IMAGE" in output_types

    def test_render_video_ply_path_force_input(self):
        cls = _import_node("sharp_nodes", "SHARPRenderVideo")
        schema = cls.define_schema()
        ply_inputs = [i for i in schema.inputs if i.id == "ply_path"]
        assert len(ply_inputs) == 1
        assert ply_inputs[0].force_input is True

    def test_render_video_outputs_string_and_image(self):
        cls = _import_node("sharp_nodes", "SHARPRenderVideo")
        schema = cls.define_schema()
        output_types = [o.io_type for o in schema.outputs]
        assert "STRING" in output_types
        assert "IMAGE" in output_types


class TestAppleNoDuplicateIds:
    """No duplicate node_ids across all Apple nodes."""

    def test_no_duplicate_node_ids(self):
        ids = []
        for module, class_name, *_ in APPLE_NODES:
            cls = _import_node(module, class_name)
            schema = cls.define_schema()
            ids.append(schema.node_id)
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"


class TestAppleProviderExport:
    """apple/__init__.py exports NODES list for ERPKExtension."""

    def test_nodes_list_exported(self):
        import importlib
        mod = importlib.import_module("apple")
        assert hasattr(mod, "NODES"), "apple package must export NODES"
        assert isinstance(mod.NODES, list)

    def test_nodes_list_has_all_classes(self):
        import importlib
        mod = importlib.import_module("apple")
        assert len(mod.NODES) == 3, f"Expected 3 Apple nodes, got {len(mod.NODES)}"

    def test_nodes_list_all_comfy_nodes(self):
        import importlib
        mod = importlib.import_module("apple")
        for cls in mod.NODES:
            assert issubclass(cls, IO.ComfyNode), \
                f"{cls.__name__} in NODES must inherit IO.ComfyNode"
