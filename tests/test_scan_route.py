# ABOUTME: Tests for the /erpk/scan aiohttp route handler and its pure request helpers.
# ABOUTME: Covers data-URL decode, max_objects clamping, response/error shapes, and registration.

"""
Validates utils.scan_route: the torch-free helpers (clamp_max_objects,
decode_data_url) and the async handle_scan handler driven by a fake request and
an injected fake engine. PIL decode is exercised with a real generated PNG; the
Gemini engine is never invoked (dispatch is monkeypatched), keeping the suite
network- and key-free.
"""

import asyncio
import base64
import io
import json

import pytest

from utils import scan_engine, scan_route
from utils.scan_route import clamp_max_objects, decode_data_url, handle_scan, register


def _png_data_url():
    """A tiny real PNG as a base64 data URL, so PIL.Image.open succeeds."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


class FakeRequest:
    """Minimal stand-in exposing the async json() handle_scan reads."""

    def __init__(self, payload, raise_json=False, content_length=None):
        self._payload = payload
        self._raise_json = raise_json
        self.content_length = content_length

    async def json(self):
        if self._raise_json:
            raise ValueError("bad json")
        return self._payload


def _body(response):
    return json.loads(response.body.decode())


@pytest.fixture(autouse=True)
def ensure_local_engine(monkeypatch):
    """Guarantee scan_engine.local_scan exists while the engine lands in parallel.

    handle_scan resolves the default engine via getattr at request time; this
    stub keeps the route's dispatch tests deterministic before the real
    local_scan ships, and steps aside once it does.
    """
    if not hasattr(scan_engine, "local_scan"):
        async def _stub(image, max_objects, model):
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "local_scan", _stub, raising=False)


class TestClampMaxObjects:
    def test_default_for_missing(self):
        assert clamp_max_objects(None) == scan_engine.DEFAULT_MAX_OBJECTS

    def test_passthrough_in_range(self):
        assert clamp_max_objects(12) == 12

    def test_clamps_low(self):
        assert clamp_max_objects(0) == 1
        assert clamp_max_objects(-5) == 1

    def test_clamps_high(self):
        assert clamp_max_objects(9999) == scan_engine.MAX_OBJECTS_CEILING

    def test_default_for_non_int(self):
        assert clamp_max_objects("abc") == scan_engine.DEFAULT_MAX_OBJECTS


class TestDecodeDataUrl:
    def test_decodes_data_url(self):
        raw = decode_data_url("data:image/png;base64,QUJD")
        assert raw == b"ABC"

    def test_decodes_raw_base64(self):
        assert decode_data_url("QUJD") == b"ABC"

    def test_missing_raises(self):
        with pytest.raises(ValueError):
            decode_data_url(None)
        with pytest.raises(ValueError):
            decode_data_url("")

    def test_malformed_raises(self):
        with pytest.raises(ValueError):
            decode_data_url("data:image/png;base64")
        with pytest.raises(ValueError):
            decode_data_url("@@@not base64@@@")


class TestHandleScan:
    def test_oversized_body_rejected(self):
        req = FakeRequest({}, content_length=scan_route.SCAN_MAX_BODY_BYTES + 1)
        resp = asyncio.run(handle_scan(req))
        assert resp.status == 413
        assert "error" in _body(resp)

    def test_success_returns_objects_and_cost(self, monkeypatch):
        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            return {
                "objects": [{"name": "car", "box": {"x": 0, "y": 0, "w": 0.5, "h": 0.5},
                             "mask": None, "group": "car", "depth_rank": 0}],
                "cost": {"usd": 0.031, "input_tokens": 2300, "output_tokens": 1550,
                         "calls": 2, "model": "gemini-2.5-flash"},
            }

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        req = FakeRequest({"image": _png_data_url(), "max_objects": 5})
        resp = asyncio.run(handle_scan(req))
        assert resp.status == 200
        body = _body(resp)
        assert body["objects"][0]["name"] == "car"
        assert body["cost"]["usd"] == 0.031
        assert body["cost"]["input_tokens"] == 2300

    def test_local_cost_is_null(self, monkeypatch):
        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        resp = asyncio.run(handle_scan(FakeRequest({"image": _png_data_url()})))
        assert resp.status == 200
        assert _body(resp)["cost"] is None

    def test_max_objects_clamped_before_engine(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["max_objects"] = max_objects
            seen["model"] = model
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        req = FakeRequest({"image": _png_data_url(), "max_objects": 9999})
        asyncio.run(handle_scan(req))
        assert seen["max_objects"] == scan_engine.MAX_OBJECTS_CEILING
        assert seen["model"] is None

    def test_blank_model_becomes_none(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["model"] = model
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        req = FakeRequest({"image": _png_data_url(), "model": "  "})
        asyncio.run(handle_scan(req))
        assert seen["model"] is None

    def test_explicit_model_forwarded(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["model"] = model
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        req = FakeRequest({"image": _png_data_url(), "model": "gemini-2.5-flash"})
        asyncio.run(handle_scan(req))
        assert seen["model"] == "gemini-2.5-flash"

    def test_segmenter_forwarded(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["segmenter"] = segmenter
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        req = FakeRequest({"image": _png_data_url(),
                           "segmenter": "facebook/sam-vit-large"})
        asyncio.run(handle_scan(req))
        assert seen["segmenter"] == "facebook/sam-vit-large"

    def test_blank_segmenter_becomes_none(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["segmenter"] = segmenter
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        asyncio.run(handle_scan(FakeRequest({"image": _png_data_url(), "segmenter": "  "})))
        assert seen["segmenter"] is None

    def test_missing_image_is_400(self):
        resp = asyncio.run(handle_scan(FakeRequest({})))
        assert resp.status == 400
        assert "image" in _body(resp)["error"].lower()

    def test_malformed_image_is_400(self):
        resp = asyncio.run(handle_scan(FakeRequest({"image": "data:image/png;base64,@@@"})))
        assert resp.status == 400

    def test_undecodable_image_is_400(self):
        # Valid base64, but not an image PIL can open.
        bogus = base64.b64encode(b"not an image").decode()
        resp = asyncio.run(handle_scan(FakeRequest({"image": bogus})))
        assert resp.status == 400

    def test_invalid_json_body_is_400(self):
        resp = asyncio.run(handle_scan(FakeRequest(None, raise_json=True)))
        assert resp.status == 400

    def test_engine_failure_is_502(self, monkeypatch):
        async def boom(image, max_objects, model, engine=None, segmenter=None):
            raise RuntimeError("Gemini blocked")

        monkeypatch.setattr(scan_engine, "scan", boom)
        resp = asyncio.run(handle_scan(FakeRequest({"image": _png_data_url()})))
        assert resp.status == 502
        assert "Gemini blocked" in _body(resp)["error"]


class TestEngineSelector:
    """The route maps the request's engine name to a scan_engine coroutine."""

    def _capture_engine(self, monkeypatch):
        seen = {}

        async def fake_scan(image, max_objects, model, engine=None, segmenter=None):
            seen["engine"] = engine
            return {"objects": [], "cost": None}

        monkeypatch.setattr(scan_engine, "scan", fake_scan)
        return seen

    def test_default_engine_is_gemini(self, monkeypatch):
        seen = self._capture_engine(monkeypatch)
        resp = asyncio.run(handle_scan(FakeRequest({"image": _png_data_url()})))
        assert resp.status == 200
        assert seen["engine"] is scan_engine.gemini_scan

    def test_explicit_local_engine(self, monkeypatch):
        seen = self._capture_engine(monkeypatch)
        req = FakeRequest({"image": _png_data_url(), "engine": "local"})
        asyncio.run(handle_scan(req))
        assert seen["engine"] is scan_engine.local_scan

    def test_explicit_gemini_engine(self, monkeypatch):
        seen = self._capture_engine(monkeypatch)
        req = FakeRequest({"image": _png_data_url(), "engine": "gemini"})
        asyncio.run(handle_scan(req))
        assert seen["engine"] is scan_engine.gemini_scan

    def test_unknown_engine_is_400(self, monkeypatch):
        self._capture_engine(monkeypatch)
        req = FakeRequest({"image": _png_data_url(), "engine": "moondream"})
        resp = asyncio.run(handle_scan(req))
        assert resp.status == 400
        assert _body(resp)["error"] == "Unknown engine"

    def test_non_string_engine_is_400(self, monkeypatch):
        self._capture_engine(monkeypatch)
        req = FakeRequest({"image": _png_data_url(), "engine": 7})
        resp = asyncio.run(handle_scan(req))
        assert resp.status == 400
        assert _body(resp)["error"] == "Unknown engine"


