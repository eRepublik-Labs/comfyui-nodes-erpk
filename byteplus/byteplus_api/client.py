# ABOUTME: BytePlusClient: BytePlus ModelArk over plain HTTPS (requests), key resolution, Seedance
# ABOUTME: task create/poll/cancel and Seedream image generation, async for ComfyUI parallelism.

import asyncio
import configparser
import json
import os
import time
from typing import Awaitable, Callable, Optional, Tuple

import requests

from . import emit

try:
    from comfy.model_management import InterruptProcessingException as _InterruptBase
except Exception:
    # ComfyUI's InterruptProcessingException derives from BaseException; match it outside ComfyUI.
    _InterruptBase = BaseException

# (method, url, headers, body bytes or None, timeout seconds) -> (HTTP status, response text)
Transport = Callable[[str, str, dict, Optional[bytes], float], Tuple[int, str]]

# ap-southeast-1 (Johor) is the only region whose docs list both Seedance and Seedream;
# keys and model activation are per region.
BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
VIDEO_TASKS_PATH = "/contents/generations/tasks"
IMAGES_PATH = "/images/generations"
MAX_BODY_BYTES = 64 * 1024 * 1024
_ERROR_TEXT_LIMIT = 300
_AUDIO_POLICY_CODE = "OutputAudioSensitiveContentDetected.PolicyViolation"
_TASK_MAY_BILL = ("The task may exist and bill anyway: check Video generation tasks in the ModelArk console "
                  "before queueing again.")
_IMAGES_MAY_BILL = ("The images may have been generated and billed: check your ModelArk usage before "
                    "queueing again.")
_CHECK_TASK = "It may still run and bill; check it with the BytePlus Seedance Task Result node."


class BytePlusAPIError(Exception):
    """ModelArk answered a request with an error status or an error envelope."""

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status

    @property
    def transient(self) -> bool:
        return self.status is not None and (self.status == 429 or self.status >= 500)


class BytePlusUnreadableReply(BytePlusAPIError):
    """A 2xx reply whose body is not a JSON object. The request may still have taken effect."""

    @property
    def transient(self) -> bool:
        return True


class BytePlusTaskFailed(Exception):
    """A Seedance task reached a state other than succeeded."""


class BytePlusInterrupted(_InterruptBase):
    """The user pressed Cancel in ComfyUI while a Seedance task was pending."""


def _resolve_interrupt_checker() -> Callable[[], bool]:
    try:
        from comfy import model_management
        return model_management.processing_interrupted
    except Exception:
        return lambda: False


def _requests_transport(session: requests.Session) -> Transport:
    def send(method, url, headers, data, timeout):
        response = session.request(method, url, headers=headers, data=data, timeout=(15, timeout))
        return response.status_code, response.text
    return send


def _error_description(status: int, text: str) -> str:
    """'HTTP 400 Code: message' from ModelArk's error envelope, else the status and raw text."""
    try:
        body = json.loads(text)
    except ValueError:
        body = None
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict) and error.get("code"):
        return f"HTTP {status} {error['code']}: {error.get('message', '')}"
    return f"HTTP {status}: {text[:_ERROR_TEXT_LIMIT]}"


