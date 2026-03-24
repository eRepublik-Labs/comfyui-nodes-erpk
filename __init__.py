# ABOUTME: V3 entrypoint for ERPK ComfyUI Custom Nodes.
# ABOUTME: Registers all nodes via ComfyExtension and aiohttp routes for settings/workflows.

"""
ERPK ComfyUI Custom Nodes

A collection of custom ComfyUI nodes from ERPK, including WaveSpeed AI, Claude API,
Gemini API integrations, and Apple ML models.
"""

from comfy_api.latest import ComfyExtension, ComfyAPI, IO

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
    # Apple ML
    "ERPK SHARP Predict": "SHARPPredict",
    "ERPK SHARP Render Views": "SHARPRenderViews",
    "ERPK SHARP Render Video": "SHARPRenderVideo",
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
            (".wavespeed", "WaveSpeed"),
            (".apple", "Apple ML"),
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


# --- API Routes (independent of V1/V3 node registration) ---

# Register multi-user API route for settings resolution
try:
    from server import PromptServer
    from aiohttp import web
    from . import settings as erpk_settings

    @PromptServer.instance.routes.post("/erpk/register_user")
    async def erpk_register_user(request):
        """Map a WebSocket client_id to a ComfyUI user_id for settings resolution."""
        try:
            data = await request.json()
            client_id = data.get("client_id")
            if client_id:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
                erpk_settings._client_user_map[client_id] = user_id
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

# Register shared workflows API routes
try:
    from server import PromptServer
    from aiohttp import web
    from . import shared_workflows

    @PromptServer.instance.routes.get("/erpk/shared_workflows")
    async def erpk_list_shared_workflows(request):
        try:
            return web.json_response(shared_workflows.list_workflows())
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
        try:
            body = await request.json()
            name = body.get("name", "")
            workflow = body.get("workflow")
            if workflow is None:
                return web.json_response({"error": "Missing 'workflow' field"}, status=400)
            try:
                user_id = PromptServer.instance.user_manager.get_request_user_id(request)
                users = PromptServer.instance.user_manager.users
                user = users.get(user_id, user_id)
            except Exception:
                user = None
            shared_workflows.save_workflow(name, workflow, user=user)
            return web.json_response({"ok": True, "name": name})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @PromptServer.instance.routes.delete("/erpk/shared_workflows/{name}")
    async def erpk_delete_shared_workflow(request):
        name = request.match_info["name"]
        try:
            deleted = shared_workflows.delete_workflow(name)
            if not deleted:
                return web.json_response({"error": "Not found"}, status=404)
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    print("[ERPK] Registered shared workflows routes")
except Exception as e:
    print(f"[ERPK] Warning: Could not register shared workflows routes: {e}")

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

__all__ = ["comfy_entrypoint", "WEB_DIRECTORY"]
