# ABOUTME: Tests for the torch-free scan cost pricer (utils/scan_cost).
# ABOUTME: Covers price math, unknown-model handling, and loading gemini/pricing.json.

"""
Validates utils.scan_cost: price() turns token counts into a USD estimate from a
rate table, returns None (not 0) for unknown models so callers can say "cost
unavailable", and load_pricing() reads the gemini/pricing.json that mirrors the
claude/pricing.json schema (input_price_per_mtok / output_price_per_mtok).
"""

import json
from datetime import date

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
        from erpk.gemini.gemini_api.client import GeminiClient
        result = price(GeminiClient.DEFAULT_MODEL, 1_000_000, 0)
        assert result is not None and result > 0


class TestLoadPricing:
    def test_returns_rates_and_date(self):
        rates, last_updated = load_pricing()
        assert isinstance(rates, dict) and rates
        assert isinstance(last_updated, str) and last_updated != "unknown"

    def test_default_model_is_priced(self):
        from erpk.gemini.gemini_api.client import GeminiClient
        rates, _ = load_pricing()
        assert GeminiClient.DEFAULT_MODEL in rates
        rate = rates[GeminiClient.DEFAULT_MODEL]
        assert rate["input"] > 0 and rate["output"] > 0

    def test_every_client_model_has_a_rate(self):
        # A model selectable in the picker but absent from pricing.json would
        # silently read as "cost unavailable" for that scan.
        from erpk.gemini.gemini_api.client import GeminiClient
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


def _write_pricing(tmp_path, models):
    path = tmp_path / "pricing.json"
    path.write_text(json.dumps({"_last_updated": "2026-11-18", "models": models}))
    return str(path)


def _scheduled(*changes):
    return {
        "name": "Scheduled",
        "input_price_per_mtok": 2.0,
        "output_price_per_mtok": 10.0,
        "price_changes": [
            {"effective_from": day, "input_price_per_mtok": inp, "output_price_per_mtok": out}
            for day, inp, out in changes
        ],
    }


class TestPriceChanges:
    """A model's base rate applies until the first price_changes date, then each
    change applies from its effective_from date (inclusive) onward."""

    @pytest.fixture
    def path(self, tmp_path):
        return _write_pricing(tmp_path, {
            "scheduled": _scheduled(("2026-12-01", 4.0, 20.0), ("2027-06-01", 5.0, 25.0)),
            "plain": {"name": "Plain", "input_price_per_mtok": 1.5, "output_price_per_mtok": 7.5},
        })

    @pytest.mark.parametrize("day, expected", [
        (date(2026, 11, 30), {"input": 2.0, "output": 10.0}),
        (date(2026, 12, 1), {"input": 4.0, "output": 20.0}),
        (date(2027, 5, 31), {"input": 4.0, "output": 20.0}),
        (date(2027, 6, 1), {"input": 5.0, "output": 25.0}),
        (date(2030, 1, 1), {"input": 5.0, "output": 25.0}),
    ])
    def test_rate_follows_the_date(self, path, day, expected):
        rates, _ = load_pricing(path, on=day)
        assert rates["scheduled"] == expected

    @pytest.mark.parametrize("day", [date(2020, 1, 1), date(2026, 12, 1), date(2030, 1, 1)])
    def test_plain_entry_ignores_the_date(self, path, day):
        rates, _ = load_pricing(path, on=day)
        assert rates["plain"] == {"input": 1.5, "output": 7.5}

    def test_no_date_uses_todays_utc_rate(self, path, monkeypatch):
        import utils.scan_cost as scan_cost
        monkeypatch.setattr(scan_cost, "_today_utc", lambda: date(2026, 12, 1))
        rates, _ = load_pricing(path)
        assert rates["scheduled"] == {"input": 4.0, "output": 20.0}


