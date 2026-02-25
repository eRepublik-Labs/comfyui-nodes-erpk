# ABOUTME: Tests for BEN2 background removal node structure and registration.
# ABOUTME: Validates INPUT_TYPES, RETURN_TYPES, and node class metadata.

"""
Tests for bgremoval/ben2_node.py

Tests node structure, registration, and metadata without requiring
the actual BEN2 model (heavy ML dependency).
"""

import pytest
import sys
import os

# These tests require numpy/torch (via bgremoval.utils). Skip if not available.
np = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBEN2NodeImport:
    """Test BEN2 node module structure."""

    def test_module_imports(self):
        """Module should import even without ben2 package installed."""
        from bgremoval import ben2_node
        assert hasattr(ben2_node, "NODE_CLASS_MAPPINGS")
        assert hasattr(ben2_node, "NODE_DISPLAY_NAME_MAPPINGS")

    def test_node_class_registered(self):
        """BEN2RemoveBackground should be in node mappings."""
        from bgremoval.ben2_node import NODE_CLASS_MAPPINGS
        assert "ERPK Remove Background (BEN2)" in NODE_CLASS_MAPPINGS

    def test_display_name(self):
        """Display name should be user-friendly."""
        from bgremoval.ben2_node import NODE_DISPLAY_NAME_MAPPINGS
        assert NODE_DISPLAY_NAME_MAPPINGS["ERPK Remove Background (BEN2)"] == "Remove Background (BEN2)"


class TestBEN2RemoveBackground:
    """Test BEN2RemoveBackground node class structure."""

    @pytest.fixture
    def node_class(self):
        from bgremoval.ben2_node import BEN2RemoveBackground
        return BEN2RemoveBackground

    def test_input_types_structure(self, node_class):
        """INPUT_TYPES should have required image and optional params."""
        inputs = node_class.INPUT_TYPES()
        assert "required" in inputs
        assert "image" in inputs["required"]
        assert inputs["required"]["image"] == ("IMAGE",)

    def test_optional_refine_foreground(self, node_class):
        """Should have optional refine_foreground boolean."""
        inputs = node_class.INPUT_TYPES()
        assert "optional" in inputs
        assert "refine_foreground" in inputs["optional"]
        rf = inputs["optional"]["refine_foreground"]
        assert rf[0] == "BOOLEAN"
        assert rf[1]["default"] is False

    def test_optional_device(self, node_class):
        """Should have optional device selector."""
        inputs = node_class.INPUT_TYPES()
        assert "device" in inputs["optional"]
        device = inputs["optional"]["device"]
        assert "auto" in device[0]
        assert "cuda" in device[0]
        assert "cpu" in device[0]
        assert "mps" in device[0]

    def test_return_types(self, node_class):
        """Should return IMAGE and MASK."""
        assert node_class.RETURN_TYPES == ("IMAGE", "MASK")
        assert node_class.RETURN_NAMES == ("image", "mask")

    def test_function_name(self, node_class):
        """Function should be remove_background."""
        assert node_class.FUNCTION == "remove_background"

    def test_category(self, node_class):
        """Category should match other bgremoval nodes."""
        assert node_class.CATEGORY == "ERPK/Background Removal"

    def test_has_description(self, node_class):
        """Node should have a description."""
        assert node_class.DESCRIPTION
        assert "BEN2" in node_class.DESCRIPTION

    def test_method_signature(self, node_class):
        """remove_background method should accept expected parameters."""
        import inspect
        sig = inspect.signature(node_class.remove_background)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "image" in params
        assert "refine_foreground" in params
        assert "device" in params

    def test_model_caching(self, node_class):
        """Should have class-level model cache."""
        assert hasattr(node_class, "_model")
        assert hasattr(node_class, "_current_device")


class TestBiRefNetVariants:
    """Test BiRefNet variant list completeness."""

    def test_variant_count(self):
        """Should have 17 variants (15 original + lite + dynamic-matting)."""
        from bgremoval.birefnet_node import BIREFNET_VARIANTS
        assert len(BIREFNET_VARIANTS) == 17

    def test_has_lite_variant(self):
        """Should include BiRefNet_lite (44.4M param lightweight model)."""
        from bgremoval.birefnet_node import VARIANT_NAMES
        assert "ZhengPeng7/BiRefNet_lite" in VARIANT_NAMES

    def test_has_dynamic_matting_variant(self):
        """Should include BiRefNet_dynamic-matting."""
        from bgremoval.birefnet_node import VARIANT_NAMES
        assert "ZhengPeng7/BiRefNet_dynamic-matting" in VARIANT_NAMES

    def test_variant_names_match_tuples(self):
        """VARIANT_NAMES should be derived from BIREFNET_VARIANTS."""
        from bgremoval.birefnet_node import BIREFNET_VARIANTS, VARIANT_NAMES
        expected = [name for name, _ in BIREFNET_VARIANTS]
        assert VARIANT_NAMES == expected