class TestScanModels:
    """GET /erpk/scan/models reports the Gemini model list and default.

    The handler does a relative `..gemini` import, so it is loaded through the
    synthetic `erpk` package (conftest) where that import resolves, mirroring
    how the Gemini-touching modules are exercised elsewhere.
    """

    def _handler(self):
        from erpk.utils.scan_route import handle_scan_models

        return handle_scan_models

    def test_returns_models_and_default(self):
        from gemini.gemini_api.client import GeminiClient

        resp = asyncio.run(self._handler()(FakeRequest({})))
        assert resp.status == 200
        body = _body(resp)
        assert body["models"] == list(GeminiClient.MODELS)
        assert body["default"] == GeminiClient.DEFAULT_MODEL

    def test_default_is_in_models(self):
        body = _body(asyncio.run(self._handler()(FakeRequest({}))))
        assert body["default"] in body["models"]


class TestScanSegmenters:
    """GET /erpk/scan/segmenters reports the runnable backbones and the default."""

    def test_returns_default_and_list_shape(self):
        # Works with or without transformers: the list is empty when transformers
        # is absent (graceful degradation), populated when it is present.
        from utils.scan_route import handle_scan_segmenters

        resp = asyncio.run(handle_scan_segmenters(FakeRequest({})))
        assert resp.status == 200
        body = _body(resp)
        assert body["default"] == scan_engine.DEFAULT_SEGMENTER
        assert isinstance(body["segmenters"], list)
        for s in body["segmenters"]:
            assert {"id", "label", "family", "downloaded"} <= set(s)

    def test_lists_backbones_when_transformers_present(self):
        pytest.importorskip("transformers")
        from utils.scan_route import handle_scan_segmenters

        body = _body(asyncio.run(handle_scan_segmenters(FakeRequest({}))))
        ids = [s["id"] for s in body["segmenters"]]
        assert scan_engine.DEFAULT_SEGMENTER in ids


