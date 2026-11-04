# ABOUTME: Tests for the image grid on Grok Image Edit: where its inputs sit in the saved widget list,
# ABOUTME: which images reach edit_image (socket or grid files at their own size), and the grid's errors.

import asyncio
import base64
import io
import json
import sys
import types
from types import SimpleNamespace

import pytest

from erpk.grok import nodes
from erpk.grok.nodes import GrokImageEdit

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")


def frontend_widget_order(schema):
    # The frontend lays out required inputs before optional ones, each group in
    # schema order (getOrderedInputSpecs in the bundled ComfyUI frontend), and
    # widgets_values follows that order.
    widgets = [i for i in schema.inputs if i.io_type in WIDGET_TYPES]
    return ([i.id for i in widgets if not i.optional]
            + [i.id for i in widgets if i.optional])


def test_grid_widgets_follow_every_saved_widget():
    assert frontend_widget_order(GrokImageEdit.define_schema()) == [
        "prompt", "model", "aspect_ratio", "resolution", "n", "quality",
        "grid_images",
    ]


def test_image_socket_is_optional_and_the_grid_starts_empty():
    inputs = {i.id: i for i in GrokImageEdit.define_schema().inputs}
    assert inputs["image"].optional is True
    assert inputs["grid_images"].default == "[]"


@pytest.fixture
def input_dir(monkeypatch, tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return inp


@pytest.fixture
def sent(monkeypatch):
    """What reaches GrokClient.edit_image; the call then fails so nothing is downloaded."""
    seen = {}

    async def edit_image(prompt, image_urls, **kwargs):
        seen["image_urls"] = image_urls
        raise RuntimeError("stop here")

    monkeypatch.setattr(nodes, "_make_grok_client", lambda client_dict: SimpleNamespace(edit_image=edit_image))
    return seen


def _edit(**inputs):
    return asyncio.run(GrokImageEdit.execute(prompt="make it blue", **inputs))


@pytest.mark.parametrize("grid", [{"grid_images": "[]"}, {}])
def test_no_socket_and_an_empty_grid_names_both_ways_in(input_dir, sent, grid):
    with pytest.raises(ValueError) as exc:
        _edit(**grid)
    assert str(exc.value) == "Connect an image or add images to the grid"
    assert sent == {}


def _write(path, size, color, **save):
    from PIL import Image

    Image.new("RGB", size, color).save(path, **save)


def _decoded(uri):
    from PIL import Image

    header, payload = uri.split(",", 1)
    with Image.open(io.BytesIO(base64.b64decode(payload))) as img:
        return header, img.format, img.size


def _edit_until_sent(**inputs):
    with pytest.raises(ValueError, match="stop here"):
        _edit(**inputs)


def test_grid_files_reach_the_api_one_data_uri_each_at_their_own_size_in_grid_order(input_dir, sent):
    _write(input_dir / "wide.jpg", (7, 2), (255, 255, 255), quality=100)
    _write(input_dir / "tall.webp", (3, 9), (0, 0, 255), lossless=True)
    _edit_until_sent(grid_images='["tall.webp", "wide.jpg"]')
    assert [_decoded(uri) for uri in sent["image_urls"]] == [
        ("data:image/jpeg;base64", "JPEG", (3, 9)),
        ("data:image/jpeg;base64", "JPEG", (7, 2)),
    ]


def test_an_entry_outside_the_input_folder_is_refused(input_dir, sent):
    _write(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        _edit(grid_images='["../outside.png"]')
    assert str(exc.value) == "grid_images entry 1 is outside ComfyUI's input directory: '../outside.png'"
    assert sent == {}


def test_a_connected_image_is_sent_and_the_grid_not_read(input_dir, sent):
    torch = pytest.importorskip("torch")
    _write(input_dir / "a.png", (5, 3), (255, 0, 0))
    # The second entry is missing, so reading the grid would raise.
    _edit_until_sent(image=torch.zeros(1, 8, 6, 3), grid_images='["a.png", "gone.png"]')
    assert [_decoded(uri) for uri in sent["image_urls"]] == [("data:image/jpeg;base64", "JPEG", (6, 8))]


def test_validation_passes_an_empty_grid_and_names_a_missing_file(input_dir):
    _write(input_dir / "a.png", (2, 2), (0, 0, 0))
    assert GrokImageEdit.validate_inputs() is True
    assert GrokImageEdit.validate_inputs(grid_images="[]") is True
    assert GrokImageEdit.validate_inputs(grid_images='["a.png"]') is True
    assert GrokImageEdit.validate_inputs(grid_images='["a.png", "gone.png"]') == (
        "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'")


def test_more_grid_files_than_xai_takes_are_refused_not_dropped(input_dir, sent):
    names = [f"{i}.png" for i in range(6)]
    for name in names:
        _write(input_dir / name, (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        _edit(model="grok-imagine-image-2.0", grid_images=json.dumps(names))
    assert str(exc.value) == "The grid holds 6 images but grok-imagine-image-2.0 takes up to 5 images; remove 1"
    assert sent == {}
