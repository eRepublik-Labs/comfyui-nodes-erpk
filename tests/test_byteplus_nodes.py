# ABOUTME: BytePlus nodes end to end down to a fake HTTP transport: the request each node sends
# ABOUTME: and the outputs it returns, for Seedance image-to-video and Seedream layer decomposition.

import asyncio
import base64
import io
import json

import pytest

torch = pytest.importorskip("torch")
Image = pytest.importorskip("PIL.Image")

from erpk.byteplus.byteplus_api import client as client_module  # noqa: E402
from erpk.byteplus.nodes import BytePlusSeedreamImageEdit  # noqa: E402
from erpk.byteplus.video_nodes import BytePlusSeedanceImageToVideo  # noqa: E402

CLIENT = {"api_key": "test-key"}


@pytest.fixture
def transport(monkeypatch):
    sent = []
    replies = []

    def fake(method, url, headers, data, timeout):
        sent.append((method, url, json.loads(data) if data else None))
        status, body = replies.pop(0)
        return status, json.dumps(body)

    monkeypatch.setattr(client_module, "_requests_transport", lambda session: fake)
    monkeypatch.setattr(client_module, "_resolve_interrupt_checker", lambda: (lambda: False))
    return sent, replies


def _png_b64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_image_to_video_on_1_0_pro_fast_sends_the_frame_and_seed_and_returns_three_urls(transport):
    sent, replies = transport
    replies += [
        (200, {"id": "cgt-9"}),
        (200, {"id": "cgt-9", "status": "succeeded", "resolution": "480p",
               "content": {"video_url": "https://cdn.example.com/v.mp4",
                           "last_frame_url": "https://cdn.example.com/last.jpeg"},
               "usage": {"completion_tokens": 50_000, "total_tokens": 50_000}}),
    ]
    output = asyncio.run(BytePlusSeedanceImageToVideo.execute(
        client=CLIENT, prompt="slow pan", first_frame=torch.zeros((1, 320, 480, 3)),
        model="seedance-1-0-pro-fast-251015", resolution="480p", ratio="16:9", duration=5, seed=5,
        return_last_frame=True,
    ))
    assert tuple(output.args) == ("https://cdn.example.com/v.mp4", "https://cdn.example.com/last.jpeg", "cgt-9")
    method, url, body = sent[0]
    assert (method, url) == ("POST", "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks")
    frame = body["content"][1]
    assert frame["role"] == "first_frame" and frame["image_url"]["url"].startswith("data:image/jpeg;base64,")
    del body["content"]
    assert body == {"model": "seedance-1-0-pro-fast-251015", "resolution": "480p", "ratio": "16:9",
                    "duration": 5, "watermark": False, "return_last_frame": True,
                    "execution_expires_after": 172800, "seed": 5, "camera_fixed": False}


def test_image_to_video_rejects_a_bad_combination_before_any_request(transport):
    sent, _ = transport
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedanceImageToVideo.execute(
            client=CLIENT, prompt="", first_frame=torch.zeros((1, 320, 480, 3)),
            model="dreamina-seedance-2-5-260628", ratio="16:9"))
    assert str(excinfo.value) == "dreamina-seedance-2-5-260628 first-frame tasks accept only ratio adaptive, got 16:9."
    assert sent == []


def test_layer_decomposition_returns_the_base_then_each_layer_with_alpha(transport):
    sent, replies = transport
    base = Image.new("RGB", (600, 500), (10, 20, 30))
    layer = Image.new("RGBA", (100, 50), (200, 0, 0, 255))
    replies.append((200, {"model": "dola-seedream-5-5-261028", "created": 1, "data": [
        {"b64_json": _png_b64(base), "z_index": 0, "size": "600x500"},
        {"b64_json": _png_b64(layer), "z_index": 1, "size": "100x50", "name": "logo",
         "bounding_box": {"absolute": [10, 20, 110, 70]}},
    ], "usage": {"generated_images": 2}}))
    images, alpha = asyncio.run(BytePlusSeedreamImageEdit.execute(
        client=CLIENT, prompt="", images=torch.zeros((1, 520, 520, 3)), layer_decomposition=True,
        size="auto", response_format="b64_json", layer_max_images=5,
    )).args
    assert tuple(images.shape) == (2, 500, 600, 3) and tuple(alpha.shape) == (2, 500, 600)
    assert alpha[1].sum().item() == 100 * 50
    assert alpha[1, 20, 10].item() == 1.0 and alpha[1, 19, 10].item() == 0.0
    body = sent[0][2]
    assert body["image"].startswith("data:image/jpeg;base64,")
    assert body["layer_decomposition"] is True
    assert body["layer_decomposition_options"] == {"max_images": 5, "text_recognition": False}
