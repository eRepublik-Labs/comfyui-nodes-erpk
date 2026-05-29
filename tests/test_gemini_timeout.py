# ABOUTME: Regression test for the Gemini HttpOptions timeout fix.
# ABOUTME: Asserts every genai.Client built via GeminiClient carries a bounded request timeout.

import importlib
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)


def _reload_client_module():
    """Reload the client module to get a fresh import for timeout assertions."""
    if "gemini.gemini_api.client" in sys.modules:
        return importlib.reload(sys.modules["gemini.gemini_api.client"])
    return importlib.import_module("gemini.gemini_api.client")


def test_genai_client_constructed_with_http_options_timeout():
    """GeminiClient must pass HttpOptions with a positive timeout when building genai.Client."""
    client_mod = _reload_client_module()

    with patch.object(client_mod.genai, "Client") as mock_client_ctor:
        mock_client_ctor.return_value = MagicMock()
        client_mod.GeminiClient(api_key="test-key-not-real")

    assert mock_client_ctor.called, "genai.Client should be constructed"
    kwargs = mock_client_ctor.call_args.kwargs
    assert "http_options" in kwargs, "Client must receive http_options to bound request time"
    http_options = kwargs["http_options"]
    timeout = getattr(http_options, "timeout", None)
    assert isinstance(timeout, int) and timeout > 0, f"timeout must be a positive int, got {timeout!r}"


def test_env_var_is_ignored(monkeypatch):
    """The legacy ERPK_GEMINI_TIMEOUT_MS env var no longer affects the timeout.

    The timeout is now sourced from the ERPK.GEMINI_TIMEOUT_MS ComfyUI setting;
    with no setting available (test env) it falls back to the 5-minute default
    regardless of the env var.
    """
    monkeypatch.setenv("ERPK_GEMINI_TIMEOUT_MS", "12345")
    client_mod = _reload_client_module()

    with patch.object(client_mod.genai, "Client") as mock_client_ctor:
        mock_client_ctor.return_value = MagicMock()
        client_mod.GeminiClient(api_key="test-key-not-real")

    http_options = mock_client_ctor.call_args.kwargs["http_options"]
    assert http_options.timeout == 300000, "env var must be ignored; default applies"


def test_resolve_timeout_reads_comfy_setting(monkeypatch):
    """resolve_timeout_ms() reads ERPK.GEMINI_TIMEOUT_MS from ComfyUI settings."""
    import erpk.settings as erpk_settings
    monkeypatch.setattr(erpk_settings, "get_comfy_setting", lambda *a, **k: 7000)
    from erpk.gemini.gemini_api.cooperative_call import resolve_timeout_ms
    assert resolve_timeout_ms() == 7000
