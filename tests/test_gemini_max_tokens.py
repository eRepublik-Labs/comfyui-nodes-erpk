# ABOUTME: Tests that max_tokens ceiling is 65536 across text-based Gemini nodes.
# ABOUTME: Verifies define_schema max value and default value for TextGen, Chat, Vision.

import pytest

from gemini.nodes import GeminiTextGeneration, GeminiChat, GeminiVision


class TestMaxTokensCeiling:
    """Verify max_tokens ceiling is 65536 in define_schema."""

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_ceiling_is_65536(self, node_cls):
        schema = node_cls.define_schema()
        max_tokens_input = [i for i in schema.inputs if i.id == "max_tokens"][0]
        assert max_tokens_input.max == 65536

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_default_is_8192(self, node_cls):
        """Default stays at 8192 — we only raise the ceiling, not the default."""
        schema = node_cls.define_schema()
        max_tokens_input = [i for i in schema.inputs if i.id == "max_tokens"][0]
        assert max_tokens_input.default == 8192
