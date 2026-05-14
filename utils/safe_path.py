# ABOUTME: Filename prefix sanitizer that strips path traversal and separators.
# ABOUTME: Used by save-file nodes to prevent user-controlled prefixes from escaping output dirs.

import os
import re

_UNSAFE_CHARS = re.compile(r"[\x00\\/]")


def safe_filename_prefix(prefix, default="output"):
    """Return a filename-safe prefix derived from user input.

    Strips path components via os.path.basename, removes null bytes and
    backslashes, and falls back to `default` for anything that would yield
    an unsafe or empty result (None, empty, whitespace-only, ".", "..",
    trailing slash, etc.).

    Args:
        prefix: User-supplied prefix string (may be None, empty, or hostile)
        default: Fallback when input is missing or sanitizes to nothing

    Returns:
        str: A safe filename prefix containing no path separators or traversal
    """
    if not prefix or not isinstance(prefix, str):
        return default

    name = os.path.basename(prefix.strip())
    name = _UNSAFE_CHARS.sub("", name)

    if not name or name in (".", ".."):
        return default

    return name
