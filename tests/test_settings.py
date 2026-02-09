# ABOUTME: Tests for the ComfyUI settings reader utility
# ABOUTME: Validates get_comfy_setting() with mocked filesystem scenarios

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import settings directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import get_comfy_setting


@pytest.fixture
def settings_dir(tmp_path):
    """Create a mock ComfyUI user directory structure with settings."""
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    default_dir = user_dir / "default"
    default_dir.mkdir()
    return user_dir, default_dir


def write_settings(default_dir, data):
    """Helper to write a comfy.settings.json file."""
    settings_path = default_dir / "comfy.settings.json"
    settings_path.write_text(json.dumps(data), encoding="utf-8")


class TestGetComfySetting:

    def test_reads_existing_setting(self, settings_dir):
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {"ERPK.ANTHROPIC_API_KEY": "sk-ant-test123"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY")
            assert result == "sk-ant-test123"

    def test_returns_default_when_missing(self, settings_dir):
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {"ERPK.ANTHROPIC_API_KEY": "sk-ant-test123"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.NONEXISTENT_KEY", "fallback")
            assert result == "fallback"

    def test_returns_default_when_empty_string(self, settings_dir):
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {"ERPK.ANTHROPIC_API_KEY": ""})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_returns_default_when_whitespace(self, settings_dir):
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {"ERPK.ANTHROPIC_API_KEY": "   "})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_returns_default_when_no_file(self, settings_dir):
        user_dir, default_dir = settings_dir
        # Don't write any settings file

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_returns_default_when_no_folder_paths(self):
        # Simulate folder_paths not being importable
        with patch.dict(sys.modules, {"folder_paths": None}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_returns_default_when_no_user_dirs(self, tmp_path):
        # User directory exists but has no subdirectories
        user_dir = tmp_path / "user"
        user_dir.mkdir()

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_handles_malformed_json(self, settings_dir):
        user_dir, default_dir = settings_dir
        settings_path = default_dir / "comfy.settings.json"
        settings_path.write_text("{not valid json!!!", encoding="utf-8")

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"

    def test_default_is_none_when_not_specified(self, settings_dir):
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.NONEXISTENT_KEY")
            assert result is None

    def test_returns_non_string_values_as_is(self, settings_dir):
        """Non-string values (like booleans or numbers) pass through without strip check."""
        user_dir, default_dir = settings_dir
        write_settings(default_dir, {"ERPK.SOME_FLAG": True})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.SOME_FLAG")
            assert result is True

    def test_returns_default_when_user_dir_not_exists(self):
        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = "/nonexistent/path"

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY", "fallback")
            assert result == "fallback"
