# ABOUTME: Prices a Gemini scan from token counts using gemini/pricing.json rates.
# ABOUTME: Torch/genai-free so the scan engine computes cost without heavy imports.

import json
import os

# Gemini owns its prices (mirrors claude/pricing.json next to claude/token_counter.py).
PRICING_PATH = os.path.join(os.path.dirname(__file__), "..", "gemini", "pricing.json")


def load_pricing(path=PRICING_PATH):
    """Return ({model_id: {"input": per_mtok, "output": per_mtok}}, last_updated).

    A missing or unreadable file yields ({}, "unknown") — pricing is best-effort
    metadata, never a reason to fail a scan. The schema matches claude/pricing.json
    (input_price_per_mtok / output_price_per_mtok).
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}, "unknown"
    rates = {}
    for model_id, model_data in data.get("models", {}).items():
        if not isinstance(model_data, dict):
            continue
        rates[model_id] = {
            "input": model_data.get("input_price_per_mtok", 0) or 0,
            "output": model_data.get("output_price_per_mtok", 0) or 0,
        }
    return rates, data.get("_last_updated", "unknown")


def price(model, input_tokens, output_tokens, rates=None):
    """USD estimate for a call, or None when the model has no known rate.

    None (not 0) lets callers distinguish "no price on file" from a genuinely
    free call, so the UI can say "cost unavailable" instead of implying $0. The
    figure is an estimate: it prices the <=200k-context tier and does not model
    cache discounts or free-tier rate limits.
    """
    if rates is None:
        rates, _ = load_pricing()
    rate = rates.get(model)
    if rate is None:
        return None
    return (input_tokens / 1_000_000) * rate["input"] + \
        (output_tokens / 1_000_000) * rate["output"]
