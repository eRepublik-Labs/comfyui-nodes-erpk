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


@pytest.fixture
def routes_app(tmp_path, monkeypatch):
    """Load the package entrypoint against a stub PromptServer and return its app."""
    server_stub = types.ModuleType("server")
    prompt_server = MagicMock()
    prompt_server.routes = web.RouteTableDef()
    prompt_server.user_manager.get_request_user_id.return_value = "default"
    prompt_server.user_manager.users = {"default": "default"}
    server_stub.PromptServer = types.SimpleNamespace(instance=prompt_server)
    monkeypatch.setitem(sys.modules, "server", server_stub)

    from erpk import shared_workflows
    monkeypatch.setattr(shared_workflows, "STORAGE_DIR", str(tmp_path))

    # The entrypoint uses relative imports, so it is loaded as a member of the
    # synthetic erpk package that conftest registers.
    entry_path = os.path.join(os.path.dirname(shared_workflows.__file__), "__init__.py")
    spec = importlib.util.spec_from_file_location("erpk.entrypoint", entry_path)
    module = importlib.util.module_from_spec(spec)
    # A file named __init__.py is treated as a package; make its relative
    # imports resolve against erpk instead.
    module.__package__ = "erpk"
    monkeypatch.setitem(sys.modules, "erpk.entrypoint", module)
    spec.loader.exec_module(module)

    app = web.Application()
    app.add_routes(prompt_server.routes)
    return app


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
