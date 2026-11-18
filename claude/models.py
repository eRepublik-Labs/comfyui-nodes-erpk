# ABOUTME: Canonical list of Claude models offered by this package's node dropdowns.
# ABOUTME: Imported by every node that exposes a model picker so the options cannot drift apart.

# Ordered newest-first within each family. The first entry is the default the
# node schemas fall back to. Adding an entry here is safe for saved workflows;
# removing one makes ComfyUI reject any workflow that still selects it, because
# combo values are validated before execute() runs.
#
# Every model listed here also needs an entry in pricing.json and in
# TokenManager.CONTEXT_WINDOWS.
TEXT_MODELS = [
    "claude-sonnet-5-5",
    "claude-sonnet-5",
    "claude-opus-5-5",
    "claude-opus-5",
    "claude-fable-5-2",
    "claude-fable-5-1",
    "claude-fable-5",
    "claude-haiku-5-5",
]

DEFAULT_TEXT_MODEL = TEXT_MODELS[0]

# Sentinel offered by nodes that can defer to the connected client's model.
INHERIT_FROM_CLIENT = "(inherit from client)"

# output_config.effort levels. Every offered model accepts all five; the
# sentinel omits the field so each model keeps its own default (high, or
# medium on Opus 5.5 and Haiku 5.5).
MODEL_DEFAULT_EFFORT = "(model default)"
EFFORT_OPTIONS = [MODEL_DEFAULT_EFFORT, "low", "medium", "high", "xhigh", "max"]
EFFORT_TOOLTIP = (
    "How much effort Claude spends (thinking depth, tool calls, answer length). "
    "Higher costs more tokens and time. (model default) leaves the model's own default."
)


def effort_input():
    """The effort Combo every Claude node that sends a Messages request appends last."""
    from comfy_api.latest import IO

    return IO.Combo.Input(
        "effort",
        options=EFFORT_OPTIONS,
        default=MODEL_DEFAULT_EFFORT,
        optional=True,
        tooltip=EFFORT_TOOLTIP,
    )


def effort_kwargs(value):
    """send_request kwargs for an effort widget value; empty for the model default."""
    return {} if value in (None, MODEL_DEFAULT_EFFORT) else {"effort": value}


# The thinking object that turns thinking off on each model, and the efforts
# the model rejects alongside it (400, measured 2026-11-18). Sonnet 5.5 takes
# between_tools in place of disabled. A model absent here always thinks and
# rejects both: Opus 5.5 (measured) and every Fable (read in the docs).
THINKING_OFF = {
    "claude-sonnet-5-5": ({"type": "between_tools"}, ("xhigh", "max")),
    "claude-sonnet-5": ({"type": "disabled"}, ()),
    "claude-opus-5": ({"type": "disabled"}, ("xhigh", "max")),
    "claude-haiku-5-5": ({"type": "disabled"}, ("xhigh", "max")),
}

THINKING_ADAPTIVE = "adaptive"
THINKING_OPTIONS = [THINKING_ADAPTIVE, "off"]
THINKING_TOOLTIP = (
    "adaptive lets Claude decide when and how much to think, steered by effort. "
    "off answers without thinking first, on Sonnet 5.5, Sonnet 5, Opus 5 and Haiku 5.5. "
    "Sonnet 5.5, Opus 5 and Haiku 5.5 allow it only at effort high or below. "
    "Opus 5.5 and every Fable always think, so off fails on them."
)


def thinking_input():
    """The thinking Combo every Claude node that sends a Messages request appends after effort."""
    from comfy_api.latest import IO

    return IO.Combo.Input(
        "thinking",
        options=THINKING_OPTIONS,
        default=THINKING_ADAPTIVE,
        optional=True,
        tooltip=THINKING_TOOLTIP,
    )


def thinking_kwargs(value):
    """send_request kwargs for a thinking widget value; empty for adaptive."""
    return {} if value in (None, THINKING_ADAPTIVE) else {"thinking_off": True}


def thinking_off_config(model, effort):
    """The thinking object that turns thinking off on model at effort (None
    for the model's default effort, which is high or lower on every model).

    Raises ValueError for a combination the model rejects, so it never reaches
    the API and never silently runs with thinking on.
    """
    if model not in THINKING_OFF:
        raise ValueError(
            f"{model} cannot turn thinking off: it always thinks. Set thinking to adaptive, "
            f"or pick a model that can: {', '.join(THINKING_OFF)}"
        )
    config, rejected_efforts = THINKING_OFF[model]
    if effort in rejected_efforts:
        raise ValueError(
            f"{model} rejects effort '{effort}' with thinking off. "
            f"Set effort to high or below, or set thinking to adaptive"
        )
    return config
