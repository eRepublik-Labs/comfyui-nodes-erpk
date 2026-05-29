# ABOUTME: Verifies the package exposes a version string sourced from pyproject.toml.
# ABOUTME: __version__ must stay in sync with pyproject.toml's [project] version.

import importlib
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version():
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "version not found in pyproject.toml"
    return match.group(1)


def test_pyproject_has_a_version():
    version = _pyproject_version()
    assert version and version != "unknown"


def test_init_exposes_version_matching_pyproject():
    mod = importlib.import_module("__init__")
    assert isinstance(mod.__version__, str) and mod.__version__
    assert mod.__version__ == _pyproject_version()


def test_resolve_version_reads_given_pyproject(tmp_path):
    mod = importlib.import_module("__init__")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\nversion = "1.2.3"\n', encoding="utf-8")
    assert mod._resolve_version(str(pyproject)) == "1.2.3"


def test_resolve_version_missing_file_returns_unknown(tmp_path):
    mod = importlib.import_module("__init__")
    assert mod._resolve_version(str(tmp_path / "does-not-exist.toml")) == "unknown"