class TestPriceChangesValidation:
    """A bad schedule fails loudly at load, naming the model and the bad value."""

    def _load(self, tmp_path, entry):
        load_pricing(_write_pricing(tmp_path, {"gemini-4-argon": entry}), on=date(2026, 12, 1))

    @pytest.mark.parametrize("bad", ["2026-12-1", "20261201", "December 1, 2026", "2026-02-30", 20261201])
    def test_malformed_date(self, tmp_path, bad):
        entry = _scheduled((bad, 4.0, 20.0))
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes effective_from {bad!r} "
            "is not a YYYY-MM-DD date")

    def test_unsorted_dates(self, tmp_path):
        entry = _scheduled(("2027-06-01", 5.0, 25.0), ("2026-12-01", 4.0, 20.0))
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes dates must be strictly "
            "increasing, got '2026-12-01' after '2027-06-01'")

    def test_duplicate_dates(self, tmp_path):
        entry = _scheduled(("2026-12-01", 4.0, 20.0), ("2026-12-01", 5.0, 25.0))
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes dates must be strictly "
            "increasing, got '2026-12-01' after '2026-12-01'")

    @pytest.mark.parametrize("bad", [None, "4.00", True, -1.0])
    def test_bad_price(self, tmp_path, bad):
        entry = _scheduled(("2026-12-01", bad, 20.0))
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes entry '2026-12-01' "
            f"input_price_per_mtok {bad!r} is not a non-negative number")

    def test_missing_price(self, tmp_path):
        entry = _scheduled(("2026-12-01", 4.0, 20.0))
        del entry["price_changes"][0]["output_price_per_mtok"]
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes entry '2026-12-01' "
            "output_price_per_mtok None is not a non-negative number")

    def test_price_changes_not_a_list(self, tmp_path):
        entry = _scheduled()
        entry["price_changes"] = {"effective_from": "2026-12-01"}
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes must be a list of "
            "{effective_from, input_price_per_mtok, output_price_per_mtok}, got "
            "{'effective_from': '2026-12-01'}")

    def test_change_not_an_object(self, tmp_path):
        entry = _scheduled()
        entry["price_changes"] = ["2026-12-01"]
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-argon price_changes must be a list of "
            "{effective_from, input_price_per_mtok, output_price_per_mtok}, got "
            "['2026-12-01']")


class TestBaseRateValidation:
    """Every model entry carries both base prices; a missing or bad one fails at load."""

    def _load(self, tmp_path, entry):
        load_pricing(_write_pricing(tmp_path, {"gemini-4-hydrogen": entry}), on=date(2026, 12, 1))

    @pytest.mark.parametrize("key", ["input_price_per_mtok", "output_price_per_mtok"])
    def test_missing_base_price(self, tmp_path, key):
        entry = {"name": "Plain", "input_price_per_mtok": 1.5, "output_price_per_mtok": 7.5}
        del entry[key]
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-hydrogen {key} None is not a non-negative number")

    @pytest.mark.parametrize("bad", [None, "1.50", False, -0.5])
    def test_bad_base_price(self, tmp_path, bad):
        entry = {"name": "Plain", "input_price_per_mtok": bad, "output_price_per_mtok": 7.5}
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, entry)
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-hydrogen input_price_per_mtok {bad!r} "
            "is not a non-negative number")

    def test_zero_base_price_is_free_not_an_error(self, tmp_path):
        path = _write_pricing(tmp_path, {
            "free": {"name": "Free", "input_price_per_mtok": 0, "output_price_per_mtok": 0.0}})
        rates, _ = load_pricing(path, on=date(2026, 12, 1))
        assert rates["free"] == {"input": 0, "output": 0.0}

    def test_entry_not_an_object(self, tmp_path):
        with pytest.raises(ValueError) as err:
            self._load(tmp_path, [1.5, 7.5])
        assert str(err.value) == (
            f"{tmp_path / 'pricing.json'}: gemini-4-hydrogen entry must be an object with "
            "input_price_per_mtok and output_price_per_mtok, got [1.5, 7.5]")
