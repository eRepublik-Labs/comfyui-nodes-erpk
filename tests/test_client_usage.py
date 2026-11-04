# ABOUTME: Tests GeminiClient._normalize_usage, the torch-free usage_metadata reader.
# ABOUTME: Verifies thinking tokens are counted as output, which is how Google bills them.

"""
Validates GeminiClient._normalize_usage: it turns the SDK's response.usage_metadata
into {input_tokens, output_tokens, total_tokens}. candidates_token_count does NOT
include thinking: on 55 of 55 measured replies that thought (gemini_study,
2026-11-03), total_token_count = prompt + candidates + thoughts. Google bills
thinking at the output rate, so output_tokens = candidates + thoughts. Missing
usage yields None. No network, no torch, a plain staticmethod over a duck-typed
object.
"""

import types

from erpk.gemini.gemini_api.client import GeminiClient


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

    def test_thoughts_are_billed_as_output(self):
        # Measured gemini-3.8-flash reply (probe_text.jsonl, baseline row,
        # 2026-11-03): prompt 4, candidates 1, thoughts 27, total 32.
        u = _usage(prompt_token_count=4, candidates_token_count=1,
                   thoughts_token_count=27, total_token_count=32)
        assert GeminiClient._normalize_usage(u) == {
            "input_tokens": 4, "output_tokens": 28, "total_tokens": 32,
        }

    def test_reply_that_spent_every_token_thinking(self):
        # Measured gemini-3.6-flash reply at a 32-token cap (same study): no
        # candidates count at all, thoughts 29, total 33.
        u = _usage(prompt_token_count=4, candidates_token_count=None,
                   thoughts_token_count=29, total_token_count=33)
        assert GeminiClient._normalize_usage(u) == {
            "input_tokens": 4, "output_tokens": 29, "total_tokens": 33,
        }

    def test_total_derived_when_absent(self):
        u = _usage(prompt_token_count=100, candidates_token_count=50)
        assert GeminiClient._normalize_usage(u)["total_tokens"] == 150

    def test_derived_total_includes_thoughts(self):
        u = _usage(prompt_token_count=100, candidates_token_count=50,
                   thoughts_token_count=25)
        assert GeminiClient._normalize_usage(u)["total_tokens"] == 175

    def test_missing_fields_default_to_zero(self):
        u = _usage(total_token_count=0)
        result = GeminiClient._normalize_usage(u)
        assert result == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def test_non_int_fields_ignored(self):
        u = _usage(prompt_token_count=None, candidates_token_count="oops")
        result = GeminiClient._normalize_usage(u)
        assert result["input_tokens"] == 0 and result["output_tokens"] == 0
