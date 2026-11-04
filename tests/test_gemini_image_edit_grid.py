# ABOUTME: Tests for the image grid on Gemini Image Edit: where its inputs sit in the saved widget list,
# ABOUTME: which images reach generate_content (socket or grid files at their own size), and the grid's errors.

import asyncio
import io
import sys
import types
from types import SimpleNamespace

import pytest
from google import genai
from google.genai import types as genai_types

from erpk.gemini.gemini_api.client import GeminiClient
from erpk.gemini.nodes import GeminiImageEdit

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")


def frontend_widget_order(schema):
    # The frontend lays out required inputs before optional ones, each group in
    # schema order (getOrderedInputSpecs in the bundled ComfyUI frontend), and
    # widgets_values follows that order.
    widgets = [i for i in schema.inputs if i.io_type in WIDGET_TYPES]
    return ([i.id for i in widgets if not i.optional]
            + [i.id for i in widgets if i.optional])


def test_grid_widgets_follow_every_saved_widget():
    assert frontend_widget_order(GeminiImageEdit.define_schema()) == [
        "prompt", "seed", "model", "temperature", "aspect_ratio", "image_size",
        "response_modalities", "enable_google_search", "grid_images", "grid_max_images",
    ]


def test_image_socket_is_optional_and_the_grid_caps_at_fourteen():
    inputs = {i.id: i for i in GeminiImageEdit.define_schema().inputs}
    assert inputs["image"].optional is True
    assert inputs["grid_images"].default == "[]"
    assert (inputs["grid_max_images"].default, inputs["grid_max_images"].min,
            inputs["grid_max_images"].max) == (10, 1, 14)


@pytest.fixture
def input_dir(monkeypatch, tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    return inp


def _png_bytes():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, "PNG")
    return buffer.getvalue()


class _RecordingModels:
    """Stands in for genai.Client.models: records the contents of each request."""

    def __init__(self):
        self.contents = []

    def generate_content(self, model, contents, config):
        self.contents.append(contents)
        return genai_types.GenerateContentResponse(candidates=[genai_types.Candidate(
            content=genai_types.Content(role="model", parts=[genai_types.Part(
                inline_data=genai_types.Blob(data=_png_bytes(), mime_type="image/png"))]),
            finish_reason=genai_types.FinishReason.STOP,
        )])


@pytest.fixture
def models(monkeypatch):
    pytest.importorskip("torch")
    recorder = _RecordingModels()
    monkeypatch.setattr(genai, "Client", lambda **kwargs: SimpleNamespace(models=recorder))
    return recorder


def _edit(**inputs):
    return asyncio.run(GeminiImageEdit.execute(
        prompt="add a hat", client=GeminiClient(api_key="test-key"), **inputs))


def _sent_images(models):
    # The prompt goes last; every part before it is an image the node sent.
    (contents,) = models.contents
    assert contents[-1] == "add a hat"
    return [(img.size, img.getpixel((0, 0))) for img in contents[:-1]]


def _write(path, size, color, **save):
    from PIL import Image

    Image.new("RGB", size, color).save(path, **save)


def _tensor(width, height, rgb):
    import torch

    return torch.tensor(rgb, dtype=torch.float32).div(255).expand(1, height, width, 3).clone()


@pytest.mark.parametrize("grid", [{"grid_images": "[]"}, {}])
def test_no_socket_and_an_empty_grid_names_both_ways_in(input_dir, models, grid):
    with pytest.raises(ValueError) as exc:
        _edit(**grid)
    assert str(exc.value) == "Connect an image or add images to the grid"
    assert models.contents == []


def test_grid_files_reach_the_model_at_their_own_size_in_grid_order(input_dir, models):
    _write(input_dir / "wide.jpg", (7, 2), (255, 255, 255), quality=100)
    _write(input_dir / "tall.webp", (3, 9), (0, 0, 255), lossless=True)
    _edit(grid_images='["tall.webp", "wide.jpg"]')
    assert _sent_images(models) == [((3, 9), (0, 0, 255)), ((7, 2), (255, 255, 255))]


def test_refs_then_additional_images_follow_the_grid(input_dir, models):
    _write(input_dir / "first.png", (4, 4), (255, 0, 0))
    _write(input_dir / "second.png", (5, 3), (0, 255, 0))
    _edit(
        grid_images='["first.png", "second.png"]',
        image_refs=[_tensor(2, 6, (0, 0, 255)), _tensor(6, 2, (255, 255, 0))],
        additional_images=_tensor(3, 3, (0, 255, 255)),
    )
    assert _sent_images(models) == [
        ((4, 4), (255, 0, 0)),
        ((5, 3), (0, 255, 0)),
        ((2, 6), (0, 0, 255)),
        ((6, 2), (255, 255, 0)),
        ((3, 3), (0, 255, 255)),
    ]


def test_a_connected_image_is_sent_and_the_grid_not_read(input_dir, models):
    _write(input_dir / "a.png", (5, 3), (255, 0, 0))
    _write(input_dir / "b.png", (5, 3), (255, 0, 0))
    # Over its cap, so reading the grid would raise.
    _edit(
        image=_tensor(6, 8, (0, 0, 0)),
        grid_images='["a.png", "b.png"]', grid_max_images=1,
        additional_images=_tensor(3, 3, (0, 255, 255)),
    )
    assert _sent_images(models) == [((6, 8), (0, 0, 0)), ((3, 3), (0, 255, 255))]


def test_more_files_than_max_images_names_both_counts(input_dir, models):
    for name in ("a.png", "b.png", "c.png"):
        _write(input_dir / name, (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        _edit(grid_images='["a.png", "b.png", "c.png"]', grid_max_images=2)
    assert str(exc.value) == "The grid holds 3 images but grid_max_images is 2; remove 1 or raise grid_max_images"
    assert models.contents == []


def test_an_entry_outside_the_input_folder_is_refused(input_dir, models):
    _write(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    with pytest.raises(ValueError) as exc:
        _edit(grid_images='["../outside.png"]')
    assert str(exc.value) == "grid_images entry 1 is outside ComfyUI's input directory: '../outside.png'"
    assert models.contents == []


def test_validation_passes_an_empty_grid_and_names_a_missing_file(input_dir):
    _write(input_dir / "a.png", (2, 2), (0, 0, 0))
    assert GeminiImageEdit.validate_inputs() is True
    assert GeminiImageEdit.validate_inputs(grid_images="[]") is True
    assert GeminiImageEdit.validate_inputs(grid_images='["a.png"]') is True
    assert GeminiImageEdit.validate_inputs(grid_images='["a.png", "gone.png"]') == (
        "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'")
