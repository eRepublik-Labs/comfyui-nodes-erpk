# ABOUTME: Runs web/openai_dynamic_sizes.js under node to check the frame_count repair on workflow load.
# ABOUTME: A workflow saved with frame_count 17-64 would fail ComfyUI's max check, so onConfigure clamps it.

import json
import pathlib
import shutil
import subprocess

import pytest

MODULE = pathlib.Path(__file__).parents[1] / "web" / "openai_dynamic_sizes.js"
APP_IMPORT = 'import { app } from "../../../scripts/app.js";'


def _repair(tmp_path, widgets):
    """Run repairFrameCount on a node holding these widgets; return each widget's value afterwards."""
    node_bin = shutil.which("node")
    if node_bin is None:
        pytest.skip("node is not installed")
    source = MODULE.read_text()
    assert APP_IMPORT in source, "the module's app import changed; update this harness"
    module = tmp_path / "openai_dynamic_sizes.mjs"
    module.write_text(source.replace(APP_IMPORT, "const app = { registerExtension() {} };"))
    script = (
        f"import {{ repairFrameCount }} from {json.dumps(module.as_uri())};\n"
        f"const node = {{ widgets: {json.dumps(widgets)} }};\n"
        "repairFrameCount(node);\n"
        "console.log(JSON.stringify(node.widgets.map((w) => w.value)));\n"
    )
    result = subprocess.run(
        [node_bin, "--input-type=module", "-e", script], capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _frame_count(value):
    return {"name": "frame_count", "value": value, "options": {"min": 2, "max": 16}}


@pytest.mark.parametrize("stored", [17, 64])
def test_a_count_above_the_widget_max_is_clamped_to_it(tmp_path, stored):
    assert _repair(tmp_path, [_frame_count(stored)]) == [16]


@pytest.mark.parametrize("stored", [2, 9, 16])
def test_a_count_the_schema_accepts_is_left_alone(tmp_path, stored):
    assert _repair(tmp_path, [_frame_count(stored)]) == [stored]


def test_a_node_without_frame_count_is_untouched(tmp_path):
    widgets = [{"name": "size", "value": "auto", "options": {"values": ["auto"]}}]
    assert _repair(tmp_path, widgets) == ["auto"]
