# ABOUTME: Tests for V3 comfy_entrypoint and ERPKExtension registration.
# ABOUTME: Validates that all node classes are discoverable via the V3 API.

"""
Tests for the V3 entrypoint (comfy_entrypoint + ERPKExtension).

Validates:
- comfy_entrypoint is an async function returning a ComfyExtension
- get_node_list returns all expected node classes
- All returned classes inherit from IO.ComfyNode and have define_schema
"""

import asyncio
import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO
ComfyExtension = pytest.importorskip("comfy_api.latest").ComfyExtension


def _run_async(coro):
    """Run an async function synchronously for testing."""
    return asyncio.run(coro)


class TestComfyEntrypoint:
    """Test the package-level comfy_entrypoint."""

    def test_entrypoint_exists(self):
        """Package must export comfy_entrypoint."""
        import importlib
        # __init__.py is the entrypoint module
        mod = importlib.import_module("__init__")
        assert hasattr(mod, "comfy_entrypoint")

    def test_entrypoint_is_async(self):
        import importlib
        mod = importlib.import_module("__init__")
        assert inspect.iscoroutinefunction(mod.comfy_entrypoint)

    def test_entrypoint_returns_extension(self):
        import importlib
        mod = importlib.import_module("__init__")
        ext = _run_async(mod.comfy_entrypoint())
        assert isinstance(ext, ComfyExtension)


class TestERPKExtension:
    """Test the ERPKExtension node list."""

    @pytest.fixture
    def extension(self):
        import importlib
        mod = importlib.import_module("__init__")
        return _run_async(mod.comfy_entrypoint())

    @pytest.fixture
    def node_list(self, extension):
        return _run_async(extension.get_node_list())

    def test_node_list_not_empty(self, node_list):
        assert len(node_list) > 0

    def test_all_nodes_are_comfy_nodes(self, node_list):
        for cls in node_list:
            assert issubclass(cls, IO.ComfyNode), f"{cls.__name__} must inherit IO.ComfyNode"

    def test_all_nodes_have_define_schema(self, node_list):
        for cls in node_list:
            assert hasattr(cls, "define_schema"), f"{cls.__name__} must have define_schema"

    def test_all_nodes_have_execute(self, node_list):
        for cls in node_list:
            assert hasattr(cls, "execute"), f"{cls.__name__} must have execute"

    def test_all_schemas_have_node_id(self, node_list):
        for cls in node_list:
            schema = cls.define_schema()
            assert schema.node_id, f"{cls.__name__} schema must have a node_id"

    def test_no_duplicate_node_ids(self, node_list):
        ids = [cls.define_schema().node_id for cls in node_list]
        assert len(ids) == len(set(ids)), f"Duplicate node_ids: {ids}"

    def test_contains_concat_strings(self, node_list):
        """ConcatenateStrings (the pilot node) should be in the list."""
        ids = [cls.define_schema().node_id for cls in node_list]
        assert "ERPK_ConcatenateStrings" in ids


class TestWEBDirectory:
    """Test that WEB_DIRECTORY is still exported."""

    def test_web_directory_exported(self):
        import importlib
        mod = importlib.import_module("__init__")
        assert hasattr(mod, "WEB_DIRECTORY")
        assert mod.WEB_DIRECTORY == "./web"
