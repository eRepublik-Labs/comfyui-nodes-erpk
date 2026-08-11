"""
WaveSpeed AI API Client

This module provides the core client for interacting with the WaveSpeed AI API.

Public methods are async so ComfyUI's executor can interleave concurrent API
nodes. Underlying HTTP work uses the synchronous `requests` library through
`asyncio.to_thread`, which preserves the existing retry/session machinery
while releasing the event loop during network I/O. The polling loop uses
`await asyncio.sleep` so multiple in-flight jobs share the event loop instead
of blocking it for minutes between status checks.
"""

import asyncio
import time
import io
import requests
from typing import Callable, Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .utils import BaseRequest


try:
    from comfy.model_management import InterruptProcessingException as _InterruptBase
except Exception:
    _InterruptBase = Exception


class WaveSpeedInterrupted(_InterruptBase):
    """Raised when the user hit Cancel/interrupt during WaveSpeed task polling.

    Subclasses ComfyUI's InterruptProcessingException when available so the
    executor recognizes it as a clean cancel (no red error node); falls back to
    plain Exception outside ComfyUI (unit tests, smoke scripts).
    """


def _resolve_interrupt_checker() -> Callable[[], bool]:
    """Return a callable reporting whether ComfyUI's interrupt flag is set.

    Falls back to a no-op when run outside ComfyUI (unit tests, smoke scripts).
    """
    try:
        from comfy import model_management
        return model_management.processing_interrupted
    except Exception:
        return lambda: False


