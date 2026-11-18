# ABOUTME: BytePlusClient against a fake HTTP transport: task states, errors, interrupt, key order.
# ABOUTME: The fake answers at the HTTP boundary only; every branch above it is the real client.

import asyncio
import json

import pytest
import requests

import erpk.settings
from erpk.byteplus.byteplus_api import client as client_module
from erpk.byteplus.byteplus_api.client import (
    BytePlusAPIError, BytePlusClient, BytePlusInterrupted, BytePlusTaskFailed,
)

BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"


class FakeTransport:
    """Replies from a script of (status, body) per call and records every request."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, method, url, headers, data, timeout):
        self.calls.append((method, url, json.loads(data) if data else None))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        status, body = reply
        return status, body if isinstance(body, str) else json.dumps(body)


def _client(replies, interrupted=lambda: False, monkeypatch=None):
    transport = FakeTransport(replies)
    if monkeypatch is not None:
        monkeypatch.setattr(client_module, "_resolve_interrupt_checker", lambda: interrupted)
    return BytePlusClient(api_key="test-key", transport=transport, poll_interval=0), transport


def _task(status, **extra):
    return 200, {"id": "cgt-1", "model": "m", "status": status, **extra}


def test_video_task_polls_until_succeeded_and_returns_the_task(monkeypatch):
    done = _task("succeeded", content={"video_url": "https://cdn.example.com/v.mp4"},
                 usage={"completion_tokens": 50220, "total_tokens": 50220})
    client, transport = _client([(200, {"id": "cgt-1"}), _task("queued"), _task("running"), done],
                                monkeypatch=monkeypatch)

    async def run():
        task_id = await client.create_video_task({"model": "m", "content": []})
        return task_id, await client.wait_for_video_task(task_id, timeout=60)

    task_id, task = asyncio.run(run())
    assert task_id == "cgt-1"
    assert task["content"]["video_url"] == "https://cdn.example.com/v.mp4"
    assert [(m, u) for m, u, _ in transport.calls] == [
        ("POST", f"{BASE}/contents/generations/tasks"),
        ("GET", f"{BASE}/contents/generations/tasks/cgt-1"),
        ("GET", f"{BASE}/contents/generations/tasks/cgt-1"),
        ("GET", f"{BASE}/contents/generations/tasks/cgt-1"),
    ]


@pytest.mark.parametrize("task, message", [
    (_task("failed", error={"code": "OutputVideoSensitiveContentDetected",
                            "message": "The output video may contain sensitive information."}),
     "Seedance task cgt-1 failed: OutputVideoSensitiveContentDetected: "
     "The output video may contain sensitive information."),
    (_task("failed", error={"code": "OutputAudioSensitiveContentDetected.PolicyViolation", "message": "m"}),
     "Seedance task cgt-1 failed: OutputAudioSensitiveContentDetected.PolicyViolation: m "
     "The generated audio was rejected; turn generate_audio off and run again."),
    (_task("expired"), "Seedance task cgt-1 expired: it stayed queued or running past execution_expires_after."),
    (_task("cancelled"), "Seedance task cgt-1 was cancelled."),
    (_task("paused"), "Seedance task cgt-1 returned unknown status 'paused'."),
])
def test_terminal_task_states_raise_with_the_vendor_reason(monkeypatch, task, message):
    client, _ = _client([task], monkeypatch=monkeypatch)
    with pytest.raises(BytePlusTaskFailed) as excinfo:
        asyncio.run(client.wait_for_video_task("cgt-1", timeout=60))
    assert str(excinfo.value) == message


def test_transient_poll_errors_keep_polling_but_a_404_raises(monkeypatch):
    import requests
    client, transport = _client([
        requests.ConnectionError("reset"), (503, "busy"),
        (429, {"error": {"code": "ServerOverloaded", "message": "slow down"}}),
        _task("succeeded", content={"video_url": "https://cdn.example.com/v.mp4"}),
    ], monkeypatch=monkeypatch)
    task = asyncio.run(client.wait_for_video_task("cgt-1", timeout=60))
    assert task["status"] == "succeeded" and len(transport.calls) == 4

    client, _ = _client([(404, {"error": {"code": "InvalidEndpointOrModel.NotFound", "message": "gone"}})],
                        monkeypatch=monkeypatch)
    with pytest.raises(BytePlusAPIError) as excinfo:
        asyncio.run(client.wait_for_video_task("cgt-1", timeout=60))
    assert str(excinfo.value) == ("ModelArk GET /contents/generations/tasks/cgt-1 returned HTTP 404 "
                                  "InvalidEndpointOrModel.NotFound: gone")


def test_create_is_sent_once_and_surfaces_the_sync_error_envelope(monkeypatch):
    client, transport = _client([(400, {"error": {"code": "InputTextSensitiveContentDetected",
                                                  "message": "The request failed because the input text "
                                                             "may contain sensitive information."}})],
                                monkeypatch=monkeypatch)
    with pytest.raises(BytePlusAPIError) as excinfo:
        asyncio.run(client.create_video_task({"model": "m"}))
    assert str(excinfo.value) == (
        "ModelArk POST /contents/generations/tasks returned HTTP 400 InputTextSensitiveContentDetected: "
        "The request failed because the input text may contain sensitive information.")
    assert len(transport.calls) == 1

    client, transport = _client([requests.ReadTimeout("read timed out")], monkeypatch=monkeypatch)
    with pytest.raises(BytePlusAPIError) as excinfo:
        asyncio.run(client.create_video_task({"model": "m"}))
    assert str(excinfo.value) == (
        "ModelArk POST /contents/generations/tasks got no reply (read timed out). The task may exist and "
        "bill anyway: check Video generation tasks in the ModelArk console before queueing again.")
    assert len(transport.calls) == 1


def test_image_response_errors(monkeypatch):
    client, _ = _client([(200, {"model": "m", "data": [], "error": {"code": "InternalServiceError",
                                                                     "message": "boom"}})],
                        monkeypatch=monkeypatch)
    with pytest.raises(BytePlusAPIError) as excinfo:
        client.generate_images({"model": "m"})
    assert str(excinfo.value) == "ModelArk POST /images/generations returned InternalServiceError: boom"


def test_request_body_over_64_mb_is_refused_before_sending(monkeypatch):
    client, transport = _client([], monkeypatch=monkeypatch)
    with pytest.raises(ValueError) as excinfo:
        asyncio.run(client.create_video_task({"model": "m", "blob": "x" * (64 * 1024 * 1024)}))
    assert str(excinfo.value) == ("The request body is 67108890 bytes; ModelArk accepts at most 67108864. "
                                  "Pass large media as URLs.")
    assert transport.calls == []


def test_key_order_is_settings_then_widget_then_config_ini_and_never_env(monkeypatch, tmp_path):
    config = tmp_path / "config.ini"
    config.write_text("[API]\nBYTEPLUS_API_KEY = from-config\n")
    commented = tmp_path / "commented.ini"
    commented.write_text("[API]\n# BYTEPLUS_API_KEY = your-byteplus-api-key-here\n")
    monkeypatch.setenv("BYTEPLUS_API_KEY", "from-env")
    monkeypatch.setenv("ARK_API_KEY", "from-env")

    monkeypatch.setattr(erpk.settings, "get_comfy_setting", lambda setting_id: (
        "from-settings" if setting_id == "ERPK.BYTEPLUS_API_KEY" else None))
    assert BytePlusClient(api_key="from-widget", config_path=str(config)).api_key == "from-settings"

    monkeypatch.setattr(erpk.settings, "get_comfy_setting", lambda setting_id: None)
    assert BytePlusClient(api_key=" from-widget ", config_path=str(config)).api_key == "from-widget"
    assert BytePlusClient(api_key="", config_path=str(config)).api_key == "from-config"
    with pytest.raises(ValueError) as excinfo:
        BytePlusClient(api_key="", config_path=str(commented))
    assert str(excinfo.value) == (
        "No BytePlus ModelArk API key found. Provide via:\n"
        "  1. ComfyUI Settings (Settings > ERPK > API Keys > BytePlus ModelArk)\n"
        "  2. The api_key input on the BytePlus API Client node\n"
        "  3. byteplus/config.ini")


@pytest.mark.parametrize("body", ["<html>gateway</html>", "[]", "null", ""])
def test_a_2xx_reply_that_is_not_a_json_object_keeps_polling(monkeypatch, body):
    client, transport = _client([(200, body), _task("succeeded", content={"video_url": "https://cdn.example.com/v.mp4"})],
                                monkeypatch=monkeypatch)
    task = asyncio.run(client.wait_for_video_task("cgt-1", timeout=60))
    assert task["status"] == "succeeded" and len(transport.calls) == 2


TASK_MAY_BILL = ("The task may exist and bill anyway: check Video generation tasks in the ModelArk console "
                 "before queueing again.")
IMAGES_MAY_BILL = ("The images may have been generated and billed: check your ModelArk usage before "
                   "queueing again.")


@pytest.mark.parametrize("call, path, reply, message", [
    ("create_video_task", "/contents/generations/tasks", (200, "<html>ok</html>"),
     f"ModelArk POST /contents/generations/tasks returned an unreadable reply (HTTP 200: <html>ok</html>). "
     f"{TASK_MAY_BILL}"),
    ("generate_images", "/images/generations", (200, "<html>ok</html>"),
     f"ModelArk POST /images/generations returned an unreadable reply (HTTP 200: <html>ok</html>). "
     f"{IMAGES_MAY_BILL}"),
    ("create_video_task", "/contents/generations/tasks", (200, ""),
     f"ModelArk POST /contents/generations/tasks returned an unreadable reply (HTTP 200: ). {TASK_MAY_BILL}"),
    ("generate_images", "/images/generations", requests.ReadTimeout("read timed out"),
     f"ModelArk POST /images/generations got no reply (read timed out). {IMAGES_MAY_BILL}"),
    ("generate_images", "/images/generations", (502, "<html>bad gateway</html>"),
     f"ModelArk POST /images/generations returned HTTP 502: <html>bad gateway</html>. {IMAGES_MAY_BILL}"),
    ("create_video_task", "/contents/generations/tasks",
     (500, {"error": {"code": "InternalServiceError", "message": "boom"}}),
     f"ModelArk POST /contents/generations/tasks returned HTTP 500 InternalServiceError: boom. {TASK_MAY_BILL}"),
])
def test_a_post_that_may_have_billed_is_sent_once_and_says_so(monkeypatch, capsys, call, path, reply, message):
    client, transport = _client([reply], monkeypatch=monkeypatch)
    capsys.readouterr()
    with pytest.raises(BytePlusAPIError) as excinfo:
        result = getattr(client, call)({"model": "m"})
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    assert str(excinfo.value) == message
    assert capsys.readouterr().out == f"[BytePlus] {message}\n"
    assert transport.calls == [("POST", f"{BASE}{path}", {"model": "m"})]


CHECK_TASK = "It may still run and bill; check it with the BytePlus Seedance Task Result node."


@pytest.mark.parametrize("replies, methods, message", [
    ([_task("queued"), (200, "")], ["GET", "DELETE"], "Cancelled queued Seedance task cgt-1."),
    ([_task("running")], ["GET"], "Stopped waiting for Seedance task cgt-1. It is already running, which "
                                  "ModelArk cannot cancel, so it will finish and be billed."),
    ([_task("succeeded", content={"video_url": "https://cdn.example.com/v.mp4"})], ["GET"],
     "Stopped waiting for Seedance task cgt-1, which had already succeeded and is billed. "
     "Video URL: https://cdn.example.com/v.mp4"),
    ([_task("failed")], ["GET"], "Stopped waiting for Seedance task cgt-1 (status failed)."),
    ([requests.ConnectionError("reset")], ["GET"],
     f"Stopped waiting for Seedance task cgt-1 without cancelling it: reading its status failed (reset). {CHECK_TASK}"),
    ([_task("queued"), (500, "boom")], ["GET", "DELETE"],
     "Stopped waiting for Seedance task cgt-1, but cancelling it failed (ModelArk DELETE "
     f"/contents/generations/tasks/cgt-1 returned HTTP 500: boom). {CHECK_TASK}"),
])
def test_every_cancel_outcome_is_printed_and_raised_as_comfyuis_interrupt(monkeypatch, capsys, replies, methods,
                                                                          message):
    client, transport = _client(replies, interrupted=lambda: True, monkeypatch=monkeypatch)
    capsys.readouterr()
    with pytest.raises(BytePlusInterrupted) as excinfo:
        asyncio.run(client.wait_for_video_task("cgt-1", timeout=60))
    assert str(excinfo.value) == message
    assert capsys.readouterr().out == f"[BytePlus] {message}\n"
    assert [m for m, _, _ in transport.calls] == methods
    assert not isinstance(excinfo.value, Exception)
