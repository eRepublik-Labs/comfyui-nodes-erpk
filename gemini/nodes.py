# ABOUTME: ComfyUI nodes for Google Gemini API integration
# ABOUTME: Provides text generation, vision, chat, and configuration nodes

from .gemini_api.client import GeminiClient
from .gemini_api.utils import ImageConverter, SafetySettings


class GeminiAPIConfig:
    """
    Gemini API Configuration Node

    Initializes and provides a Gemini API client for use by other nodes.
    Handles API key configuration and model selection.
    """

    @classmethod
    def INPUT_TYPES(cls):
        model_descriptions = "\n".join([f"{k}: {v}" for k, v in GeminiClient.MODELS.items()])
        return {
            "required": {
                "model": (
                    list(GeminiClient.MODELS.keys()),
                    {
                        "default": GeminiClient.DEFAULT_MODEL,
                        "tooltip": f"Gemini model to use:\n{model_descriptions}"
                    }
                ),
            },
            "optional": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Google API key. If empty, will use GOOGLE_API_KEY env var or config.ini."
                    }
                ),
            }
        }

    RETURN_TYPES = ("GEMINI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "create_client"
    CATEGORY = "ERPK/Gemini"

    def create_client(self, model: str, api_key: str = ""):
        """
        Create and return a Gemini API client.

        Args:
            model: Gemini model to use
            api_key: Optional API key

        Returns:
            Tuple containing the client instance
        """
        try:
            client = GeminiClient(
                api_key=api_key if api_key.strip() else None,
                model=model
            )

            print(f"[Gemini] Client initialized with model: {model}")

            return (client,)

        except Exception as e:
            error_msg = f"Failed to create Gemini client: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiTextGeneration:
    """
    Gemini Text Generation Node

    General-purpose text generation for various tasks including:
    - Text completion and expansion
    - Creative writing
    - Text transformation
    - Content generation
    """

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
                        "tooltip": "Text prompt for Gemini"
                    }
                ),
            },
            "optional": {
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.7,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Creativity level (0.0=focused, 2.0=very creative)"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 8192,
                        "min": 256,
                        "max": 8192,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/Gemini"

    def generate(
        self,
        client: GeminiClient,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ):
        """
        Generate text using Gemini.

        Args:
            client: Gemini API client
            prompt: User prompt
            temperature: Creativity level
            max_tokens: Max output tokens

        Returns:
            Tuple containing generated text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            response = client.generate_content(
                prompt=prompt.strip(),
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by safety filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[Gemini] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[Gemini] Text generated successfully ({len(text)} characters)")

            return (text,)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiChat:
    """
    Gemini Chat Node

    Maintains multi-turn conversations with Gemini, preserving message history
    across multiple node executions.
    """

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
                        "tooltip": "Your message in the conversation"
                    }
                ),
            },
            "optional": {
                "chat_session": (
                    "GEMINI_CHAT_SESSION",
                    {"tooltip": "Previous chat session (connect from previous chat node)"}
                ),
                "reset_conversation": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Start a new conversation, discarding history"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.7,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Creativity level"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 8192,
                        "min": 256,
                        "max": 8192,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "GEMINI_CHAT_SESSION")
    RETURN_NAMES = ("response", "chat_session")
    FUNCTION = "chat"
    CATEGORY = "ERPK/Gemini"

    def chat(
        self,
        client: GeminiClient,
        prompt: str,
        chat_session=None,
        reset_conversation: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ):
        """
        Continue or start a conversation with Gemini.

        Args:
            client: Gemini API client
            prompt: User message
            chat_session: Previous chat session
            reset_conversation: Start new conversation
            temperature: Creativity level
            max_tokens: Max output tokens

        Returns:
            Tuple containing (response text, chat session)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Start new session or use existing
            if reset_conversation or chat_session is None:
                # Update client config with temperature/max_tokens before starting chat
                from google.genai import types
                config = types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
                # Temporarily store config and start chat
                original_config = (client.system_instruction, client.safety_settings)
                chat_session = client.start_chat()
                print("[Gemini] Started new conversation")
            else:
                print(f"[Gemini] Continuing conversation")

            # Send message and get response
            from google.genai import types
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            response = chat_session.send_message(
                prompt.strip(),
                config=config
            )

            text = response.text
            print(f"[Gemini] Chat response generated ({len(text)} characters)")

            return (text, chat_session)

        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiVision:
    """
    Gemini Vision Analysis Node

    Uses Gemini's vision capabilities to analyze images and answer questions about them.
    Supports single or multiple images.
    """

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
                    {"tooltip": "Image(s) to analyze (ComfyUI tensor)"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Describe this image in detail.",
                        "tooltip": "Question or instruction about the image(s)"
                    }
                ),
            },
            "optional": {
                "max_tokens": (
                    "INT",
                    {
                        "default": 8192,
                        "min": 256,
                        "max": 8192,
                        "step": 128,
                        "tooltip": "Maximum length of analysis"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.4,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Creativity level (lower=more factual)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("analysis",)
    FUNCTION = "analyze"
    CATEGORY = "ERPK/Gemini"

    def analyze(
        self,
        client: GeminiClient,
        image,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.4
    ):
        """
        Analyze image(s) using Gemini's vision capabilities.

        Args:
            client: Gemini API client
            image: Image tensor(s)
            prompt: Question or instruction about images
            max_tokens: Max output tokens
            temperature: Creativity level

        Returns:
            Tuple containing analysis text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Convert tensor(s) to PIL images
            pil_images = ImageConverter.tensors_to_pil_list(image)
            print(f"[Gemini] Analyzing {len(pil_images)} image(s)")

            # Generate content with images
            response = client.generate_content(
                prompt=prompt.strip(),
                images=pil_images,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by safety filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[Gemini] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[Gemini] Vision analysis completed ({len(text)} characters)")

            return (text,)

        except Exception as e:
            error_msg = f"Failed to analyze image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiSystemInstruction:
    """
    Gemini System Instruction Node

    Sets a system-level instruction that persists across all requests
    for a Gemini client. System instructions guide the model's behavior.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client to configure"}
                ),
                "system_instruction": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "System-level instruction to guide model behavior"
                    }
                ),
            }
        }

    RETURN_TYPES = ("GEMINI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "set_instruction"
    CATEGORY = "ERPK/Gemini"

    def set_instruction(self, client: GeminiClient, system_instruction: str):
        """
        Set system instruction for the client.

        Args:
            client: Gemini API client
            system_instruction: System instruction text

        Returns:
            Tuple containing the updated client
        """
        try:
            instruction = system_instruction.strip() if system_instruction else None

            if instruction:
                client.update_config(system_instruction=instruction)
                print(f"[Gemini] System instruction set ({len(instruction)} characters)")
            else:
                print("[Gemini] Warning: Empty system instruction, skipping")

            return (client,)

        except Exception as e:
            error_msg = f"Failed to set system instruction: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiSafetySettings:
    """
    Gemini Safety Settings Node

    Configures content safety filters for Gemini API requests.
    Controls blocking thresholds for different harm categories.
    """

    @classmethod
    def INPUT_TYPES(cls):
        threshold_options = ["none", "low", "medium", "high"]
        return {
            "required": {
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client to configure"}
                ),
            },
            "optional": {
                "preset": (
                    ["balanced", "strict", "permissive", "custom"],
                    {
                        "default": "balanced",
                        "tooltip": "Safety preset or custom configuration"
                    }
                ),
                "harassment": (
                    threshold_options,
                    {
                        "default": "medium",
                        "tooltip": "Threshold for harassment content (only used if preset=custom)"
                    }
                ),
                "hate_speech": (
                    threshold_options,
                    {
                        "default": "medium",
                        "tooltip": "Threshold for hate speech (only used if preset=custom)"
                    }
                ),
                "sexually_explicit": (
                    threshold_options,
                    {
                        "default": "medium",
                        "tooltip": "Threshold for sexually explicit content (only used if preset=custom)"
                    }
                ),
                "dangerous_content": (
                    threshold_options,
                    {
                        "default": "medium",
                        "tooltip": "Threshold for dangerous content (only used if preset=custom)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("GEMINI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "configure_safety"
    CATEGORY = "ERPK/Gemini"

    def configure_safety(
        self,
        client: GeminiClient,
        preset: str = "balanced",
        harassment: str = "medium",
        hate_speech: str = "medium",
        sexually_explicit: str = "medium",
        dangerous_content: str = "medium"
    ):
        """
        Configure safety settings for the client.

        Args:
            client: Gemini API client
            preset: Safety preset (balanced/strict/permissive/custom)
            harassment: Harassment threshold (for custom preset)
            hate_speech: Hate speech threshold (for custom preset)
            sexually_explicit: Sexually explicit threshold (for custom preset)
            dangerous_content: Dangerous content threshold (for custom preset)

        Returns:
            Tuple containing the updated client
        """
        try:
            # Get safety settings
            if preset == "custom":
                safety_settings = SafetySettings.create_settings(
                    harassment=harassment,
                    hate_speech=hate_speech,
                    sexually_explicit=sexually_explicit,
                    dangerous_content=dangerous_content
                )
                print(f"[Gemini] Custom safety settings configured")
            else:
                safety_settings = SafetySettings.get_preset(preset)
                print(f"[Gemini] Safety preset '{preset}' configured")

            # Update client with safety settings
            client.update_config(safety_settings=safety_settings)

            return (client,)

        except Exception as e:
            error_msg = f"Failed to configure safety settings: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiImageGeneration:
    """
    Gemini Image Generation Node

    Generates images using Gemini's image generation models.
    Uses dedicated image generation models like gemini-2.5-flash-image.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Only include image generation models
        image_models = {
            "gemini-2.5-flash-image": "Gemini 2.5 Flash Image (Recommended)",
            "gemini-2.5-flash-image-preview": "Gemini 2.5 Flash Image Preview (Experimental)",
        }

        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Description of the image to generate"
                    }
                ),
            },
            "optional": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Google API key (uses env/config if empty)"
                    }
                ),
                "model": (
                    list(image_models.keys()),
                    {
                        "default": "gemini-2.5-flash-image",
                        "tooltip": "Image generation model"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.1,
                        "tooltip": "Creativity level (higher = more creative)"
                    }
                ),
                "aspect_ratio": (
                    ["default", "1:1", "9:16", "16:9", "4:3", "3:4"],
                    {
                        "default": "default",
                        "tooltip": "Image aspect ratio (default uses model's default)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"
    CATEGORY = "ERPK/Gemini"

    def generate_image(
        self,
        prompt: str,
        api_key: str = "",
        model: str = "gemini-2.5-flash-image",
        temperature: float = 1.0,
        aspect_ratio: str = "default"
    ):
        """
        Generate an image using Gemini's image generation models.

        Args:
            prompt: Text description of image to generate
            api_key: Optional API key
            model: Image generation model to use
            temperature: Creativity level
            aspect_ratio: Image aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4, or default)

        Returns:
            Tuple containing generated image tensor
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Create a temporary client for image generation
            client = GeminiClient(
                api_key=api_key if api_key.strip() else None,
                model=model
            )

            print(f"[Gemini] Generating image with model: {model}")
            print(f"[Gemini] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if aspect_ratio != "default":
                print(f"[Gemini] Aspect ratio: {aspect_ratio}")

            # Build generation config
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
            )

            # Add aspect ratio if specified
            if aspect_ratio != "default":
                config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)

            # Generate content using NEW SDK
            response = client.client.models.generate_content(
                model=client.model_name,
                contents=[prompt.strip()],
                config=config
            )

            # Extract image from response
            image_tensor = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    # Check if data is empty
                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    # Convert bytes to tensor
                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image generated successfully: {image_tensor.shape}")
                        break
                    elif isinstance(image_data, str):
                        # Handle base64 string if needed
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image generated successfully: {image_tensor.shape}")
                            break

            if image_tensor is None:
                # Provide helpful error message based on what we found
                error_parts = ["No image was generated."]

                # Check if we got text instead
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            error_parts.append(f"Model returned text: {part.text[:100]}")

                # Check finish reason
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    error_parts.append(f"Finish reason: {finish_reason}")

                # Check if blocked
                if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                    error_parts.append(f"Blocked: {response.prompt_feedback.block_reason}")

                raise ValueError(" ".join(error_parts))

            return (image_tensor,)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiImageEdit:
    """
    Gemini Image Editing Node

    Uses Gemini's image generation models to edit/modify existing images based on text prompts.
    Supports 1-3 input images for best results.
    """

    # Same image generation models as GeminiImageGeneration
    image_models = {
        "gemini-2.5-flash-image": "Gemini 2.5 Flash Image (Recommended)",
        "gemini-2.5-flash-image-preview": "Gemini 2.5 Flash Image Preview (Experimental)",
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    "IMAGE",
                    {"tooltip": "Input image(s) to edit (supports 1-3 images)"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Description of how to modify the image(s)"
                    }
                ),
            },
            "optional": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Google API key (uses env/config if empty)"
                    }
                ),
                "model": (
                    list(cls.image_models.keys()),
                    {
                        "default": "gemini-2.5-flash-image",
                        "tooltip": "Image generation model"
                    }
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.1,
                        "tooltip": "Creativity level (higher = more creative)"
                    }
                ),
                "aspect_ratio": (
                    ["default", "1:1", "9:16", "16:9", "4:3", "3:4"],
                    {
                        "default": "default",
                        "tooltip": "Image aspect ratio (default uses model's default)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "edit_image"
    CATEGORY = "ERPK/Gemini"

    def edit_image(
        self,
        image,
        prompt: str,
        api_key: str = "",
        model: str = "gemini-2.5-flash-image",
        temperature: float = 1.0,
        aspect_ratio: str = "default"
    ):
        """
        Edit an image using Gemini's image generation models.

        Args:
            image: Input image(s) as ComfyUI tensor
            prompt: Text description of how to modify the image
            api_key: Optional API key
            model: Image generation model to use
            temperature: Creativity level
            aspect_ratio: Image aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4, or default)

        Returns:
            Tuple containing edited image tensor
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Create a temporary client for image editing
            client = GeminiClient(
                api_key=api_key if api_key.strip() else None,
                model=model
            )

            # Convert ComfyUI tensors to PIL images
            pil_images = ImageConverter.tensors_to_pil_list(image)
            num_images = len(pil_images)

            print(f"[Gemini] Editing image with model: {model}")
            print(f"[Gemini] Number of input images: {num_images}")
            print(f"[Gemini] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if aspect_ratio != "default":
                print(f"[Gemini] Aspect ratio: {aspect_ratio}")

            # Warn if using more than 3 images (API works best with 1-3)
            if num_images > 3:
                print(f"[Gemini] Warning: Using {num_images} images. API works best with 1-3 images.")

            # Build generation config
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
            )

            # Add aspect ratio if specified
            if aspect_ratio != "default":
                config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)

            # Build content list: images first, then prompt
            contents = pil_images + [prompt.strip()]

            # Generate content using NEW SDK
            response = client.client.models.generate_content(
                model=client.model_name,
                contents=contents,
                config=config
            )

            # Extract image from response
            image_tensor = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    # Check if data is empty
                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    # Convert bytes to tensor
                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image edited successfully: {image_tensor.shape}")
                        break
                    elif isinstance(image_data, str):
                        # Handle base64 string if needed
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image edited successfully: {image_tensor.shape}")
                            break

            if image_tensor is None:
                # Provide helpful error message
                error_parts = ["No image was generated."]

                # Check if we got text instead
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            error_parts.append(f"Model returned text: {part.text[:100]}")

                # Check finish reason
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    error_parts.append(f"Finish reason: {finish_reason}")

                # Check if blocked
                if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                    error_parts.append(f"Blocked: {response.prompt_feedback.block_reason}")

                raise ValueError(" ".join(error_parts))

            return (image_tensor,)

        except Exception as e:
            error_msg = f"Failed to edit image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


# Node registration
NODE_CLASS_MAPPINGS = {
    "GeminiAPIConfig": GeminiAPIConfig,
    "GeminiTextGeneration": GeminiTextGeneration,
    "GeminiChat": GeminiChat,
    "GeminiVision": GeminiVision,
    "GeminiSystemInstruction": GeminiSystemInstruction,
    "GeminiSafetySettings": GeminiSafetySettings,
    "GeminiImageGeneration": GeminiImageGeneration,
    "GeminiImageEdit": GeminiImageEdit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiAPIConfig": "Gemini API Config",
    "GeminiTextGeneration": "Gemini Text Generation",
    "GeminiChat": "Gemini Chat",
    "GeminiVision": "Gemini Vision",
    "GeminiSystemInstruction": "Gemini System Instruction",
    "GeminiSafetySettings": "Gemini Safety Settings",
    "GeminiImageGeneration": "Gemini Image Generation",
    "GeminiImageEdit": "Gemini Image Edit",
}
