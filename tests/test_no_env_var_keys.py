# ABOUTME: Verifies API keys are NOT resolved from environment variables (security hardening).
# ABOUTME: Resolution order is ComfyUI Settings > node input > config.ini only — no env-var tier.

import importlib

import pytest


# (module_path, class_name, env_var) for the four client-class providers that
# expose _resolve_api_key. Gemini reads two env names, so both are covered.
# Imported under the synthetic `erpk` package (conftest) so the providers'
# relative imports resolve the same way ComfyUI's package loader resolves them.
CLIENT_PROVIDERS = [
    ("erpk.claude.claude_api.client", "ClaudeClient", "ANTHROPIC_API_KEY"),
    ("erpk.openai.openai_api.client", "OpenAIClient", "OPENAI_API_KEY"),
    ("erpk.gemini.gemini_api.client", "GeminiClient", "GOOGLE_API_KEY"),
    ("erpk.gemini.gemini_api.client", "GeminiClient", "GEMINI_API_KEY"),
    ("erpk.grok.grok_api.client", "GrokClient", "XAI_API_KEY"),
]


@pytest.mark.parametrize("module_path, class_name, env_var", CLIENT_PROVIDERS)
def test_env_var_is_ignored_for_client_resolution(
    monkeypatch, tmp_path, module_path, class_name, env_var
):
    """An env var alone must NOT satisfy key resolution.

    With no Settings, no node input, and no config file, a key present only in
    the environment must raise ValueError — the env-var tier has been removed.
    """
    mod = importlib.import_module(module_path)
    client_cls = getattr(mod, class_name)
    monkeypatch.setenv(env_var, "env-sentinel-should-be-ignored")

    # __new__ skips __init__, so _resolve_api_key runs without building an SDK client.
    inst = client_cls.__new__(client_cls)
    missing_config = str(tmp_path / "nonexistent.ini")

    with pytest.raises(ValueError):
        inst._resolve_api_key("", missing_config)


def test_env_var_is_ignored_for_wavespeed(monkeypatch):
    """WaveSpeed's execute() must not fall back to the WAVESPEED_API_KEY env var.

    With no Settings, no node input, and an empty config.ini, a key present only
    in the environment must raise ValueError rather than resolve.
    """
    from erpk.wavespeed.nodes import WaveSpeedAIAPIClient

    monkeypatch.setenv("WAVESPEED_API_KEY", "env-sentinel-should-be-ignored")

    with pytest.raises(ValueError):
        WaveSpeedAIAPIClient.execute(api_key="")