class TestRegister:
    def test_register_adds_post_route(self):
        from aiohttp import web

        routes = web.RouteTableDef()

        class FakeServer:
            pass

        server = FakeServer()
        server.routes = routes
        register(server)
        registered = list(routes)
        assert any(
            getattr(r, "path", None) == "/erpk/scan" and r.method == "POST"
            for r in registered
        )

    def test_register_adds_models_get_route(self):
        from aiohttp import web

        routes = web.RouteTableDef()

        class FakeServer:
            pass

        server = FakeServer()
        server.routes = routes
        register(server)
        registered = list(routes)
        assert any(
            getattr(r, "path", None) == "/erpk/scan/models" and r.method == "GET"
            for r in registered
        )

    def test_register_adds_segmenters_get_route(self):
        from aiohttp import web

        routes = web.RouteTableDef()

        class FakeServer:
            pass

        server = FakeServer()
        server.routes = routes
        register(server)
        registered = list(routes)
        assert any(
            getattr(r, "path", None) == "/erpk/scan/segmenters" and r.method == "GET"
            for r in registered
        )


class TestRegistrationWiring:
    """The root package wires the route from its real location."""

    def test_root_init_imports_scan_route_from_utils(self):
        import ast
        import os
        root_init = os.path.join(os.path.dirname(__file__), "..", "__init__.py")
        with open(root_init) as f:
            tree = ast.parse(f.read())
        imports = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and any(alias.name == "scan_route" for alias in node.names)
        ]
        assert imports, "root __init__.py no longer imports scan_route"
        for node in imports:
            assert node.level == 1 and node.module == "utils", (
                "scan_route lives in utils/; importing it from the package "
                "root raises ModuleNotFoundError at ComfyUI startup and the "
                "route silently never registers (POST /erpk/scan -> 405)"
            )
