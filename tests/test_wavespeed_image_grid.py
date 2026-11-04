# ABOUTME: Tests for the image grid as a source of WaveSpeed edit images: input_image_list sends a
# ABOUTME: connected IMAGE batch, else the grid's files at their own size, else the URL text.

import base64
import io
import sys
import types

import pytest

pytest.importorskip("torch")

from erpk.wavespeed.wavespeed_api.utils import input_image_list


@pytest.fixture
def input_dir(monkeypatch, tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return inp


def _write(path, size, color, **save):
    from PIL import Image

    Image.new("RGB", size, color).save(path, **save)


def _decoded(uri):
    from PIL import Image

    header, payload = uri.split(",", 1)
    with Image.open(io.BytesIO(base64.b64decode(payload))) as img:
        return header, img.format, img.size


# ---- input_image_list ------------------------------------------------------

def test_grid_files_become_jpeg_data_uris_at_their_own_size_in_grid_order(input_dir):
    _write(input_dir / "wide.png", (7, 2), (255, 0, 0))
    _write(input_dir / "tall.webp", (3, 9), (0, 0, 255), lossless=True)
    uris = input_image_list(None, "", 10, "Seedream", grid='["tall.webp", "wide.png"]')
    assert [_decoded(uri) for uri in uris] == [
        ("data:image/jpeg;base64", "JPEG", (3, 9)),
        ("data:image/jpeg;base64", "JPEG", (7, 2)),
    ]


def test_grid_files_beat_the_url_text(input_dir):
    _write(input_dir / "a.png", (4, 4), (0, 0, 0))
    uris = input_image_list(None, "https://example.com/a.png", 3, "Qwen", grid='["a.png"]')
    assert [_decoded(uri) for uri in uris] == [("data:image/jpeg;base64", "JPEG", (4, 4))]


def test_a_connected_batch_is_sent_and_the_grid_not_read(input_dir):
    import torch

    _write(input_dir / "a.png", (4, 4), (0, 0, 0))
    _write(input_dir / "b.png", (4, 4), (0, 0, 0))
    # Over grid_max, so reading the grid would raise.
    uris = input_image_list(torch.zeros(2, 8, 6, 3), "", 3, "Qwen", grid='["a.png", "b.png"]', grid_max=1)
    assert [_decoded(uri) for uri in uris] == [("data:image/jpeg;base64", "JPEG", (6, 8))] * 2


def test_an_empty_grid_falls_through_to_the_url_text(input_dir):
    urls = "https://example.com/a.png\nhttps://example.com/b.png"
    assert input_image_list(None, urls, 3, "Qwen", grid="[]") == [
        "https://example.com/a.png", "https://example.com/b.png"]


def test_an_empty_grid_and_no_url_send_nothing(input_dir):
    assert input_image_list(None, "", 3, "Qwen", grid="[]") is None


def test_more_grid_files_than_grid_max_names_both_counts(input_dir):
    for name in ("a.png", "b.png", "c.png"):
        _write(input_dir / name, (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        input_image_list(None, "", 10, "Seedream", grid='["a.png", "b.png", "c.png"]', grid_max=2)
    assert str(exc.value) == "The grid holds 3 images but grid_max_images is 2; remove 1 or raise grid_max_images"


def test_grid_max_defaults_to_the_model_cap(input_dir):
    for name in ("a.png", "b.png", "c.png"):
        _write(input_dir / name, (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        input_image_list(None, "", 2, "Qwen", grid='["a.png", "b.png", "c.png"]')
    assert str(exc.value) == "The grid holds 3 images but grid_max_images is 2; remove 1 or raise grid_max_images"


def test_a_grid_entry_outside_the_input_folder_is_refused(input_dir):
    _write(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        input_image_list(None, "", 3, "Qwen", grid='["../outside.png"]')
    assert str(exc.value) == "grid_images entry 1 is outside ComfyUI's input directory: '../outside.png'"


def test_no_grid_reads_nothing_from_comfyui(monkeypatch):
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    assert input_image_list(None, "https://example.com/a.png", 3, "Qwen") == ["https://example.com/a.png"]
