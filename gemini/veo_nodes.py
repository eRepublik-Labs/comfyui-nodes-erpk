# ABOUTME: ComfyUI V3 nodes for Google Veo video generation API.
# ABOUTME: Provides text-to-video and image-to-video generation nodes.

import os
import time
import tempfile

from comfy_api.latest import IO


VEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.1-fast-generate-preview",
    "veo-3.0-generate-001",
    "veo-3.0-fast-generate-001",
    "veo-2.0-generate-001",
]

VEO_ASPECT_RATIOS = ["16:9", "9:16"]
VEO_DURATIONS = [5, 6, 7, 8]
VEO_PERSON_GENERATION_OPTIONS = ["allow_adult", "dont_allow", "allow_all"]


class VeoTextToVideo(IO.ComfyNode):
    """Generates videos from text prompts using Google's Veo models.
    Veo 3 generates videos with synchronized audio."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="VeoTextToVideo",
            display_name="Veo Text to Video",
            category="ERPK/Gemini/Veo",
            description="Generate video from a text prompt using Veo.",
            not_idempotent=True,
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    tooltip="Gemini API client from Gemini API Config node",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text description of the video to generate (max 2500 characters)",
                ),
                IO.Combo.Input(
                    "model",
                    options=VEO_MODELS,
                    default="veo-3.1-generate-preview",
                    optional=True,
                    tooltip="Veo model to use. Veo 3+ generates video with audio.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=VEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Video aspect ratio (16:9 landscape, 9:16 portrait)",
                ),
                IO.Combo.Input(
                    "duration_seconds",
                    options=VEO_DURATIONS,
                    default=8,
                    optional=True,
                    tooltip="Video duration in seconds (5-8). Veo 3 defaults to 8.",
                ),
                IO.Combo.Input(
                    "person_generation",
                    options=VEO_PERSON_GENERATION_OPTIONS,
                    default="allow_adult",
                    optional=True,
                    tooltip="Person generation safety setting. Veo 3 only supports allow_all.",
                ),
                IO.Boolean.Input(
                    "enhance_prompt",
                    default=True,
                    optional=True,
                    tooltip="Let the model enhance your prompt for better results",
                ),
                IO.String.Input(
                    "negative_prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Elements to exclude from the video",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xffffffff,
                    optional=True,
                    control_after_generate=True,
                    tooltip="Random seed for reproducibility. -1 for random.",
                ),
                IO.String.Input(
                    "output_directory",
                    default="",
                    optional=True,
                    tooltip="Directory to save video. Empty uses ComfyUI output folder.",
                ),
            ],
            outputs=[
                IO.String.Output("video_path"),
            ],
        )


    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.client import GeminiClient

        client = kwargs.get("client")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "veo-3.1-generate-preview")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        duration_seconds = kwargs.get("duration_seconds", 8)
        person_generation = kwargs.get("person_generation", "allow_adult")
        enhance_prompt = kwargs.get("enhance_prompt", True)
        negative_prompt = kwargs.get("negative_prompt", "")
        seed = kwargs.get("seed", -1)
        output_directory = kwargs.get("output_directory", "")

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

            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "enhance_prompt": enhance_prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }

            if negative_prompt and negative_prompt.strip():
                config_params["negative_prompt"] = negative_prompt.strip()

            config = types.GenerateVideosConfig(**config_params)

            request_params = {
                "model": model,
                "prompt": prompt.strip(),
                "config": config,
            }

            if seed >= 0:
                request_params["seed"] = seed

            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = client.client.models.generate_videos(**request_params)

            poll_count = 0
            max_polls = 120  # 40 minutes max at 20s intervals
            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    raise TimeoutError("Video generation timed out after 40 minutes")

                print(f"[Veo] Waiting for video generation... ({poll_count * 20}s elapsed)")
                time.sleep(20)
                operation = client.client.operations.get(operation)

            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")

            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            if output_directory and output_directory.strip():
                out_dir = output_directory.strip()
            else:
                import folder_paths
                out_dir = folder_paths.get_output_directory()

            os.makedirs(out_dir, exist_ok=True)

            timestamp = int(time.time())
            filename = f"veo_{timestamp}.mp4"
            output_path = os.path.join(out_dir, filename)

            print(f"[Veo] Saving video to: {output_path}")

            if hasattr(video, 'save'):
                video.save(output_path)
            elif hasattr(video, 'uri') and video.uri:
                downloaded = client.client.files.download(file=video)
                downloaded.save(output_path)
            else:
                if hasattr(video, 'video_bytes') and video.video_bytes:
                    with open(output_path, 'wb') as f:
                        f.write(video.video_bytes)
                else:
                    raise ValueError("Could not extract video data from response")

            print(f"[Veo] Video saved successfully: {output_path}")
            return IO.NodeOutput(output_path)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)


class VeoImageToVideo(IO.ComfyNode):
    """Generates videos from an input image and optional text prompt.
    The image serves as the first frame or style reference."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="VeoImageToVideo",
            display_name="Veo Image to Video",
            category="ERPK/Gemini/Veo",
            description="Generate video from an image using Veo.",
            not_idempotent=True,
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    tooltip="Gemini API client from Gemini API Config node",
                ),
                IO.Image.Input(
                    "image",
                    tooltip="Input image to generate video from (first frame)",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Optional text description to guide the video generation",
                ),
                IO.Combo.Input(
                    "model",
                    options=VEO_MODELS,
                    default="veo-3.1-generate-preview",
                    optional=True,
                    tooltip="Veo model to use. Veo 3+ generates video with audio.",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=VEO_ASPECT_RATIOS,
                    default="16:9",
                    optional=True,
                    tooltip="Video aspect ratio (16:9 landscape, 9:16 portrait)",
                ),
                IO.Combo.Input(
                    "duration_seconds",
                    options=VEO_DURATIONS,
                    default=8,
                    optional=True,
                    tooltip="Video duration in seconds (5-8). Veo 3 defaults to 8.",
                ),
                IO.Combo.Input(
                    "person_generation",
                    options=VEO_PERSON_GENERATION_OPTIONS,
                    default="allow_adult",
                    optional=True,
                    tooltip="Person generation safety setting. Veo 3 only supports allow_all.",
                ),
                IO.Boolean.Input(
                    "enhance_prompt",
                    default=True,
                    optional=True,
                    tooltip="Let the model enhance your prompt for better results",
                ),
                IO.String.Input(
                    "negative_prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Elements to exclude from the video",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=0xffffffff,
                    optional=True,
                    control_after_generate=True,
                    tooltip="Random seed for reproducibility. -1 for random.",
                ),
                IO.String.Input(
                    "output_directory",
                    default="",
                    optional=True,
                    tooltip="Directory to save video. Empty uses ComfyUI output folder.",
                ),
            ],
            outputs=[
                IO.String.Output("video_path"),
            ],
        )


    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.client import GeminiClient
        from .gemini_api.utils import ImageConverter

        client = kwargs.get("client")
        image = kwargs.get("image")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "veo-3.1-generate-preview")
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        duration_seconds = kwargs.get("duration_seconds", 8)
        person_generation = kwargs.get("person_generation", "allow_adult")
        enhance_prompt = kwargs.get("enhance_prompt", True)
        negative_prompt = kwargs.get("negative_prompt", "")
        seed = kwargs.get("seed", -1)
        output_directory = kwargs.get("output_directory", "")

        try:
            from google.genai import types

            pil_image = ImageConverter.tensor_to_pil(image)
            print(f"[Veo] Input image size: {pil_image.size}")

            print(f"[Veo] Generating video from image with model: {model}")
            if prompt and prompt.strip():
                print(f"[Veo] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[Veo] Aspect ratio: {aspect_ratio}, Duration: {duration_seconds}s")

            config_params = {
                "number_of_videos": 1,
                "duration_seconds": duration_seconds,
                "enhance_prompt": enhance_prompt,
                "aspect_ratio": aspect_ratio,
                "person_generation": person_generation,
            }

            if negative_prompt and negative_prompt.strip():
                config_params["negative_prompt"] = negative_prompt.strip()

            config = types.GenerateVideosConfig(**config_params)

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pil_image.save(tmp.name, 'PNG')
                genai_image = types.Image.from_file(tmp.name)

            request_params = {
                "model": model,
                "image": genai_image,
                "config": config,
            }

            if prompt and prompt.strip():
                if len(prompt) > 2500:
                    print(f"[Veo] Warning: Prompt exceeds 2500 characters, truncating")
                    prompt = prompt[:2500]
                request_params["prompt"] = prompt.strip()

            if seed >= 0:
                request_params["seed"] = seed

            print("[Veo] Starting video generation (this may take several minutes)...")
            operation = client.client.models.generate_videos(**request_params)

            try:
                os.unlink(tmp.name)
            except Exception:
                pass

            poll_count = 0
            max_polls = 120  # 40 minutes max at 20s intervals
            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    raise TimeoutError("Video generation timed out after 40 minutes")

                print(f"[Veo] Waiting for video generation... ({poll_count * 20}s elapsed)")
                time.sleep(20)
                operation = client.client.operations.get(operation)

            if operation.error:
                raise ValueError(f"Video generation failed: {operation.error}")

            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")

            video = operation.response.generated_videos[0].video
            print(f"[Veo] Video generated successfully")

            if output_directory and output_directory.strip():
                out_dir = output_directory.strip()
            else:
                import folder_paths
                out_dir = folder_paths.get_output_directory()

            os.makedirs(out_dir, exist_ok=True)

            timestamp = int(time.time())
            filename = f"veo_i2v_{timestamp}.mp4"
            output_path = os.path.join(out_dir, filename)

            print(f"[Veo] Saving video to: {output_path}")

            if hasattr(video, 'save'):
                video.save(output_path)
            elif hasattr(video, 'uri') and video.uri:
                downloaded = client.client.files.download(file=video)
                downloaded.save(output_path)
            else:
                if hasattr(video, 'video_bytes') and video.video_bytes:
                    with open(output_path, 'wb') as f:
                        f.write(video.video_bytes)
                else:
                    raise ValueError("Could not extract video data from response")

            print(f"[Veo] Video saved successfully: {output_path}")
            return IO.NodeOutput(output_path)

        except Exception as e:
            error_msg = f"Failed to generate video: {str(e)}"
            print(f"[Veo] Error: {error_msg}")
            raise ValueError(error_msg)
