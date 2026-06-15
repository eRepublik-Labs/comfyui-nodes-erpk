# ABOUTME: Tests for the shared workflows CRUD module
# ABOUTME: Covers name validation, list/get/save/delete, and owner-only auth

import json
import os
import sys
import time
import types

import pytest

from shared_workflows import (
    _resolve_storage_dir,
    delete_workflow,
    get_workflow,
    list_trashed_workflows,
    list_workflows,
    purge_trashed_workflow,
    restore_workflow,
    save_workflow,
    validate_name,
    validate_trash_id,
)


@pytest.fixture
def storage_dir(tmp_path, monkeypatch):
    d = tmp_path / "shared_workflows"
    d.mkdir()
    import shared_workflows
    monkeypatch.setattr(shared_workflows, "STORAGE_DIR", str(d))
    return d


# ── Phase 0: Storage directory resolution ─────────────────────────


class TestResolveStorageDir:
    def test_uses_comfyui_base_when_folder_paths_available(self, monkeypatch, tmp_path):
        import shared_workflows

        user_dir = str(tmp_path / "user")
        mock_module = types.ModuleType("folder_paths")
        mock_module.get_user_directory = lambda: user_dir
        monkeypatch.setitem(sys.modules, "folder_paths", mock_module)

        result = _resolve_storage_dir()
        assert result == os.path.join(str(tmp_path), "shared_workflows")

    def test_falls_back_to_plugin_dir(self, monkeypatch):
        import shared_workflows

        monkeypatch.delitem(sys.modules, "folder_paths", raising=False)

        result = _resolve_storage_dir()
        plugin_dir = os.path.dirname(os.path.abspath(shared_workflows.__file__))
        assert result == os.path.join(plugin_dir, "shared_workflows")


# ── Phase 1: Name validation ──────────────────────────────────────


