# ABOUTME: TDD test driving WaveSpeedClient.wait_for_task to honor ComfyUI's interrupt flag.
# ABOUTME: Asserts the polling loop aborts promptly on Cancel instead of polling until completion/timeout.

import asyncio
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

pytest.importorskip("requests")

from wavespeed.wavespeed_api import client as client_module
from wavespeed.wavespeed_api.client import WaveSpeedClient


def test_wait_for_task_aborts_on_interrupt(monkeypatch):
    """When ComfyUI's interrupt flag is set, wait_for_task must raise, not keep polling.

    Pressing Cancel in ComfyUI sets model_management.processing_interrupted().
    A video job polls for up to `timeout` seconds (900s for Seedance); if the
    loop never checks the flag, Cancel does nothing until the job finishes on
    its own. The loop must check the flag each iteration and bail out.
    """
    monkeypatch.setattr(
        client_module, "_resolve_interrupt_checker", lambda: (lambda: True)
    )

    poll_calls = {"n": 0}

    async def fake_check_task_status(request_id):
        poll_calls["n"] += 1
        return {"status": "processing"}

    async def _drive():
        cl = WaveSpeedClient(api_key="test")
        cl.check_task_status = fake_check_task_status
        await cl.wait_for_task("task-1", polling_interval=10, timeout=900)

    with pytest.raises(client_module.WaveSpeedInterrupted):
        asyncio.run(_drive())

    # It must abort on the first interrupt check, not poll the API for 900s.
    assert poll_calls["n"] <= 1, (
        f"wait_for_task polled {poll_calls['n']} times after interrupt; "
        "it should bail out before/at the first status check."
    )


def test_wait_for_task_interrupt_survives_loop_except(monkeypatch):
    """An interrupt must not be swallowed by the loop's except-and-continue handler.

    wait_for_task catches transient status-check errors and keeps polling. The
    interrupt exception must be re-raised by that handler, not treated as a
    transient error and retried forever.
    """
    flag = {"interrupted": False}
    monkeypatch.setattr(
        client_module,
        "_resolve_interrupt_checker",
        lambda: (lambda: flag["interrupted"]),
    )

    async def flaky_check_task_status(request_id):
        # First call raises a transient error (normally swallowed + retried),
        # and flips the interrupt flag so the next loop iteration must bail.
        flag["interrupted"] = True
        raise Exception("transient network blip")

    async def _drive():
        cl = WaveSpeedClient(api_key="test")
        cl.check_task_status = flaky_check_task_status
        await cl.wait_for_task("task-1", polling_interval=10, timeout=900)

    with pytest.raises(client_module.WaveSpeedInterrupted):
        asyncio.run(_drive())
