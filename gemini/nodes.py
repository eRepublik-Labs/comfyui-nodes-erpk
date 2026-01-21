# ABOUTME: ComfyUI nodes for Google Gemini API integration
# ABOUTME: Provides text generation, vision, chat, and configuration nodes

from .gemini_api.client import GeminiClient
from .gemini_api.utils import ImageConverter, SafetySettings


class GeminiAPIConfig:
    """
    Gemini API Configuration Node

    Initializes and provides a Gemini API client for use by other nodes.
    Handles API key configuration. Each node selects its own model.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
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

    def create_client(self, api_key: str = ""):
        """
        Create and return a Gemini API client.

        Args:
            api_key: Optional API key

        Returns:
            Tuple containing the client instance
        """
        try:
            client = GeminiClient(
                api_key=api_key if api_key.strip() else None
            )

            print(f"[Gemini] Client initialized")

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

    # Text generation models
    TEXT_MODELS = list(GeminiClient.MODELS.keys())

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
                "model": (
                    cls.TEXT_MODELS,
                    {
                        "default": GeminiClient.DEFAULT_MODEL,
                        "tooltip": "Gemini model to use for generation"
                    }
                ),
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
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.95,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling - cumulative probability threshold (0.0=disabled)"
                    }
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 40,
                        "min": 0,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Top-k sampling - limit token selection (0=disabled)"
                    }
                ),
                "stop_sequences": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Stop generation at these sequences (one per line, leave empty to disable)"
                    }
                ),
                "response_mime_type": (
                    ["default", "text/plain", "application/json"],
                    {
                        "default": "default",
                        "tooltip": "Output format (use application/json for JSON mode)"
                    }
                ),
                "response_schema": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "JSON schema for structured output (only used with application/json, leave empty for free-form JSON)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for text generation
        return float("nan")

    def generate(
        self,
        client: GeminiClient,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: str = "",
        response_mime_type: str = "default",
        response_schema: str = ""
    ):
        """
        Generate text using Gemini.

        Args:
            client: Gemini API client
            prompt: User prompt
            model: Gemini model to use
            temperature: Creativity level
            max_tokens: Max output tokens
            top_p: Nucleus sampling threshold (0.0 to disable)
            top_k: Top-k sampling limit (0 to disable)
            stop_sequences: Newline-separated stop sequences
            response_mime_type: Output format (default/text/plain/application/json)
            response_schema: JSON schema for structured output

        Returns:
            Tuple containing generated text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Use specified model or default
        if model is None:
            model = GeminiClient.DEFAULT_MODEL

        # Parse stop sequences (one per line)
        stop_seq_list = None
        if stop_sequences and stop_sequences.strip():
            stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]

        # Parse response schema if provided
        schema_obj = None
        if response_schema and response_schema.strip():
            import json
            try:
                schema_obj = json.loads(response_schema.strip())
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON schema: {str(e)}")

        try:
            response = client.generate_content(
                prompt=prompt.strip(),
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p > 0.0 else None,
                top_k=top_k if top_k > 0 else None,
                stop_sequences=stop_seq_list,
                response_mime_type=response_mime_type if response_mime_type != "default" else None,
                response_schema=schema_obj
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

    # Text generation models
    TEXT_MODELS = list(GeminiClient.MODELS.keys())

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
                "model": (
                    cls.TEXT_MODELS,
                    {
                        "default": GeminiClient.DEFAULT_MODEL,
                        "tooltip": "Gemini model to use for chat"
                    }
                ),
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
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.95,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling - cumulative probability threshold (0.0=disabled)"
                    }
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 40,
                        "min": 0,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Top-k sampling - limit token selection (0=disabled)"
                    }
                ),
                "stop_sequences": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Stop generation at these sequences (one per line, leave empty to disable)"
                    }
                ),
                "response_mime_type": (
                    ["default", "text/plain", "application/json"],
                    {
                        "default": "default",
                        "tooltip": "Output format (use application/json for JSON mode)"
                    }
                ),
                "response_schema": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "JSON schema for structured output (only used with application/json, leave empty for free-form JSON)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "GEMINI_CHAT_SESSION")
    RETURN_NAMES = ("response", "chat_session")
    FUNCTION = "chat"
    CATEGORY = "ERPK/Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for chat
        return float("nan")

    def chat(
        self,
        client: GeminiClient,
        prompt: str,
        model: str = None,
        chat_session=None,
        reset_conversation: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: str = "",
        response_mime_type: str = "default",
        response_schema: str = ""
    ):
        """
        Continue or start a conversation with Gemini.

        Args:
            client: Gemini API client
            prompt: User message
            model: Gemini model to use
            chat_session: Previous chat session
            reset_conversation: Start new conversation
            temperature: Creativity level
            max_tokens: Max output tokens
            top_p: Nucleus sampling threshold (0.0 to disable)
            top_k: Top-k sampling limit (0 to disable)
            stop_sequences: Newline-separated stop sequences
            response_mime_type: Output format (default/text/plain/application/json)
            response_schema: JSON schema for structured output

        Returns:
            Tuple containing (response text, chat session)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Use specified model or default
        if model is None:
            model = GeminiClient.DEFAULT_MODEL

        try:
            # Start new session or use existing
            if reset_conversation or chat_session is None:
                chat_session = client.start_chat(model=model)
                print(f"[Gemini] Started new conversation with {model}")
            else:
                print(f"[Gemini] Continuing conversation")

            # Send message and get response
            from google.genai import types
            import json

            # Parse stop sequences (one per line)
            stop_seq_list = None
            if stop_sequences and stop_sequences.strip():
                stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]

            # Parse response schema if provided
            schema_obj = None
            if response_schema and response_schema.strip():
                try:
                    schema_obj = json.loads(response_schema.strip())
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON schema: {str(e)}")

            # Build config with optional sampling parameters
            config_params = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
            if top_p > 0.0:
                config_params["top_p"] = top_p
            if top_k > 0:
                config_params["top_k"] = top_k
            if stop_seq_list:
                config_params["stop_sequences"] = stop_seq_list
            if response_mime_type != "default":
                config_params["response_mime_type"] = response_mime_type
            if schema_obj:
                config_params["response_schema"] = schema_obj

            config = types.GenerateContentConfig(**config_params)
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

    # Text generation models (vision works with all)
    TEXT_MODELS = list(GeminiClient.MODELS.keys())

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
                "model": (
                    cls.TEXT_MODELS,
                    {
                        "default": GeminiClient.DEFAULT_MODEL,
                        "tooltip": "Gemini model to use for vision analysis"
                    }
                ),
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
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.95,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling - cumulative probability threshold (0.0=disabled)"
                    }
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 40,
                        "min": 0,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Top-k sampling - limit token selection (0=disabled)"
                    }
                ),
                "stop_sequences": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "Stop generation at these sequences (one per line, leave empty to disable)"
                    }
                ),
                "response_mime_type": (
                    ["default", "text/plain", "application/json"],
                    {
                        "default": "default",
                        "tooltip": "Output format (use application/json for JSON mode)"
                    }
                ),
                "response_schema": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "JSON schema for structured output (only used with application/json, leave empty for free-form JSON)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("analysis",)
    FUNCTION = "analyze"
    CATEGORY = "ERPK/Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for vision analysis
        return float("nan")

    def analyze(
        self,
        client: GeminiClient,
        image,
        prompt: str,
        model: str = None,
        max_tokens: int = 8192,
        temperature: float = 0.4,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: str = "",
        response_mime_type: str = "default",
        response_schema: str = ""
    ):
        """
        Analyze image(s) using Gemini's vision capabilities.

        Args:
            client: Gemini API client
            image: Image tensor(s)
            prompt: Question or instruction about images
            model: Gemini model to use
            max_tokens: Max output tokens
            temperature: Creativity level
            top_p: Nucleus sampling threshold (0.0 to disable)
            top_k: Top-k sampling limit (0 to disable)
            stop_sequences: Newline-separated stop sequences
            response_mime_type: Output format (default/text/plain/application/json)
            response_schema: JSON schema for structured output

        Returns:
            Tuple containing analysis text
        """
        # Use specified model or default
        if model is None:
            model = GeminiClient.DEFAULT_MODEL
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Convert tensor(s) to PIL images
            pil_images = ImageConverter.tensors_to_pil_list(image)
            print(f"[Gemini] Analyzing {len(pil_images)} image(s)")

            # Parse stop sequences (one per line)
            stop_seq_list = None
            if stop_sequences and stop_sequences.strip():
                stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]

            # Parse response schema if provided
            schema_obj = None
            if response_schema and response_schema.strip():
                import json
                try:
                    schema_obj = json.loads(response_schema.strip())
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON schema: {str(e)}")

            # Generate content with images
            response = client.generate_content(
                prompt=prompt.strip(),
                images=pil_images,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p > 0.0 else None,
                top_k=top_k if top_k > 0 else None,
                stop_sequences=stop_seq_list,
                response_mime_type=response_mime_type if response_mime_type != "default" else None,
                response_schema=schema_obj
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
    Can use a client from GeminiAPIConfig or work standalone with an API key.
    """

    # Image generation models
    IMAGE_MODELS = [
        "gemini-3-pro-image-preview",
        "gemini-2.5-flash-image",
    ]

    @classmethod
    def INPUT_TYPES(cls):
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
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client from Gemini API Config node (uses API key from config)"}
                ),
                "model": (
                    cls.IMAGE_MODELS,
                    {
                        "default": "gemini-3-pro-image-preview",
                        "tooltip": "Image generation model (overrides client model)"
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
                    ["default", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                    {
                        "default": "default",
                        "tooltip": "Image aspect ratio (default uses model's default)"
                    }
                ),
                "image_size": (
                    ["default", "1K", "2K", "4K"],
                    {
                        "default": "default",
                        "tooltip": "Image resolution (only for gemini-3-pro-image-preview; 2.5-flash always uses 1024px)"
                    }
                ),
                "response_modalities": (
                    ["IMAGE", "TEXT+IMAGE"],
                    {
                        "default": "IMAGE",
                        "tooltip": "What to return - image only or both text description and image"
                    }
                ),
                "enable_google_search": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable Google Search grounding (only for gemini-3-pro-image-preview)"
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Google API key (only needed if not using client input)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "description")
    FUNCTION = "generate_image"
    CATEGORY = "ERPK/Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for image generation
        return float("nan")

    def generate_image(
        self,
        prompt: str,
        client: GeminiClient = None,
        model: str = "gemini-2.5-flash-image",
        temperature: float = 1.0,
        aspect_ratio: str = "default",
        image_size: str = "default",
        response_modalities: str = "IMAGE",
        enable_google_search: bool = False,
        api_key: str = "",
    ):
        """
        Generate an image using Gemini's image generation models.

        Args:
            prompt: Text description of image to generate
            client: Optional Gemini API client from GeminiAPIConfig
            model: Image generation model to use
            temperature: Creativity level
            aspect_ratio: Image aspect ratio
            image_size: Image resolution (1K/2K/4K, only for gemini-3-pro-image-preview)
            response_modalities: Return image only or image+text description
            enable_google_search: Enable Google Search grounding (gemini-3-pro only)
            api_key: Optional API key (fallback if no client)

        Returns:
            Tuple containing (image tensor, description text)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Use provided client's API key, or create new client
            if client is not None:
                # Create new client with image model but same API key
                image_client = GeminiClient(
                    api_key=client.api_key,
                    model=model
                )
                # Inherit safety settings and system instruction from passed client
                if client.safety_settings:
                    image_client.safety_settings = client.safety_settings
                if client.system_instruction:
                    image_client.system_instruction = client.system_instruction
            else:
                # Standalone mode - use provided API key or env/config
                image_client = GeminiClient(
                    api_key=api_key if api_key.strip() else None,
                    model=model
                )

            print(f"[Gemini] Generating image with model: {model}")
            print(f"[Gemini] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if aspect_ratio != "default":
                print(f"[Gemini] Aspect ratio: {aspect_ratio}")
            if image_size != "default":
                print(f"[Gemini] Image size: {image_size}")

            # Build generation config
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
            )

            # Set response modalities
            if response_modalities == "TEXT+IMAGE":
                config.response_modalities = ["TEXT", "IMAGE"]
            else:
                config.response_modalities = ["IMAGE"]

            # Enable Google Search if requested (only for gemini-3-pro)
            if enable_google_search and model == "gemini-3-pro-image-preview":
                config.tools = [{"google_search": {}}]
                print(f"[Gemini] Google Search grounding enabled")

            # Build image config if needed
            image_config_params = {}
            if aspect_ratio != "default":
                image_config_params["aspect_ratio"] = aspect_ratio
            if image_size != "default" and model == "gemini-3-pro-image-preview":
                # Check SDK support - older versions don't have image_size field
                if "image_size" in types.ImageConfig.model_fields:
                    image_config_params["image_size"] = image_size
                else:
                    print(f"[Gemini] Warning: image_size not supported by SDK, ignoring")

            if image_config_params:
                config.image_config = types.ImageConfig(**image_config_params)

            # Generate content using NEW SDK
            response = image_client.client.models.generate_content(
                model=image_client.model_name,
                contents=[prompt.strip()],
                config=config
            )

            # Extract image and text from response
            image_tensor = None
            description_text = ""

            # Defensive check: Gemini can return 200 OK with empty content
            parts = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts = candidate.content.parts

            for part in (parts or []):
                # Extract text if present
                if hasattr(part, 'text') and part.text:
                    description_text = part.text

                # Extract image
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    # Check if data is empty
                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    # Convert bytes to tensor
                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image generated successfully: {image_tensor.shape}")
                    elif isinstance(image_data, str):
                        # Handle base64 string if needed
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image generated successfully: {image_tensor.shape}")

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

            if description_text:
                print(f"[Gemini] Also got description: {description_text[:100]}...")

            return (image_tensor, description_text)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiImageEdit:
    """
    Gemini Image Editing Node

    Uses Gemini's image generation models to edit/modify existing images based on text prompts.
    Gemini 3 Pro supports up to 14 reference images (up to 6 objects, up to 5 humans).
    Can use a client from GeminiAPIConfig or work standalone with an API key.
    """

    # Same image generation models as GeminiImageGeneration
    IMAGE_MODELS = [
        "gemini-3-pro-image-preview",
        "gemini-2.5-flash-image",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    "IMAGE",
                    {"tooltip": "Reference image(s) to edit (Gemini 3 Pro supports up to 14 images)"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Describe the edit. Reference images by order (first/second), content (the logo), or role (the style reference)"
                    }
                ),
            },
            "optional": {
                "additional_images": (
                    "IMAGE",
                    {"tooltip": "Additional reference image(s) to combine with main image input"}
                ),
                "client": (
                    "GEMINI_API_CLIENT",
                    {"tooltip": "Gemini API client from Gemini API Config node (uses API key from config)"}
                ),
                "model": (
                    cls.IMAGE_MODELS,
                    {
                        "default": "gemini-3-pro-image-preview",
                        "tooltip": "Image generation model (overrides client model)"
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
                    ["default", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                    {
                        "default": "default",
                        "tooltip": "Image aspect ratio (default uses model's default)"
                    }
                ),
                "image_size": (
                    ["default", "1K", "2K", "4K"],
                    {
                        "default": "default",
                        "tooltip": "Image resolution (only for gemini-3-pro-image-preview; 2.5-flash always uses 1024px)"
                    }
                ),
                "response_modalities": (
                    ["IMAGE", "TEXT+IMAGE"],
                    {
                        "default": "IMAGE",
                        "tooltip": "What to return - image only or both text description and image"
                    }
                ),
                "enable_google_search": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable Google Search grounding (only for gemini-3-pro-image-preview)"
                    }
                ),
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Google API key (only needed if not using client input)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "description")
    FUNCTION = "edit_image"
    CATEGORY = "ERPK/Gemini"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for image editing
        return float("nan")

    def edit_image(
        self,
        image,
        prompt: str,
        additional_images=None,
        client: GeminiClient = None,
        model: str = "gemini-2.5-flash-image",
        temperature: float = 1.0,
        aspect_ratio: str = "default",
        image_size: str = "default",
        response_modalities: str = "IMAGE",
        enable_google_search: bool = False,
        api_key: str = "",
    ):
        """
        Edit an image using Gemini's image generation models.

        Args:
            image: Input image(s) as ComfyUI tensor
            prompt: Text description of how to modify the image
            client: Optional Gemini API client from GeminiAPIConfig
            model: Image generation model to use
            temperature: Creativity level
            aspect_ratio: Image aspect ratio
            image_size: Image resolution (1K/2K/4K, only for gemini-3-pro-image-preview)
            response_modalities: Return image only or image+text description
            enable_google_search: Enable Google Search grounding (gemini-3-pro only)
            api_key: Optional API key (fallback if no client)

        Returns:
            Tuple containing (edited image tensor, description text)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Use provided client's API key, or create new client
            if client is not None:
                # Create new client with image model but same API key
                image_client = GeminiClient(
                    api_key=client.api_key,
                    model=model
                )
                # Inherit safety settings and system instruction from passed client
                if client.safety_settings:
                    image_client.safety_settings = client.safety_settings
                if client.system_instruction:
                    image_client.system_instruction = client.system_instruction
            else:
                # Standalone mode - use provided API key or env/config
                image_client = GeminiClient(
                    api_key=api_key if api_key.strip() else None,
                    model=model
                )

            # Convert ComfyUI tensors to PIL images, combining all inputs
            pil_images = ImageConverter.tensors_to_pil_list(image)
            if additional_images is not None:
                pil_images.extend(ImageConverter.tensors_to_pil_list(additional_images))
            num_images = len(pil_images)

            print(f"[Gemini] Editing image with model: {model}")
            print(f"[Gemini] Number of input images: {num_images}")
            print(f"[Gemini] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if aspect_ratio != "default":
                print(f"[Gemini] Aspect ratio: {aspect_ratio}")
            if image_size != "default":
                print(f"[Gemini] Image size: {image_size}")

            # Warn if using more than 14 images (Gemini 3 Pro limit)
            if num_images > 14:
                print(f"[Gemini] Warning: Using {num_images} images. Gemini 3 Pro supports up to 14 reference images.")

            # Build generation config
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
            )

            # Set response modalities
            if response_modalities == "TEXT+IMAGE":
                config.response_modalities = ["TEXT", "IMAGE"]
            else:
                config.response_modalities = ["IMAGE"]

            # Enable Google Search if requested (only for gemini-3-pro)
            if enable_google_search and model == "gemini-3-pro-image-preview":
                config.tools = [{"google_search": {}}]
                print(f"[Gemini] Google Search grounding enabled")

            # Build image config if needed
            image_config_params = {}
            if aspect_ratio != "default":
                image_config_params["aspect_ratio"] = aspect_ratio
            if image_size != "default" and model == "gemini-3-pro-image-preview":
                # Check SDK support - older versions don't have image_size field
                if "image_size" in types.ImageConfig.model_fields:
                    image_config_params["image_size"] = image_size
                else:
                    print(f"[Gemini] Warning: image_size not supported by SDK, ignoring")

            if image_config_params:
                config.image_config = types.ImageConfig(**image_config_params)

            # Build content list: images first, then prompt
            contents = pil_images + [prompt.strip()]

            # Generate content using NEW SDK
            response = image_client.client.models.generate_content(
                model=image_client.model_name,
                contents=contents,
                config=config
            )

            # Extract image and text from response
            image_tensor = None
            description_text = ""

            # Defensive check: Gemini can return 200 OK with empty content
            parts = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts = candidate.content.parts

            for part in (parts or []):
                # Extract text if present
                if hasattr(part, 'text') and part.text:
                    description_text = part.text

                # Extract image
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    # Check if data is empty
                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    # Convert bytes to tensor
                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image edited successfully: {image_tensor.shape}")
                    elif isinstance(image_data, str):
                        # Handle base64 string if needed
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image edited successfully: {image_tensor.shape}")

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

            if description_text:
                print(f"[Gemini] Also got description: {description_text[:100]}...")

            return (image_tensor, description_text)

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
