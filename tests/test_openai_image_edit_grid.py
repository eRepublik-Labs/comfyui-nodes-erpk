# ABOUTME: Tests for the image grid on OpenAI Image Edit: where its inputs sit in the saved widget list,
# ABOUTME: which images reach images.edit (socket or grid files at their own size), and the grid's errors.

import asyncio
import io
import sys
import types
from types import SimpleNamespace

import pytest

from erpk.openai.image_nodes import OpenAIImageEdit

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")


def frontend_widget_order(schema):
    # The frontend lays out required inputs before optional ones, each group in
    # schema order (getOrderedInputSpecs in the bundled ComfyUI frontend), and
    # widgets_values follows that order.
    widgets = [i for i in schema.inputs if i.io_type in WIDGET_TYPES]
    return ([i.id for i in widgets if not i.optional]
            + [i.id for i in widgets if i.optional])


def test_grid_widgets_follow_every_saved_widget():
    assert frontend_widget_order(OpenAIImageEdit.define_schema()) == [
        "prompt", "seed", "model", "size", "custom_width", "custom_height",
        "quality", "moderation", "n", "background", "input_fidelity",
        "output_format", "output_compression", "grid_images", "grid_max_images",
    ]


def test_image_socket_is_optional_and_the_grid_caps_at_sixteen():
    inputs = {i.id: i for i in OpenAIImageEdit.define_schema().inputs}
    assert inputs["image"].optional is True
    assert inputs["grid_images"].default == "[]"
    assert (inputs["grid_max_images"].default, inputs["grid_max_images"].min, inputs["grid_max_images"].max) == (10, 1, 16)


@pytest.fixture
def input_dir(monkeypatch, tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return inp


def _recording_client(seen):
    async def edit_image(**kwargs):
        seen.update(kwargs)
        return {"blocked": True, "error": "stop here"}
    return SimpleNamespace(edit_image=edit_image)


def _edit(seen, **inputs):
    with pytest.raises(ValueError, match="stop here"):
        asyncio.run(OpenAIImageEdit.execute(prompt="add a hat", client=_recording_client(seen), **inputs))


@pytest.mark.parametrize("grid", [{"grid_images": "[]"}, {}])
def test_no_socket_and_an_empty_grid_names_both_ways_in(input_dir, grid):
    seen = {}
    with pytest.raises(ValueError) as exc:
        asyncio.run(OpenAIImageEdit.execute(prompt="add a hat", client=_recording_client(seen), **grid))
    assert str(exc.value) == "Connect an image or add images to the grid"
    assert seen == {}


def _write(path, size, color, **save):
    from PIL import Image

    Image.new("RGB", size, color).save(path, **save)


def _decoded(payload):
    from PIL import Image

    with Image.open(io.BytesIO(payload)) as img:
        return img.format, img.size, img.getpixel((0, 0))


def test_grid_files_reach_the_api_one_png_each_at_their_own_size_in_grid_order(input_dir):
    _write(input_dir / "wide.jpg", (7, 2), (255, 255, 255), quality=100)
    _write(input_dir / "tall.webp", (3, 9), (0, 0, 255), lossless=True)
    seen = {}
    _edit(seen, grid_images='["tall.webp", "wide.jpg"]')
    assert [_decoded(payload) for payload in seen["image_data"]] == [
        ("PNG", (3, 9), (0, 0, 255)),
        ("PNG", (7, 2), (255, 255, 255)),
    ]


def test_more_files_than_max_images_names_both_counts(input_dir):
    for name in ("a.png", "b.png", "c.png"):
        _write(input_dir / name, (2, 2), (0, 0, 0))
    seen = {}
    with pytest.raises(ValueError) as exc:
        asyncio.run(OpenAIImageEdit.execute(
            prompt="add a hat", client=_recording_client(seen),
            grid_images='["a.png", "b.png", "c.png"]', grid_max_images=2,
        ))
    assert str(exc.value) == "The grid holds 3 images but grid_max_images is 2; remove 1 or raise grid_max_images"
    assert seen == {}


def test_an_entry_outside_the_input_folder_is_refused(input_dir):
    _write(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    seen = {}
    with pytest.raises(ValueError) as exc:
        asyncio.run(OpenAIImageEdit.execute(
            prompt="add a hat", client=_recording_client(seen), grid_images='["../outside.png"]',
        ))
    assert str(exc.value) == "grid_images entry 1 is outside ComfyUI's input directory: '../outside.png'"
    assert seen == {}


def test_a_connected_image_is_sent_and_the_grid_not_read(input_dir):
    torch = pytest.importorskip("torch")
    _write(input_dir / "a.png", (5, 3), (255, 0, 0))
    _write(input_dir / "b.png", (5, 3), (255, 0, 0))
    seen = {}
    # Over its cap, so reading the grid would raise.
    _edit(seen, image=torch.zeros(1, 8, 6, 3), grid_images='["a.png", "b.png"]', grid_max_images=1)
    assert _decoded(seen["image_data"]) == ("PNG", (6, 8), (0, 0, 0))


def test_a_mask_shapes_the_first_grid_image(input_dir):
    torch = pytest.importorskip("torch")
    from PIL import Image

    _write(input_dir / "first.png", (3, 2), (0, 255, 0))
    _write(input_dir / "second.png", (5, 5), (0, 0, 255))
    mask = torch.zeros(1, 2, 3)
    mask[0, 0, 1] = 1.0
    seen = {}
    _edit(seen, mask=mask, grid_images='["first.png", "second.png"]')
    with Image.open(io.BytesIO(seen["mask_data"])) as sent:
        assert (sent.mode, sent.size) == ("RGBA", (3, 2))
        assert list(sent.getdata()) == [
            (0, 255, 0, 255), (0, 255, 0, 0), (0, 255, 0, 255),
            (0, 255, 0, 255), (0, 255, 0, 255), (0, 255, 0, 255),
        ]


def test_validation_passes_an_empty_grid_and_names_a_missing_file(input_dir):
    _write(input_dir / "a.png", (2, 2), (0, 0, 0))
    assert OpenAIImageEdit.validate_inputs() is True
    assert OpenAIImageEdit.validate_inputs(grid_images="[]") is True
    assert OpenAIImageEdit.validate_inputs(grid_images='["a.png"]') is True
    assert OpenAIImageEdit.validate_inputs(grid_images='["a.png", "gone.png"]') == (
        "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'")
