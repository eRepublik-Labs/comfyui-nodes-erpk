"""
Core WaveSpeed AI nodes for ComfyUI

This module provides the essential nodes for WaveSpeed AI integration:
- API Client node for authentication
- Preview nodes for videos and audio
- Upload nodes for images, videos, and audio
"""

import os
import time
import requests
import configparser
from typing import Tuple, Dict, Any, List

# ComfyUI imports
try:
    import folder_paths
except ImportError:
    # Fallback for testing outside ComfyUI
    class folder_paths:
        @staticmethod
        def get_output_directory():
            return os.path.join(os.path.dirname(__file__), "output")

        @staticmethod
        def get_save_image_path(prefix, directory):
            filename = f"{prefix}_{int(time.time())}"
            return directory, filename, 0, None, None

from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.utils import tensor2images

# Configuration handling
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(current_dir, '.temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    config_path = os.path.join(current_dir, 'config.ini')
    config = configparser.ConfigParser()

    if not os.path.exists(config_path):
        config['API'] = {'WAVESPEED_API_KEY': ''}
        with open(config_path, 'w') as config_file:
            config.write(config_file)

    config.read(config_path)
except Exception as e:
    print(f"[WaveSpeed] Error reading or creating config file: {e}")
    config = None


class WaveSpeedAIAPIClient:
    """
    WaveSpeed AI API Client Node

    This node creates a client for connecting to the WaveSpeed AI API.
    It can use an API key from the input or from the config.ini file.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "api_key": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": "WaveSpeed AI API key. If empty, checks WAVESPEED_API_KEY environment variable, then config.ini"
                    }
                ),
            },
        }

    RETURN_TYPES = ("WAVESPEED_AI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "create_client"
    CATEGORY = "ERPK/WaveSpeedAI"

    def create_client(self, api_key: str) -> Tuple[Dict[str, str]]:
        """
        Create a WaveSpeed AI API client.

        API key priority (highest to lowest):
        1. Direct input parameter
        2. WAVESPEED_API_KEY environment variable
        3. config.ini file

        Args:
            api_key: WaveSpeed AI API key (leave empty to use env var or config)

        Returns:
            Tuple containing client configuration dict

        Raises:
            ValueError: If no API key is found in any source
        """
        wavespeed_api_key = ""

        # Priority 1: Direct input (highest priority)
        if api_key and api_key.strip():
            wavespeed_api_key = api_key.strip()
            print("[WaveSpeed] Using API key from node input")

        # Priority 2 & 3: Environment variable, then config file
        else:
            # Try environment variable
            env_key = os.getenv("WAVESPEED_API_KEY", "").strip()
            if env_key:
                wavespeed_api_key = env_key
                print("[WaveSpeed] Using API key from environment variable WAVESPEED_API_KEY")

            # Fall back to config file
            elif config:
                try:
                    config_key = config['API']['WAVESPEED_API_KEY'].strip()
                    if config_key:
                        wavespeed_api_key = config_key
                        print("[WaveSpeed] Using API key from config.ini")
                    else:
                        raise ValueError(
                            "No API key found. Please provide via:\n"
                            "  1. Node input parameter\n"
                            "  2. WAVESPEED_API_KEY environment variable\n"
                            "  3. config.ini file"
                        )
                except KeyError:
                    raise ValueError(
                        "No API key found. Please provide via:\n"
                        "  1. Node input parameter\n"
                        "  2. WAVESPEED_API_KEY environment variable\n"
                        "  3. config.ini file"
                    )

            # No source available
            else:
                raise ValueError(
                    "No API key found. Please provide via:\n"
                    "  1. Node input parameter\n"
                    "  2. WAVESPEED_API_KEY environment variable\n"
                    "  3. config.ini file"
                )

        if not wavespeed_api_key:
            raise ValueError(
                "No API key found. Please provide via:\n"
                "  1. Node input parameter\n"
                "  2. WAVESPEED_API_KEY environment variable\n"
                "  3. config.ini file"
            )

        # Return client configuration
        return ({"api_key": wavespeed_api_key},)


class PreviewVideo:
    """
    Preview Video Node for ComfyUI

    This node allows previewing and saving videos generated by WaveSpeed AI.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "video_url": (
                    "STRING",
                    {
                        "forceInput": False,
                        "tooltip": "URL of the video to preview and save"
                    }
                ),
                "save_file_prefix": (
                    "STRING",
                    {
                        "default": "wavespeed_video",
                        "tooltip": "Prefix for the saved video file"
                    }
                ),
            }
        }

    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "ERPK/WaveSpeedAI"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)

    def run(self, video_url: str, save_file_prefix: str) -> Dict[str, Any]:
        """
        Preview and save a video.

        Args:
            video_url: URL of the video
            save_file_prefix: Prefix for the saved file

        Returns:
            Dict with UI data and result containing file path

        Raises:
            ValueError: If no video URL provided
            RuntimeError: If download fails
        """
        if not video_url:
            raise ValueError("No video URL provided")

        # Download video
        try:
            response = requests.get(video_url, timeout=60)
            response.raise_for_status()
            video_data = response.content
        except requests.RequestException as e:
            raise RuntimeError(f"Error downloading video: {e}")

        # Determine file extension
        file_extension = os.path.splitext(video_url)[-1].lower()
        if not file_extension or file_extension == '.' or len(file_extension) > 5:
            file_extension = '.mp4'

        # Save video to output directory
        output_dir = folder_paths.get_output_directory()
        filename = f"{save_file_prefix}_{int(time.time())}{file_extension}"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, "wb") as f:
            f.write(video_data)

        print(f"[WaveSpeed] Video saved to: {file_path}")

        # Return UI data for ComfyUI preview
        return {
            "ui": {"video_url": [video_url]},
            "result": (file_path,)
        }


