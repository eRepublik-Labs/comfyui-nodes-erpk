# ABOUTME: CRUD module for shared workflows accessible to all users
# ABOUTME: Provides list, get, save, delete with path-safe name validation and authorship tracking

import json
import os
import re
import tempfile

def _resolve_storage_dir():
    """Resolve storage path: ComfyUI base dir when available, plugin dir otherwise."""
    try:
        import folder_paths
        user_dir = folder_paths.get_user_directory()
        return os.path.join(os.path.dirname(user_dir), "shared_workflows")
    except (ImportError, ValueError):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_workflows")


STORAGE_DIR = _resolve_storage_dir()

# Whitelist: alphanumeric/bracket start/end, spaces/hyphens/underscores/brackets in middle, max 200 chars
_NAME_RE = re.compile(r"^[a-zA-Z0-9\[\]()]([a-zA-Z0-9 _\-\[\]()]{0,198}[a-zA-Z0-9\[\]()])?$")


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


def _read_envelope(filepath):
    """Read a workflow file and return (meta, workflow).

    Handles both envelope format {"meta": ..., "workflow": ...} and
    raw workflow JSON (for manually placed or legacy files).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "meta" in data and "workflow" in data:
        return data["meta"], data["workflow"]
    # Raw workflow without envelope
    return {}, data


def list_workflows():
    """Return metadata for all shared workflows, sorted newest-first.

    Each entry is a dict with keys: name, size, mtime, created_by, modified_by.
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
            meta, _ = _read_envelope(filepath)
            entries.append({
                "name": filename[:-5],  # strip .json
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "created_by": meta.get("created_by"),
                "modified_by": meta.get("modified_by"),
            })
        except (OSError, json.JSONDecodeError):
            continue

    entries.sort(key=lambda e: e["mtime"], reverse=True)
    return entries


def get_workflow(name):
    """Read and parse a shared workflow by name.

    Returns the workflow data (unwrapped from envelope if present),
    or None if the file doesn't exist.
    Raises ValueError for invalid names.
    """
    name = validate_name(name)
    filepath = os.path.join(STORAGE_DIR, name + ".json")
    if not os.path.isfile(filepath):
        return None
    _, workflow = _read_envelope(filepath)
    return workflow


def save_workflow(name, workflow, user=None):
    """Atomically save a workflow to the shared storage.

    Wraps the workflow in an envelope with authorship metadata.
    On overwrite, preserves the original creator.
    Creates the storage directory if it doesn't exist.
    Uses tempfile + os.replace() for atomic writes.
    Raises ValueError for invalid names.
    """
    name = validate_name(name)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    filepath = os.path.join(STORAGE_DIR, name + ".json")

    # Preserve original creator on overwrite
    created_by = user
    if os.path.isfile(filepath):
        try:
            existing_meta, _ = _read_envelope(filepath)
            if existing_meta.get("created_by") is not None:
                created_by = existing_meta["created_by"]
        except (OSError, json.JSONDecodeError):
            pass

    envelope = {
        "meta": {
            "created_by": created_by,
            "modified_by": user,
        },
        "workflow": workflow,
    }

    fd, tmp_path = tempfile.mkstemp(dir=STORAGE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
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
