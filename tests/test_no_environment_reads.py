# ABOUTME: Keeps shipped code from reading process environment variables.
# ABOUTME: The Comfy Registry scan flags env reads and stops serving the version.

"""
The Comfy Registry scans every published version. Its automated rule
python_environment_manipulation flagged 2026.9.1 through 2026.9.9 for one
os.environ.get("HF_HUB_CACHE") call, and a flagged version is never served
to users. API keys also stopped coming from env vars on 2026-05-29. So no
module that ships may read the environment.
"""

import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_READ = re.compile(r"\bos\.environ\b|\bos\.getenv\b|\bgetenv\(")


def _shipped_python_files():
    # Tracked files are what gets published; local caches and venvs are not.
    tracked = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    for name in tracked:
        if not name.startswith("tests/"):
            yield ROOT / name


def test_shipped_code_scan_covers_the_package():
    names = {p.relative_to(ROOT).as_posix() for p in _shipped_python_files()}
    assert "__init__.py" in names
    assert "utils/scan_engine.py" in names


def test_shipped_code_reads_no_environment_variables():
    hits = []
    for path in _shipped_python_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ENV_READ.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert hits == []
