# ABOUTME: Canonical list of Claude models offered by this package's node dropdowns.
# ABOUTME: Imported by every node that exposes a model picker so the options cannot drift apart.

# Ordered newest-first within each family. The first entry is the default the
# node schemas fall back to. Adding an entry here is safe for saved workflows;
# removing one makes ComfyUI reject any workflow that still selects it, because
# combo values are validated before execute() runs.
#
# Every model listed here also needs an entry in pricing.json and in
# TokenManager.CONTEXT_WINDOWS, and — for Claude 4.7 and later, which reject
# sampling params — in ClaudeClient.THINKING_ONLY_MODELS.
TEXT_MODELS = [
    "claude-sonnet-5",
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-fable-5",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5-20250929",
]

DEFAULT_TEXT_MODEL = TEXT_MODELS[0]

# Sentinel offered by nodes that can defer to the connected client's model.
INHERIT_FROM_CLIENT = "(inherit from client)"
