"""
WaveSpeed AI API Client

This module provides the core client for interacting with the WaveSpeed AI API.
"""

import time
import io
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import PIL.Image
except ImportError:
    from PIL import Image as PIL

from .utils import BaseRequest


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

    def post(self, endpoint: str, payload: Dict[str, Any], timeout: float = 60) -> Dict[str, Any]:
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

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 30) -> Dict[str, Any]:
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

    def check_task_status(self, request_id: str) -> Dict[str, Any]:
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
        return self.get(f"/api/v2/predictions/{request_id}/result", timeout=30)

    def wait_for_task(
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

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            try:
                task_status = self.check_task_status(request_id)
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

                time.sleep(polling_interval)

            except Exception as e:
                # If it's a task failure, re-raise
                if "Task failed" in str(e):
                    raise
                # Otherwise log and continue polling
                print(f"[WaveSpeed] Error checking task status: {e}")
                time.sleep(polling_interval)

        raise Exception(f"Task timed out after {timeout} seconds")

    def send_request(
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

        # Submit request with appropriate timeout
        initial_timeout = 60  # 60s for initial request submission
        response = self.post(request.get_api_path(), payload, timeout=initial_timeout)

        # Extract request ID
        request_id = response.get("id")
        if not request_id:
            raise Exception("No request ID in response")

        print(f"[WaveSpeed] Task submitted with ID: {request_id}")

        # Return immediately if not waiting for completion
        if not wait_for_completion:
            return {"request_id": request_id, "status": "processing"}

        # Wait for task completion
        task_result = self.wait_for_task(
            request_id,
            polling_interval=polling_interval,
            timeout=timeout
        )

        return task_result

    def upload_file(self, image: PIL.Image.Image) -> str:
        """
        Upload an image file to WaveSpeed AI API.

        Args:
            image: PIL Image to upload

        Returns:
            str: URL of the uploaded image

        Raises:
            Exception: If upload fails
        """
        url = f"{self.BASE_URL}/api/v2/media/upload/binary"

        # Convert image to PNG bytes
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        buffered.seek(0)

        files = {'file': ('image.png', buffered, 'image/png')}

        # Set timeout for file uploads
        timeout_tuple = (15, 180)  # 15s connect, 180s read for uploads

        try:
            response = self.session.post(
                url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                files=files,
                timeout=timeout_tuple
            )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code}")

            response_data = response.json()

            # Handle API response format
            if isinstance(response_data, dict) and 'code' in response_data:
                if response_data['code'] != 200:
                    raise Exception(f"API Error: {response_data.get('message', 'Unknown error')}")
                data = response_data.get('data', {})
                if "download_url" in data:
                    return data["download_url"]

            raise Exception("No download URL in response")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")

    def upload_file_with_type(self, file_path: str, file_type: str) -> str:
        """
        Upload a file of specified type to WaveSpeed AI API.

        Args:
            file_path: Path to the file to upload
            file_type: MIME type of the file (e.g., "video/mp4", "audio/mp3")

        Returns:
            str: URL of the uploaded file

        Raises:
            Exception: If upload fails or invalid file type
        """
        url = f"{self.BASE_URL}/api/v2/media/upload/binary"

        # Determine filename based on type
        file_name = ""
        if "video" in file_type:
            file_name = "video.mp4"
        elif "image" in file_type:
            file_name = "image.png"
        elif "audio" in file_type:
            file_name = "audio.mp3"
        else:
            raise Exception(f"Invalid file type: {file_type}")

        # Upload file
        try:
            with open(file_path, "rb") as file:
                files = {'file': (file_name, file, file_type)}

                # Set timeout for file uploads
                timeout_tuple = (15, 180)  # 15s connect, 180s read

                response = self.session.post(
                    url,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    files=files,
                    timeout=timeout_tuple
                )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code}")

            response_data = response.json()

            # Handle API response format
            if isinstance(response_data, dict) and 'code' in response_data:
                if response_data['code'] != 200:
                    raise Exception(f"API Error: {response_data.get('message', 'Unknown error')}")
                data = response_data.get('data', {})
                if "download_url" in data:
                    return data["download_url"]

            raise Exception("No download URL in response")

        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")