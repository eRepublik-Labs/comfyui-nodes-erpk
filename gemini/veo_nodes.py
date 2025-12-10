# ABOUTME: ComfyUI nodes for Google Veo video generation API
# ABOUTME: Provides text-to-video and image-to-video generation nodes

import os
import time
import tempfile
from typing import Optional

from .gemini_api.client import GeminiClient
from .gemini_api.utils import ImageConverter


class VeoTextToVideo:
    """
    Veo Text-to-Video Generation Node

    Generates videos from text prompts using Google's Veo models.
    Veo 3 generates videos with synchronized audio.
    """

    VEO_MODELS = [
        "veo-3.0-generate-preview",
        "veo-2.0-generate-001",
    ]

    ASPECT_RATIOS = ["16:9", "9:16"]
    DURATIONS = [5, 6, 7, 8]
    PERSON_GENERATION_OPTIONS = ["allow_adult", "dont_allow", "allow_all"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client from Gemini API Config node"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description of the video to generate (max 2500 characters)"
                    }
                ),
            },
            "optional": {
                "model": (
                    cls.VEO_MODELS,
                    {
                        "default": "veo-3.0-generate-preview",
                        "tooltip": "Veo model to use. Veo 3 generates video with audio."
                    }
                ),
                "aspect_ratio": (
                    cls.ASPECT_RATIOS,
                    {
                        "default": "16:9",
                        "tooltip": "Video aspect ratio (16:9 landscape, 9:16 portrait)"
                    }
                ),
                "duration_seconds": (
                    cls.DURATIONS,
                    {
                        "default": 8,
                        "tooltip": "Video duration in seconds (5-8). Veo 3 defaults to 8."
                    }
                ),
                "person_generation": (
                    cls.PERSON_GENERATION_OPTIONS,
                    {
                        "default": "allow_adult",
                        "tooltip": "Person generation safety setting. Veo 3 only supports allow_all."
                    }
                ),
                "enhance_prompt": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Let the model enhance your prompt for better results"
                    }
                ),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Elements to exclude from the video"
                    }
                ),
                "seed": (
                    "INT",
                    {
                        "default": -1,
                        "min": -1,
                        "max": 0xffffffff,
                        "tooltip": "Random seed for reproducibility. -1 for random."
                    }
                ),
                "output_directory": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Directory to save video. Empty uses ComfyUI output folder."
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/Gemini/Veo"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for video generation
        return float("nan")

    def generate(
        self,
        client: GeminiClient,
        prompt: str,
        model: str = "veo-3.0-generate-preview",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        person_generation: str = "allow_adult",
        enhance_prompt: bool = True,
        negative_prompt: str = "",
        seed: int = -1,
        output_directory: str = "",
    ):
        """
        Generate a video from a text prompt using Veo.

        Args:
            client: Gemini API client
            prompt: Text description of video
            model: Veo model to use
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration
            person_generation: Person generation safety setting
            enhance_prompt: Whether to enhance the prompt
            negative_prompt: Elements to exclude
            seed: Random seed (-1 for random)
            output_directory: Where to save the video

        Returns:
            Tuple containing the video file path
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if len(prompt) > 2500:
            print(f"[Veo] Warning: Prompt exceeds 2500 characters, truncating")
            prompt = prompt[:2500]

        try:
            from google.genai import types

            print(f"[Veo] Generating video with model: {model}")
            print(f"[Veo] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[Veo] Aspect ratio: {aspect_ratio}, Duration: {duration_seconds}s")

            # Build config
            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "enhance_prompt": enhance_prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }

            # Add negative prompt if provided
            if negative_prompt and negative_prompt.strip():
                config_params["negative_prompt"] = negative_prompt.strip()

            config = types.GenerateVideosConfig(**config_params)

            # Build request params
            request_params = {
                "model": model,
                "prompt": prompt.strip(),
                "config": config,
            }

            # Add seed if specified
            if seed >= 0:
                request_params["seed"] = seed

            # Start video generation
            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = client.client.models.generate_videos(**request_params)

            # Poll for completion
            poll_count = 0
            max_polls = 120  # 40 minutes max at 20s intervals
            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    raise TimeoutError("Video generation timed out after 40 minutes")

                print(f"[Veo] Waiting for video generation... ({poll_count * 20}s elapsed)")
                time.sleep(20)
                operation = client.client.operations.get(operation)

            # Check for errors
            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")

            # Get the generated video
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            # Determine output directory
            if output_directory and output_directory.strip():
                out_dir = output_directory.strip()
            else:
                # Use ComfyUI output folder
                import folder_paths
                out_dir = folder_paths.get_output_directory()

            # Ensure directory exists
            os.makedirs(out_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"veo_{timestamp}.mp4"
            output_path = os.path.join(out_dir, filename)

            # Download and save video
            print(f"[Veo] Saving video to: {output_path}")

            # The video object has a save method or we can download it
            if hasattr(video, 'save'):
                video.save(output_path)
            elif hasattr(video, 'uri') and video.uri:
                # If video is stored in GCS, we need to download it
                downloaded = client.client.files.download(file=video)
                downloaded.save(output_path)
            else:
                # Try to get video data directly
                if hasattr(video, 'video_bytes') and video.video_bytes:
                    with open(output_path, 'wb') as f:
                        f.write(video.video_bytes)
                else:
                    raise ValueError("Could not extract video data from response")

            print(f"[Veo] Video saved successfully: {output_path}")
            return (output_path,)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)


class VeoImageToVideo:
    """
    Veo Image-to-Video Generation Node

    Generates videos from an input image and optional text prompt.
    The image serves as the first frame or style reference.
    """

    VEO_MODELS = [
        "veo-3.0-generate-preview",
        "veo-2.0-generate-001",
    ]

    ASPECT_RATIOS = ["16:9", "9:16"]
    DURATIONS = [5, 6, 7, 8]
    PERSON_GENERATION_OPTIONS = ["allow_adult", "dont_allow", "allow_all"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client from Gemini API Config node"}
                ),
                "image": (
                    "IMAGE",
                    {"tooltip": "Input image to generate video from (first frame)"}
                ),
            },
            "optional": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional text description to guide the video generation"
                    }
                ),
                "model": (
                    cls.VEO_MODELS,
                    {
                        "default": "veo-3.0-generate-preview",
                        "tooltip": "Veo model to use. Veo 3 generates video with audio."
                    }
                ),
                "aspect_ratio": (
                    cls.ASPECT_RATIOS,
                    {
                        "default": "16:9",
                        "tooltip": "Video aspect ratio (16:9 landscape, 9:16 portrait)"
                    }
                ),
                "duration_seconds": (
                    cls.DURATIONS,
                    {
                        "default": 8,
                        "tooltip": "Video duration in seconds (5-8). Veo 3 defaults to 8."
                    }
                ),
                "person_generation": (
                    cls.PERSON_GENERATION_OPTIONS,
                    {
                        "default": "allow_adult",
                        "tooltip": "Person generation safety setting. Veo 3 only supports allow_all."
                    }
                ),
                "enhance_prompt": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Let the model enhance your prompt for better results"
                    }
                ),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Elements to exclude from the video"
                    }
                ),
                "seed": (
                    "INT",
                    {
                        "default": -1,
                        "min": -1,
                        "max": 0xffffffff,
                        "tooltip": "Random seed for reproducibility. -1 for random."
                    }
                ),
                "output_directory": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Directory to save video. Empty uses ComfyUI output folder."
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/Gemini/Veo"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for video generation
        return float("nan")

    def generate(
        self,
        client: GeminiClient,
        image,
        prompt: str = "",
        model: str = "veo-3.0-generate-preview",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        person_generation: str = "allow_adult",
        enhance_prompt: bool = True,
        negative_prompt: str = "",
        seed: int = -1,
        output_directory: str = "",
    ):
        """
        Generate a video from an image using Veo.

        Args:
            client: Gemini API client
            image: Input image tensor
            prompt: Optional text description
            model: Veo model to use
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration
            person_generation: Person generation safety setting
            enhance_prompt: Whether to enhance the prompt
            negative_prompt: Elements to exclude
            seed: Random seed (-1 for random)
            output_directory: Where to save the video

        Returns:
            Tuple containing the video file path
        """
        try:
            from google.genai import types

            # Convert ComfyUI tensor to PIL Image
            pil_image = ImageConverter.tensor_to_pil(image)
            print(f"[Veo] Input image size: {pil_image.size}")

            print(f"[Veo] Generating video from image with model: {model}")
            if prompt and prompt.strip():
                print(f"[Veo] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[Veo] Aspect ratio: {aspect_ratio}, Duration: {duration_seconds}s")

            # Build config
            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "enhance_prompt": enhance_prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }

            # Add negative prompt if provided
            if negative_prompt and negative_prompt.strip():
                config_params["negative_prompt"] = negative_prompt.strip()

            config = types.GenerateVideosConfig(**config_params)

            # Convert PIL Image to google.genai Image type
            # Save to temp file first since the API may need a file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pil_image.save(tmp.name, 'PNG')
                genai_image = types.Image.from_file(tmp.name)

            # Build request params
            request_params = {
                "model": model,
                "image": genai_image,
                "config": config,
            }

            # Add prompt if provided
            if prompt and prompt.strip():
                if len(prompt) > 2500:
                    print(f"[Veo] Warning: Prompt exceeds 2500 characters, truncating")
                    prompt = prompt[:2500]
                request_params["prompt"] = prompt.strip()

            # Add seed if specified
            if seed >= 0:
                request_params["seed"] = seed

            # Start video generation
            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = client.client.models.generate_videos(**request_params)

            # Clean up temp file
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

            # Poll for completion
            poll_count = 0
            max_polls = 120  # 40 minutes max at 20s intervals
            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    raise TimeoutError("Video generation timed out after 40 minutes")

                print(f"[Veo] Waiting for video generation... ({poll_count * 20}s elapsed)")
                time.sleep(20)
                operation = client.client.operations.get(operation)

            # Check for errors
            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")

            # Get the generated video
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            # Determine output directory
            if output_directory and output_directory.strip():
                out_dir = output_directory.strip()
            else:
                # Use ComfyUI output folder
                import folder_paths
                out_dir = folder_paths.get_output_directory()

            # Ensure directory exists
            os.makedirs(out_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"veo_i2v_{timestamp}.mp4"
            output_path = os.path.join(out_dir, filename)

            # Download and save video
            print(f"[Veo] Saving video to: {output_path}")

            # The video object has a save method or we can download it
            if hasattr(video, 'save'):
                video.save(output_path)
            elif hasattr(video, 'uri') and video.uri:
                # If video is stored in GCS, we need to download it
                downloaded = client.client.files.download(file=video)
                downloaded.save(output_path)
            else:
                # Try to get video data directly
                if hasattr(video, 'video_bytes') and video.video_bytes:
                    with open(output_path, 'wb') as f:
                        f.write(video.video_bytes)
                else:
                    raise ValueError("Could not extract video data from response")

            print(f"[Veo] Video saved successfully: {output_path}")
            return (output_path,)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)


# Node registration
NODE_CLASS_MAPPINGS = {
    "VeoTextToVideo": VeoTextToVideo,
    "VeoImageToVideo": VeoImageToVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VeoTextToVideo": "Veo Text to Video",
    "VeoImageToVideo": "Veo Image to Video",
}