class BytePlusClient:
    """ModelArk data-plane client. Key priority: ComfyUI Settings > argument > config.ini."""

    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None,
                 transport: Optional[Transport] = None, poll_interval: float = 8.0):
        self.api_key = self._resolve_api_key(api_key, config_path)
        self._transport = transport or _requests_transport(requests.Session())
        self.poll_interval = poll_interval

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        try:
            from ...settings import get_comfy_setting
            settings_key = get_comfy_setting("ERPK.BYTEPLUS_API_KEY")
            if settings_key:
                emit("Using API key from ComfyUI Settings")
                return settings_key
        except (ImportError, ValueError):
            pass

        if api_key and api_key.strip():
            emit("Using API key from node input")
            return api_key.strip()

        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini")
        try:
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            file_key = cfg["API"]["BYTEPLUS_API_KEY"].strip()
            if file_key:
                emit("Using API key from config.ini")
                return file_key
        except (KeyError, configparser.Error):
            pass

        raise ValueError(
            "No BytePlus ModelArk API key found. Provide via:\n"
            "  1. ComfyUI Settings (Settings > ERPK > API Keys > BytePlus ModelArk)\n"
            "  2. The api_key input on the BytePlus API Client node\n"
            "  3. byteplus/config.ini"
        )

    def _call_sync(self, method: str, path: str, payload: Optional[dict] = None, timeout: float = 60,
                   allow_empty: bool = False) -> dict:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            if len(data) > MAX_BODY_BYTES:
                raise ValueError(f"The request body is {len(data)} bytes; ModelArk accepts at most "
                                 f"{MAX_BODY_BYTES}. Pass large media as URLs.")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        status, text = self._transport(method, f"{BASE_URL}{path}", headers, data, timeout)
        if status >= 400:
            raise BytePlusAPIError(f"ModelArk {method} {path} returned {_error_description(status, text)}", status)
        if allow_empty and not text.strip():
            return {}
        try:
            body = json.loads(text)
        except ValueError:
            body = None
        if not isinstance(body, dict):
            raise BytePlusUnreadableReply(f"ModelArk {method} {path} returned an unreadable reply "
                                          f"(HTTP {status}: {text[:_ERROR_TEXT_LIMIT]})", status)
        return body

    async def _call(self, method: str, path: str, payload: Optional[dict] = None, timeout: float = 60,
                    allow_empty: bool = False) -> dict:
        return await asyncio.to_thread(self._call_sync, method, path, payload, timeout, allow_empty)

    def _post_once_sync(self, path: str, body: dict, timeout: float, may_bill: str) -> dict:
        """POST once, never retried: a retry could start a second billed generation.

        Blocking, so the caller's worker thread finishes it even after the node is cancelled;
        a possibly billed outcome is printed because nobody may be left to receive the error.
        """
        try:
            return self._call_sync("POST", path, body, timeout=timeout)
        except requests.RequestException as e:
            raise _may_have_billed(f"ModelArk POST {path} got no reply ({e}). {may_bill}") from e
        except BytePlusUnreadableReply as e:
            raise _may_have_billed(f"{e}. {may_bill}", e.status) from e
        except BytePlusAPIError as e:
            # A 5xx can arrive after the generation started; a 4xx is a rejection.
            if e.status is not None and e.status >= 500:
                raise _may_have_billed(f"{e}. {may_bill}", e.status) from e
            raise

    async def create_video_task(self, body: dict) -> str:
        return await asyncio.to_thread(self._create_video_task_sync, body)

    def _create_video_task_sync(self, body: dict) -> str:
        response = self._post_once_sync(VIDEO_TASKS_PATH, body, 300, _TASK_MAY_BILL)
        task_id = response.get("id")
        if not task_id:
            raise BytePlusAPIError(f"ModelArk created a video task without an id: {str(response)[:_ERROR_TEXT_LIMIT]}")
        # Printed here, in the worker thread, so the ID survives a node cancelled during the POST.
        emit(f"Created Seedance task {task_id}. If this run stops before the video is returned, "
             "fetch it with the BytePlus Seedance Task Result node.")
        return task_id

    async def get_video_task(self, task_id: str) -> dict:
        return await self._call("GET", f"{VIDEO_TASKS_PATH}/{task_id}", timeout=30)

    async def delete_video_task(self, task_id: str) -> None:
        # DELETE has no response parameters, so an empty body is a valid answer.
        await self._call("DELETE", f"{VIDEO_TASKS_PATH}/{task_id}", timeout=30, allow_empty=True)

    def generate_images(self, body: dict) -> dict:
        """Blocking: call it from a worker thread. The response carries the images; there is no task to poll."""
        response = self._post_once_sync(IMAGES_PATH, body, 600, _IMAGES_MAY_BILL)
        error = response.get("error")
        if isinstance(error, dict) and error.get("code"):
            raise BytePlusAPIError(f"ModelArk POST {IMAGES_PATH} returned {error['code']}: {error.get('message', '')}")
        return response

    async def wait_for_video_task(self, task_id: str, timeout: float, cancel_on_interrupt: bool = True) -> dict:
        """Poll until the task succeeds; raise BytePlusTaskFailed on any other final state.

        Connection errors, unreadable replies, 429 and 5xx keep polling; other HTTP errors raise.
        On Cancel, a queued task is deleted unless cancel_on_interrupt is False.
        """
        try:
            return await self._poll(task_id, timeout, cancel_on_interrupt)
        except asyncio.CancelledError:
            # ComfyUI cancels every pending node when another node fails or is interrupted.
            emit(f"Stopped waiting for Seedance task {task_id} when the ComfyUI run ended. It may "
                 "still finish and bill; fetch it with the BytePlus Seedance Task Result node.")
            raise

    async def _poll(self, task_id: str, timeout: float, cancel_on_interrupt: bool) -> dict:
        is_interrupted = _resolve_interrupt_checker()
        on_interrupt = self._cancel_on_interrupt if cancel_on_interrupt else _leave_on_interrupt
        deadline = time.monotonic() + timeout
        last_status = None
        while time.monotonic() < deadline:
            if is_interrupted():
                await on_interrupt(task_id)
            try:
                task = await self.get_video_task(task_id)
            except (requests.RequestException, BytePlusAPIError) as e:
                if isinstance(e, BytePlusAPIError) and not e.transient:
                    raise
                emit(f"Polling task {task_id} hit a transient error, retrying: {e}")
                await self._sleep(task_id, is_interrupted, on_interrupt)
                continue
            status = task.get("status")
            if status != last_status:
                emit(f"Task {task_id} status: {status}")
                last_status = status
            if status == "succeeded":
                return task
            if status not in ("queued", "running"):
                raise BytePlusTaskFailed(task_failure_message(task_id, task))
            await self._sleep(task_id, is_interrupted, on_interrupt)
        raise BytePlusTaskFailed(f"Seedance task {task_id} did not finish within {timeout:.0f} s.")

    async def _sleep(self, task_id: str, is_interrupted: Callable[[], bool],
                     on_interrupt: Callable[[str], Awaitable[None]]) -> None:
        elapsed = 0.0
        while elapsed < self.poll_interval:
            if is_interrupted():
                await on_interrupt(task_id)
            step = min(0.5, self.poll_interval - elapsed)
            await asyncio.sleep(step)
            elapsed += step

    async def _cancel_on_interrupt(self, task_id: str) -> None:
        # DELETE cancels only a queued task; on a finished task it deletes the record,
        # and a running task cannot be stopped. Whatever happens, the user's Cancel wins.
        try:
            task = await self.get_video_task(task_id)
        except Exception as e:
            raise _interrupted(f"Stopped waiting for Seedance task {task_id} without cancelling it: "
                               f"reading its status failed ({e}). {_CHECK_TASK}") from e
        status = task.get("status")
        if status == "queued":
            try:
                await self.delete_video_task(task_id)
            except Exception as e:
                raise _interrupted(f"Stopped waiting for Seedance task {task_id}, but cancelling it "
                                   f"failed ({e}). {_CHECK_TASK}") from e
            raise _interrupted(f"Cancelled queued Seedance task {task_id}.")
        if status == "running":
            raise _interrupted(f"Stopped waiting for Seedance task {task_id}. It is already running, "
                               "which ModelArk cannot cancel, so it will finish and be billed.")
        if status == "succeeded":
            video_url = (task.get("content") or {}).get("video_url")
            raise _interrupted(f"Stopped waiting for Seedance task {task_id}, which had already succeeded "
                               f"and is billed. Video URL: {video_url}")
        raise _interrupted(f"Stopped waiting for Seedance task {task_id} (status {status}).")


async def _leave_on_interrupt(task_id: str) -> None:
    raise _interrupted(f"Stopped waiting for Seedance task {task_id}. The Task Result node only reads a task, "
                       "so the task is untouched.")


def _may_have_billed(message: str, status: Optional[int] = None) -> BytePlusAPIError:
    emit(message)
    return BytePlusAPIError(message, status)


def _interrupted(message: str) -> BytePlusInterrupted:
    # ComfyUI shows no text for an interrupt, so the console line is the user's only record.
    emit(message)
    return BytePlusInterrupted(message)


def task_failure_message(task_id: str, task: dict) -> str:
    status = task.get("status")
    if status == "failed":
        error = task.get("error") or {}
        code = error.get("code", "unknown error")
        message = f"Seedance task {task_id} failed: {code}: {error.get('message', '')}"
        if code == _AUDIO_POLICY_CODE:
            message += " The generated audio was rejected; turn generate_audio off and run again."
        return message
    if status == "expired":
        return f"Seedance task {task_id} expired: it stayed queued or running past execution_expires_after."
    if status == "cancelled":
        return f"Seedance task {task_id} was cancelled."
    return f"Seedance task {task_id} returned unknown status {status!r}."
