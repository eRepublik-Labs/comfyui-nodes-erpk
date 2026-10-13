# ABOUTME: Tests the Qwen Image 3.0 edit/text-to-image nodes and the 96-pose Multiple Angles node.
# ABOUTME: Checks the endpoint and wire payload each node sends, against the WaveSpeed API schemas.

import asyncio
import importlib
from unittest.mock import patch

import pydantic
import pytest

torch = pytest.importorskip("torch")

URL_A = "https://example.com/a.png"
URL_B = "https://example.com/b.png"


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # import of the shared inline preview resolves.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


def _send(node, **kwargs):
    """Runs the node and returns the (api path, wire payload) it would POST."""
    sent = {}

    async def fake_send(self, request, *args, **kw):
        sent["path"] = request.get_api_path()
        sent["payload"] = request.build_payload()
        return {"outputs": ["https://example.com/out.png"]}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)), \
         patch("erpk.utils.inline_preview.inline_preview_image", return_value=None):
        asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent["path"], sent["payload"]


def _edit():
    return _node("qwen_image_3_0_edit", "QwenImage30EditNode")


def _t2i():
    return _node("qwen_image_3_0_text_to_image", "QwenImage30TextToImageNode")


def _angles():
    return _node("qwen_image_multiple_angles_96", "QwenImageMultipleAngles96Node")


# ---- Qwen Image 3.0 Edit ---------------------------------------------------

@pytest.mark.parametrize("model,path", [
    ("Qwen Image 3.0", "/api/v3/alibaba/qwen-image-3.0/edit"),
    ("Qwen Image 3.0 Pro", "/api/v3/alibaba/qwen-image-3.0-pro/edit"),
])
def test_edit_model_selects_endpoint(model, path):
    sent_path, _ = _send(_edit(), model=model, prompt="make it blue", reference_images_url=URL_A)
    assert sent_path == path


def test_edit_payload_with_defaults():
    _, payload = _send(_edit(), model="Qwen Image 3.0", prompt="make it blue", reference_images_url=URL_A)
    assert payload == {
        "prompt": "make it blue",
        "images": [URL_A],
        "resolution": "1k",
        "enable_prompt_expansion": False,
        "seed": -1,
    }


def test_edit_sends_chosen_aspect_ratio_resolution_and_expansion():
    _, payload = _send(_edit(), model="Qwen Image 3.0 Pro", prompt="p", reference_images_url=f"{URL_A}\n{URL_B}",
                       aspect_ratio="21:9", resolution="2k", enable_prompt_expansion=True, seed=7)
    assert payload == {
        "prompt": "p",
        "images": [URL_A, URL_B],
        "aspect_ratio": "21:9",
        "resolution": "2k",
        "enable_prompt_expansion": True,
        "seed": 7,
    }


def test_edit_image_batch_is_sent_inline_and_beats_urls():
    _, payload = _send(_edit(), model="Qwen Image 3.0", prompt="p",
                       reference_images=torch.rand(2, 16, 16, 3), reference_images_url=URL_A)
    assert len(payload["images"]) == 2
    assert all(uri.startswith("data:image/") for uri in payload["images"])


def test_edit_rejects_a_fourth_image():
    with pytest.raises(ValueError, match="^Qwen Image 3.0 Pro accepts at most 3 input images, got 4$"):
        _send(_edit(), model="Qwen Image 3.0 Pro", prompt="p", reference_images=torch.rand(4, 16, 16, 3))


def test_edit_requires_an_image():
    with pytest.raises(ValueError, match="^Connect reference_images or enter at least one image URL$"):
        _send(_edit(), model="Qwen Image 3.0", prompt="p")


def test_edit_requires_a_prompt():
    with pytest.raises(ValueError, match="^Prompt is required$"):
        _send(_edit(), model="Qwen Image 3.0", prompt="", reference_images_url=URL_A)


def test_edit_rejects_prompt_over_800_characters():
    with pytest.raises(pydantic.ValidationError, match="at most 800 characters"):
        _send(_edit(), model="Qwen Image 3.0", prompt="x" * 801, reference_images_url=URL_A)


