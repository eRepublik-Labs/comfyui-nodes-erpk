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
    "claude-fable-5-1",
    "claude-fable-5",
]

DEFAULT_TEXT_MODEL = TEXT_MODELS[0]

# Sentinel offered by nodes that can defer to the connected client's model.
INHERIT_FROM_CLIENT = "(inherit from client)"

# output_config.effort levels. Every offered model accepts all five; the
# sentinel omits the field so each model keeps its own default (high, or
# medium on Opus 5.5).
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
