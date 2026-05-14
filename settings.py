# ABOUTME: Reads ComfyUI user settings from comfy.settings.json
# ABOUTME: Supports multi-user via client_id-to-user_id mapping from PromptServer

import json
import os
import re
import threading
from collections import OrderedDict

# Maps WebSocket client_id -> user_id, populated by /erpk/register_user.
# OrderedDict + lock + size cap give thread safety and prevent unbounded growth.
_client_user_map = OrderedDict()
_client_user_map_lock = threading.Lock()
_MAX_CLIENT_USER_MAP_SIZE = 10000

# ComfyUI client_ids are hex/UUID-like; reject anything off-shape to avoid
# treating attacker-supplied junk as a real binding.
_CLIENT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")


def register_client_user(client_id, user_id):
    """Bind a WebSocket client_id to a user_id with anti-poisoning protection.

    Rebinding the same client_id to the same user_id is idempotent (handles
    page reloads). Attempts to rebind an existing client_id to a *different*
    user_id are refused — this prevents a malicious user from hijacking
    another user's settings resolution by guessing their client_id.

    At map capacity, the oldest entry is FIFO-evicted.

    Returns True if accepted, False if rejected (bad format, empty user_id,
    or cross-user rebind attempt).
    """
    if not isinstance(client_id, str) or not _CLIENT_ID_RE.match(client_id):
        return False
    if not user_id:
        return False
    with _client_user_map_lock:
        existing = _client_user_map.get(client_id)
        if existing is not None and existing != user_id:
            return False
        if client_id not in _client_user_map and len(_client_user_map) >= _MAX_CLIENT_USER_MAP_SIZE:
            _client_user_map.popitem(last=False)
        _client_user_map[client_id] = user_id
        _client_user_map.move_to_end(client_id)
    return True


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
        if client_id:
            with _client_user_map_lock:
                return _client_user_map.get(client_id)
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

    Resolves against the identified user only. If user_id is omitted,
    get_current_user_id() is consulted; if that yields nothing
    (background tasks, no WebSocket context, unmapped client_id), only
    the shared "default" directory is read.

    User isolation is strict: this function will NEVER return a setting
    belonging to another identified user, and an unresolved session
    cannot borrow a peer's value. A miss returns the caller's default.

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

    if user_id is None:
        user_id = get_current_user_id()

    if user_id:
        settings_path = os.path.join(user_dir, user_id, "comfy.settings.json")
        result = _read_settings_file(settings_path, setting_id, default)
        if result is not None:
            return result
        return default

    settings_path = os.path.join(user_dir, "default", "comfy.settings.json")
    result = _read_settings_file(settings_path, setting_id, default)
    if result is not None:
        return result
    return default
