# ABOUTME: Reads ComfyUI user settings from comfy.settings.json
# ABOUTME: Supports multi-user via client_id-to-user_id mapping from PromptServer

import json
import os

# Populated by __init__.py's on_prompt_handler: maps WebSocket client_id -> user_id
_client_user_map = {}


def get_current_user_id():
    """Determine the current user_id from the executing prompt's client_id.

    During execution, PromptServer.instance.client_id holds the WebSocket
    client that queued the running prompt. We look that up in _client_user_map
    (populated by the /erpk/register_user route) to get the actual user_id.

    Returns:
        user_id string, or None if unavailable
    """
    try:
        from server import PromptServer
        client_id = PromptServer.instance.client_id
        if client_id and client_id in _client_user_map:
            return _client_user_map[client_id]
    except (ImportError, AttributeError, TypeError):
        pass
    return None


def _read_settings_file(settings_path, setting_id, default):
    """Read a single setting from a comfy.settings.json file."""
    if not os.path.exists(settings_path):
        return None
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        value = settings.get(setting_id, default)
        if isinstance(value, str) and not value.strip():
            return None
        return value
    except (json.JSONDecodeError, OSError):
        return None


def get_comfy_setting(setting_id, default=None, user_id=None):
    """Read a setting from ComfyUI's per-user settings file.

    In multi-user mode, uses user_id to read the correct user's settings.
    If user_id is not provided, tries get_current_user_id() to auto-detect
    from the executing prompt's context, then falls back to iterating
    directories with "default" first.

    Args:
        setting_id: The setting key (e.g. "ERPK.ANTHROPIC_API_KEY")
        default: Value to return if the setting is not found
        user_id: Specific user directory to read from (for multi-user)

    Returns:
        The setting value, or default if not found/empty
    """
    try:
        import folder_paths
        user_dir = folder_paths.get_user_directory()
    except (ImportError, AttributeError, TypeError):
        return default

    # Auto-detect user_id from execution context if not provided
    if user_id is None:
        user_id = get_current_user_id()

    # If we have a specific user_id, try that directory first
    if user_id:
        settings_path = os.path.join(user_dir, user_id, "comfy.settings.json")
        result = _read_settings_file(settings_path, setting_id, default)
        if result is not None:
            return result

    # Fallback: iterate directories with "default" first
    try:
        user_dirs = [
            d for d in os.listdir(user_dir)
            if os.path.isdir(os.path.join(user_dir, d))
        ]
    except OSError:
        return default

    if not user_dirs:
        return default

    if "default" in user_dirs:
        user_dirs.remove("default")
        user_dirs.insert(0, "default")

    for subdir in user_dirs:
        # Skip the user_id we already tried
        if subdir == user_id:
            continue
        settings_path = os.path.join(user_dir, subdir, "comfy.settings.json")
        result = _read_settings_file(settings_path, setting_id, default)
        if result is not None:
            return result

    return default
