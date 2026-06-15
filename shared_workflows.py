# ABOUTME: CRUD module for shared workflows accessible to all users
# ABOUTME: Provides list, get, save, delete with path-safe name validation and authorship tracking

import json
import os
import re
import tempfile
import time

def _resolve_storage_dir():
    """Resolve storage path: ComfyUI base dir when available, plugin dir otherwise."""
    try:
        import folder_paths
        user_dir = folder_paths.get_user_directory()
        return os.path.join(os.path.dirname(user_dir), "shared_workflows")
    except (ImportError, ValueError):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_workflows")


STORAGE_DIR = _resolve_storage_dir()
TRASH_DIR_NAME = ".trash"

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


def _workflow_path(name):
    return os.path.join(STORAGE_DIR, name + ".json")


def _trash_dir():
    return os.path.join(STORAGE_DIR, TRASH_DIR_NAME)


def _trash_path(trash_id):
    return os.path.join(_trash_dir(), trash_id + ".json")


def validate_trash_id(trash_id):
    """Validate a generated trash entry id."""
    trash_id = trash_id.strip()
    if not trash_id or not re.match(r"^[A-Za-z0-9_\-\[\]() ]{1,240}$", trash_id):
        raise ValueError(f"Invalid trash id: {trash_id!r}")

    target = os.path.realpath(_trash_path(trash_id))
    if not target.startswith(os.path.realpath(_trash_dir()) + os.sep):
        raise ValueError(f"Invalid trash id: {trash_id!r}")
    return trash_id


def _require_user(user_id, action):
    if not user_id:
        raise PermissionError(f"user_id required to {action} shared workflow")


def _assert_owner(meta, user_id, name):
    existing_user_id = meta.get("created_by_user_id")
    if existing_user_id is not None and existing_user_id != user_id:
        raise PermissionError(f"Workflow {name!r} is owned by another user")


def _unique_trash_id(name):
    os.makedirs(_trash_dir(), exist_ok=True)
    base = f"{name}__deleted_{int(time.time() * 1000)}"
    trash_id = base
    counter = 1
    while os.path.exists(_trash_path(trash_id)):
        trash_id = f"{base}_{counter}"
        counter += 1
    return trash_id


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
    filepath = _workflow_path(name)
    if not os.path.isfile(filepath):
        return None
    _, workflow = _read_envelope(filepath)
    return workflow


