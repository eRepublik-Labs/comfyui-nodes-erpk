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


def _size_on_disk(path):
    with Image.open(path) as image:
        return image.size


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


@pytest.fixture
def output_dir(monkeypatch, tmp_path):
    import sys
    import types

    from erpk.byteplus.byteplus_api import media

    fake = types.ModuleType("folder_paths")
    fake.get_output_directory = lambda: str(tmp_path)
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    monkeypatch.setattr(media, "_timestamp", lambda: "20261118-120000-000000")
    return tmp_path / "byteplus_recovered"


def test_url_results_download_off_the_event_loop_and_a_partial_batch_keeps_its_billed_images(
        transport, monkeypatch, capsys, output_dir):
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
    images, alpha = asyncio.run(BytePlusSeedreamTextToImage.execute(**kwargs)).args
    assert tuple(images.shape) == (1, 48, 64, 3) and alpha.min().item() == 1.0
    out = capsys.readouterr().out
    assert "https://cdn.example.com/a.png" in out
    assert "[BytePlus] Seedream refused 1 of 2 images: OutputImageSensitiveContentDetected: blocked" in out

    replies.append((200, reply))
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedreamTextToImage.execute(**kwargs, fail_on_partial=True))
    saved = output_dir / "20261118-120000-000000-01.png"
    assert str(excinfo.value) == ("Seedream returned 1 of 2 images; failures: OutputImageSensitiveContentDetected: "
                                  f"blocked. The billed images are saved as {saved}")
    assert _size_on_disk(saved) == (64, 48)
    assert downloads == [("https://cdn.example.com/a.png", False)] * 2


def test_a_layer_that_cannot_be_placed_saves_every_billed_image_and_never_overwrites(transport, output_dir):
    _, replies = transport
    output_dir.mkdir()
    (output_dir / "20261118-120000-000000-01.png").write_bytes(b"earlier run")
    replies.append((200, {"data": [
        {"b64_json": _png_b64(Image.new("RGB", (600, 500))), "z_index": 0},
        {"b64_json": _png_b64(Image.new("RGBA", (100, 50))), "z_index": 1},
    ]}))
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedreamImageEdit.execute(
            client=CLIENT, images=torch.zeros((1, 520, 520, 3)), layer_decomposition=True, size="auto",
            response_format="b64_json"))
    first, second = output_dir / "20261118-120000-000000-01-1.png", output_dir / "20261118-120000-000000-02.png"
    assert str(excinfo.value) == ("A Seedream layer is 100x50 with no bounding box on a 600x500 base. The billed "
                                  f"images are saved as {first}, {second}")
    assert (output_dir / "20261118-120000-000000-01.png").read_bytes() == b"earlier run"
    assert _size_on_disk(first) == (600, 500) and _size_on_disk(second) == (100, 50)


def test_an_image_that_does_not_decode_saves_the_others_and_names_it(transport, output_dir):
    _, replies = transport
    replies.append((200, {"data": [{"b64_json": _png_b64(Image.new("RGB", (64, 48)))},
                                   {"b64_json": "bm90IGFuIGltYWdl"}]}))
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedreamTextToImage.execute(client=CLIENT, prompt="a kite", model="seedream-4-0-250828",
                                                        sequential="auto", max_images=2, response_format="b64_json"))
    saved = output_dir / "20261118-120000-000000-01.png"
    message = str(excinfo.value)
    assert message.startswith("Seedream images could not be decoded: image 2 of 2: ")
    assert message.endswith(f". The billed images are saved as {saved}")
    assert _size_on_disk(saved) == (64, 48)

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


