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

    def test_finds_settings_when_manager_dir_exists(self, tmp_path):
        """Settings in 'default' are found even when '__manager' dir comes first."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        # __manager comes first alphabetically but has no settings file
        (user_dir / "__manager").mkdir()
        default_dir = user_dir / "default"
        default_dir.mkdir()
        write_settings(default_dir, {"ERPK.ANTHROPIC_API_KEY": "sk-ant-test123"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.ANTHROPIC_API_KEY")
            assert result == "sk-ant-test123"


class TestMultiUserSettings:
    """Tests for multi-user settings resolution via user_id parameter."""

    def test_reads_specific_user_settings(self, tmp_path):
        """When user_id is provided, reads that user's settings file."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        alice_dir = user_dir / "alice_abc123"
        alice_dir.mkdir()
        write_settings(alice_dir, {"ERPK.GOOGLE_API_KEY": "alice-key"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.GOOGLE_API_KEY", user_id="alice_abc123")
            assert result == "alice-key"

    def test_different_users_get_different_keys(self, tmp_path):
        """Two users with different API keys get their own values."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        alice_dir = user_dir / "alice_abc123"
        alice_dir.mkdir()
        write_settings(alice_dir, {"ERPK.GOOGLE_API_KEY": "alice-key"})
        bob_dir = user_dir / "bob_def456"
        bob_dir.mkdir()
        write_settings(bob_dir, {"ERPK.GOOGLE_API_KEY": "bob-key"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            assert get_comfy_setting("ERPK.GOOGLE_API_KEY", user_id="alice_abc123") == "alice-key"
            assert get_comfy_setting("ERPK.GOOGLE_API_KEY", user_id="bob_def456") == "bob-key"

    def test_identified_user_missing_key_does_not_borrow_from_peer(self, tmp_path):
        """An identified user whose settings file exists but lacks the key
        must NOT receive another user's value for that key.

        Mirrors how production callers invoke this: no default, so the
        per-user lookup returns None and the previous code fell through
        to the peer scan."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()

        alice_dir = user_dir / "alice_abc123"
        alice_dir.mkdir()
        write_settings(alice_dir, {"ERPK.GOOGLE_API_KEY": "alice-key"})

        bob_dir = user_dir / "bob_def456"
        bob_dir.mkdir()
        write_settings(bob_dir, {"ERPK.UNRELATED": "bob-other"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.GOOGLE_API_KEY", user_id="bob_def456")
            assert result is None

    def test_identified_user_empty_value_does_not_borrow_from_peer(self, tmp_path):
        """An identified user whose value is empty/whitespace must NOT
        receive another user's value for that key."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()

        alice_dir = user_dir / "alice_abc123"
        alice_dir.mkdir()
        write_settings(alice_dir, {"ERPK.GOOGLE_API_KEY": "alice-key"})

        bob_dir = user_dir / "bob_def456"
        bob_dir.mkdir()
        write_settings(bob_dir, {"ERPK.GOOGLE_API_KEY": ""})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting(
                "ERPK.GOOGLE_API_KEY", default="missing", user_id="bob_def456"
            )
            assert result == "missing"

    def test_unknown_user_id_does_not_borrow_from_peers(self, tmp_path):
        """An identified user_id whose directory doesn't exist must NOT
        cause a peer scan. Strict isolation: user_id is a closed lookup."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        default_dir = user_dir / "default"
        default_dir.mkdir()
        write_settings(default_dir, {"ERPK.GOOGLE_API_KEY": "default-key"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting(
                "ERPK.GOOGLE_API_KEY", default="missing", user_id="nonexistent_user"
            )
            assert result == "missing"

    def test_no_user_id_uses_iteration(self, tmp_path):
        """Without user_id, falls back to iterating (default first)."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        default_dir = user_dir / "default"
        default_dir.mkdir()
        write_settings(default_dir, {"ERPK.GOOGLE_API_KEY": "default-key"})

        mock_folder_paths = MagicMock()
        mock_folder_paths.get_user_directory.return_value = str(user_dir)

        with patch.dict(sys.modules, {"folder_paths": mock_folder_paths}):
            result = get_comfy_setting("ERPK.GOOGLE_API_KEY")
            assert result == "default-key"

    def test_resolve_current_user_from_server(self, tmp_path):
        """get_current_user_id() reads client_id from PromptServer and maps to user_id."""
        from settings import get_current_user_id, _client_user_map

        # Set up the mapping
        _client_user_map["ws-client-42"] = "alice_abc123"

        # Mock PromptServer.instance.client_id
        mock_server = MagicMock()
        mock_server.client_id = "ws-client-42"

        mock_server_module = MagicMock()
        mock_server_module.PromptServer.instance = mock_server

        with patch.dict(sys.modules, {"server": mock_server_module}):
            result = get_current_user_id()
            assert result == "alice_abc123"

        # Clean up
        _client_user_map.clear()

    def test_resolve_current_user_returns_none_when_no_mapping(self):
        """get_current_user_id() returns None when client_id has no mapping."""
        from settings import get_current_user_id, _client_user_map
        _client_user_map.clear()

        mock_server = MagicMock()
        mock_server.client_id = "unknown-client"

        mock_server_module = MagicMock()
        mock_server_module.PromptServer.instance = mock_server

        with patch.dict(sys.modules, {"server": mock_server_module}):
            result = get_current_user_id()
            assert result is None

    def test_resolve_current_user_returns_none_when_no_server(self):
        """get_current_user_id() returns None when PromptServer unavailable."""
        from settings import get_current_user_id

        with patch.dict(sys.modules, {"server": None}):
            result = get_current_user_id()
            assert result is None
