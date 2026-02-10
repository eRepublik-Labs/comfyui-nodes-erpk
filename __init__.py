"""
ERPK ComfyUI Custom Nodes

A collection of custom ComfyUI nodes from ERPK, including WaveSpeed AI, Claude API,
Gemini API integrations, background removal utilities, and Apple ML models.
"""

# Initialize combined mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Web directory for frontend extensions
WEB_DIRECTORY = "./web"

# Import and register WaveSpeed nodes
try:
    from .wavespeed import (
        NODE_CLASS_MAPPINGS as WAVESPEED_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WAVESPEED_NODE_DISPLAY_NAME_MAPPINGS,
    )
    NODE_CLASS_MAPPINGS.update(WAVESPEED_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(WAVESPEED_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load WaveSpeed nodes: {e}")

# Import and register Claude nodes
try:
    from .claude import (
        NODE_CLASS_MAPPINGS as CLAUDE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CLAUDE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(CLAUDE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CLAUDE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Claude nodes: {e}")

# Import and register Gemini nodes
try:
    from .gemini import (
        NODE_CLASS_MAPPINGS as GEMINI_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as GEMINI_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(GEMINI_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(GEMINI_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Gemini nodes: {e}")

# Import and register OpenAI nodes
try:
    from .openai import (
        NODE_CLASS_MAPPINGS as OPENAI_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as OPENAI_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(OPENAI_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(OPENAI_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load OpenAI nodes: {e}")

# Import and register Background Removal nodes
try:
    from .bgremoval import (
        NODE_CLASS_MAPPINGS as BGREMOVAL_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as BGREMOVAL_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(BGREMOVAL_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(BGREMOVAL_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Background Removal nodes: {e}")

# Import and register Apple ML nodes
try:
    from .apple import (
        NODE_CLASS_MAPPINGS as APPLE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as APPLE_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(APPLE_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(APPLE_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load Apple ML nodes: {e}")

# Import and register utility nodes
try:
    from .utils import (
        NODE_CLASS_MAPPINGS as UTILS_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as UTILS_NODE_DISPLAY_NAME_MAPPINGS
    )
    NODE_CLASS_MAPPINGS.update(UTILS_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(UTILS_NODE_DISPLAY_NAME_MAPPINGS)
except ImportError as e:
    print(f"[ERPK] Warning: Could not load utility nodes: {e}")

# Print loaded nodes summary
print(f"[ERPK] Loaded {len(NODE_CLASS_MAPPINGS)} total nodes")

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
            shared_workflows.save_workflow(name, workflow)
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

# Export for ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
