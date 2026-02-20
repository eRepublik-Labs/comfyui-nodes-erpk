# ABOUTME: Tests that max_tokens ceiling is 65536 across text-based Gemini nodes
# ABOUTME: Verifies INPUT_TYPES max value and default value for TextGen, Chat, Vision

import sys
from unittest.mock import MagicMock

import pytest

for mod_name in ["numpy", "torch", "PIL", "PIL.Image"]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from gemini.nodes import GeminiTextGeneration, GeminiChat, GeminiVision


class TestMaxTokensCeiling:
    """Verify max_tokens ceiling is 65536 in INPUT_TYPES."""

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_ceiling_is_65536(self, node_cls):
        inputs = node_cls.INPUT_TYPES()
        max_tokens_config = inputs["optional"]["max_tokens"][1]
        assert max_tokens_config["max"] == 65536

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_default_is_8192(self, node_cls):
        """Default stays at 8192 — we only raise the ceiling, not the default."""
        inputs = node_cls.INPUT_TYPES()
        max_tokens_config = inputs["optional"]["max_tokens"][1]
        assert max_tokens_config["default"] == 8192
