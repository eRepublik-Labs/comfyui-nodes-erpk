# ABOUTME: Guards against per-module requirements.txt floors drifting below pyproject.toml.
# ABOUTME: pyproject.toml is the source of truth; every module floor must be >= its floor.

import os
import re

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _parse_floor(text):
    """Return (name_lower, version_tuple) for a `pkg>=X.Y.Z` spec, else None."""
    m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*>=\s*([0-9]+(?:\.[0-9]+)*)", text)
    if not m:
        return None
    return m.group(1).lower(), tuple(int(p) for p in m.group(2).split("."))


def _floors_from_specs(specs):
    floors = {}
    for spec in specs:
        parsed = _parse_floor(spec.split("#", 1)[0])
        if parsed:
            floors[parsed[0]] = parsed[1]
    return floors


def _pyproject_floors():
    with open(os.path.join(_REPO, "pyproject.toml")) as f:
        text = f.read()
    block = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S).group(1)
    return _floors_from_specs(re.findall(r'"([^"]+)"', block))


def _module_requirement_files():
    names = ("requirements.txt", "claude/requirements.txt", "gemini/requirements.txt",
             "grok/requirements.txt", "wavespeed/requirements.txt", "openai/requirements.txt")
    return [(n, os.path.join(_REPO, n)) for n in names if os.path.exists(os.path.join(_REPO, n))]


def test_no_module_floor_below_pyproject():
    pyproject = _pyproject_floors()
    problems = []
    for name, path in _module_requirement_files():
        with open(path) as f:
            floors = _floors_from_specs(f.readlines())
        for pkg, ver in floors.items():
            if pkg in pyproject and ver < pyproject[pkg]:
                problems.append(
                    f"{name}: {pkg}>={'.'.join(map(str, ver))} "
                    f"< pyproject {'.'.join(map(str, pyproject[pkg]))}"
                )
    assert not problems, "Per-module requirement floors below pyproject:\n" + "\n".join(problems)
