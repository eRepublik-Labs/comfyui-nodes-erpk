# ABOUTME: Tests for the ThreadPoolExecutor + /interrupt polling helper used by Gemini nodes.
# ABOUTME: Covers normal return, timeout, interrupt-during-call, and exception propagation.

import os
import sys
import time
from unittest.mock import patch

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

from gemini.gemini_api.cooperative_call import (
    GeminiCallInterrupted,
    call_with_interrupt,
    call_with_retry,
)


def test_returns_result_on_success():
    result = call_with_interrupt(lambda x, y: x + y, 2, 3, timeout_s=5)
    assert result == 5


def test_propagates_exception_from_fn():
    def fn_that_raises():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        call_with_interrupt(fn_that_raises, timeout_s=5)


def test_raises_timeout_when_fn_runs_too_long():
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        call_with_interrupt(time.sleep, 10, timeout_s=0.3, poll_interval_s=0.05)
    elapsed = time.monotonic() - start
    assert elapsed < 1.5, f"Timeout took {elapsed:.2f}s — should be ~0.3s"


def test_raises_interrupted_when_flag_flips_mid_call():
    flips = {"n": 0}

    def fake_interrupted():
        flips["n"] += 1
        return flips["n"] >= 3

    with patch(
        "gemini.gemini_api.cooperative_call._resolve_interrupt_checker",
        return_value=fake_interrupted,
    ):
        with pytest.raises(GeminiCallInterrupted):
            call_with_interrupt(time.sleep, 10, timeout_s=5, poll_interval_s=0.05)


# ---------- call_with_retry ----------


class _FakeServerError(Exception):
    """Stand-in for a google-genai ServerError; class name matches the retry filter."""


def test_retry_eventually_succeeds_on_transient_error():
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise _FakeServerError("transient")
        return "ok"

    result = call_with_retry(flaky, max_retries=2, initial_delay_s=0.01, backoff_factor=1.0)
    assert result == "ok"
    assert attempts["n"] == 3


def test_retry_gives_up_after_max_retries():
    attempts = {"n": 0}

    def always_fails():
        attempts["n"] += 1
        raise _FakeServerError("never recovers")

    with pytest.raises(_FakeServerError):
        call_with_retry(always_fails, max_retries=2, initial_delay_s=0.01, backoff_factor=1.0)
    assert attempts["n"] == 3, "should have tried 1 + max_retries times"


def test_no_retry_on_permanent_error():
    attempts = {"n": 0}

    def value_error_always():
        attempts["n"] += 1
        raise ValueError("bad input")

    with pytest.raises(ValueError):
        call_with_retry(value_error_always, max_retries=5, initial_delay_s=0.01)
    assert attempts["n"] == 1, "ValueError is not transient; must not retry"


def test_no_retry_on_user_interrupt():
    """GeminiCallInterrupted must propagate without retry."""
    flips = {"n": 0}

    def fake_interrupted():
        flips["n"] += 1
        return True

    attempts = {"n": 0}

    def slow_fn():
        attempts["n"] += 1
        time.sleep(10)

    with patch(
        "gemini.gemini_api.cooperative_call._resolve_interrupt_checker",
        return_value=fake_interrupted,
    ):
        with pytest.raises(GeminiCallInterrupted):
            call_with_retry(slow_fn, max_retries=3, initial_delay_s=0.01,
                            timeout_s=5, poll_interval_s=0.02)
    assert attempts["n"] == 1, "interrupt must not trigger retry"


def test_retry_treats_status_code_500_as_transient():
    class _StatusError(Exception):
        def __init__(self):
            super().__init__("server down")
            self.code = 503

    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise _StatusError()
        return "recovered"

    result = call_with_retry(flaky, max_retries=2, initial_delay_s=0.01)
    assert result == "recovered"
    assert attempts["n"] == 2
