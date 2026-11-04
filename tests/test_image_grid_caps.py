# ABOUTME: Tests for the per-model image grid caps: the registry each grid node fills at import,
# ABOUTME: the over-cap error that names the model or node setting the cap, and the /erpk/grid_caps route.

import asyncio
import pathlib
import re
import sys
import types

import pytest
from aiohttp.test_utils import TestClient, TestServer

import erpk.gemini  # noqa: F401  (each grid node module registers its caps on import)
import erpk.grok  # noqa: F401
import erpk.openai  # noqa: F401
import erpk.utils  # noqa: F401
import erpk.wavespeed  # noqa: F401
from erpk.utils import image_grid
from erpk.utils.image_grid import GridCap, grid_cap_for, load_grid_images, register_grid_caps
from tests.test_shared_workflow_routes import routes_app  # noqa: F401  (pytest fixture)


@pytest.fixture(autouse=True)
def registry():
    saved = dict(image_grid.GRID_CAPS)
    yield image_grid.GRID_CAPS
    image_grid.GRID_CAPS.clear()
    image_grid.GRID_CAPS.update(saved)


def test_a_listed_model_gets_its_own_cap():
    register_grid_caps("CapsProbe", {"model-a": 4, "model-b": 9}, model_widget="model")
    assert grid_cap_for("CapsProbe", "model-a") == 4
    assert grid_cap_for("CapsProbe", "model-b") == 9


def test_an_unlisted_model_gets_the_star_cap():
    register_grid_caps("CapsProbe", {"model-a": 4, "*": 6}, model_widget="model")
    assert grid_cap_for("CapsProbe", "model-z") == 6


def test_an_unlisted_model_without_a_star_gets_the_largest_cap():
    register_grid_caps("CapsProbe", {"model-a": 4, "model-b": 9}, model_widget="model")
    assert grid_cap_for("CapsProbe", "model-z") == 9


def test_an_unregistered_node_is_refused():
    with pytest.raises(ValueError) as exc:
        grid_cap_for("NoSuchNode", "model-a")
    assert str(exc.value) == "No grid caps registered for NoSuchNode"


def test_a_node_without_a_model_widget_takes_only_a_star_cap():
    with pytest.raises(ValueError) as exc:
        register_grid_caps("CapsProbe", {"model-a": 4}, model_widget=None)
    assert str(exc.value) == "CapsProbe has no model widget, so its grid caps must be {'*': n}, got {'model-a': 4}"
    assert "CapsProbe" not in image_grid.GRID_CAPS


@pytest.mark.parametrize("caps", [{}, {"model-a": 0}, {"model-a": "4"}])
def test_caps_must_be_positive_counts(caps):
    with pytest.raises(ValueError) as exc:
        register_grid_caps("CapsProbe", caps, model_widget="model")
    assert str(exc.value) == f"Grid caps for CapsProbe must map models to positive counts, got {caps!r}"


@pytest.fixture
def five_files(monkeypatch, tmp_path):
    from PIL import Image

    inp = tmp_path / "input"
    inp.mkdir()
    names = [f"{i}.png" for i in range(1, 6)]
    for name in names:
        Image.new("RGB", (2, 2), (0, 0, 0)).save(inp / name)
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return '["' + '", "'.join(names) + '"]'


@pytest.mark.parametrize("name,cap,message", [
    ("gpt-image-2.5-flare", 4, "The grid holds 5 images but gpt-image-2.5-flare takes up to 4 images; remove 1"),
    ("Seedream", 1, "The grid holds 5 images but Seedream takes up to 1 image; remove 4"),
])
def test_a_grid_over_its_cap_names_what_sets_the_cap(five_files, name, cap, message):
    with pytest.raises(ValueError) as exc:
        load_grid_images(five_files, GridCap(name, cap))
    assert str(exc.value) == message


def test_a_grid_at_its_cap_loads_every_image(five_files):
    pictures = load_grid_images(five_files, GridCap("gpt-image-2.5-flare", 5))
    assert [(p.mode, p.size) for p in pictures] == [("RGB", (2, 2))] * 5


def _get_grid_caps(app):
    async def run():
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.get("/erpk/grid_caps")
            return resp.status, await resp.json()
        finally:
            await client.close()

    return asyncio.run(run())


def test_the_route_serves_caps_registered_after_it_was_defined(routes_app):
    register_grid_caps("CapsProbe", {"model-a": 4, "*": 6}, model_widget="model")
    register_grid_caps("CapsLoaderProbe", {"*": 14}, model_widget=None)
    status, body = _get_grid_caps(routes_app)
    assert status == 200
    assert body["CapsProbe"] == {"model_widget": "model", "caps": {"model-a": 4, "*": 6}}
    assert body["CapsLoaderProbe"] == {"model_widget": None, "caps": {"*": 14}}


def test_the_route_serves_the_openai_edit_and_loader_caps(routes_app):
    status, body = _get_grid_caps(routes_app)
    assert status == 200
    assert body["OpenAIImageEdit"] == {"model_widget": "model", "caps": {"*": 16}}
    assert body["ImageGridLoader"] == {"model_widget": None, "caps": {"*": 14}}


GRID_NODE_IDS = re.findall(
    r'nodeId: "(\w+)"', (pathlib.Path(__file__).parents[1] / "web" / "image_grid.js").read_text())


def _schema_of(node_id):
    import erpk.gemini, erpk.grok, erpk.openai, erpk.utils, erpk.wavespeed  # noqa: E401

    for module in (erpk.gemini, erpk.grok, erpk.openai, erpk.utils, erpk.wavespeed):
        for node in module.NODES:
            schema = node.define_schema()
            if schema.node_id == node_id:
                return schema
    raise AssertionError(f"No node class has node_id {node_id}")


def test_every_grid_node_in_the_frontend_has_caps():
    assert len(GRID_NODE_IDS) == 18
    assert sorted(set(GRID_NODE_IDS) - set(image_grid.GRID_CAPS)) == []


@pytest.mark.parametrize("node_id", GRID_NODE_IDS)
def test_a_model_widget_is_a_combo_on_the_node_and_lists_every_capped_model(node_id):
    entry = image_grid.GRID_CAPS[node_id]
    inputs = {i.id: i for i in _schema_of(node_id).inputs}
    if entry["model_widget"] is None:
        assert "model" not in inputs
        return
    combo = inputs[entry["model_widget"]]
    assert combo.io_type == "COMBO"
    assert sorted(set(entry["caps"]) - {"*"} - set(combo.options)) == []
