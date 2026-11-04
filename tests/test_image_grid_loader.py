# ABOUTME: Tests for ImageGridLoader: parsing the grid's filename list, the input/ containment
# ABOUTME: guard, the grid_max_images cap, and batching mixed-size files into one IMAGE tensor.

import sys
import types

import pytest

from utils.image_grid import resolve_grid_images
from utils.image_grid_loader import ImageGridLoader


@pytest.fixture
def input_dir(monkeypatch, tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return inp


def test_the_grid_holds_fourteen_by_default():
    inputs = {i.id: i for i in ImageGridLoader.define_schema().inputs}
    assert (inputs["grid_max_images"].default, inputs["grid_max_images"].min,
            inputs["grid_max_images"].max) == (14, 1, 14)


def test_empty_list_resolves_to_no_files(input_dir):
    assert resolve_grid_images("[]", str(input_dir)) == []


def test_loader_rejects_an_empty_grid_before_and_during_the_run(input_dir):
    assert ImageGridLoader.validate_inputs(grid_images="[]") == "Add at least one image"
    with pytest.raises(ValueError) as exc:
        ImageGridLoader.execute(grid_images="[]", grid_max_images=10)
    assert str(exc.value) == "Add at least one image"


def test_text_that_is_not_json_is_rejected(input_dir):
    with pytest.raises(ValueError) as exc:
        resolve_grid_images("a.png, b.png", str(input_dir))
    assert str(exc.value) == "grid_images must be a JSON list of filenames, got 'a.png, b.png'"


@pytest.mark.parametrize("raw,bad", [
    ('{"a": "a.png"}', "{'a': 'a.png'}"),
    ('"a.png"', "'a.png'"),
])
def test_json_that_is_not_a_list_is_rejected(input_dir, raw, bad):
    with pytest.raises(ValueError) as exc:
        resolve_grid_images(raw, str(input_dir))
    assert str(exc.value) == f"grid_images must be a JSON list of filenames, got {bad}"


@pytest.mark.parametrize("raw,bad", [
    ('["a.png", 3]', "3"),
    ('["a.png", ""]', "''"),
    ('["a.png", null]', "None"),
])
def test_entry_that_is_not_a_filename_is_rejected(input_dir, raw, bad):
    with pytest.raises(ValueError) as exc:
        resolve_grid_images(raw, str(input_dir))
    assert str(exc.value) == f"grid_images entry 2 is not a filename: {bad}"


def _write_png(path, size, color):
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


@pytest.mark.parametrize("name", [
    "../outside.png",
    "sub/../../outside.png",
])
def test_name_that_escapes_input_dir_is_rejected(input_dir, name):
    _write_png(input_dir / "a.png", (2, 2), (0, 0, 0))
    _write_png(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        resolve_grid_images(f'["a.png", "{name}"]', str(input_dir))
    assert str(exc.value) == f"grid_images entry 2 is outside ComfyUI's input directory: {name!r}"


def test_absolute_path_is_rejected_even_inside_input_dir(input_dir):
    _write_png(input_dir / "a.png", (2, 2), (0, 0, 0))
    name = str(input_dir / "a.png")
    with pytest.raises(ValueError) as exc:
        resolve_grid_images(f'["{name}"]', str(input_dir))
    assert str(exc.value) == f"grid_images entry 1 is outside ComfyUI's input directory: {name!r}"


def test_symlink_pointing_outside_input_dir_is_rejected(input_dir):
    _write_png(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    (input_dir / "link.png").symlink_to(input_dir.parent / "outside.png")
    with pytest.raises(ValueError) as exc:
        resolve_grid_images('["link.png"]', str(input_dir))
    assert str(exc.value) == "grid_images entry 1 is outside ComfyUI's input directory: 'link.png'"


def test_missing_file_is_rejected(input_dir):
    _write_png(input_dir / "a.png", (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        resolve_grid_images('["a.png", "gone.png"]', str(input_dir))
    assert str(exc.value) == "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'"


def test_directory_entry_is_rejected(input_dir):
    (input_dir / "sub").mkdir()
    with pytest.raises(ValueError) as exc:
        resolve_grid_images('["sub"]', str(input_dir))
    assert str(exc.value) == "grid_images entry 1 not found in ComfyUI's input directory: 'sub'"


def test_names_resolve_in_order_including_subfolder_entries(input_dir):
    _write_png(input_dir / "b.png", (2, 2), (0, 0, 0))
    _write_png(input_dir / "pasted" / "a.png", (2, 2), (0, 0, 0))
    paths = resolve_grid_images('["b.png", "pasted/a.png"]', str(input_dir))
    real = input_dir.resolve()
    assert paths == [str(real / "b.png"), str(real / "pasted" / "a.png")]


def test_more_images_than_max_images_is_rejected(input_dir):
    for name in ("a.png", "b.png", "c.png"):
        _write_png(input_dir / name, (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        ImageGridLoader.execute(grid_images='["a.png", "b.png", "c.png"]', grid_max_images=2)
    assert str(exc.value) == "The grid holds 3 images but grid_max_images is 2; remove 1 or raise grid_max_images"


def _output(images, max_images=10):
    return ImageGridLoader.execute(grid_images=images, grid_max_images=max_images)[0]


def test_same_size_images_batch_in_list_order(input_dir):
    import torch

    _write_png(input_dir / "a.png", (3, 2), (255, 0, 0))
    _write_png(input_dir / "b.png", (3, 2), (0, 0, 255))
    batch = _output('["b.png", "a.png"]')
    expected = torch.tensor([
        [[[0.0, 0.0, 1.0]] * 3] * 2,
        [[[1.0, 0.0, 0.0]] * 3] * 2,
    ])
    assert batch.dtype == torch.float32
    assert batch.shape == (2, 2, 3, 3)
    assert torch.equal(batch, expected)


def test_mixed_sizes_letterbox_onto_the_largest_height_and_width_with_grey(input_dir):
    import torch

    _write_png(input_dir / "wide.png", (7, 2), (255, 255, 255))
    _write_png(input_dir / "tall.png", (4, 8), (0, 0, 0))
    batch = _output('["wide.png", "tall.png"]')
    assert batch.shape == (2, 8, 7, 3)
    wide = torch.full((8, 7, 3), 0.5)
    wide[3:5, 0:7] = 1.0
    tall = torch.full((8, 7, 3), 0.5)
    tall[0:8, 1:5] = 0.0
    assert torch.equal(batch[0], wide)
    assert torch.equal(batch[1], tall)


def test_exif_orientation_is_applied(input_dir):
    from PIL import Image

    exif = Image.Exif()
    exif[0x0112] = 6
    Image.new("RGB", (4, 2), (255, 255, 255)).save(input_dir / "rotated.jpg", exif=exif)
    batch = _output('["rotated.jpg"]')
    assert batch.shape == (1, 4, 2, 3)


@pytest.mark.parametrize("mode,color,pixel", [
    ("L", 51, [0.2, 0.2, 0.2]),
    ("RGBA", (0, 255, 0, 128), [0.0, 1.0, 0.0]),
])
def test_grayscale_and_alpha_files_load_as_three_channels(input_dir, mode, color, pixel):
    import torch
    from PIL import Image

    Image.new(mode, (2, 2), color).save(input_dir / "x.png")
    batch = _output('["x.png"]')
    assert torch.equal(batch, torch.tensor([[[pixel] * 2] * 2]))


def test_validation_names_a_missing_file_before_the_run(input_dir):
    _write_png(input_dir / "a.png", (2, 2), (0, 0, 0))
    assert ImageGridLoader.validate_inputs(grid_images='["a.png"]') is True
    assert ImageGridLoader.validate_inputs(grid_images='["a.png", "gone.png"]') == (
        "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'")
