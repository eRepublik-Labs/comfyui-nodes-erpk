"""
Claude Vision Analysis Node

Analyzes images using Claude's multimodal capabilities.
"""

from .claude_api.client import ClaudeClient
from .claude_api.utils import ImageConverter


class ClaudeVisionAnalysis:
    """
    Claude Vision Analysis Node

    Uses Claude's vision capabilities to analyze images and answer questions about them.

    Supports:
    - Single or multiple images (up to 20)
    - Image description and captioning
    - Visual question answering
    - Detailed image analysis
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "CLAUDE_API_CLIENT",
                    {"tooltip": "Claude API client from Claude API Client node"}
                ),
                "image": (
                    "IMAGE",
                    {"tooltip": "Primary image to analyze (ComfyUI tensor)"}
                ),
                "question": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Describe this image in detail.",
                        "tooltip": "Question or instruction about the image(s)"
                    }
                ),
            },
            "optional": {
                "additional_images": (
                    "IMAGE",
                    {"tooltip": "Optional additional images (up to 19 more, for 20 total)"}
                ),
                "detail_level": (
                    ["low", "medium", "high"],
                    {
                        "default": "high",
                        "tooltip": "Level of detail in analysis"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 256,
                        "max": 4096,
                        "step": 128,
                        "tooltip": "Maximum length of analysis"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("analysis",)
    FUNCTION = "analyze"
    CATEGORY = "ERPK/Claude"

    def analyze(
        self,
        client: ClaudeClient,
        image,
        question: str,
        additional_images=None,
        detail_level: str = "high",
        max_tokens: int = 2048
    ):
        """
        Analyze image(s) using Claude's vision capabilities.

        Args:
            client: Claude API client
            image: Primary image tensor
            question: Question or instruction about images
            additional_images: Optional additional image tensors
            detail_level: Analysis detail level
            max_tokens: Max output tokens

        Returns:
            Tuple containing analysis text
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            # Convert images to base64
            images_base64 = self._prepare_images(image, additional_images)

            print(f"[Claude] Analyzing {len(images_base64)} image(s)")

            # Build multimodal content
            content = self._build_multimodal_content(images_base64, question)

            # Build messages
            messages = [
                {"role": "user", "content": content}
            ]

            # Build system prompt based on detail level
            system = self._build_system_prompt(detail_level)

            # Send request
            response = client.send_request(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=0.7
            )

            # Extract analysis text
            if hasattr(response, 'content') and len(response.content) > 0:
                analysis_text = response.content[0].text
            else:
                raise ValueError("Invalid response format from Claude API")

            print(f"[Claude] Analysis completed ({len(analysis_text)} characters)")

            return (analysis_text,)

        except Exception as e:
            error_msg = f"Failed to analyze image(s): {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    def _prepare_images(self, primary_image, additional_images=None) -> list:
        """
        Prepare images for API by converting to base64.

        Args:
            primary_image: Primary image tensor
            additional_images: Optional additional image tensors

        Returns:
            List of base64 encoded images

        Raises:
            ValueError: If too many images or invalid images
        """
        images = []

        # Convert primary image
        try:
            pil_image = ImageConverter.tensor_to_pil(primary_image)

            # Validate and resize if needed
            is_valid, error = ImageConverter.validate_image_for_claude(pil_image)
            if not is_valid:
                print(f"[Claude] Warning: {error}. Attempting to resize...")
                pil_image = ImageConverter.resize_if_needed(pil_image, max_dimension=8000)

            # Convert to base64
            base64_str = ImageConverter.pil_to_base64(pil_image, format="PNG")
            images.append(base64_str)

        except Exception as e:
            raise ValueError(f"Failed to process primary image: {str(e)}")

        # Convert additional images if provided
        if additional_images is not None:
            try:
                # Handle batch dimension
                import torch
                if isinstance(additional_images, torch.Tensor):
                    # If batched, process each image
                    if len(additional_images.shape) == 4:
                        batch_size = additional_images.shape[0]
                        for i in range(min(batch_size, 19)):  # Max 19 additional (20 total)
                            single_image = additional_images[i:i+1]
                            pil_image = ImageConverter.tensor_to_pil(single_image)

                            # Validate and resize
                            is_valid, error = ImageConverter.validate_image_for_claude(pil_image)
                            if not is_valid:
                                print(f"[Claude] Warning for image {i+2}: {error}. Resizing...")
                                pil_image = ImageConverter.resize_if_needed(pil_image, max_dimension=8000)

                            base64_str = ImageConverter.pil_to_base64(pil_image, format="PNG")
                            images.append(base64_str)
                    else:
                        # Single additional image
                        pil_image = ImageConverter.tensor_to_pil(additional_images)
                        is_valid, error = ImageConverter.validate_image_for_claude(pil_image)
                        if not is_valid:
                            print(f"[Claude] Warning: {error}. Resizing...")
                            pil_image = ImageConverter.resize_if_needed(pil_image, max_dimension=8000)

                        base64_str = ImageConverter.pil_to_base64(pil_image, format="PNG")
                        images.append(base64_str)

            except Exception as e:
                print(f"[Claude] Warning: Failed to process additional images: {str(e)}")

        # Check total count
        if len(images) > 20:
            print(f"[Claude] Warning: Too many images ({len(images)}). Using first 20.")
            images = images[:20]

        return images

    def _build_multimodal_content(self, images_base64: list, question: str) -> list:
        """
        Build multimodal content array for API.

        Claude prefers images before text for best results.

        Args:
            images_base64: List of base64 encoded images
            question: Question about the images

        Returns:
            Content array with images and text
        """
        content = []

        # Add all images first
        for base64_str in images_base64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_str
                }
            })

        # Add text question after images
        content.append({
            "type": "text",
            "text": question
        })

        return content

    def _build_system_prompt(self, detail_level: str) -> str:
        """
        Build system prompt based on detail level.

        Args:
            detail_level: low, medium, or high

        Returns:
            System prompt
        """
        prompts = {
            "low": "You are an image analysis assistant. Provide concise, focused responses about images.",
            "medium": "You are an image analysis expert. Provide clear, detailed responses about images with relevant observations and insights.",
            "high": "You are an expert image analyst. Provide comprehensive, detailed analysis of images including composition, content, style, mood, technical qualities, and any other relevant aspects. Be thorough and precise in your observations."
        }

        return prompts.get(detail_level, prompts["high"])


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudeVisionAnalysis": ClaudeVisionAnalysis,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeVisionAnalysis": "Claude Vision Analysis",
}
