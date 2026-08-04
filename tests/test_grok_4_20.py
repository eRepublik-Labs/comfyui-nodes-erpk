# ABOUTME: Locks the Grok 4.20 family into TEXT_MODELS and keeps retired IDs out.
# ABOUTME: grok-4, grok-4-fast and grok-3-mini were retired 2026-05-15.

"""
xAI publishes its live catalog as embedded JSON on docs.x.ai/docs/models. The
canonical `name` of each 4.20 variant carries the 0309 date; the short forms
(grok-4.20, grok-4.20-reasoning, ...) are aliases onto it. We offer the
canonical names so a saved workflow keeps pointing at the same model when an
alias is later repointed.

grok-4, grok-4-fast and grok-3-mini return zero hits across every cluster in
that catalog and are not listed as an alias of anything — they are gone, and a
node that still offers them produces a dead call.
"""

from erpk.grok.grok_api.client import GrokClient
from erpk.grok.nodes import TEXT_MODELS


REASONING = "grok-4.20-0309-reasoning"
NON_REASONING = "grok-4.20-0309-non-reasoning"
MULTI_AGENT = "grok-4.20-multi-agent-0309"

RETIRED = ["grok-4", "grok-4-fast", "grok-3-mini", "grok-3", "grok-code-fast-1"]


def test_grok_4_20_reasoning_offered():
    assert REASONING in TEXT_MODELS


def test_grok_4_20_non_reasoning_offered():
    assert NON_REASONING in TEXT_MODELS


def test_grok_4_20_multi_agent_offered():
    assert MULTI_AGENT in TEXT_MODELS


def test_retired_models_not_offered():
    for model in RETIRED:
        assert model not in TEXT_MODELS, f"{model} was retired and must not be selectable"


def test_flagship_and_coding_models_retained():
    # grok-4.5 is the flagship; grok-4.3 is the documented migration target for
    # the retired IDs; grok-build-0.1 is the current coding model.
    for model in ("grok-4.5", "grok-4.3", "grok-build-0.1"):
        assert model in TEXT_MODELS


def test_default_text_model_is_offered():
    assert GrokClient.DEFAULT_TEXT_MODEL in TEXT_MODELS
