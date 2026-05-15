# ABOUTME: Guards against absolute imports of the package's settings module.
# ABOUTME: ComfyUI loads the package via spec_from_file_location; absolute imports break.

import ast
import pathlib


SKIP_DIRS = {"tests", "web", ".cs", ".git", "__pycache__", ".venv", "venv", "build", "dist"}


def test_no_absolute_settings_imports_in_package():
    """Production modules must not use `from settings import ...` or `import settings`.

    ComfyUI loads custom-node packages with `importlib.util.spec_from_file_location`,
    which sets the package's `__path__` but does not add the package directory to
    `sys.path`. Relative imports (`from .settings import ...`) resolve via `__path__`
    and work; absolute imports fall through to `sys.path` and fail at startup with
    `ModuleNotFoundError: No module named 'settings'`.

    Tests are allowed to use absolute imports because the test harness explicitly
    inserts the project root into `sys.path` via conftest.py.
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
                if node.level == 0 and node.module == "settings":
                    offenders.append(
                        f"{py_file.relative_to(root)}:{node.lineno}: from settings import ..."
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "settings":
                        offenders.append(
                            f"{py_file.relative_to(root)}:{node.lineno}: import settings"
                        )

    assert not offenders, (
        "Absolute imports of the package's settings module break ComfyUI's loader. "
        "Use relative imports (from .settings or from ..settings) instead:\n  "
        + "\n  ".join(offenders)
    )
