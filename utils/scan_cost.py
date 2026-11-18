# ABOUTME: Prices a Gemini scan from token counts using gemini/pricing.json rates.
# ABOUTME: Torch/genai-free so the scan engine computes cost without heavy imports.

import json
import os
from datetime import date, datetime, timezone

# Gemini owns its prices (mirrors claude/pricing.json next to claude/token_counter.py).
PRICING_PATH = os.path.join(os.path.dirname(__file__), "..", "gemini", "pricing.json")

_PRICE_KEYS = ("input_price_per_mtok", "output_price_per_mtok")


def _today_utc():
    # Google's pricing page gives change dates without a timezone; UTC is our pick.
    return datetime.now(timezone.utc).date()


def load_pricing(path=PRICING_PATH, on=None):
    """Return ({model_id: {"input": per_mtok, "output": per_mtok}}, last_updated).

    Each model's rate is the one in effect on `on` (default: today, UTC). A model
    entry holds its base rate in input_price_per_mtok / output_price_per_mtok
    (the schema claude/pricing.json uses) and may add "price_changes", a list of
    {effective_from: "YYYY-MM-DD", input_price_per_mtok, output_price_per_mtok}
    in strictly increasing date order; each change applies from its date onward.

    A missing or unreadable file yields ({}, "unknown") — pricing is best-effort
    metadata, never a reason to fail a scan. A malformed price_changes list
    raises ValueError naming the model and the bad value.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}, "unknown"
    day = on or _today_utc()
    rates = {}
    for model_id, model_data in data.get("models", {}).items():
        if not isinstance(model_data, dict):
            continue
        rate = {
            "input": model_data.get("input_price_per_mtok", 0) or 0,
            "output": model_data.get("output_price_per_mtok", 0) or 0,
        }
        for effective_from, change in _parse_price_changes(path, model_id, model_data):
            if effective_from <= day:
                rate = {"input": change["input_price_per_mtok"], "output": change["output_price_per_mtok"]}
        rates[model_id] = rate
    return rates, data.get("_last_updated", "unknown")


def _parse_price_changes(path, model_id, model_data):
    """Validated [(effective_from, change)] for one model, in date order."""
    changes = model_data.get("price_changes", [])
    where = f"{path}: {model_id} price_changes"
    if not isinstance(changes, list) or not all(isinstance(c, dict) for c in changes):
        raise ValueError(
            f"{where} must be a list of {{effective_from, input_price_per_mtok, "
            f"output_price_per_mtok}}, got {changes!r}")
    parsed = []
    for change in changes:
        raw_day = change.get("effective_from")
        effective_from = _parse_iso_day(raw_day)
        if effective_from is None:
            raise ValueError(f"{where} effective_from {raw_day!r} is not a YYYY-MM-DD date")
        if parsed and effective_from <= parsed[-1][0]:
            raise ValueError(
                f"{where} dates must be strictly increasing, got {raw_day!r} "
                f"after {parsed[-1][0].isoformat()!r}")
        for key in _PRICE_KEYS:
            value = change.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{where} entry {raw_day!r} {key} {value!r} is not a non-negative number")
        parsed.append((effective_from, change))
    return parsed


def _parse_iso_day(value):
    # date.fromisoformat also accepts "20261201" and week dates; only YYYY-MM-DD round-trips.
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def price(model, input_tokens, output_tokens, rates=None, on=None):
    """USD estimate for a call, or None when the model has no known rate.

    None (not 0) lets callers distinguish "no price on file" from a genuinely
    free call, so the UI can say "cost unavailable" instead of implying $0. The
    figure is an estimate: it prices the <=200k-context tier at the rate in
    effect on `on` (default: today, UTC) and does not model cache discounts or
    free-tier rate limits. `on` is ignored when `rates` is given.
    """
    if rates is None:
        rates, _ = load_pricing(on=on)
    rate = rates.get(model)
    if rate is None:
        return None
    return (input_tokens / 1_000_000) * rate["input"] + \
        (output_tokens / 1_000_000) * rate["output"]
