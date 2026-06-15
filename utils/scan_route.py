# ABOUTME: aiohttp handler for POST /erpk/scan: validates the request, decodes the posted image,
# ABOUTME: and runs the scan engine. PIL and aiohttp.web import lazily so the package imports outside ComfyUI.

import asyncio
import base64
import binascii
import json

from . import scan_engine

# The editor downscales before posting, so anything near this size is not a
# legitimate scan request.
SCAN_MAX_BODY_BYTES = 24 * 1024 * 1024

# Engine name -> scan_engine coroutine attribute. The attribute is resolved at
# request time (not imported) so this module loads even before the local engine
# exists. "gemini" is the default; "local" stays reachable for the local
# Florence/Depth-Anything pipeline.
SCAN_ENGINES = {"local": "local_scan", "gemini": "gemini_scan"}
DEFAULT_SCAN_ENGINE = "gemini"


def clamp_max_objects(value):
    """Coerce the request's max_objects into the supported 1..ceiling range."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        return scan_engine.DEFAULT_MAX_OBJECTS
    return max(1, min(scan_engine.MAX_OBJECTS_CEILING, count))


def decode_data_url(data_url):
    """Decode a base64 data URL (or raw base64 string) into raw image bytes."""
    if not isinstance(data_url, str) or not data_url.strip():
        raise ValueError("Missing 'image' field")
    text = data_url.strip()
    if text.startswith("data:"):
        comma = text.find(",")
        if comma == -1:
            raise ValueError("Malformed image data URL")
        text = text[comma + 1:]
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Malformed image data URL")


async def handle_scan(request):
    """Decode the posted image and return scan objects as JSON."""
    from aiohttp import web

    try:
        # Content-Length is a cheap early-out, but it is absent on chunked
        # uploads, so the actual bytes read are capped too before parsing.
        length = getattr(request, "content_length", None)
        if length is not None and length > SCAN_MAX_BODY_BYTES:
            return web.json_response({"error": "Request body too large"}, status=413)
        try:
            raw = await request.read()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)
        if len(raw) > SCAN_MAX_BODY_BYTES:
            return web.json_response({"error": "Request body too large"}, status=413)
        try:
            body = json.loads(raw)
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)
        if not isinstance(body, dict):
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        engine_name = body.get("engine")
        if engine_name is None:
            engine_name = DEFAULT_SCAN_ENGINE
        if engine_name not in SCAN_ENGINES:
            return web.json_response({"error": "Unknown engine"}, status=400)

        try:
            image_bytes = decode_data_url(body.get("image"))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

        max_objects = clamp_max_objects(body.get("max_objects"))
        model = body.get("model")
        if not isinstance(model, str) or not model.strip():
            model = None

        # Segmenter (SAM backbone) is validated in the engine via
        # resolve_segmenter, which falls back to the default for unknown ids.
        segmenter = body.get("segmenter")
        if not isinstance(segmenter, str) or not segmenter.strip():
            segmenter = None

        from io import BytesIO
        from PIL import Image
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return web.json_response({"error": "Could not decode image"}, status=400)

        engine = getattr(scan_engine, SCAN_ENGINES[engine_name])
        try:
            result = await scan_engine.scan(image, max_objects, model, engine=engine,
                                            segmenter=segmenter)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=502)

        # Engines return {"objects": [...], "cost": {...}|None}; cost is the
        # priced token usage for Gemini scans, None for the local pipeline.
        return web.json_response({
            "objects": result.get("objects", []),
            "cost": result.get("cost"),
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_scan_models(request):
    """Return the selectable Gemini scan models and the default as JSON."""
    from aiohttp import web

    # GeminiClient imports lazily (genai-free until ComfyUI runtime), mirroring
    # the engine: the model list is the editor's source of truth for the picker.
    from ..gemini.gemini_api.client import GeminiClient

    return web.json_response({
        "models": list(GeminiClient.MODELS),
        "default": GeminiClient.DEFAULT_MODEL,
    })


async def handle_scan_segmenters(request):
    """Return the segmentation backbones this install can run, and the default.

    The editor populates its segmenter picker from this; entries are filtered to
    families whose transformers classes import, each flagged downloaded/not.
    """
    from aiohttp import web

    # available_segmenters does a cold `import transformers`; offload it so the
    # editor-open path never stalls the aiohttp event loop.
    segmenters = await asyncio.to_thread(scan_engine.available_segmenters)
    return web.json_response({
        "segmenters": segmenters,
        "default": scan_engine.DEFAULT_SEGMENTER,
    })


def register(server):
    """Attach the scan routes to the PromptServer's aiohttp route table."""
    server.routes.post("/erpk/scan")(handle_scan)
    server.routes.get("/erpk/scan/models")(handle_scan_models)
    server.routes.get("/erpk/scan/segmenters")(handle_scan_segmenters)
