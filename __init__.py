# ABOUTME: V3 entrypoint for ERPK ComfyUI Custom Nodes.
# ABOUTME: Registers all nodes via ComfyExtension and aiohttp routes for settings/workflows.

"""
ERPK ComfyUI Custom Nodes

A collection of custom ComfyUI nodes from ERPK, including WaveSpeed AI, Claude API,
Gemini, OpenAI, Grok and BytePlus ModelArk API integrations.
"""

import re
from pathlib import Path

from comfy_api.latest import ComfyExtension, ComfyAPI, IO


def _resolve_version(pyproject_path=None):
    """Resolve the package version from pyproject.toml (the single source of truth)."""
    path = Path(pyproject_path) if pyproject_path else Path(__file__).parent / "pyproject.toml"
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        pass
    # Fallback for Python < 3.11 (no tomllib) or a malformed file.
    try:
        match = re.search(
            r'^version\s*=\s*"([^"]+)"',
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if match:
            return match.group(1)
    except Exception:
        pass
    return "unknown"


__version__ = _resolve_version()

# Web directory for frontend extensions
WEB_DIRECTORY = "./web"

# V1→V3 node ID replacements for backward compatibility with saved workflows.
# Only nodes whose class_type changed during the V3 migration need entries here.
_NODE_REPLACEMENTS = {
    # WaveSpeed
    "WaveSpeed Custom Client": "WaveSpeedAIAPIClient",
    "WaveSpeed Custom Preview Video": "PreviewVideo",
    "WaveSpeed Custom Save Audio": "SaveAudio",
    "WaveSpeed Custom Upload Image": "UploadImage",
    "WaveSpeed Custom SeedreamV4": "SeedreamV4Node",
    "WaveSpeed Custom SeedreamV4Edit": "SeedreamV4EditNode",
    "WaveSpeed Custom SeedreamV4Sequential": "SeedreamV4SequentialNode",
    "WaveSpeed Custom SeedreamV4EditSequential": "SeedreamV4EditSequentialNode",
    "WaveSpeed Custom SeedreamV4_5": "SeedreamV4_5Node",
    "WaveSpeed Custom SeedreamV4_5Edit": "SeedreamV4_5EditNode",
    "WaveSpeed Custom SeedreamV4_5Sequential": "SeedreamV4_5SequentialNode",
    "WaveSpeed Custom SeedreamV4_5EditSequential": "SeedreamV4_5EditSequentialNode",
    "WaveSpeed Custom QwenImageT2I": "QwenImageTextToImageNode",
    "WaveSpeed Custom QwenImageEdit": "QwenImageEditNode",
    "WaveSpeed Custom QwenImageEditPlus": "QwenImageEditPlusNode",
    # Regional prompt builder generalized beyond Gemini
    "GeminiRegionalPromptBuilder": "RegionalPromptBuilder",
}


class ERPKExtension(ComfyExtension):
    """V3 extension that aggregates all ERPK node classes."""

    async def on_load(self) -> None:
        api = ComfyAPI()
        for old_id, new_id in _NODE_REPLACEMENTS.items():
            await api.node_replacement.register(
                IO.NodeReplace(new_node_id=new_id, old_node_id=old_id)
            )
        print(f"[ERPK] Registered {len(_NODE_REPLACEMENTS)} node replacements")

    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        nodes: list[type[IO.ComfyNode]] = []

        # Collect V3 nodes from each provider
        _providers = [
            (".utils", "utility"),
            (".claude", "Claude"),
            (".gemini", "Gemini"),
            (".openai", "OpenAI"),
            (".grok", "Grok"),
            (".byteplus", "BytePlus"),
            (".wavespeed", "WaveSpeed"),
        ]

        for module_path, label in _providers:
            try:
                import importlib
                try:
                    mod = importlib.import_module(module_path, package=__package__)
                except TypeError:
                    # __package__ is None in test environment — use absolute import
                    mod = importlib.import_module(module_path.lstrip("."))
                provider_nodes = getattr(mod, "NODES", [])
                nodes.extend(provider_nodes)
            except ImportError as e:
                print(f"[ERPK] Warning: Could not load {label} nodes: {e}")

        print(f"[ERPK] Loaded {len(nodes)} V3 nodes")
        return nodes


async def comfy_entrypoint() -> ERPKExtension:
    return ERPKExtension()


# --- API key migration (before any route or node reads a key) ---

# ComfyUI serves comfy.settings.json to anyone who names a user, so API keys
# saved there by older versions move to the private key store on every start.
try:
    import folder_paths
    from . import key_store

    _user_dir = folder_paths.get_user_directory()
    key_store.migrate_settings(_user_dir, key_store.store_for(_user_dir))
except Exception as e:
    print(
        f"[ERPK] ERROR: API key migration failed: {e!r}. API keys in comfy.settings.json "
        "stay readable by other users until it succeeds.",
        flush=True,
    )

# --- API Routes (independent of V1/V3 node registration) ---

# Register multi-user API route for settings resolution
try:
    from server import PromptServer
    from aiohttp import web
    from . import settings as erpk_settings

    @PromptServer.instance.routes.post("/erpk/register_user")
    async def erpk_register_user(request):
        """Map a WebSocket client_id to a ComfyUI user_id for settings resolution.

        Refuses to overwrite an existing binding to a different user_id —
        prevents map poisoning where Bob could hijack Alice's client_id and
        cause Alice's prompts to resolve settings as Bob.
        """
        try:
            data = await request.json()
            client_id = data.get("client_id")
            if client_id:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
                if not erpk_settings.register_client_user(client_id, user_id):
                    return web.Response(status=409)
        except (KeyError, Exception):
            pass
        return web.Response(status=200)

    @PromptServer.instance.routes.get("/erpk/user_info")
    async def erpk_user_info(request):
        """Return current user info for the settings UI."""
        try:
            from comfy.cli_args import args
            user_id = PromptServer.instance.user_manager.get_request_user_id(request)
            users = PromptServer.instance.user_manager.users
            display_name = users.get(user_id, user_id)
            return web.json_response({
                "multi_user": args.multi_user,
                "user_id": user_id,
                "display_name": display_name,
            })
        except Exception:
            return web.json_response({"multi_user": False, "user_id": "default", "display_name": "default"})

    print("[ERPK] Registered multi-user settings routes")
except Exception as e:
    print(f"[ERPK] Warning: Could not register settings routes: {e}")

# Register version route (read by the frontend to display the package version)
try:
    from server import PromptServer
    from aiohttp import web

    @PromptServer.instance.routes.get("/erpk/version")
    async def erpk_version(request):
        return web.json_response({"version": __version__})

    print("[ERPK] Registered version route")
except Exception as e:
    print(f"[ERPK] Warning: Could not register version route: {e}")

# Register the image grid caps route (read by the grid to cap each node by its selected model)
try:
    from server import PromptServer
    from aiohttp import web
    from .utils.image_grid import GRID_CAPS

    @PromptServer.instance.routes.get("/erpk/grid_caps")
    async def erpk_grid_caps(request):
        # Read per request: node modules register their caps when get_node_list
        # imports them, after this route is defined.
        return web.json_response(GRID_CAPS)

    print("[ERPK] Registered image grid caps route")
except Exception as e:
    print(f"[ERPK] Warning: Could not register image grid caps route: {e}")

# Register shared workflows API routes
try:
    from server import PromptServer
    from aiohttp import web
    from . import shared_workflows
    from .write_guard import check_write_request, write_token

    def refuse_unless_page_request(request):
        """403 response for a write request that fails the token gate, else None."""
        try:
            check_write_request(request.headers)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        return None

    @PromptServer.instance.routes.get("/erpk/write_token")
    async def erpk_write_token(request):
        return web.json_response({"token": write_token()})

    @PromptServer.instance.routes.get("/erpk/shared_workflows")
    async def erpk_list_shared_workflows(request):
        try:
            return web.json_response(shared_workflows.list_workflows())
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.get("/erpk/shared_workflows/trash")
    async def erpk_list_trashed_workflows(request):
        try:
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
            except Exception:
                user_id = None
            return web.json_response(shared_workflows.list_trashed_workflows(user_id=user_id))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.post("/erpk/shared_workflows/trash/{trash_id}/restore")
    async def erpk_restore_shared_workflow(request):
        refused = refuse_unless_page_request(request)
        if refused:
            return refused
        trash_id = request.match_info["trash_id"]
        try:
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
            except Exception:
                user_id = None
            restored = shared_workflows.restore_workflow(trash_id, user_id=user_id)
            if not restored:
                return web.json_response({"error": "Not found"}, status=404)
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        except FileExistsError as e:
            return web.json_response({"error": str(e)}, status=409)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.delete("/erpk/shared_workflows/trash/{trash_id}")
    async def erpk_purge_shared_workflow(request):
        refused = refuse_unless_page_request(request)
        if refused:
            return refused
        trash_id = request.match_info["trash_id"]
        try:
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
            except Exception:
                user_id = None
            purged = shared_workflows.purge_trashed_workflow(trash_id, user_id=user_id)
            if not purged:
                return web.json_response({"error": "Not found"}, status=404)
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.get("/erpk/shared_workflows/{name}")
    async def erpk_get_shared_workflow(request):
        name = request.match_info["name"]
        try:
            data = shared_workflows.get_workflow(name)
            if data is None:
                return web.json_response({"error": "Not found"}, status=404)
            return web.json_response(data)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.post("/erpk/shared_workflows")
    async def erpk_save_shared_workflow(request):
        refused = refuse_unless_page_request(request)
        if refused:
            return refused
        try:
            body = await request.json()
            name = body.get("name", "")
            workflow = body.get("workflow")
            if workflow is None:
                return web.json_response({"error": "Missing 'workflow' field"}, status=400)
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
                users = PromptServer.instance.user_manager.users
                display_name = users.get(user_id, user_id)
            except Exception:
                user_id = None
                display_name = None
            shared_workflows.save_workflow(
                name, workflow, user_id=user_id, display_name=display_name
            )
            return web.json_response({"ok": True, "name": name})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.delete("/erpk/shared_workflows/{name}")
    async def erpk_delete_shared_workflow(request):
        refused = refuse_unless_page_request(request)
        if refused:
            return refused
        name = request.match_info["name"]
        try:
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
                users = PromptServer.instance.user_manager.users
                display_name = users.get(user_id, user_id)
            except Exception:
                user_id = None
                display_name = None
            deleted = shared_workflows.delete_workflow(
                name, user_id=user_id, display_name=display_name
            )
            if not deleted:
                return web.json_response({"error": "Not found"}, status=404)
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    print("[ERPK] Registered shared workflows routes")
except Exception as e:
    print(f"[ERPK] Warning: Could not register shared workflows routes: {e}")

# Register the API key routes. They return which keys are set and the last
# four characters of each, never a key.
try:
    from server import PromptServer
    from aiohttp import web
    import folder_paths
    from . import key_store
    from .write_guard import check_write_request

    def _keys_user_or_refusal(request):
        """(user_id, None) for a known user, else (None, 403 response)."""
        try:
            return PromptServer.instance.user_manager.get_request_user_id(request), None
        except KeyError as e:
            return None, web.json_response({"error": e.args[0]}, status=403)

    def _keys_store():
        return key_store.store_for(folder_paths.get_user_directory())

    @PromptServer.instance.routes.get("/erpk/keys")
    async def erpk_key_status(request):
        user_id, refusal = _keys_user_or_refusal(request)
        if refusal:
            return refusal
        try:
            return web.json_response(_keys_store().status(user_id))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

    @PromptServer.instance.routes.post("/erpk/keys")
    async def erpk_save_key(request):
        try:
            check_write_request(request.headers)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403)
        user_id, refusal = _keys_user_or_refusal(request)
        if refusal:
            return refusal
        try:
            body = await request.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            return web.json_response({"error": "Body must be a JSON object"}, status=400)
        if "key" not in body:
            return web.json_response({"error": "Missing 'key' field"}, status=400)
        store = _keys_store()
        try:
            if body["key"] is None:
                store.clear(user_id, body.get("provider"))
            else:
                store.set(user_id, body.get("provider"), body["key"])
            return web.json_response(store.status(user_id))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

    print("[ERPK] Registered API key routes")
