# ABOUTME: Tests GeminiClient._normalize_usage, the torch-free usage_metadata reader.
# ABOUTME: Verifies token counts are surfaced without double-counting thinking tokens.

"""
Validates GeminiClient._normalize_usage: it turns the SDK's response.usage_metadata
into {input_tokens, output_tokens, total_tokens}. candidates_token_count already
includes thinking tokens on the Gemini Developer API, so thoughts_token_count is
NOT added (that would double-count). Missing usage yields None. No network, no
torch — a plain staticmethod over a duck-typed object.
"""

import types

from gemini.gemini_api.client import GeminiClient


def _usage(**fields):
    return types.SimpleNamespace(**fields)


class TestNormalizeUsage:
    def test_none_returns_none(self):
        assert GeminiClient._normalize_usage(None) is None

    def test_basic_counts(self):
        u = _usage(prompt_token_count=1200, candidates_token_count=1500,
                   total_token_count=2700)
        assert GeminiClient._normalize_usage(u) == {
            "input_tokens": 1200, "output_tokens": 1500, "total_tokens": 2700,
        }

    def test_thoughts_not_double_counted(self):
        # candidates already includes the 900 thinking tokens; output must stay 1500.
        u = _usage(prompt_token_count=1200, candidates_token_count=1500,
                   thoughts_token_count=900, total_token_count=2700)
        result = GeminiClient._normalize_usage(u)
        assert result["output_tokens"] == 1500

    def test_total_derived_when_absent(self):
        u = _usage(prompt_token_count=100, candidates_token_count=50)
        assert GeminiClient._normalize_usage(u)["total_tokens"] == 150

    def test_missing_fields_default_to_zero(self):
        u = _usage(total_token_count=0)
        result = GeminiClient._normalize_usage(u)
        assert result == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def test_non_int_fields_ignored(self):
        u = _usage(prompt_token_count=None, candidates_token_count="oops")
        result = GeminiClient._normalize_usage(u)
        assert result["input_tokens"] == 0 and result["output_tokens"] == 0