def test_task_result_waits_for_a_task_and_returns_its_urls_and_status(transport, monkeypatch):
    from erpk.byteplus.video_nodes import BytePlusSeedanceTaskResult

    async def no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    sent, replies = transport
    replies += [(200, {"id": "cgt-9", "status": "running"}),
                _succeeded(last_frame_url="https://cdn.example.com/last.jpeg")]
    output = asyncio.run(BytePlusSeedanceTaskResult.execute(client=CLIENT, task_id=" cgt-9 "))
    assert tuple(output.args) == (VIDEO, "https://cdn.example.com/last.jpeg", "succeeded")
    task_url = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/cgt-9"
    assert sent == [("GET", task_url, None), ("GET", task_url, None)]

    sent.clear()
    replies.append((200, {"id": "cgt-9", "status": "queued", "content": None}))
    output = asyncio.run(BytePlusSeedanceTaskResult.execute(client=CLIENT, task_id="cgt-9", wait=False))
    assert tuple(output.args) == ("", "", "queued")
    assert sent == [("GET", task_url, None)]


def test_task_result_refuses_a_task_id_that_is_not_one(transport):
    from erpk.byteplus.video_nodes import BytePlusSeedanceTaskResult

    sent, _ = transport
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(BytePlusSeedanceTaskResult.execute(client=CLIENT, task_id="cgt-9/../../x"))
    assert str(excinfo.value) == ("task_id must be a ModelArk task ID such as cgt-20261119021437-q68pg, "
                                  "got 'cgt-9/../../x'.")
    assert sent == []


def test_size_auto_is_offered_only_where_layer_decomposition_is():
    def size_options(node):
        return next(i for i in node.define_schema().inputs if i.id == "size").options

    assert "auto" not in size_options(BytePlusSeedreamTextToImage)
    assert "auto" in size_options(BytePlusSeedreamImageEdit)


def test_cancel_while_task_result_waits_stops_waiting_and_never_deletes_the_task(transport, monkeypatch, capsys):
    from erpk.byteplus.byteplus_api.client import BytePlusInterrupted
    from erpk.byteplus.video_nodes import BytePlusSeedanceTaskResult

    monkeypatch.setattr(client_module, "_resolve_interrupt_checker", lambda: (lambda: True))
    sent, replies = transport
    replies += [(200, {"id": "cgt-9", "status": "queued"}), (200, {})]
    with pytest.raises(BytePlusInterrupted) as excinfo:
        asyncio.run(BytePlusSeedanceTaskResult.execute(client=CLIENT, task_id="cgt-9"))
    message = ("Stopped waiting for Seedance task cgt-9. The Task Result node only reads a task, so the task "
               "is untouched.")
    assert str(excinfo.value) == message
    assert capsys.readouterr().out.splitlines()[-1] == f"[BytePlus] {message}"
    assert sent == []


def test_task_result_with_wait_on_raises_the_vendor_reason_for_a_failed_task(transport):
    from erpk.byteplus.byteplus_api.client import BytePlusTaskFailed
    from erpk.byteplus.video_nodes import BytePlusSeedanceTaskResult

    _, replies = transport
    replies.append((200, {"id": "cgt-9", "status": "failed",
                          "error": {"code": "OutputVideoSensitiveContentDetected", "message": "blocked"}}))
    with pytest.raises(BytePlusTaskFailed) as excinfo:
        asyncio.run(BytePlusSeedanceTaskResult.execute(client=CLIENT, task_id="cgt-9"))
    assert str(excinfo.value) == "Seedance task cgt-9 failed: OutputVideoSensitiveContentDetected: blocked"


class BlockingTransport:
    """Holds the first request in flight until released, then answers it; later requests answer at once."""

    def __init__(self, first_reply, later_replies=()):
        import threading

        self.in_flight = threading.Event()
        self.release = threading.Event()
        self.replies = [first_reply, *later_replies]
        self.sent = []

    def __call__(self, method, url, headers, data, timeout):
        self.sent.append((method, url))
        if len(self.sent) == 1:
            self.in_flight.set()
            assert self.release.wait(5), "the test never released the request"
        status, body = self.replies.pop(0)
        return status, json.dumps(body)