class WaveSpeedClient:
    """
    WaveSpeed AI API Client

    This class handles core communication with the WaveSpeed AI API, including:
    - Authentication
    - Request submission
    - Task status checking
    - File uploads
    """

    BASE_URL = "https://api.wavespeed.ai"

    def __init__(self, api_key: str):
        """
        Initialize WaveSpeed AI API client.

        Args:
            api_key: WaveSpeed AI API key
        """
        self.api_key = api_key
        self.once_timeout = 1800  # Default timeout is 30 minutes

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create session with connection pooling and retry strategy
        self.session = requests.Session()

        # Configure retry strategy for resilient connections
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )

        # Configure adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _post_sync(self, endpoint: str, payload: Dict[str, Any], timeout: float = 60) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"

        # Use tuple for timeout: (connect_timeout, read_timeout)
        connect_timeout = min(15, timeout / 4)  # Up to 15s for connection
        read_timeout = timeout
        timeout_tuple = (connect_timeout, read_timeout)

        try:
            response = self.session.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout_tuple
            )

            # Check for authentication errors
            if response.status_code == 401:
                raise Exception("Unauthorized: Invalid API key")

            # Check for other HTTP errors
            if response.status_code != 200:
                error_message = f"Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = f"Error: {error_data['message']}"
                    elif "error" in error_data:
                        error_message = f"Error: {error_data['error']}"
                except:
                    pass
                raise Exception(error_message)

            # Parse response
            response_data = response.json()

            # Handle API-level errors in response
            if isinstance(response_data, dict) and 'code' in response_data:
                if response_data['code'] == 401:
                    raise Exception("Unauthorized: Invalid API key")
                if response_data['code'] != 200:
                    raise Exception(f"API Error: {response_data.get('message', 'Unknown error')}")
                return response_data.get('data', {})

            return response_data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    async def post(self, endpoint: str, payload: Dict[str, Any], timeout: float = 60) -> Dict[str, Any]:
        """
        Send POST request to WaveSpeed AI API.

        Args:
            endpoint: API endpoint path
            payload: Request payload
            timeout: Request timeout in seconds

        Returns:
            dict: API response data

        Raises:
            Exception: If request fails or returns error status
        """
        return await asyncio.to_thread(self._post_sync, endpoint, payload, timeout)

    def _get_sync(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 30) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"

        # Use tuple for timeout: (connect_timeout, read_timeout)
        connect_timeout = min(10, timeout / 3)
        read_timeout = timeout
        timeout_tuple = (connect_timeout, read_timeout)

        try:
            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=timeout_tuple
            )

            if response.status_code != 200:
                error_message = f"Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_message = f"Error: {error_data['error']}"
                    elif "message" in error_data:
                        error_message = f"Error: {error_data['message']}"
                except:
                    pass
                raise Exception(error_message)

            response_data = response.json()

            # Handle API-level errors in response
            if isinstance(response_data, dict) and 'code' in response_data:
                if response_data['code'] != 200:
                    raise Exception(f"API Error: {response_data.get('message', 'Unknown error')}")
                return response_data.get('data', {})

            return response_data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 30) -> Dict[str, Any]:
        """
        Send GET request to WaveSpeed AI API.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            dict: API response data

        Raises:
            Exception: If request fails or returns error status
        """
        return await asyncio.to_thread(self._get_sync, endpoint, params, timeout)

    async def check_task_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check the status of a submitted task.

        Args:
            request_id: Task ID to check

        Returns:
            dict: Task status information including status, progress, output, etc.

        Raises:
            Exception: If no valid task ID provided or request fails
        """
        if not request_id:
            raise Exception("No valid task ID provided")

        # Use 30s timeout for status checks - these should be quick
        return await self.get(f"/api/v3/predictions/{request_id}/result", timeout=30)

    async def wait_for_task(
        self,
        request_id: str,
        polling_interval: int = 5,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wait for task completion and return the result.

        Args:
            request_id: Task ID to wait for
            polling_interval: Polling interval in seconds
            timeout: Maximum time to wait for task completion in seconds

        Returns:
            dict: Task result

        Raises:
            Exception: If the task fails or times out
        """
        if not timeout:
            timeout = self.once_timeout

        if not request_id:
            raise Exception("No valid task ID provided")

        is_interrupted = _resolve_interrupt_checker()
        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            # ComfyUI's Cancel only sets a flag; a long-running node must poll
            # it. Check before each status request so Cancel bails out fast.
            if is_interrupted():
                raise WaveSpeedInterrupted(
                    f"WaveSpeed task {request_id} polling aborted by ComfyUI interrupt"
                )
            try:
                task_status = await self.check_task_status(request_id)
                status = task_status.get("status")

                # Log status changes
                if status != last_status:
                    print(f"[WaveSpeed] Task {request_id} status: {status}")
                    last_status = status

                if status == "completed":
                    return task_status
                elif status == "failed":
                    error_message = task_status.get("error", "Task failed")
                    raise Exception(f"Task failed: {error_message}")

                await self._interruptible_sleep(polling_interval, is_interrupted)

            except WaveSpeedInterrupted:
                # User interrupt must not be swallowed by the retry-and-continue path.
                raise
            except Exception as e:
                # If it's a task failure, re-raise
                if "Task failed" in str(e):
                    raise
                # Otherwise log and continue polling
                print(f"[WaveSpeed] Error checking task status: {e}")
                await self._interruptible_sleep(polling_interval, is_interrupted)

        raise Exception(f"Task timed out after {timeout} seconds")

    async def _interruptible_sleep(
        self,
        seconds: float,
        is_interrupted: Callable[[], bool],
        check_interval: float = 0.5,
    ) -> None:
        """Sleep up to `seconds`, bailing out within `check_interval` of an interrupt.

        Polling intervals are long (10s for video jobs); a single asyncio.sleep
        would leave Cancel unnoticed until it elapses. Sleeping in small chunks
        keeps the event loop shared with other API nodes while making Cancel
        feel immediate.
        """
        elapsed = 0.0
        while elapsed < seconds:
            if is_interrupted():
                raise WaveSpeedInterrupted("WaveSpeed task polling aborted by ComfyUI interrupt")
            step = min(check_interval, seconds - elapsed)
            await asyncio.sleep(step)
            elapsed += step

    async def send_request(
        self,
        request: BaseRequest,
        wait_for_completion: bool = True,
        polling_interval: int = 5,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send an API request using a request object.

        Args:
            request: The request object containing payload and endpoint logic
            wait_for_completion: Whether to wait for task completion
            polling_interval: Polling interval in seconds
            timeout: Maximum time to wait for task completion in seconds

        Returns:
            dict: API response or task result

        Raises:
            Exception: If request submission fails or task fails
        """
        # Build request payload
        payload = request.build_payload()

        # Add common fields
        payload["enable_base64_output"] = False

        # Handle seed field if present
        if "seed" in payload:
            if payload["seed"] == -1:
                payload["seed"] = -1
            else:
                payload["seed"] = payload["seed"] % 9999999999

        # i2v endpoints can post several MB of base64 data URIs (start + end frame);
        # 60s was too tight on degraded uplinks and tripped write timeouts.
        initial_timeout = 180
        response = await self.post(request.get_api_path(), payload, timeout=initial_timeout)

        # Extract request ID
        request_id = response.get("id")
        if not request_id:
            raise Exception("No request ID in response")

        print(f"[WaveSpeed] Task submitted with ID: {request_id}")

        # Return immediately if not waiting for completion
        if not wait_for_completion:
            return {"request_id": request_id, "status": "processing"}

        # Wait for task completion
        task_result = await self.wait_for_task(
            request_id,
            polling_interval=polling_interval,
            timeout=timeout
        )

        return task_result

    def _request_upload_ticket(self, filename: str, size: int, content_type: str) -> Dict[str, Any]:
        """
        Ask the API where to put a file's bytes.

        Args:
            filename: Name the file will be stored under, including extension
            size: Exact byte count of the payload; the API caps this at 200 MiB
            content_type: MIME type of the payload

        Returns:
            dict: Ticket carrying `download_url` and an `upload` block describing
                  the storage request to make next

        Raises:
            Exception: If the API rejects the request or returns no ticket
        """
        url = f"{self.BASE_URL}/api/v3/media/uploads"
        payload = {"filename": filename, "size": size, "content_type": content_type}

        response = self.session.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=(15, 30)
        )

        if response.status_code != 200:
            raise Exception(f"Upload ticket request failed: {response.status_code}")

        response_data = response.json()
        if isinstance(response_data, dict) and 'code' in response_data:
            if response_data['code'] != 200:
                raise Exception(f"API Error: {response_data.get('message', 'Unknown error')}")
            ticket = response_data.get('data', {})
            if "download_url" in ticket and "upload" in ticket:
                return ticket

        raise Exception("No upload ticket in response")

    def _upload_bytes_sync(self, filename: str, content_type: str, data: bytes) -> str:
        """
        Upload raw bytes and return the URL they can be read back from.

        The bytes go straight to storage rather than through the API gateway, so
        the ticket request is the only call that carries the API key. Sending it
        to the storage URL would leak it to a third party.

        Args:
            filename: Name the file will be stored under, including extension
            content_type: MIME type of the payload
            data: The file contents

        Returns:
            str: URL the uploaded file can be downloaded from

        Raises:
            Exception: If the ticket request or the storage upload fails
        """
        try:
            ticket = self._request_upload_ticket(filename, len(data), content_type)
            destination = ticket["upload"]

            response = self.session.put(
                destination["url"],
                headers=destination.get("headers", {}),
                data=data,
                timeout=(15, 300)
            )

            if not 200 <= response.status_code < 300:
                raise Exception(f"Upload failed: {response.status_code}")

            return ticket["download_url"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")

    def _upload_file_sync(self, image) -> str:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")

        return self._upload_bytes_sync("image.png", "image/png", buffered.getvalue())

    async def upload_file(self, image) -> str:
        """
        Upload an image file to WaveSpeed AI API.

        Args:
            image: PIL Image to upload

        Returns:
            str: URL of the uploaded image

        Raises:
            Exception: If upload fails
        """
        return await asyncio.to_thread(self._upload_file_sync, image)
