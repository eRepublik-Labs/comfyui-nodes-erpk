# ABOUTME: ComfyUI V3 node for analyzing images using Claude's multimodal vision capabilities.
# ABOUTME: Supports single or multiple images (up to 20) with configurable detail levels.

from comfy_api.latest import IO


class ClaudeVisionAnalysis(IO.ComfyNode):
    """Analyzes images using Claude's vision capabilities."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeVisionAnalysis",
            display_name="Claude Vision Analysis",
            category="ERPK/Claude",
            description="Analyze images using Claude's multimodal vision capabilities.",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip="Primary image to analyze (ComfyUI tensor)",
                ),
                IO.String.Input(
                    "question",
                    multiline=True,
                    default="Describe this image in detail.",
                    tooltip="Question or instruction about the image(s)",
                ),
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Claude API client (optional if API key is configured in Settings)",
                ),
                IO.Image.Input(
                    "additional_images",
                    optional=True,
                    tooltip="Optional additional images (up to 19 more, for 20 total)",
                ),
                IO.Combo.Input(
                    "detail_level",
                    options=["low", "medium", "high"],
                    default="high",
                    optional=True,
                    tooltip="Level of detail in analysis",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=2048,
                    min=256,
                    max=4096,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of analysis",
                ),
                IO.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for cache control. Randomizes by default to ensure fresh results each run.",
                ),
            ],
            outputs=[
                IO.String.Output("analysis"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.client import ClaudeClient
        from .claude_api.utils import ImageConverter

        image = kwargs.get("image")
        question = kwargs.get("question", "")
        client = kwargs.get("client")
        additional_images = kwargs.get("additional_images")
        detail_level = kwargs.get("detail_level", "high")
        max_tokens = kwargs.get("max_tokens", 2048)

        if client is None:
            client = ClaudeClient(api_key=None)

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            images_base64 = cls._prepare_images(ImageConverter, image, additional_images)
            print(f"[Claude] Analyzing {len(images_base64)} image(s)")

            content = cls._build_multimodal_content(images_base64, question)
            messages = [{"role": "user", "content": content}]
            system = cls._build_system_prompt(detail_level)

            response = client.send_request(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=0.7,
            )

            if hasattr(response, 'content') and len(response.content) > 0:
                analysis_text = response.content[0].text
            else:
                raise ValueError("Invalid response format from Claude API")

            print(f"[Claude] Analysis completed ({len(analysis_text)} characters)")
            return IO.NodeOutput(analysis_text)

        except Exception as e:
            error_msg = f"Failed to analyze image(s): {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def _prepare_images(cls, image_converter, primary_image, additional_images=None):
        """Prepare images for API by converting to base64."""
        images = []

        try:
            pil_image = image_converter.tensor_to_pil(primary_image)
            is_valid, error = image_converter.validate_image_for_claude(pil_image)
            if not is_valid:
                print(f"[Claude] Warning: {error}. Attempting to resize...")
                pil_image = image_converter.resize_if_needed(pil_image, max_dimension=8000)
            base64_str = image_converter.pil_to_base64(pil_image, format="PNG")
            images.append(base64_str)
        except Exception as e:
            raise ValueError(f"Failed to process primary image: {str(e)}")

        if additional_images is not None:
            try:
                import torch
                if isinstance(additional_images, torch.Tensor):
                    if len(additional_images.shape) == 4:
                        batch_size = additional_images.shape[0]
                        for i in range(min(batch_size, 19)):
                            single_image = additional_images[i:i+1]
                            pil_image = image_converter.tensor_to_pil(single_image)
                            is_valid, error = image_converter.validate_image_for_claude(pil_image)
                            if not is_valid:
                                print(f"[Claude] Warning for image {i+2}: {error}. Resizing...")
                                pil_image = image_converter.resize_if_needed(pil_image, max_dimension=8000)
                            base64_str = image_converter.pil_to_base64(pil_image, format="PNG")
                            images.append(base64_str)
                    else:
                        pil_image = image_converter.tensor_to_pil(additional_images)
                        is_valid, error = image_converter.validate_image_for_claude(pil_image)
                        if not is_valid:
                            print(f"[Claude] Warning: {error}. Resizing...")
                            pil_image = image_converter.resize_if_needed(pil_image, max_dimension=8000)
                        base64_str = image_converter.pil_to_base64(pil_image, format="PNG")
                        images.append(base64_str)
            except Exception as e:
                print(f"[Claude] Warning: Failed to process additional images: {str(e)}")

        if len(images) > 20:
            print(f"[Claude] Warning: Too many images ({len(images)}). Using first 20.")
            images = images[:20]

        return images

    @classmethod
    def _build_multimodal_content(cls, images_base64, question):
        """Build multimodal content array for API (images before text)."""
        content = []
        for base64_str in images_base64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_str,
                },
            })
        content.append({"type": "text", "text": question})
        return content

    @classmethod
    def _build_system_prompt(cls, detail_level):
        """Build system prompt based on detail level."""
        prompts = {
            "low": "You are an image analysis assistant. Provide concise, focused responses about images.",
            "medium": "You are an image analysis expert. Provide clear, detailed responses about images with relevant observations and insights.",
            "high": "You are an expert image analyst. Provide comprehensive, detailed analysis of images including composition, content, style, mood, technical qualities, and any other relevant aspects. Be thorough and precise in your observations.",
        }
        return prompts.get(detail_level, prompts["high"])