class SaveAudio:
    """
    Save Audio Node for ComfyUI

    This node allows saving audio files generated by WaveSpeed AI.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "audio_url": (
                    "STRING",
                    {
                        "forceInput": False,
                        "tooltip": "URL of the audio to download and save"
                    }
                ),
                "save_file_prefix": (
                    "STRING",
                    {
                        "default": "wavespeed_audio",
                        "tooltip": "Prefix for the saved audio file"
                    }
                ),
            }
        }

    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "ERPK/WaveSpeedAI"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)

    def run(self, audio_url: str, save_file_prefix: str) -> Tuple[str]:
        """
        Download and save an audio file.

        Args:
            audio_url: URL of the audio
            save_file_prefix: Prefix for the saved file

        Returns:
            Tuple containing the file path

        Raises:
            ValueError: If no audio URL provided
            RuntimeError: If download fails
        """
        if not audio_url:
            raise ValueError("No audio URL provided")

        # Download audio
        try:
            response = requests.get(audio_url, timeout=60)
            response.raise_for_status()
            audio_data = response.content
        except requests.RequestException as e:
            raise RuntimeError(f"Error downloading audio: {e}")

        # Determine file extension
        file_extension = os.path.splitext(audio_url)[-1].lower()
        if not file_extension or file_extension == '.' or len(file_extension) > 5:
            file_extension = '.mp3'

        # Save audio to output directory
        full_output_folder, filename, counter, _, _ = folder_paths.get_save_image_path(
            save_file_prefix,
            folder_paths.get_output_directory()
        )

        file = f"{filename}_{counter:05d}{file_extension}"
        file_path = os.path.join(full_output_folder, file)

        with open(file_path, "wb") as f:
            f.write(audio_data)

        print(f"[WaveSpeed] Audio saved to: {file_path}")

        return (file_path,)


class UploadImage:
    """
    Upload Image Node for WaveSpeed AI

    This node uploads images to WaveSpeed AI and returns the URL.
    Note: Uploaded URLs expire after a short time.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "image": ("IMAGE",)
            }
        }

    DESCRIPTION = "Upload an image to WaveSpeed AI API. The URL expires after a short time."
    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("first_image_url", "image_urls",)
    CATEGORY = "ERPK/WaveSpeedAI"
    FUNCTION = "upload_file"

    def upload_file(self, client: Dict[str, str], image) -> Tuple[str, List[str]]:
        """
        Upload image(s) to WaveSpeed AI.

        Args:
            client: API client configuration
            image: ComfyUI image tensor

        Returns:
            Tuple of (first_image_url, list_of_image_urls)
        """
        # Convert tensor to PIL images
        images = tensor2images(image)
        image_urls = []

        # Create client and upload each image
        real_client = WaveSpeedClient(api_key=client["api_key"])
        for img in images:
            image_url = real_client.upload_file(img)
            image_urls.append(image_url)
            print(f"[WaveSpeed] Image uploaded: {image_url}")

        # Return first URL and list of all URLs
        return (
            image_urls[0] if image_urls else "",
            image_urls
        )


# Node registration mappings
NODE_CLASS_MAPPINGS = {
    'WaveSpeed Custom Client': WaveSpeedAIAPIClient,
    'WaveSpeed Custom Preview Video': PreviewVideo,
    'WaveSpeed Custom Save Audio': SaveAudio,
    'WaveSpeed Custom Upload Image': UploadImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    'WaveSpeed Custom Client': 'WaveSpeed Client (Custom)',
    'WaveSpeed Custom Preview Video': 'WaveSpeed Preview Video (Custom)',
    'WaveSpeed Custom Save Audio': 'WaveSpeed Save Audio (Custom)',
    'WaveSpeed Custom Upload Image': 'WaveSpeed Upload Image (Custom)',
}