def test_edit_offers_every_api_aspect_ratio_plus_auto():
    inputs = {i.id: i for i in _edit().define_schema().inputs}
    assert inputs["aspect_ratio"].options == ["auto", "1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4",
                                              "4:3", "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    assert inputs["resolution"].options == ["1k", "2k"]


# ---- Qwen Image 3.0 Text-to-Image ------------------------------------------

@pytest.mark.parametrize("model,path", [
    ("Qwen Image 3.0", "/api/v3/alibaba/qwen-image-3.0/text-to-image"),
    ("Qwen Image 3.0 Pro", "/api/v3/alibaba/qwen-image-3.0-pro/text-to-image"),
])
def test_t2i_model_selects_endpoint(model, path):
    sent_path, _ = _send(_t2i(), model=model, prompt="a red fox")
    assert sent_path == path


def test_t2i_payload():
    _, payload = _send(_t2i(), model="Qwen Image 3.0", prompt="a red fox", aspect_ratio="9:16",
                       resolution="2k", enable_prompt_expansion=True, seed=0)
    assert payload == {
        "prompt": "a red fox",
        "aspect_ratio": "9:16",
        "resolution": "2k",
        "enable_prompt_expansion": True,
        "seed": 0,
    }


def test_t2i_requires_a_prompt():
    with pytest.raises(ValueError, match="^Prompt is required$"):
        _send(_t2i(), model="Qwen Image 3.0", prompt="")


def test_t2i_rejects_an_aspect_ratio_the_api_lacks():
    from erpk.wavespeed.wavespeed_api.requests.qwen_image_3_0_text_to_image import QwenImage30TextToImage
    with pytest.raises(pydantic.ValidationError):
        QwenImage30TextToImage(prompt="p", aspect_ratio="7:5")


# ---- Multiple Angles (96 poses) --------------------------------------------

def test_angles_endpoint_and_default_pose():
    path, payload = _send(_angles(), reference_images_url=URL_A)
    assert path == "/api/v3/wavespeed-ai/qwen-image/edit-multiple-angles"
    assert payload == {
        "images": [URL_A],
        "horizontal_angle": 0,
        "vertical_angle": 0,
        "distance": 1,
        "seed": -1,
        "output_format": "jpeg",
    }


@pytest.mark.parametrize("azimuth,degrees", [
    ("front (0°)", 0), ("front-right (45°)", 45), ("right side (90°)", 90), ("back-right (135°)", 135),
    ("back (180°)", 180), ("back-left (225°)", 225), ("left side (270°)", 270), ("front-left (315°)", 315),
])
def test_angles_azimuth_maps_to_api_degrees(azimuth, degrees):
    _, payload = _send(_angles(), reference_images_url=URL_A, azimuth=azimuth)
    assert payload["horizontal_angle"] == degrees


@pytest.mark.parametrize("elevation,degrees", [
    ("low angle (-30°)", -30), ("eye level (0°)", 0), ("elevated (30°)", 30), ("high angle (60°)", 60),
])
def test_angles_elevation_maps_to_api_degrees(elevation, degrees):
    _, payload = _send(_angles(), reference_images_url=URL_A, elevation=elevation)
    assert payload["vertical_angle"] == degrees


@pytest.mark.parametrize("framing,distance", [("close-up", 0), ("medium", 1), ("wide", 2)])
def test_angles_framing_maps_to_api_distance(framing, distance):
    _, payload = _send(_angles(), reference_images_url=URL_A, framing=framing)
    assert payload["distance"] == distance


def test_angles_sends_prompt_seed_and_format():
    _, payload = _send(_angles(), reference_images_url=URL_A, prompt="keep the logo readable",
                       seed=42, output_format="png")
    assert payload["prompt"] == "keep the logo readable"
    assert payload["seed"] == 42
    assert payload["output_format"] == "png"


def test_angles_offers_96_poses():
    inputs = {i.id: i for i in _angles().define_schema().inputs}
    poses = len(inputs["azimuth"].options) * len(inputs["elevation"].options) * len(inputs["framing"].options)
    assert poses == 96


def test_angles_request_rejects_an_angle_between_poses():
    from erpk.wavespeed.wavespeed_api.requests.qwen_image_multiple_angles_96 import QwenImageMultipleAngles96
    with pytest.raises(pydantic.ValidationError):
        QwenImageMultipleAngles96(images=[URL_A], horizontal_angle=30)


def test_angles_requires_an_image():
    with pytest.raises(ValueError, match="^Connect reference_images or enter at least one image URL$"):
        _send(_angles())
