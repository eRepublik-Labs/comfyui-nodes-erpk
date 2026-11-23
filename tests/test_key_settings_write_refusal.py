# ABOUTME: Runs ComfyUI's settings write routes behind the pack's middleware on a real aiohttp app.
# ABOUTME: A page loaded before the key store must not save an ERPK API key into comfy.settings.json.

import asyncio
import json

import pytest
from aiohttp import FormData, web
from aiohttp.test_utils import TestClient, TestServer

from tests.test_shared_workflow_routes import load_entrypoint

KEY = "xai-0123456789abcdefWXYZ"
REFUSAL = {"error": "ERPK API keys are saved in Settings > ERPK > API Keys. Reload this page."}


@pytest.fixture
def app_and_writes(tmp_path, monkeypatch):
    """The entrypoint's app with stand-ins for ComfyUI's settings write
    handlers, which record what they read from each request they receive."""
    user_dir = tmp_path / "comfy" / "user"
    user_dir.mkdir(parents=True)
    workflows = tmp_path / "shared_workflows"
    workflows.mkdir()
    app, _ = load_entrypoint(monkeypatch, user_dir, workflows)

    writes = []

    async def write_setting(request):
        writes.append((request.path, await request.json()))
        return web.Response(status=200)

    async def read_setting(request):
        writes.append((request.path, None))
        return web.json_response(None)

    async def write_userdata(request):
        writes.append((request.path, (await request.read()).decode()))
        return web.Response(status=200)

    async def upload(request):
        form = await request.post()
        writes.append((request.path, form["image"].file.read().decode()))
        return web.Response(status=200)

    # ComfyUI serves every route twice, with and without /api (server.add_routes).
    for prefix in ("", "/api"):
        app.router.add_post(prefix + "/settings/{id}", write_setting)
        app.router.add_post(prefix + "/settings", write_setting)
        app.router.add_get(prefix + "/settings/{id}", read_setting)
        app.router.add_post(prefix + "/upload/image", upload)
        app.router.add_post(prefix + "/userdata/{file}", write_userdata)
    return app, writes


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


@pytest.mark.parametrize("path", ["/api/settings/ERPK.XAI_API_KEY", "/settings/ERPK.XAI_API_KEY"])
def test_saving_one_key_setting_is_refused(app_and_writes, path):
    app, writes = app_and_writes

    status, text = call(app, "post", path, json=KEY)

    assert status == 403
    assert json.loads(text) == REFUSAL
    assert writes == []


@pytest.mark.parametrize("path", ["/api/settings", "/settings"])
def test_saving_settings_that_include_a_key_setting_is_refused(app_and_writes, path):
    app, writes = app_and_writes

    status, text = call(app, "post", path, json={"Comfy.Locale": "en", "ERPK.XAI_API_KEY": KEY})

    assert status == 403
    assert json.loads(text) == REFUSAL
    assert writes == []


def test_saving_settings_without_a_key_setting_reaches_comfyui_with_its_body(app_and_writes):
    app, writes = app_and_writes
    settings = {"Comfy.Locale": "en", "ERPK.PARALLEL_WORKERS": 4}

    status, _ = call(app, "post", "/api/settings", json=settings)

    assert status == 200
    assert writes == [("/api/settings", settings)]


@pytest.mark.parametrize("setting_id", ["ERPK.PARALLEL_WORKERS", "Comfy.Locale"])
def test_saving_another_setting_reaches_comfyui(app_and_writes, setting_id):
    app, writes = app_and_writes

    status, _ = call(app, "post", f"/api/settings/{setting_id}", json="value")

    assert status == 200
    assert writes == [(f"/api/settings/{setting_id}", "value")]


def test_reading_a_key_setting_reaches_comfyui(app_and_writes):
    app, writes = app_and_writes

    status, _ = call(app, "get", "/api/settings/ERPK.XAI_API_KEY")

    assert status == 200
    assert writes == [("/api/settings/ERPK.XAI_API_KEY", None)]


def test_an_upload_naming_a_key_setting_reaches_comfyui_with_its_form(app_and_writes):
    app, writes = app_and_writes
    form = FormData()
    form.add_field("image", b"ERPK.XAI_API_KEY", filename="note.txt", content_type="text/plain")

    status, _ = call(app, "post", "/api/upload/image", data=form)

    assert status == 200
    assert writes == [("/api/upload/image", "ERPK.XAI_API_KEY")]


# ComfyUI percent-decodes the file name once more and resolves it inside the
# user's directory (user_manager.get_request_user_filepath), so these all
# name the user's comfy.settings.json.
@pytest.mark.parametrize("file", [
    "comfy.settings.json",
    "workflows%2F..%2Fcomfy.settings.json",
    "workflows%252F..%252Fcomfy.settings.json",
])
def test_writing_a_key_setting_into_the_settings_file_is_refused(app_and_writes, file):
    app, writes = app_and_writes
    body = json.dumps({"Comfy.Locale": "en", "ERPK.XAI_API_KEY": KEY}, indent=4)

    status, text = call(app, "post", f"/api/userdata/{file}", data=body)

    assert status == 403
    assert json.loads(text) == REFUSAL
    assert writes == []


def test_writing_the_settings_file_without_a_key_setting_reaches_comfyui(app_and_writes):
    app, writes = app_and_writes
    body = json.dumps({"Comfy.Locale": "en"}, indent=4)

    status, _ = call(app, "post", "/api/userdata/comfy.settings.json", data=body)

    assert status == 200
    assert writes == [("/api/userdata/comfy.settings.json", body)]


def test_writing_another_user_file_that_names_a_key_setting_reaches_comfyui(app_and_writes):
    app, writes = app_and_writes

    status, _ = call(app, "post", "/api/userdata/workflows%2Fnotes.json", data="ERPK.XAI_API_KEY")

    assert status == 200
    assert writes == [("/api/userdata/workflows/notes.json", "ERPK.XAI_API_KEY")]
