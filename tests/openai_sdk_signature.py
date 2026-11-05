# ABOUTME: Reads keyword parameters of the installed openai SDK's methods in a clean subprocess.
# ABOUTME: Tests use it to prove a request would bind to the real SDK, which a MagicMock never checks.

import functools
import json
import subprocess
import sys

# Our openai/ package shadows the SDK inside pytest (the repo root is on
# sys.path), so the SDK is imported in an isolated interpreter (-I drops the
# cwd and script directory from sys.path).
_SCRIPT = """
import importlib, inspect, json, sys
module_name, class_name, method_name = sys.argv[1:4]
cls = getattr(importlib.import_module(module_name), class_name)
print(json.dumps(sorted(inspect.signature(getattr(cls, method_name)).parameters)))
"""


@functools.lru_cache(maxsize=None)
def sdk_parameters(module_name: str, class_name: str, method_name: str) -> frozenset:
    """Parameter names of e.g. openai.resources.images.Images.edit."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", _SCRIPT, module_name, class_name, method_name],
        capture_output=True, text=True, check=True, cwd="/",
    )
    return frozenset(json.loads(result.stdout))


@functools.lru_cache(maxsize=None)
def sdk_has(module_name: str, attribute: str) -> bool:
    """Whether the installed SDK's module exposes `attribute`, e.g. openai.types.ImagesResponse."""
    result = subprocess.run(
        [sys.executable, "-I", "-c",
         "import importlib, sys; print(hasattr(importlib.import_module(sys.argv[1]), sys.argv[2]))",
         module_name, attribute],
        capture_output=True, text=True, check=True, cwd="/",
    )
    return result.stdout.strip() == "True"


def assert_binds(params: dict, module_name: str, class_name: str, method_name: str) -> None:
    """Fail with the offending names when the SDK method has no such keyword."""
    unknown = set(params) - sdk_parameters(module_name, class_name, method_name)
    assert not unknown, (
        f"{class_name}.{method_name}() has no keyword {sorted(unknown)}; "
        f"the real SDK raises TypeError before any request is sent"
    )