def _cancel_while_in_flight(monkeypatch, fake, coroutine):
    """Cancel the node as ComfyUI's loop teardown does while the first request is in flight,
    then let the vendor answer. asyncio.run returns only after the worker thread has finished."""
    monkeypatch.setattr(client_module, "_requests_transport", lambda session: fake)

    async def scenario():
        task = asyncio.create_task(coroutine)
        assert await asyncio.to_thread(fake.in_flight.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        fake.release.set()

    asyncio.run(scenario())


SEEDANCE_KWARGS = dict(client=CLIENT, first_frame=torch.zeros((1, 320, 480, 3)), model=MINI, resolution="480p")
CREATED_LINE = ("[BytePlus] Created Seedance task cgt-9. If this run stops before the video is returned, fetch it "
                "with the BytePlus Seedance Task Result node.")


def test_a_seedance_task_created_after_its_node_was_cancelled_still_prints_its_id(monkeypatch, capsys):
    fake = BlockingTransport((200, {"id": "cgt-9"}))
    _cancel_while_in_flight(monkeypatch, fake, BytePlusSeedanceImageToVideo.execute(**SEEDANCE_KWARGS))
    assert capsys.readouterr().out.splitlines()[-1] == CREATED_LINE
    assert fake.sent == [("POST", "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks")]


def test_a_seedance_node_cancelled_while_waiting_prints_that_the_task_may_still_bill(transport, capsys):
    sent, replies = transport
    replies += [(200, {"id": "cgt-9"}), (200, {"id": "cgt-9", "status": "running"})]

    async def scenario():
        task = asyncio.create_task(BytePlusSeedanceImageToVideo.execute(**SEEDANCE_KWARGS))
        while len(sent) < 2:
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    lines = capsys.readouterr().out.splitlines()
    assert CREATED_LINE in lines
    assert lines[-1] == ("[BytePlus] Stopped waiting for Seedance task cgt-9 when the ComfyUI run ended. It may "
                         "still finish and bill; fetch it with the BytePlus Seedance Task Result node.")
    assert [method for method, _, _ in sent] == ["POST", "GET"]


SEEDREAM_KWARGS = dict(client=CLIENT, prompt="a kite", model="seedream-4-0-250828", sequential="auto", max_images=2,
                       response_format="b64_json")


@pytest.mark.parametrize("data, fail_on_partial, saved_count, printed", [
    ([{"b64_json": "A"}, {"b64_json": "B"}], False, 2,
     "[BytePlus] The ComfyUI run ended before Seedream's images were returned. The billed images are saved as {}"),
    ([{"b64_json": "A"}, {"error": {"code": "OutputImageSensitiveContentDetected", "message": "blocked"}}], True, 1,
     "[BytePlus] Seedream returned 1 of 2 images; failures: OutputImageSensitiveContentDetected: blocked. "
     "The billed images are saved as {}"),
])
def test_seedream_images_billed_after_the_node_was_cancelled_are_saved_and_named(
        monkeypatch, capsys, output_dir, data, fail_on_partial, saved_count, printed):
    pngs = {"A": _png_b64(Image.new("RGB", (64, 48))), "B": _png_b64(Image.new("RGB", (32, 16)))}
    data = [{"b64_json": pngs[item["b64_json"]]} if "b64_json" in item else item for item in data]
    fake = BlockingTransport((200, {"data": data}))
    _cancel_while_in_flight(monkeypatch, fake, BytePlusSeedreamTextToImage.execute(
        **SEEDREAM_KWARGS, fail_on_partial=fail_on_partial))
    saved = [output_dir / f"20261118-120000-000000-{index:02d}.png" for index in range(1, saved_count + 1)]
    assert capsys.readouterr().out.splitlines()[-1] == printed.format(", ".join(str(path) for path in saved))
    assert [_size_on_disk(path) for path in saved] == [(64, 48), (32, 16)][:saved_count]
    assert sorted(output_dir.iterdir()) == saved


def test_a_billed_result_reaches_exactly_one_side_whichever_finishes_first():
    from erpk.byteplus.nodes import _Handoff

    ran = []
    received = _Handoff()
    received.finish(lambda: ran.append("received"))
    cancelled_after = _Handoff()
    cancelled_after.finish(lambda: ran.append("cancelled after the worker finished"))
    cancelled_after.abandon()
    cancelled_before = _Handoff()
    cancelled_before.abandon()
    cancelled_before.finish(lambda: ran.append("cancelled before the worker finished"))
    assert ran == ["cancelled after the worker finished", "cancelled before the worker finished"]