except Exception as e:
    print(f"[ERPK] Warning: Could not register API key routes: {e}")

# Refuse to save an API key into comfy.settings.json, which a page loaded
# before the key store still tries. aiohttp freezes the middleware list when
# the server starts, after ComfyUI imports this package.
try:
    from server import PromptServer
    from aiohttp import web
    from . import key_store

    @web.middleware
    async def erpk_refuse_key_settings_write(request, handler):
        resource = request.match_info.route.resource
        route = resource.canonical if resource else None
        # Read the body only for these routes: reading it before a multipart
        # handler would consume the stream that handler parses.
        if request.method == "POST" and route in key_store.SETTINGS_WRITE_ROUTES:
            body = await request.read()
            if key_store.writes_key_setting(request.method, route, dict(request.match_info), body):
                return web.json_response({"error": key_store.KEY_SETTING_REFUSAL}, status=403)
        return await handler(request)

    PromptServer.instance.app.middlewares.append(erpk_refuse_key_settings_write)
    print("[ERPK] Registered API key settings write refusal")
except Exception as e:
    print(
        f"[ERPK] ERROR: Could not register the API key settings write refusal: {e!r}. "
        "A page loaded before this version can still save API keys into comfy.settings.json.",
        flush=True,
    )

# Register the editor scan route (vision-based region detection)
try:
    from server import PromptServer
    from .utils import scan_route
    scan_route.register(PromptServer.instance)
    print("[ERPK] Registered scan route")
except Exception as e:
    print(f"[ERPK] Warning: Could not register scan route: {e}")

# --- Monkey-patches (independent of V1/V3 node registration) ---

try:
    from . import metadata_filter
    metadata_filter.install()
except Exception as e:
    print(f"[ERPK] Warning: Could not install metadata filter: {e}")

try:
    from . import history_cleaner
    history_cleaner.install()
except Exception as e:
    print(f"[ERPK] Warning: Could not install history cleaner: {e}")

try:
    from . import parallel_workers
    parallel_workers.install()
except Exception as e:
    print(f"[ERPK] Warning: Could not install parallel workers: {e}")

__all__ = ["comfy_entrypoint", "WEB_DIRECTORY", "__version__"]
