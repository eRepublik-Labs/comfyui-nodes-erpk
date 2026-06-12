# ABOUTME: aiohttp handler for POST /erpk/scan: validates the request, decodes the posted image,
# ABOUTME: and runs the scan engine. PIL and aiohttp.web import lazily so the package imports outside ComfyUI.

import base64
import binascii

from . import scan_engine

# The editor downscales before posting, so anything near this size is not a
# legitimate scan request.
SCAN_MAX_BODY_BYTES = 24 * 1024 * 1024

# Engine name -> scan_engine coroutine attribute. The attribute is resolved at
# request time (not imported) so this module loads even before the local engine
# exists. "local" is the default; Shift-click in the editor selects "gemini".
SCAN_ENGINES = {"local": "local_scan", "gemini": "gemini_scan"}
DEFAULT_SCAN_ENGINE = "local"


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
        length = getattr(request, "content_length", None)
        if length is not None and length > SCAN_MAX_BODY_BYTES:
            return web.json_response({"error": "Request body too large"}, status=413)
        try:
            body = await request.json()
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

        from io import BytesIO
        from PIL import Image
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return web.json_response({"error": "Could not decode image"}, status=400)

        engine = getattr(scan_engine, SCAN_ENGINES[engine_name])
        try:
            objects = await scan_engine.scan(image, max_objects, model, engine=engine)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=502)

        return web.json_response({"objects": objects})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(server):
    """Attach the scan route to the PromptServer's aiohttp route table."""
    server.routes.post("/erpk/scan")(handle_scan)
