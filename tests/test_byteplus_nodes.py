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
from erpk.byteplus.nodes import BytePlusSeedreamImageEdit, BytePlusSeedreamTextToImage  # noqa: E402
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


def test_url_results_download_off_the_event_loop_and_print_before_a_partial_failure_raises(
        transport, monkeypatch, capsys):
    import threading

    import erpk.utils.safe_fetch as safe_fetch

    _, replies = transport
    downloads = []

    def fake_fetch(url, **_):
        downloads.append((url, threading.current_thread() is threading.main_thread()))
        buffer = io.BytesIO()
        Image.new("RGB", (64, 48), (1, 2, 3)).save(buffer, format="PNG")
        return buffer.getvalue()

    monkeypatch.setattr(safe_fetch, "fetch_remote_bytes", fake_fetch)
    reply = {"data": [{"url": "https://cdn.example.com/a.png", "size": "64x48"},
                      {"error": {"code": "OutputImageSensitiveContentDetected", "message": "blocked"}}],
             "usage": {"generated_images": 1}}
    kwargs = dict(client=CLIENT, prompt="a kite", model="seedream-4-0-250828", sequential="auto", max_images=2)

    replies.append((200, reply))
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedreamTextToImage.execute(**kwargs))
    assert str(excinfo.value) == ("Seedream returned 1 of 2 images; failures: "
                                  "OutputImageSensitiveContentDetected: blocked")
    assert "https://cdn.example.com/a.png" in capsys.readouterr().out

    replies.append((200, reply))
    images, alpha = asyncio.run(BytePlusSeedreamTextToImage.execute(**kwargs, fail_on_partial=False)).args
    assert tuple(images.shape) == (1, 48, 64, 3) and alpha.min().item() == 1.0
    assert downloads == [("https://cdn.example.com/a.png", False)]


MINI = "dreamina-seedance-2-0-mini-260615"
VIDEO = "https://cdn.example.com/v.mp4"


def _succeeded(**content):
    return (200, {"id": "cgt-9", "status": "succeeded", "content": {"video_url": VIDEO, **content},
                  "usage": {"completion_tokens": 40_594, "total_tokens": 40_594}})


@pytest.mark.parametrize("return_last_frame, content, warned", [
    (False, {"last_frame_url": None}, False),
    (True, {"last_frame_url": None}, True),
    (True, {}, True),
])
def test_a_billed_video_is_returned_even_without_its_last_frame(transport, capsys, return_last_frame, content,
                                                                 warned):
    _, replies = transport
    replies += [(200, {"id": "cgt-9"}), _succeeded(**content)]
    output = asyncio.run(BytePlusSeedanceImageToVideo.execute(
        client=CLIENT, first_frame=torch.zeros((1, 320, 480, 3)), model=MINI, resolution="480p",
        return_last_frame=return_last_frame))
    assert tuple(output.args) == (VIDEO, "", "cgt-9")
    warning = ("[BytePlus] Task cgt-9 returned no last_frame_url although return_last_frame was on; "
               "returning the video without it.")
    assert (warning in capsys.readouterr().out) is warned


def test_a_gap_in_the_seedance_price_list_does_not_discard_the_video(transport, monkeypatch, capsys):
    from dataclasses import replace

    from erpk.byteplus.byteplus_api import seedance

    monkeypatch.setitem(seedance.SEEDANCE_MODELS, MINI,
                        replace(seedance.SEEDANCE_MODELS[MINI], price_per_million={}))
    _, replies = transport
    replies += [(200, {"id": "cgt-9"}), _succeeded()]
    output = asyncio.run(BytePlusSeedanceImageToVideo.execute(
        client=CLIENT, first_frame=torch.zeros((1, 320, 480, 3)), model=MINI, resolution="480p"))
    assert tuple(output.args) == (VIDEO, "", "cgt-9")
    assert ("[BytePlus] Task cgt-9: 40594 tokens; cost unknown: dreamina-seedance-2-0-mini-260615 has no "
            "price for 480p.") in capsys.readouterr().out

