# ABOUTME: Pytest configuration that installs comfy_api stub for V3 node tests.
# ABOUTME: Uses a lightweight stub so tests run anywhere without a ComfyUI installation.

import sys
import os
import types

# Add project root for package imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Install comfy_api stub as a fake package in sys.modules.
# This lets `from comfy_api.latest import IO, ComfyExtension` work in tests
# without requiring a real ComfyUI installation.
if "comfy_api" not in sys.modules:
    from tests import comfy_api_stub as stub

    # Create the package hierarchy: comfy_api -> comfy_api.latest
    comfy_api_pkg = types.ModuleType("comfy_api")
    comfy_api_pkg.__path__ = []

    comfy_api_latest = types.ModuleType("comfy_api.latest")
    comfy_api_latest.IO = stub
    comfy_api_latest.ComfyExtension = stub.ComfyExtension

    comfy_api_pkg.latest = comfy_api_latest

    sys.modules["comfy_api"] = comfy_api_pkg
    sys.modules["comfy_api.latest"] = comfy_api_latest
