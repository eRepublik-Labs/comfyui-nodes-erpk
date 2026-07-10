# ABOUTME: Runs blocking SDK calls in a thread while polling ComfyUI's interrupt flag.
# ABOUTME: Lets users abort an in-flight Gemini call via /interrupt instead of waiting out the HTTP timeout.

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Callable, Optional

DEFAULT_POLL_INTERVAL_S = 0.25
_DEFAULT_TIMEOUT_MS = 300000


def resolve_timeout_ms() -> int:
    """Per-request Gemini timeout in milliseconds.

    Configurable via the ERPK.GEMINI_TIMEOUT_MS ComfyUI setting; falls back to
    5 minutes. Read at call time so the setting applies per run with no restart.
    """
    try:
        from ...settings import get_comfy_setting
        return int(get_comfy_setting("ERPK.GEMINI_TIMEOUT_MS", _DEFAULT_TIMEOUT_MS))
    except (ImportError, ValueError, TypeError):
        return _DEFAULT_TIMEOUT_MS

# A cancelled or timed-out call cannot abort its blocking thread (Python has no
# preemption), so the slot stays busy until the genai HTTP timeout
# (resolve_timeout_ms, pushed into the Client) elapses and the thread returns.
# Size the pool so a burst of interrupted calls does not starve fresh ones
# during that window.
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="erpk-gemini-call")


class GeminiCallInterrupted(Exception):
    """Raised when the user hit /interrupt during a Gemini SDK call."""


def _resolve_interrupt_checker() -> Callable[[], bool]:
    """Return a callable that reports whether ComfyUI's interrupt flag is set.

    Falls back to a no-op when run outside ComfyUI (unit tests, smoke scripts).
    """
    try:
        from comfy import model_management
        return model_management.processing_interrupted
    except Exception:
        return lambda: False


def call_with_interrupt(
    fn: Callable[..., Any],
    *args: Any,
    timeout_s: Optional[float] = None,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    **kwargs: Any,
) -> Any:
    """Run fn(*args, **kwargs) in a background thread, polling for /interrupt.

    Returns fn's result on success. Raises GeminiCallInterrupted on user
    interrupt or TimeoutError when timeout_s elapses. Exceptions from fn are
    re-raised in the caller's thread.

    The background thread's blocking call cannot itself be aborted — Python
    threads have no preemption. But raising back to the ComfyUI executor lets
    the workflow surface as cancelled instead of frozen. The HTTP timeout on
    the genai.Client still bounds the wall-clock cost.
    """
    if timeout_s is None:
        timeout_s = resolve_timeout_ms() / 1000.0
    is_interrupted = _resolve_interrupt_checker()

    future = _executor.submit(fn, *args, **kwargs)
    deadline = time.monotonic() + timeout_s

    while True:
        try:
            return future.result(timeout=poll_interval_s)
        except FutureTimeoutError:
            pass
        if is_interrupted():
            future.cancel()
            raise GeminiCallInterrupted("Gemini call aborted by ComfyUI /interrupt")
        if time.monotonic() >= deadline:
            future.cancel()
            raise TimeoutError(f"Gemini call exceeded {timeout_s:.1f}s without completing")


# Status codes (and SDK exception name fragments) that indicate a transient
# server-side failure worth retrying. Excludes 4xx client errors and 429
# rate-limit (the SDK already implements its own backoff for the latter).
_TRANSIENT_STATUS_CODES = {500, 502, 503, 504}
_TRANSIENT_NAME_FRAGMENTS = (
    "ServerError",
    "ServiceUnavailable",
    "InternalServerError",
    "DeadlineExceeded",
    "GatewayTimeout",
)


def _is_transient(exc: BaseException) -> bool:
    """True when exc looks like a retryable transient failure."""
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(status, int) and status in _TRANSIENT_STATUS_CODES:
        return True
    name = type(exc).__name__
    return any(fragment in name for fragment in _TRANSIENT_NAME_FRAGMENTS)


def call_with_retry(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 2,
    initial_delay_s: float = 1.0,
    backoff_factor: float = 2.0,
    timeout_s: Optional[float] = None,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    **kwargs: Any,
) -> Any:
    """Run fn with /interrupt cooperation and exponential-backoff retries.

    max_retries is the number of retries AFTER the first attempt — so the
    total attempt count is max_retries + 1. Default 2 → 3 attempts total.
    Retries fire only on transient errors (see _is_transient). User-initiated
    interrupts and permanent client errors propagate without retry.
    """
    delay = initial_delay_s
    last_error: BaseException = RuntimeError("no attempts made")
    for attempt in range(max_retries + 1):
        try:
            return call_with_interrupt(
                fn,
                *args,
                timeout_s=timeout_s,
                poll_interval_s=poll_interval_s,
                **kwargs,
            )
        except GeminiCallInterrupted:
            raise
        except BaseException as exc:
            last_error = exc
            if not _is_transient(exc) or attempt >= max_retries:
                raise
            print(f"[Gemini] Transient error ({type(exc).__name__}): retrying in {delay:.1f}s "
                  f"(attempt {attempt + 1}/{max_retries + 1})")
            time.sleep(delay)
            delay *= backoff_factor
    raise last_error