class TestValidateName:
    def test_accepts_simple_alphanumeric(self):
        assert validate_name("myworkflow") == "myworkflow"

    def test_accepts_spaces_and_hyphens(self):
        assert validate_name("my cool workflow-v2") == "my cool workflow-v2"

    def test_accepts_underscores(self):
        assert validate_name("my_workflow_1") == "my_workflow_1"

    def test_accepts_brackets_and_parentheses(self):
        assert validate_name("Background Removal [DEMO]") == "Background Removal [DEMO]"
        assert validate_name("workflow (copy)") == "workflow (copy)"

    def test_accepts_single_character(self):
        assert validate_name("a") == "a"

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            validate_name("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError):
            validate_name("   ")

    def test_rejects_path_traversal_dots(self):
        with pytest.raises(ValueError):
            validate_name("..")

    def test_rejects_slashes(self):
        with pytest.raises(ValueError):
            validate_name("foo/bar")

    def test_rejects_backslashes(self):
        with pytest.raises(ValueError):
            validate_name("foo\\bar")

    def test_rejects_null_bytes(self):
        with pytest.raises(ValueError):
            validate_name("foo\x00bar")

    def test_rejects_dots_in_name(self):
        with pytest.raises(ValueError):
            validate_name("workflow.json")

    def test_rejects_leading_hyphen_after_strip(self):
        with pytest.raises(ValueError):
            validate_name(" -leading")

    def test_rejects_trailing_hyphen_after_strip(self):
        with pytest.raises(ValueError):
            validate_name("trailing- ")

    def test_rejects_name_over_200_chars(self):
        with pytest.raises(ValueError):
            validate_name("a" * 201)

    def test_accepts_name_at_200_chars(self):
        name = "a" * 200
        assert validate_name(name) == name

    def test_strips_whitespace_before_validation(self):
        # Outer whitespace is stripped, but the resulting name must still
        # start/end with alphanumeric. "  hello  " strips to "hello" which is valid.
        assert validate_name("  hello  ") == "hello"


# ── Phase 2: CRUD operations ──────────────────────────────────────


class TestListWorkflows:
    def test_list_empty(self, storage_dir):
        assert list_workflows() == []

    def test_list_multiple_sorted_newest_first(self, storage_dir):
        save_workflow("alpha", {"nodes": []}, user_id="alice")
        time.sleep(0.05)
        save_workflow("beta", {"nodes": [], "extra": True}, user_id="bob")

        result = list_workflows()
        assert len(result) == 2
        # Newest first
        assert result[0]["name"] == "beta"
        assert result[1]["name"] == "alpha"
        # Each entry has expected keys
        for entry in result:
            assert "name" in entry
            assert "size" in entry
            assert "mtime" in entry
            assert "created_by" in entry
            assert "modified_by" in entry

    def test_list_includes_user_metadata(self, storage_dir):
        save_workflow("tracked", {"nodes": []}, user_id="alice")
        result = list_workflows()
        assert result[0]["created_by"] == "alice"
        assert result[0]["modified_by"] == "alice"

    def test_list_ignores_non_json(self, storage_dir):
        (storage_dir / "readme.txt").write_text("not a workflow")
        save_workflow("real", {}, user_id="alice")
        result = list_workflows()
        assert len(result) == 1
        assert result[0]["name"] == "real"

    def test_list_handles_raw_json_without_envelope(self, storage_dir):
        # A manually placed file without the envelope format
        (storage_dir / "legacy.json").write_text(json.dumps({"nodes": []}))
        result = list_workflows()
        assert len(result) == 1
        assert result[0]["name"] == "legacy"
        assert result[0]["created_by"] is None
        assert result[0]["modified_by"] is None


class TestGetWorkflow:
    def test_get_existing(self, storage_dir):
        data = {"nodes": [1, 2, 3]}
        save_workflow("demo", data, user_id="alice")
        result = get_workflow("demo")
        assert result == data

    def test_get_raw_json_without_envelope(self, storage_dir):
        # A manually placed file without the envelope format
        data = {"nodes": [1, 2, 3]}
        (storage_dir / "legacy.json").write_text(json.dumps(data))
        result = get_workflow("legacy")
        assert result == data

    def test_get_missing(self, storage_dir):
        assert get_workflow("nonexistent") is None

    def test_get_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            get_workflow("../etc/passwd")


class TestSaveWorkflow:
    def test_save_new(self, storage_dir):
        data = {"nodes": [1]}
        save_workflow("newflow", data, user_id="alice")
        saved = json.loads((storage_dir / "newflow.json").read_text())
        # Stored in envelope format
        assert saved["workflow"] == data
        # display defaults to user_id when display_name is not provided
        assert saved["meta"]["created_by"] == "alice"
        assert saved["meta"]["modified_by"] == "alice"
        # Immutable identifier stored alongside display name
        assert saved["meta"]["created_by_user_id"] == "alice"
        assert saved["meta"]["modified_by_user_id"] == "alice"

    def test_overwrite_by_creator_updates_modified(self, storage_dir):
        save_workflow("shared", {"v": 1}, user_id="alice", display_name="Alice")
        save_workflow("shared", {"v": 2}, user_id="alice", display_name="Alice (renamed)")
        saved = json.loads((storage_dir / "shared.json").read_text())
        assert saved["workflow"] == {"v": 2}
        assert saved["meta"]["created_by_user_id"] == "alice"
        assert saved["meta"]["created_by"] == "Alice"  # display preserved from creation
        assert saved["meta"]["modified_by"] == "Alice (renamed)"  # display updated

    def test_save_creates_dir(self, tmp_path, monkeypatch):
        import shared_workflows
        new_dir = str(tmp_path / "brand_new")
        monkeypatch.setattr(shared_workflows, "STORAGE_DIR", new_dir)
        save_workflow("first", {"created": True}, user_id="alice")
        assert os.path.isfile(os.path.join(new_dir, "first.json"))

    def test_save_no_tmp_left(self, storage_dir):
        save_workflow("clean", {"data": True}, user_id="alice")
        files = os.listdir(str(storage_dir))
        assert files == ["clean.json"]

    def test_save_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            save_workflow("../escape", {"bad": True}, user_id="alice")


class TestDeleteWorkflow:
    def test_delete_existing_legacy_file(self, storage_dir):
        # Raw JSON with no envelope and no user_id is trashable by any authenticated user
        (storage_dir / "doomed.json").write_text(json.dumps({}))
        assert delete_workflow("doomed", user_id="alice") is True
        assert not (storage_dir / "doomed.json").exists()
        trashed = list_trashed_workflows(user_id="alice")
        assert len(trashed) == 1
        assert trashed[0]["name"] == "doomed"

    def test_delete_missing(self, storage_dir):
        assert delete_workflow("ghost", user_id="alice") is False

    def test_delete_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            delete_workflow("../escape", user_id="alice")


# ── Phase 3: Authorization (owner-only model) ──────────────────────


class TestSaveWorkflowAuth:
    """Owner-only sharing model: only the creator can overwrite. Anonymous
    saves are refused. Legacy files (no created_by_user_id) are claimable
    on first authenticated save."""

    def test_non_creator_overwrite_raises_permission_error(self, storage_dir):
        save_workflow("guarded", {"v": 1}, user_id="alice", display_name="Alice")
        with pytest.raises(PermissionError):
            save_workflow("guarded", {"v": 2}, user_id="bob", display_name="Bob")
        # Alice's content is preserved
        saved = json.loads((storage_dir / "guarded.json").read_text())
        assert saved["workflow"] == {"v": 1}
        assert saved["meta"]["created_by_user_id"] == "alice"

    def test_save_without_user_id_fails_closed(self, storage_dir):
        with pytest.raises(PermissionError):
            save_workflow("anon", {"v": 1})

    def test_save_with_empty_user_id_fails_closed(self, storage_dir):
        with pytest.raises(PermissionError):
            save_workflow("anon", {"v": 1}, user_id="")

    def test_legacy_envelope_without_user_id_can_be_claimed(self, storage_dir):
        # Envelope written before the auth refactor — has display name but no user_id
        legacy = {
            "meta": {"created_by": "old_display", "modified_by": "old_display"},
            "workflow": {"v": 0},
        }
        (storage_dir / "legacy.json").write_text(json.dumps(legacy))
        save_workflow("legacy", {"v": 1}, user_id="alice", display_name="Alice")
        saved = json.loads((storage_dir / "legacy.json").read_text())
        assert saved["meta"]["created_by_user_id"] == "alice"
        assert saved["workflow"] == {"v": 1}

    def test_legacy_raw_json_can_be_claimed(self, storage_dir):
        # File without any envelope — manually placed
        (storage_dir / "raw.json").write_text(json.dumps({"nodes": [1, 2]}))
        save_workflow("raw", {"nodes": [3, 4]}, user_id="alice", display_name="Alice")
        saved = json.loads((storage_dir / "raw.json").read_text())
        assert saved["meta"]["created_by_user_id"] == "alice"
        assert saved["workflow"] == {"nodes": [3, 4]}


class TestDeleteWorkflowAuth:
    def test_creator_can_delete_own(self, storage_dir):
        save_workflow("mine", {}, user_id="alice", display_name="Alice")
        assert delete_workflow("mine", user_id="alice") is True
        assert not (storage_dir / "mine.json").exists()
        assert list_trashed_workflows(user_id="alice")[0]["name"] == "mine"

    def test_non_creator_delete_raises_permission_error(self, storage_dir):
        save_workflow("guarded", {}, user_id="alice", display_name="Alice")
        with pytest.raises(PermissionError):
            delete_workflow("guarded", user_id="bob")
        assert (storage_dir / "guarded.json").exists()

    def test_delete_without_user_id_fails_closed(self, storage_dir):
        save_workflow("guarded", {}, user_id="alice", display_name="Alice")
        with pytest.raises(PermissionError):
            delete_workflow("guarded")

    def test_delete_with_empty_user_id_fails_closed(self, storage_dir):
        save_workflow("guarded", {}, user_id="alice", display_name="Alice")
        with pytest.raises(PermissionError):
            delete_workflow("guarded", user_id="")

    def test_delete_legacy_envelope_without_user_id_allowed_with_auth(self, storage_dir):
        # Legacy envelope (display name only, no user_id) is deletable by any authenticated user
        legacy = {
            "meta": {"created_by": "old_display"},
            "workflow": {"nodes": []},
        }
        (storage_dir / "legacy.json").write_text(json.dumps(legacy))
        assert delete_workflow("legacy", user_id="alice") is True


# ── Phase 4: Trash operations ─────────────────────────────────────


class TestTrashWorkflow:
    def test_validate_trash_id_rejects_path_traversal(self, storage_dir):
        with pytest.raises(ValueError):
            validate_trash_id("../escape")

    def test_delete_moves_to_trash_and_preserves_payload(self, storage_dir):
        data = {"nodes": [1]}
        save_workflow("demo", data, user_id="alice", display_name="Alice")
        assert delete_workflow("demo", user_id="alice", display_name="Alice") is True

        assert get_workflow("demo") is None
        trashed = list_trashed_workflows(user_id="alice")
        assert len(trashed) == 1
        assert trashed[0]["name"] == "demo"
        assert trashed[0]["deleted_by"] == "Alice"
        assert trashed[0]["deleted_at"] is not None

        trash_file = storage_dir / ".trash" / f"{trashed[0]['trash_id']}.json"
        saved = json.loads(trash_file.read_text())
        assert saved["workflow"] == data
        assert saved["meta"]["original_name"] == "demo"

    def test_list_workflows_excludes_trash(self, storage_dir):
        save_workflow("demo", {}, user_id="alice")
        delete_workflow("demo", user_id="alice")
        assert list_workflows() == []
        assert len(list_trashed_workflows(user_id="alice")) == 1

    def test_restore_round_trips_from_trash(self, storage_dir):
        data = {"nodes": [1, 2, 3]}
        save_workflow("demo", data, user_id="alice")
        delete_workflow("demo", user_id="alice")
        trash_id = list_trashed_workflows(user_id="alice")[0]["trash_id"]

        assert restore_workflow(trash_id, user_id="alice") is True
        assert get_workflow("demo") == data
        assert list_trashed_workflows(user_id="alice") == []

    def test_restore_missing_returns_false(self, storage_dir):
        assert restore_workflow("missing", user_id="alice") is False

    def test_restore_refuses_to_overwrite_active_workflow(self, storage_dir):
        save_workflow("demo", {"v": 1}, user_id="alice")
        delete_workflow("demo", user_id="alice")
        trash_id = list_trashed_workflows(user_id="alice")[0]["trash_id"]
        save_workflow("demo", {"v": 2}, user_id="alice")

        with pytest.raises(FileExistsError):
            restore_workflow(trash_id, user_id="alice")
        assert get_workflow("demo") == {"v": 2}

    def test_restore_by_non_owner_raises_permission_error(self, storage_dir):
        save_workflow("demo", {}, user_id="alice")
        delete_workflow("demo", user_id="alice")
        trash_id = list_trashed_workflows(user_id="alice")[0]["trash_id"]

        with pytest.raises(PermissionError):
            restore_workflow(trash_id, user_id="bob")

    def test_purge_deletes_trash_entry(self, storage_dir):
        save_workflow("demo", {}, user_id="alice")
        delete_workflow("demo", user_id="alice")
        trash_id = list_trashed_workflows(user_id="alice")[0]["trash_id"]

        assert purge_trashed_workflow(trash_id, user_id="alice") is True
        assert list_trashed_workflows(user_id="alice") == []

    def test_purge_by_non_owner_raises_permission_error(self, storage_dir):
        save_workflow("demo", {}, user_id="alice")
        delete_workflow("demo", user_id="alice")
        trash_id = list_trashed_workflows(user_id="alice")[0]["trash_id"]

        with pytest.raises(PermissionError):
            purge_trashed_workflow(trash_id, user_id="bob")
