# ABOUTME: Runs the shared-workflow HTTP routes on a real aiohttp app.
# ABOUTME: Write routes must refuse a request without the page token before touching disk.

import importlib.util
import os
import sys
import types
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from erpk.write_guard import TOKEN_HEADER, write_token


def load_entrypoint(monkeypatch, user_dir, storage_dir):
    """Load the package entrypoint against a stub PromptServer and a ComfyUI
    user dir at user_dir. Returns the aiohttp app and the PromptServer stub."""
    server_stub = types.ModuleType("server")
    prompt_server = MagicMock()
    prompt_server.app = web.Application()
    prompt_server.routes = web.RouteTableDef()
    prompt_server.user_manager.get_request_user_id.return_value = "default"
    prompt_server.user_manager.users = {"default": "default"}
    server_stub.PromptServer = types.SimpleNamespace(instance=prompt_server)
    monkeypatch.setitem(sys.modules, "server", server_stub)

    folder_paths = types.ModuleType("folder_paths")
    folder_paths.get_user_directory = lambda: str(user_dir)
    monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)

    from erpk import shared_workflows
    monkeypatch.setattr(shared_workflows, "STORAGE_DIR", str(storage_dir))

    # The entrypoint uses relative imports, so it is loaded as a member of the
    # synthetic erpk package that conftest registers.
    entry_path = os.path.join(os.path.dirname(shared_workflows.__file__), "__init__.py")
    # Without submodule_search_locations=None a file named __init__.py becomes
    # a package of its own, and its relative imports miss erpk.
    spec = importlib.util.spec_from_file_location("erpk.entrypoint", entry_path, submodule_search_locations=None)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "erpk.entrypoint", module)
    spec.loader.exec_module(module)

    app = prompt_server.app
    app.add_routes(prompt_server.routes)
    return app, prompt_server


@pytest.fixture
def routes_app(tmp_path, tmp_path_factory, monkeypatch):
    user_dir = tmp_path_factory.mktemp("comfy") / "user"
    user_dir.mkdir()
    return load_entrypoint(monkeypatch, user_dir, tmp_path)[0]


async def _client(app):
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def test_save_without_token_is_refused_before_writing(routes_app, tmp_path):
    import asyncio

    async def run():
        client = await _client(routes_app)
        try:
            resp = await client.post("/erpk/shared_workflows", json={"name": "probe", "workflow": {}})
            return resp.status, await resp.json()
        finally:
            await client.close()

    status, body = asyncio.run(run())
    assert status == 403
    assert body == {"error": f"Missing {TOKEN_HEADER} header"}
    assert os.listdir(tmp_path) == []


def test_save_with_token_writes_the_file(routes_app, tmp_path):
    import asyncio

    async def run():
        client = await _client(routes_app)
        try:
            resp = await client.post(
                "/erpk/shared_workflows",
                json={"name": "probe", "workflow": {"nodes": []}},
                headers={TOKEN_HEADER: write_token()},
            )
            return resp.status
        finally:
            await client.close()

    assert asyncio.run(run()) == 200
    assert os.listdir(tmp_path) == ["probe.json"]


@pytest.mark.parametrize("method,path", [
    ("delete", "/erpk/shared_workflows/probe"),
    ("post", "/erpk/shared_workflows/trash/abc/restore"),
    ("delete", "/erpk/shared_workflows/trash/abc"),
])
def test_every_write_route_is_gated(routes_app, method, path):
    import asyncio

    async def run():
        client = await _client(routes_app)
        try:
            resp = await getattr(client, method)(path)
            return resp.status
        finally:
            await client.close()

    assert asyncio.run(run()) == 403


def test_read_routes_stay_open(routes_app):
    import asyncio

    async def run():
        client = await _client(routes_app)
        try:
            listing = await client.get("/erpk/shared_workflows")
            token = await client.get("/erpk/write_token")
            return listing.status, token.status, (await token.json())["token"]
        finally:
            await client.close()

    listing_status, token_status, token = asyncio.run(run())
    assert listing_status == 200
    assert token_status == 200
    assert token == write_token()
