# ABOUTME: Tests for utils.safe_path — filename prefix sanitization.
# ABOUTME: Prevents path traversal via user-controlled save_file_prefix / filename_prefix.

import pytest

from utils.safe_path import safe_filename_prefix


class TestSafeFilenamePrefix:
    """safe_filename_prefix strips path traversal and separators from
    user-supplied filename prefixes."""

    def test_passes_through_plain_name(self):
        assert safe_filename_prefix("preview") == "preview"

    def test_passes_through_name_with_underscore_hyphen(self):
        assert safe_filename_prefix("my_cool-file") == "my_cool-file"

    def test_strips_parent_dir_traversal(self):
        assert safe_filename_prefix("../../../etc/passwd") == "passwd"

    def test_strips_double_dot_only(self):
        # basename("..") is ".." — caller must reject that
        result = safe_filename_prefix("..", default="safe")
        assert result == "safe"

    def test_strips_absolute_path(self):
        assert safe_filename_prefix("/etc/passwd") == "passwd"

    def test_strips_windows_path(self):
        # basename handles forward slashes; backslash is preserved on POSIX,
        # but the filename then contains a literal backslash (not a separator
        # at the FS layer on POSIX). We treat backslashes conservatively too.
        result = safe_filename_prefix(r"C:\Windows\System32\file")
        assert "/" not in result
        assert "\\" not in result

    def test_empty_string_returns_default(self):
        assert safe_filename_prefix("", default="fallback") == "fallback"

    def test_none_returns_default(self):
        assert safe_filename_prefix(None, default="fallback") == "fallback"

    def test_whitespace_only_returns_default(self):
        assert safe_filename_prefix("   ", default="fallback") == "fallback"

    def test_dot_only_returns_default(self):
        # basename(".") is "." — caller must reject
        assert safe_filename_prefix(".", default="safe") == "safe"

    def test_trailing_slash_returns_default(self):
        # basename("foo/") is "" — falls through to default
        assert safe_filename_prefix("foo/", default="safe") == "safe"

    def test_null_byte_rejected(self):
        # Null bytes are filesystem boundaries — must be rejected
        result = safe_filename_prefix("foo\x00bar", default="safe")
        assert "\x00" not in result
