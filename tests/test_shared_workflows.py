# ABOUTME: Tests for the shared workflows CRUD module
# ABOUTME: Covers name validation, list/get/save/delete operations

import json
import os
import time

import pytest

from shared_workflows import (
    STORAGE_DIR,
    delete_workflow,
    get_workflow,
    list_workflows,
    save_workflow,
    validate_name,
)


@pytest.fixture
def storage_dir(tmp_path, monkeypatch):
    d = tmp_path / "shared_workflows"
    d.mkdir()
    import shared_workflows
    monkeypatch.setattr(shared_workflows, "STORAGE_DIR", str(d))
    return d


# ── Phase 1: Name validation ──────────────────────────────────────


class TestValidateName:
    def test_accepts_simple_alphanumeric(self):
        assert validate_name("myworkflow") == "myworkflow"

    def test_accepts_spaces_and_hyphens(self):
        assert validate_name("my cool workflow-v2") == "my cool workflow-v2"

    def test_accepts_underscores(self):
        assert validate_name("my_workflow_1") == "my_workflow_1"

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
        # Write two workflows with different mtimes
        w1 = storage_dir / "alpha.json"
        w1.write_text(json.dumps({"nodes": []}))
        time.sleep(0.05)
        w2 = storage_dir / "beta.json"
        w2.write_text(json.dumps({"nodes": [], "extra": True}))

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

    def test_list_ignores_non_json(self, storage_dir):
        (storage_dir / "readme.txt").write_text("not a workflow")
        (storage_dir / "real.json").write_text(json.dumps({}))
        result = list_workflows()
        assert len(result) == 1
        assert result[0]["name"] == "real"


class TestGetWorkflow:
    def test_get_existing(self, storage_dir):
        data = {"nodes": [1, 2, 3]}
        (storage_dir / "demo.json").write_text(json.dumps(data))
        result = get_workflow("demo")
        assert result == data

    def test_get_missing(self, storage_dir):
        assert get_workflow("nonexistent") is None

    def test_get_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            get_workflow("../etc/passwd")


class TestSaveWorkflow:
    def test_save_new(self, storage_dir):
        data = {"nodes": [1]}
        save_workflow("newflow", data)
        saved = json.loads((storage_dir / "newflow.json").read_text())
        assert saved == data

    def test_save_overwrites(self, storage_dir):
        save_workflow("overwrite", {"v": 1})
        save_workflow("overwrite", {"v": 2})
        saved = json.loads((storage_dir / "overwrite.json").read_text())
        assert saved == {"v": 2}

    def test_save_creates_dir(self, tmp_path, monkeypatch):
        import shared_workflows
        new_dir = str(tmp_path / "brand_new")
        monkeypatch.setattr(shared_workflows, "STORAGE_DIR", new_dir)
        save_workflow("first", {"created": True})
        assert os.path.isfile(os.path.join(new_dir, "first.json"))

    def test_save_no_tmp_left(self, storage_dir):
        save_workflow("clean", {"data": True})
        files = os.listdir(str(storage_dir))
        assert files == ["clean.json"]

    def test_save_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            save_workflow("../escape", {"bad": True})


class TestDeleteWorkflow:
    def test_delete_existing(self, storage_dir):
        (storage_dir / "doomed.json").write_text(json.dumps({}))
        assert delete_workflow("doomed") is True
        assert not (storage_dir / "doomed.json").exists()

    def test_delete_missing(self, storage_dir):
        assert delete_workflow("ghost") is False

    def test_delete_invalid_name(self, storage_dir):
        with pytest.raises(ValueError):
            delete_workflow("../escape")
