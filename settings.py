# ABOUTME: Reads ComfyUI user settings from comfy.settings.json
# ABOUTME: Provides API key resolution from the Settings UI

import json
import os


def get_comfy_setting(setting_id, default=None):
    """Read a setting from ComfyUI's per-user settings file.

    ComfyUI stores per-user settings in user/{user_id}/comfy.settings.json.
    Checks "default" user directory first, then tries remaining directories.

    Args:
        setting_id: The setting key (e.g. "ERPK.ANTHROPIC_API_KEY")
        default: Value to return if the setting is not found

    Returns:
        The setting value, or default if not found/empty
    """
    try:
        import folder_paths
        user_dir = folder_paths.get_user_directory()
    except (ImportError, AttributeError, TypeError):
        return default

    try:
        user_dirs = [
            d for d in os.listdir(user_dir)
            if os.path.isdir(os.path.join(user_dir, d))
        ]
    except OSError:
        return default

    if not user_dirs:
        return default

    # Check "default" first since that's the standard single-user profile,
    # then try remaining directories (skips __manager and similar internal dirs)
    if "default" in user_dirs:
        user_dirs.remove("default")
        user_dirs.insert(0, "default")

    for subdir in user_dirs:
        settings_path = os.path.join(user_dir, subdir, "comfy.settings.json")
        if not os.path.exists(settings_path):
            continue
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            value = settings.get(setting_id, default)
            if isinstance(value, str) and not value.strip():
                continue
            return value
        except (json.JSONDecodeError, OSError):
            continue

    return default
