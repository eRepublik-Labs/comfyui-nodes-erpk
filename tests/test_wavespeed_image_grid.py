# ABOUTME: Tests for the image grid as a source of WaveSpeed edit images: input_image_list sends a
# ABOUTME: connected IMAGE batch, else the grid's files at their own size, else the URL text.

import asyncio
import base64
import importlib
import io
import sys
import types
from unittest.mock import patch

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


# ---- the edit nodes --------------------------------------------------------

GRID = ["grid_images", "grid_max_images"]
NO_INPUT_IMAGE = "Connect an image or add images to the grid, or enter at least one image URL"
PROMPT = {"prompt": "edit it"}


class Node:
    def __init__(self, module, name, socket, url, cap, order, run_kwargs=PROMPT, needs_image=True):
        self.module, self.name, self.socket, self.url, self.cap = module, name, socket, url, cap
        self.order, self.run_kwargs, self.needs_image = order, run_kwargs, needs_image

    def __repr__(self):
        return self.name

    @property
    def cls(self):
        # Loaded under the erpk test package (see conftest) so relative imports resolve.
        return getattr(importlib.import_module(f"erpk.wavespeed.{self.module}"), self.name)


QWEN_SIZE_WIDGETS = ["width", "height", "seed", "output_format", "enable_sync_mode", "enable_base64_output"]

NODES = [
    Node("qwen_image_max_edit", "QwenImageMaxEditNode", "reference_images", "images", 6,
         ["prompt", "images", "width", "height", "seed"]),
    Node("qwen_image_2_0_edit", "QwenImage20EditNode", "reference_images", "images", 3,
         ["model", "prompt", "images", *QWEN_SIZE_WIDGETS]),
    Node("qwen_image_3_0_edit", "QwenImage30EditNode", "reference_images", "reference_images_url", 3,
         ["model", "prompt", "reference_images_url", "aspect_ratio", "resolution",
          "enable_prompt_expansion", "seed"]),
    Node("qwen_image_edit_plus", "QwenImageEditPlusNode", "reference_images", "images", 3,
         ["model", "prompt", "images", *QWEN_SIZE_WIDGETS]),
    Node("qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode", "reference_images", "images", 3,
         ["model", "prompt", "images", "lora_1_path", "lora_1_scale", "lora_2_path", "lora_2_scale",
          "lora_3_path", "lora_3_scale", *QWEN_SIZE_WIDGETS],
         run_kwargs={**PROMPT, "lora_1_path": "https://example.com/style.safetensors"}),
    Node("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode", "reference_images", "images", 3,
         ["images", "prompt", "horizontal_angle", "vertical_angle", "distance", *QWEN_SIZE_WIDGETS]),
]
NEEDS_IMAGE = [node for node in NODES if node.needs_image]
WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")


def frontend_widget_order(schema):
    # The frontend lays out required inputs before optional ones, each group in
    # schema order, and widgets_values follows that order.
    widgets = [i for i in schema.inputs if i.io_type in WIDGET_TYPES]
    return [i.id for i in widgets if not i.optional] + [i.id for i in widgets if i.optional]


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_grid_widgets_follow_every_saved_widget(node):
    assert frontend_widget_order(node.cls.define_schema()) == node.order + GRID


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_the_socket_is_optional_and_the_grid_caps_at_the_model_limit(node):
    inputs = {i.id: i for i in node.cls.define_schema().inputs}
    assert (inputs[node.socket].io_type, inputs[node.socket].optional) == ("IMAGE", True)
    assert inputs["grid_images"].default == "[]"
    grid_max = inputs["grid_max_images"]
    assert (grid_max.default, grid_max.min, grid_max.max) == (node.cap, 1, node.cap)


def _sent(node, **inputs):
    sent = {}

    async def fake_send(self, request, *args, **kwargs):
        sent["images"] = request.images
        return {"outputs": ["https://example.com/out.png"]}

    import torch

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)):
        asyncio.run(node.cls.execute(client={"api_key": "test-key"}, **node.run_kwargs, **inputs))
    return sent["images"]


def _refused(node, **inputs):
    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request") as send:
        with pytest.raises(ValueError) as exc:
            asyncio.run(node.cls.execute(client={"api_key": "test-key"}, **node.run_kwargs, **inputs))
    assert not send.called
    return str(exc.value)


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_two_grid_files_reach_the_api_at_their_own_size_in_grid_order(node, input_dir):
    _write(input_dir / "wide.png", (7, 2), (255, 0, 0))
    _write(input_dir / "tall.webp", (3, 9), (0, 0, 255), lossless=True)
    sent = _sent(node, grid_images='["tall.webp", "wide.png"]')
    assert [_decoded(uri) for uri in sent] == [
        ("data:image/jpeg;base64", "JPEG", (3, 9)),
        ("data:image/jpeg;base64", "JPEG", (7, 2)),
    ]


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_the_node_sends_grid_files_over_the_url_text(node, input_dir):
    _write(input_dir / "a.png", (4, 4), (0, 0, 0))
    sent = _sent(node, grid_images='["a.png"]', **{node.url: "https://example.com/a.png"})
    assert [_decoded(uri) for uri in sent] == [("data:image/jpeg;base64", "JPEG", (4, 4))]


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_the_node_sends_a_connected_batch_and_not_the_grid(node, input_dir):
    import torch

    _write(input_dir / "a.png", (4, 4), (0, 0, 0))
    _write(input_dir / "b.png", (4, 4), (0, 0, 0))
    # Over grid_max_images, so reading the grid would raise.
    sent = _sent(node, grid_images='["a.png", "b.png"]', grid_max_images=1,
                 **{node.socket: torch.zeros(1, 8, 6, 3)})
    assert [_decoded(uri) for uri in sent] == [("data:image/jpeg;base64", "JPEG", (6, 8))]


@pytest.mark.parametrize("node", NEEDS_IMAGE, ids=repr)
def test_no_socket_no_grid_and_no_url_names_every_way_in(node, input_dir):
    assert _refused(node, grid_images="[]") == NO_INPUT_IMAGE


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_more_grid_files_than_grid_max_images_names_both_counts(node, input_dir):
    _write(input_dir / "a.png", (2, 2), (0, 0, 0))
    _write(input_dir / "b.png", (2, 2), (0, 0, 0))
    assert _refused(node, grid_images='["a.png", "b.png"]', grid_max_images=1) == (
        "The grid holds 2 images but grid_max_images is 1; remove 1 or raise grid_max_images")


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_a_grid_entry_outside_the_input_folder_is_refused_at_run_time(node, input_dir):
    _write(input_dir.parent / "outside.png", (2, 2), (0, 0, 0))
    assert _refused(node, grid_images='["../outside.png"]') == (
        "grid_images entry 1 is outside ComfyUI's input directory: '../outside.png'")


@pytest.mark.parametrize("node", NODES, ids=repr)
def test_validation_passes_an_empty_grid_and_names_a_missing_file(node, input_dir):
    _write(input_dir / "a.png", (2, 2), (0, 0, 0))
    assert node.cls.validate_inputs() is True
    assert node.cls.validate_inputs(grid_images='["a.png"]') is True
    assert node.cls.validate_inputs(grid_images='["a.png", "gone.png"]') == (
        "grid_images entry 2 not found in ComfyUI's input directory: 'gone.png'")
