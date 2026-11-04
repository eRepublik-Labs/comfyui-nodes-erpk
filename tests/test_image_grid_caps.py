# ABOUTME: Tests for the per-model image grid caps: the registry each grid node fills at import,
# ABOUTME: the over-cap errors that name the model or the grid_max_images widget, and the /erpk/grid_caps route.

import asyncio
import sys
import types

import pytest
from aiohttp.test_utils import TestClient, TestServer

from erpk.utils import image_grid
from erpk.utils.image_grid import ModelCap, grid_cap_for, load_grid_images, register_grid_caps
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


@pytest.mark.parametrize("max_images", [10, 4])
def test_a_model_cap_at_or_below_the_widget_names_the_model(five_files, max_images):
    with pytest.raises(ValueError) as exc:
        load_grid_images(five_files, max_images, model_cap=ModelCap("gpt-image-2.5-flare", 4))
    assert str(exc.value) == "The grid holds 5 images but gpt-image-2.5-flare takes up to 4; remove 1"


def test_a_widget_below_the_model_cap_names_the_widget(five_files):
    with pytest.raises(ValueError) as exc:
        load_grid_images(five_files, 3, model_cap=ModelCap("gpt-image-2.5-flare", 4))
    assert str(exc.value) == "The grid holds 5 images but grid_max_images is 3; remove 2 or raise grid_max_images"


def test_a_grid_within_both_caps_loads_every_image(five_files):
    pictures = load_grid_images(five_files, 5, model_cap=ModelCap("gpt-image-2.5-flare", 5))
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

