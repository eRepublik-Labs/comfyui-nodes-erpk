# ABOUTME: Guards against absolute imports of internal top-level package modules.
# ABOUTME: ComfyUI loads the package via spec_from_file_location; absolute imports break.

import ast
import pathlib


SKIP_DIRS = {"tests", "web", ".cs", ".git", "__pycache__", ".venv", "venv", "build", "dist"}

# Top-level package directories and modules inside this custom-node package.
# Any absolute import of these names from inside the package is a bug — they
# resolve via sys.path under pytest (conftest inserts project root) but fail
# at ComfyUI runtime, where the loader uses spec_from_file_location and does
# NOT extend sys.path.
#
# `openai` is intentionally excluded: the internal `openai/` directory shares a
# name with the third-party OpenAI SDK (PyPI), and `from openai import OpenAI`
# is the canonical SDK call. The guard can't distinguish without context. A
# hypothetical misuse of `from openai import <our_internal_symbol>` would fail
# loudly with `ImportError: cannot import name X from openai`, so the silent-
# failure risk that motivates this guard doesn't apply.
INTERNAL_NAMES = {
    "claude",
    "gemini",
    "wavespeed",
    "utils",
    "settings",
    "shared_workflows",
    "metadata_filter",
    "history_cleaner",
}


def _root_name(dotted):
    """First segment of a dotted module name. 'utils.safe_fetch' -> 'utils'."""
    return dotted.split(".", 1)[0] if dotted else ""


def test_no_absolute_imports_of_internal_modules():
    """Production modules must use relative imports for sibling/internal modules.

    ComfyUI loads custom-node packages with `importlib.util.spec_from_file_location`,
    which sets the package's `__path__` but does not add the package directory to
    `sys.path`. Relative imports resolve via `__path__` and work; absolute imports
    fall through to `sys.path` and fail at startup with `ModuleNotFoundError`.

    Tests are allowed to use absolute imports because conftest.py inserts the
    project root into `sys.path`.

    Catches both shapes:
        from utils.safe_fetch import x   (ImportFrom, level=0, module starts with internal name)
        import utils.safe_fetch          (Import, alias starts with internal name)
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    offenders = []

    for py_file in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in py_file.relative_to(root).parts):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 0 and _root_name(node.module) in INTERNAL_NAMES:
                    offenders.append(
                        f"{py_file.relative_to(root)}:{node.lineno}: from {node.module} import ..."
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if _root_name(alias.name) in INTERNAL_NAMES:
                        offenders.append(
                            f"{py_file.relative_to(root)}:{node.lineno}: import {alias.name}"
                        )

    assert not offenders, (
        "Absolute imports of internal package modules break ComfyUI's loader. "
        "Use relative imports (from . / from .. / from ...) instead:\n  "
        + "\n  ".join(offenders)
    )
