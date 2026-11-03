# ABOUTME: ComfyUI V3 node for analyzing images using Claude's multimodal vision capabilities.
# ABOUTME: Sends every image of both batches (up to 600) with configurable detail levels.

from comfy_api.latest import IO

from .models import INHERIT_FROM_CLIENT, TEXT_MODELS, effort_input, effort_kwargs


class ClaudeVisionAnalysis(IO.ComfyNode):
    """Analyzes images using Claude's vision capabilities."""

    # Measured 2026-11-03: 600 images returned 200, 601 returned 400. Each side
    # may be 8000 px, but only 3000 px once a request has more than 20 images.
    MAX_IMAGES = 600
    MANY_IMAGES = 20
    MAX_SIDE = 8000
    MAX_SIDE_MANY_IMAGES = 3000

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
                    tooltip="Images to analyze. The node sends every image in the batch.",
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
                IO.Combo.Input(
                    "model",
                    options=[INHERIT_FROM_CLIENT] + TEXT_MODELS,
                    default=INHERIT_FROM_CLIENT,
                    optional=True,
                    tooltip="Override the client's model for this vision call.",
                ),
                IO.Image.Input(
                    "additional_images",
                    optional=True,
                    tooltip="Optional additional images, all sent after the primary batch. Up to 600 images in total; above 20, each is resized to at most 3000 px on its longest side.",
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
                    default=8192,
                    min=256,
                    max=128000,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of analysis. Thinking counts toward this limit. Current Claude models allow up to 128K.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for cache control. Randomizes by default to ensure fresh results each run.",
                ),
                effort_input(),
            ],
            outputs=[
                IO.String.Output("analysis"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.client import ClaudeClient, response_text
        from .claude_api.utils import ImageConverter

        image = kwargs.get("image")
        question = kwargs.get("question", "")
        client = kwargs.get("client")
        additional_images = kwargs.get("additional_images")
        detail_level = kwargs.get("detail_level", "high")
        max_tokens = kwargs.get("max_tokens", 8192)
        model = kwargs.get("model", "(inherit from client)")

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

            send_kwargs = {
                "messages": messages,
                "system": system,
                "max_tokens": max_tokens,
                **effort_kwargs(kwargs.get("effort")),
            }
            if model and model != "(inherit from client)":
                send_kwargs["model"] = model

            response = await client.send_request(**send_kwargs)

            analysis_text = response_text(response)

            print(f"[Claude] Analysis completed ({len(analysis_text)} characters)")
            return IO.NodeOutput(analysis_text)

        except Exception as e:
            error_msg = f"Failed to analyze image(s): {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def _prepare_images(cls, image_converter, primary_image, additional_images=None):
        """Base64-encode every image of both batches, resized to the side limit
        that applies to this many images."""
        frames = cls._frames(primary_image)
        if additional_images is not None:
            frames += cls._frames(additional_images)
        if len(frames) > cls.MAX_IMAGES:
            raise ValueError(f"Claude accepts at most {cls.MAX_IMAGES} images per request; got {len(frames)}")
        max_side = cls.MAX_SIDE if len(frames) <= cls.MANY_IMAGES else cls.MAX_SIDE_MANY_IMAGES

        images = []
        for number, frame in enumerate(frames, start=1):
            pil_image = image_converter.tensor_to_pil(frame)
            width, height = pil_image.size
            if max(width, height) > max_side:
                print(f"[Claude] Image {number} of {len(frames)}: resizing {width}x{height} to fit {max_side}px")
                pil_image = image_converter.resize_if_needed(pil_image, max_dimension=max_side)
            try:
                images.append(image_converter.encode_and_validate_for_claude(pil_image, format="PNG"))
            except ValueError as e:
                raise ValueError(f"Image {number} of {len(frames)}: {e}") from e
        return images

    @staticmethod
    def _frames(images):
        """One [H, W, C] tensor per image of a ComfyUI [B, H, W, C] batch."""
        if len(images.shape) == 4:
            return [images[i] for i in range(images.shape[0])]
        return [images]

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
