# ABOUTME: Runs the /erpk/keys routes and the import-time key migration on a real aiohttp app.
# ABOUTME: No route may return a full key, and writes need the page's write token.

import asyncio
import json

import pytest
from aiohttp.test_utils import TestClient, TestServer

from erpk.key_store import KeyStore
from erpk.write_guard import TOKEN_HEADER, write_token
from tests.test_shared_workflow_routes import load_entrypoint

KEY = "sk-ant-api03-0123456789abcdefWXYZ"

NOTHING_SET = {
    provider: {"set": False, "last4": None}
    for provider in ("anthropic", "google", "openai", "xai", "wavespeed", "byteplus")
}


@pytest.fixture
def user_dir(tmp_path):
    folder = tmp_path / "comfy" / "user"
    folder.mkdir(parents=True)
    return folder


@pytest.fixture
def store(tmp_path):
    return KeyStore(str(tmp_path / "comfy" / "erpk_keys"))


@pytest.fixture
def server(tmp_path, user_dir, monkeypatch):
    """Loads the entrypoint and returns (app, PromptServer stub)."""
    workflows = tmp_path / "shared_workflows"
    workflows.mkdir()
    return load_entrypoint(monkeypatch, user_dir, workflows)


def call(app, method, path, **kwargs):
    async def run():
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await getattr(client, method)(path, **kwargs)
            return resp.status, await resp.text()
        finally:
            await client.close()

    return asyncio.run(run())


def test_status_route_reports_only_the_last_four_characters(server, store):
    app, prompt_server = server
    prompt_server.user_manager.get_request_user_id.return_value = "alice"
    store.set("alice", "anthropic", KEY)

    status, text = call(app, "get", "/erpk/keys")

    assert status == 200
    assert json.loads(text) == {**NOTHING_SET, "anthropic": {"set": True, "last4": "WXYZ"}}
    assert KEY not in text


def test_save_without_the_write_token_is_refused_before_touching_the_store(server, store):
    app, _ = server

    status, text = call(app, "post", "/erpk/keys", json={"provider": "anthropic", "key": KEY})

    assert status == 403
    assert json.loads(text) == {"error": f"Missing {TOKEN_HEADER} header"}
    assert store.get("default", "anthropic") is None


def test_save_with_a_wrong_write_token_is_refused(server, store):
    app, _ = server

    status, text = call(app, "post", "/erpk/keys", json={"provider": "anthropic", "key": KEY},
                        headers={TOKEN_HEADER: "guess"})

    assert status == 403
    assert json.loads(text) == {"error": f"Invalid {TOKEN_HEADER}"}
    assert store.get("default", "anthropic") is None


def test_save_stores_the_key_for_the_requesting_user_and_returns_only_status(server, store):
    app, prompt_server = server
    prompt_server.user_manager.get_request_user_id.return_value = "alice"

    status, text = call(app, "post", "/erpk/keys", json={"provider": "anthropic", "key": KEY},
                        headers={TOKEN_HEADER: write_token()})

    assert status == 200
    assert json.loads(text) == {**NOTHING_SET, "anthropic": {"set": True, "last4": "WXYZ"}}
    assert KEY not in text
    assert store.get("alice", "anthropic") == KEY
    assert store.get("default", "anthropic") is None


def test_a_null_key_clears_it(server, store):
    app, _ = server
    store.set("default", "anthropic", KEY)

    status, text = call(app, "post", "/erpk/keys", json={"provider": "anthropic", "key": None},
                        headers={TOKEN_HEADER: write_token()})

    assert status == 200
    assert json.loads(text) == NOTHING_SET
    assert store.get("default", "anthropic") is None


@pytest.mark.parametrize("body,error", [
    ({"provider": "mistral", "key": KEY}, "Unknown provider: 'mistral'"),
    ({"provider": "anthropic"}, "Missing 'key' field"),
    ({"provider": "anthropic", "key": "sk-ant api03 0123456789"}, "API key contains whitespace"),
    (["anthropic", KEY], "Body must be a JSON object"),
])
def test_bad_input_is_a_400_that_never_echoes_the_key(server, store, body, error):
    app, _ = server

    status, text = call(app, "post", "/erpk/keys", json=body, headers={TOKEN_HEADER: write_token()})

    assert status == 400
    assert json.loads(text) == {"error": error}
    assert store.status("default") == NOTHING_SET


@pytest.mark.parametrize("method,kwargs", [
    ("get", {}),
    ("post", {"json": {"provider": "anthropic", "key": KEY}, "headers": {TOKEN_HEADER: write_token()}}),
])
def test_an_unknown_user_is_refused(server, store, method, kwargs):
    app, prompt_server = server
    prompt_server.user_manager.get_request_user_id.side_effect = KeyError("Unknown user: mallory")

    status, text = call(app, method, "/erpk/keys", **kwargs)

    assert status == 403
    assert json.loads(text) == {"error": "Unknown user: mallory"}
    assert store.status("mallory") == NOTHING_SET


def test_loading_the_package_moves_keys_out_of_comfy_settings(tmp_path, user_dir, store, monkeypatch, console):
    alice = user_dir / "alice"
    alice.mkdir()
    settings = alice / "comfy.settings.json"
    settings.write_text(json.dumps({"Comfy.Locale": "ro", "ERPK.ANTHROPIC_API_KEY": KEY}, indent=4), encoding="utf-8")
    workflows = tmp_path / "shared_workflows"
    workflows.mkdir()

    load_entrypoint(monkeypatch, user_dir, workflows)

    assert settings.read_text(encoding="utf-8") == json.dumps({"Comfy.Locale": "ro"}, indent=4)
    assert store.get("alice", "anthropic") == KEY
    assert ("[ERPK] API keys for user alice: moved 1 to the key store (anthropic), "
            "removed 0 already stored (), removed 0 empty (), set aside 0 unusable values ()\n") in console()
