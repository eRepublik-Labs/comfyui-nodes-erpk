# ABOUTME: Tests for the job history auto-clear monkey-patch.
# ABOUTME: Verifies the wrapper logic, setting-based gating, and install patching.

import types
import threading
from unittest.mock import MagicMock, patch

import pytest


class FakePromptQueue:
    """Minimal stand-in for ComfyUI's PromptQueue."""

    def __init__(self):
        self.mutex = threading.Lock()
        self.currently_running = {}
        self.history = {}
        self.server = MagicMock()
        self.task_done_calls = []

    def task_done(self, item_id, outputs, status):
        self.task_done_calls.append((item_id, outputs, status))


class TestHistoryCleanerWrapper:
    """Test the wrapped task_done logic."""

    def test_always_calls_original(self):
        """Original task_done must always be called regardless of setting."""
        from history_cleaner import make_wrapped_task_done

        queue = FakePromptQueue()
        original = MagicMock()
        wrapped = make_wrapped_task_done(original)
        bound = types.MethodType(wrapped, queue)

        with patch("history_cleaner.get_comfy_setting", return_value=False):
            bound(1, {}, {})

        original.assert_called_once_with(1, {}, {})

    def test_no_delete_when_setting_off(self):
        """When AUTO_CLEAR_HISTORY is False, history should not be touched."""
        from history_cleaner import make_wrapped_task_done

        queue = FakePromptQueue()
        queue.currently_running = {1: (None, "prompt-abc")}
        queue.history = {"prompt-abc": {"outputs": {}}}

        original = MagicMock()
        wrapped = make_wrapped_task_done(original)
        bound = types.MethodType(wrapped, queue)

        with patch("history_cleaner.get_comfy_setting", return_value=False):
            with patch("threading.Thread") as mock_thread:
                bound(1, {}, {})

        mock_thread.assert_not_called()

    def test_schedules_delete_when_setting_on(self):
        """When AUTO_CLEAR_HISTORY is True, a delayed delete thread should be spawned."""
        from history_cleaner import make_wrapped_task_done

        queue = FakePromptQueue()
        queue.currently_running = {1: (None, "prompt-xyz")}
        queue.history = {"prompt-xyz": {"outputs": {}}}

        original = MagicMock()
        wrapped = make_wrapped_task_done(original)
        bound = types.MethodType(wrapped, queue)

        with patch("history_cleaner.get_comfy_setting", return_value=True):
            with patch("threading.Thread") as mock_thread:
                mock_thread.return_value = MagicMock()
                bound(1, {}, {})

        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args
        assert call_kwargs.kwargs.get("daemon") is True

    def test_original_called_even_when_setting_on(self):
        """Original task_done must fire even when auto-clear is enabled."""
        from history_cleaner import make_wrapped_task_done

        queue = FakePromptQueue()
        queue.currently_running = {1: (None, "prompt-123")}

        original = MagicMock()
        wrapped = make_wrapped_task_done(original)
        bound = types.MethodType(wrapped, queue)

        with patch("history_cleaner.get_comfy_setting", return_value=True):
            with patch("threading.Thread") as mock_thread:
                mock_thread.return_value = MagicMock()
                bound(1, {}, {})

        original.assert_called_once()

    def test_no_crash_when_item_not_in_currently_running(self):
        """Should handle missing item_id gracefully (no thread spawned)."""
        from history_cleaner import make_wrapped_task_done

        queue = FakePromptQueue()
        queue.currently_running = {}

        original = MagicMock()
        wrapped = make_wrapped_task_done(original)
        bound = types.MethodType(wrapped, queue)

        with patch("history_cleaner.get_comfy_setting", return_value=True):
            with patch("threading.Thread") as mock_thread:
                bound(99, {}, {})

        original.assert_called_once()
        mock_thread.assert_not_called()


class TestInstall:
    """Test that install() patches PromptQueue.task_done."""

    def test_patches_task_done(self):
        from history_cleaner import install

        fake_queue = FakePromptQueue()
        original_method = fake_queue.task_done

        fake_server = MagicMock()
        fake_server.prompt_queue = fake_queue

        with patch("history_cleaner.PromptServer") as mock_ps:
            mock_ps.instance = fake_server
            install()

        assert fake_queue.task_done is not original_method
