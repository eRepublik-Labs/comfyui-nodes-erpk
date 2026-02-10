# ABOUTME: CRUD module for shared workflows accessible to all users
# ABOUTME: Provides list, get, save, delete with path-safe name validation

import json
import os
import re
import tempfile

# Storage lives inside the extension directory, not in ComfyUI's user/ tree
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_workflows")

# Whitelist: alphanumeric start/end, spaces/hyphens/underscores in the middle, max 200 chars
_NAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9 _-]{0,198}[a-zA-Z0-9])?$")


def validate_name(name):
    """Validate and return a sanitized workflow name.

    Strips outer whitespace, then checks against a whitelist regex and verifies
    the resolved file path stays inside STORAGE_DIR.

    Raises ValueError for invalid names.
    """
    name = name.strip()
    if not name or not _NAME_RE.match(name):
        raise ValueError(f"Invalid workflow name: {name!r}")

    # Belt-and-suspenders: resolved path must stay inside STORAGE_DIR
    target = os.path.realpath(os.path.join(STORAGE_DIR, name + ".json"))
    if not target.startswith(os.path.realpath(STORAGE_DIR) + os.sep):
        raise ValueError(f"Invalid workflow name: {name!r}")

    return name


def list_workflows():
    """Return metadata for all shared workflows, sorted newest-first.

    Each entry is a dict with keys: name, size, mtime.
    Returns an empty list if the storage directory doesn't exist.
    """
    if not os.path.isdir(STORAGE_DIR):
        return []

    entries = []
    for filename in os.listdir(STORAGE_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(STORAGE_DIR, filename)
        try:
            stat = os.stat(filepath)
            entries.append({
                "name": filename[:-5],  # strip .json
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })
        except OSError:
            continue

    entries.sort(key=lambda e: e["mtime"], reverse=True)
    return entries


def get_workflow(name):
    """Read and parse a shared workflow by name.

    Returns the parsed JSON dict, or None if the file doesn't exist.
    Raises ValueError for invalid names.
    """
    name = validate_name(name)
    filepath = os.path.join(STORAGE_DIR, name + ".json")
    if not os.path.isfile(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workflow(name, workflow):
    """Atomically save a workflow to the shared storage.

    Creates the storage directory if it doesn't exist.
    Uses tempfile + os.replace() for atomic writes.
    Raises ValueError for invalid names.
    """
    name = validate_name(name)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    filepath = os.path.join(STORAGE_DIR, name + ".json")
    fd, tmp_path = tempfile.mkstemp(dir=STORAGE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2)
        os.replace(tmp_path, filepath)
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def delete_workflow(name):
    """Delete a shared workflow by name.

    Returns True if the file was deleted, False if it didn't exist.
    Raises ValueError for invalid names.
    """
    name = validate_name(name)
    filepath = os.path.join(STORAGE_DIR, name + ".json")
    try:
        os.unlink(filepath)
        return True
    except FileNotFoundError:
        return False