def save_workflow(name, workflow, user_id=None, display_name=None):
    """Atomically save a workflow to shared storage with owner-only auth.

    Requires user_id. On overwrite, only the original creator can write;
    a mismatch raises PermissionError. Legacy files lacking
    created_by_user_id are claimable by the first authenticated save.

    Args:
        name: workflow name (validated against whitelist)
        workflow: workflow JSON to save
        user_id: immutable identifier of the saver (required)
        display_name: human-readable name for UI (defaults to user_id)

    Raises:
        ValueError: invalid name
        PermissionError: missing user_id or overwrite by non-creator
    """
    name = validate_name(name)

    if not user_id:
        raise PermissionError("user_id required to save shared workflow")

    if display_name is None:
        display_name = user_id

    os.makedirs(STORAGE_DIR, exist_ok=True)
    filepath = _workflow_path(name)

    created_by_user_id = user_id
    created_by_display = display_name
    if os.path.isfile(filepath):
        try:
            existing_meta, _ = _read_envelope(filepath)
        except (OSError, json.JSONDecodeError):
            existing_meta = {}
        _assert_owner(existing_meta, user_id, name)
        if existing_meta.get("created_by_user_id") is not None:
            created_by_display = existing_meta.get("created_by", display_name)

    envelope = {
        "meta": {
            "created_by": created_by_display,
            "created_by_user_id": created_by_user_id,
            "modified_by": display_name,
            "modified_by_user_id": user_id,
        },
        "workflow": workflow,
    }

    fd, tmp_path = tempfile.mkstemp(dir=STORAGE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        os.replace(tmp_path, filepath)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def delete_workflow(name, user_id=None, display_name=None):
    """Move a shared workflow to trash by name, with owner-only auth.

    Requires user_id. Only the original creator can delete an owned
    workflow. Legacy files lacking created_by_user_id are deletable by
    any authenticated caller.

    Returns True if the file was deleted, False if it didn't exist.
    Raises ValueError for invalid names, PermissionError for
    unauthenticated or non-creator deletes.
    """
    name = validate_name(name)

    _require_user(user_id, "delete")
    if display_name is None:
        display_name = user_id

    filepath = _workflow_path(name)
    if not os.path.isfile(filepath):
        return False

    try:
        existing_meta, _ = _read_envelope(filepath)
    except (OSError, json.JSONDecodeError):
        existing_meta = {}
    _assert_owner(existing_meta, user_id, name)

    existing_meta["deleted_by_user_id"] = user_id
    existing_meta["deleted_by"] = display_name
    existing_meta["deleted_at"] = time.time()

    trash_id = _unique_trash_id(name)
    trash_filepath = _trash_path(trash_id)
    try:
        _, workflow = _read_envelope(filepath)
        envelope = {
            "meta": {
                **existing_meta,
                "original_name": name,
                "trash_id": trash_id,
            },
            "workflow": workflow,
        }
        fd, tmp_path = tempfile.mkstemp(dir=_trash_dir(), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(envelope, f, indent=2)
            os.replace(tmp_path, trash_filepath)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        os.unlink(filepath)
        return True
    except FileNotFoundError:
        return False


def list_trashed_workflows(user_id=None):
    """Return trashed workflow metadata, newest-first.

    If user_id is supplied, only entries owned by that user, entries deleted
    by that user, or legacy entries without owner metadata are returned.
    """
    trash_dir = _trash_dir()
    if not os.path.isdir(trash_dir):
        return []

    entries = []
    for filename in os.listdir(trash_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(trash_dir, filename)
        try:
            stat = os.stat(filepath)
            meta, _ = _read_envelope(filepath)
            owner_id = meta.get("created_by_user_id")
            deleted_by_id = meta.get("deleted_by_user_id")
            if user_id and owner_id not in (None, user_id) and deleted_by_id != user_id:
                continue
            entries.append({
                "trash_id": filename[:-5],
                "name": meta.get("original_name") or filename[:-5],
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "created_by": meta.get("created_by"),
                "modified_by": meta.get("modified_by"),
                "deleted_by": meta.get("deleted_by"),
                "deleted_at": meta.get("deleted_at"),
            })
        except (OSError, json.JSONDecodeError):
            continue

    entries.sort(key=lambda e: e.get("deleted_at") or e["mtime"], reverse=True)
    return entries


def restore_workflow(trash_id, user_id=None):
    """Restore a trashed workflow to its original name.

    Refuses to overwrite an active workflow with the same name.
    """
    trash_id = validate_trash_id(trash_id)
    _require_user(user_id, "restore")

    trash_filepath = _trash_path(trash_id)
    if not os.path.isfile(trash_filepath):
        return False

    meta, workflow = _read_envelope(trash_filepath)
    name = validate_name(meta.get("original_name") or trash_id.split("__deleted_", 1)[0])
    _assert_owner(meta, user_id, name)

    filepath = _workflow_path(name)
    if os.path.exists(filepath):
        raise FileExistsError(f"Workflow {name!r} already exists")

    restored_meta = dict(meta)
    for key in ("deleted_by", "deleted_by_user_id", "deleted_at", "trash_id", "original_name"):
        restored_meta.pop(key, None)

    os.makedirs(STORAGE_DIR, exist_ok=True)
    envelope = {"meta": restored_meta, "workflow": workflow}
    fd, tmp_path = tempfile.mkstemp(dir=STORAGE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        os.replace(tmp_path, filepath)
        os.unlink(trash_filepath)
        return True
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def purge_trashed_workflow(trash_id, user_id=None):
    """Permanently delete a trashed workflow with owner-only auth."""
    trash_id = validate_trash_id(trash_id)
    _require_user(user_id, "permanently delete")

    try:
        meta, _ = _read_envelope(_trash_path(trash_id))
        name = meta.get("original_name") or trash_id
        _assert_owner(meta, user_id, name)
        os.unlink(_trash_path(trash_id))
        return True
    except FileNotFoundError:
        return False
