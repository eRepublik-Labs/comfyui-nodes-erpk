# ABOUTME: Tests for the torch-free scan cost pricer (utils/scan_cost).
# ABOUTME: Covers price math, unknown-model handling, and loading gemini/pricing.json.

"""
Validates utils.scan_cost: price() turns token counts into a USD estimate from a
rate table, returns None (not 0) for unknown models so callers can say "cost
unavailable", and load_pricing() reads the gemini/pricing.json that mirrors the
claude/pricing.json schema (input_price_per_mtok / output_price_per_mtok).
"""

import json

import pytest

from utils.scan_cost import load_pricing, price


# Explicit rates keep the math tests independent of the shipped pricing file.
RATES = {
    "gemini-3.5-flash": {"input": 1.5, "output": 9.0},
    "gemini-2.5-flash": {"input": 0.3, "output": 2.5},
    "free-model": {"input": 0.0, "output": 0.0},
}


class TestPrice:
    def test_input_only(self):
        assert price("gemini-3.5-flash", 1_000_000, 0, rates=RATES) == pytest.approx(1.5)

    def test_output_only(self):
        assert price("gemini-3.5-flash", 0, 1_000_000, rates=RATES) == pytest.approx(9.0)

    def test_combined(self):
        # 0.5M input + 0.25M output = 0.75 + 2.25 = 3.0
        assert price("gemini-3.5-flash", 500_000, 250_000, rates=RATES) == pytest.approx(3.0)

    def test_other_model_rate(self):
        assert price("gemini-2.5-flash", 1_000_000, 1_000_000, rates=RATES) == pytest.approx(2.8)

    def test_zero_tokens_is_zero_for_known_model(self):
        assert price("gemini-3.5-flash", 0, 0, rates=RATES) == 0.0

    def test_zero_rate_model_is_zero_not_none(self):
        assert price("free-model", 1_000_000, 1_000_000, rates=RATES) == 0.0

    def test_unknown_model_is_none(self):
        # None (not 0) so the UI distinguishes "no price" from "free".
        assert price("totally-bogus-model", 1_000_000, 0, rates=RATES) is None

    def test_loads_rates_from_file_when_none_given(self):
        # Falls back to the shipped pricing.json; the default scan model must price.
        from gemini.gemini_api.client import GeminiClient
        result = price(GeminiClient.DEFAULT_MODEL, 1_000_000, 0)
        assert result is not None and result > 0


class TestLoadPricing:
    def test_returns_rates_and_date(self):
        rates, last_updated = load_pricing()
        assert isinstance(rates, dict) and rates
        assert isinstance(last_updated, str) and last_updated != "unknown"

    def test_default_model_is_priced(self):
        from gemini.gemini_api.client import GeminiClient
        rates, _ = load_pricing()
        assert GeminiClient.DEFAULT_MODEL in rates
        rate = rates[GeminiClient.DEFAULT_MODEL]
        assert rate["input"] > 0 and rate["output"] > 0

    def test_every_client_model_has_a_rate(self):
        # A model selectable in the picker but absent from pricing.json would
        # silently read as "cost unavailable" for that scan.
        from gemini.gemini_api.client import GeminiClient
        rates, _ = load_pricing()
        missing = [m for m in GeminiClient.MODELS if m not in rates]
        assert not missing, f"models in MODELS but not priced: {missing}"

    def test_missing_file_degrades(self):
        rates, last_updated = load_pricing(path="/nonexistent/pricing.json")
        assert rates == {}
        assert last_updated == "unknown"

    def test_pricing_json_schema_matches_claude(self, tmp_path):
        # The gemini pricing file uses the same key names the claude one does.
        import os
        gemini_pricing = os.path.join(
            os.path.dirname(__file__), "..", "gemini", "pricing.json")
        with open(gemini_pricing) as f:
            data = json.load(f)
        assert "models" in data and "_last_updated" in data
        for model_id, md in data["models"].items():
            assert "input_price_per_mtok" in md, model_id
            assert "output_price_per_mtok" in md, model_id
