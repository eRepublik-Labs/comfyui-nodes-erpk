# ABOUTME: ComfyUI nodes for OpenAI API integration
# ABOUTME: Provides text generation, vision, chat, and configuration nodes

from .openai_api.client import OpenAIClient
from .openai_api.utils import ImageConverter


class OpenAIAPIConfig:
    """
    OpenAI API Configuration Node

    Initializes and provides an OpenAI API client for use by other nodes.
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
                        "tooltip": "OpenAI API key. If empty, will use OPENAI_API_KEY env var or config.ini."
                    }
                ),
            }
        }

    RETURN_TYPES = ("OPENAI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "create_client"
    CATEGORY = "ERPK/OpenAI"

    def create_client(self, api_key: str = ""):
        """
        Create and return an OpenAI API client.

        Args:
            api_key: Optional API key

        Returns:
            Tuple containing the client instance
        """
        try:
            client = OpenAIClient(
                api_key=api_key if api_key.strip() else None
            )

            print(f"[OpenAI] Client initialized")

            return (client,)

        except Exception as e:
            error_msg = f"Failed to create OpenAI client: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAITextGeneration:
    """
    OpenAI Text Generation Node

    General-purpose text generation for various tasks including:
    - Text completion and expansion
    - Creative writing
    - Text transformation
    - Content generation
    """

    # Text generation models
    TEXT_MODELS = list(OpenAIClient.MODELS.keys())

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client from OpenAI API Config node"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text prompt for OpenAI"
                    }
                ),
            },
            "optional": {
                "model": (
                    cls.TEXT_MODELS,
                    {
                        "default": OpenAIClient.DEFAULT_MODEL,
                        "tooltip": "OpenAI model to use for generation"
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
                        "default": 4096,
                        "min": 256,
                        "max": 16384,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling - cumulative probability threshold (1.0=disabled)"
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
                "response_format": (
                    ["default", "json_object"],
                    {
                        "default": "default",
                        "tooltip": "Output format (use json_object for JSON mode)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "ERPK/OpenAI"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for text generation
        return float("nan")

    def generate(
        self,
        client: OpenAIClient,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 1.0,
        stop_sequences: str = "",
        response_format: str = "default"
    ):
        """
        Generate text using OpenAI.

        Args:
            client: OpenAI API client
            prompt: User prompt
            model: OpenAI model to use
            temperature: Creativity level
            max_tokens: Max output tokens
            top_p: Nucleus sampling threshold (1.0 to disable)
            stop_sequences: Newline-separated stop sequences
            response_format: Output format (default/json_object)

        Returns:
            Tuple containing generated text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Use specified model or default
        if model is None:
            model = OpenAIClient.DEFAULT_MODEL

        # Parse stop sequences (one per line)
        stop_seq_list = None
        if stop_sequences and stop_sequences.strip():
            stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]

        # Parse response format
        resp_format = None
        if response_format == "json_object":
            resp_format = {"type": "json_object"}

        try:
            response = client.generate_content(
                prompt=prompt.strip(),
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p < 1.0 else None,
                stop_sequences=stop_seq_list,
                response_format=resp_format
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by content filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[OpenAI] Text generated successfully ({len(text)} characters)")

            return (text,)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIChat:
    """
    OpenAI Chat Node

    Maintains multi-turn conversations with OpenAI, preserving message history
    across multiple node executions.
    """

    # Text generation models
    TEXT_MODELS = list(OpenAIClient.MODELS.keys())

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client from OpenAI API Config node"}
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
                        "default": OpenAIClient.DEFAULT_MODEL,
                        "tooltip": "OpenAI model to use for chat"
                    }
                ),
                "chat_session": (
                    "OPENAI_CHAT_SESSION",
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
                        "default": 4096,
                        "min": 256,
                        "max": 16384,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling - cumulative probability threshold (1.0=disabled)"
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
                "response_format": (
                    ["default", "json_object"],
                    {
                        "default": "default",
                        "tooltip": "Output format (use json_object for JSON mode)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "OPENAI_CHAT_SESSION")
    RETURN_NAMES = ("response", "chat_session")
    FUNCTION = "chat"
    CATEGORY = "ERPK/OpenAI"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for chat
        return float("nan")

    def chat(
        self,
        client: OpenAIClient,
        prompt: str,
        model: str = None,
        chat_session=None,
        reset_conversation: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 1.0,
        stop_sequences: str = "",
        response_format: str = "default"
    ):
        """
        Continue or start a conversation with OpenAI.

        Args:
            client: OpenAI API client
            prompt: User message
            model: OpenAI model to use
            chat_session: Previous chat session (list of messages)
            reset_conversation: Start new conversation
            temperature: Creativity level
            max_tokens: Max output tokens
            top_p: Nucleus sampling threshold (1.0 to disable)
            stop_sequences: Newline-separated stop sequences
            response_format: Output format (default/json_object)

        Returns:
            Tuple containing (response text, chat session)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Use specified model or default
        if model is None:
            model = OpenAIClient.DEFAULT_MODEL

        try:
            # Start new session or use existing
            if reset_conversation or chat_session is None:
                messages = []
                print(f"[OpenAI] Started new conversation with {model}")
            else:
                messages = list(chat_session)  # Copy to avoid mutation
                print(f"[OpenAI] Continuing conversation ({len(messages)} messages)")

            # Add user message
            messages.append({"role": "user", "content": prompt.strip()})

            # Parse stop sequences (one per line)
            stop_seq_list = None
            if stop_sequences and stop_sequences.strip():
                stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]

            # Parse response format
            resp_format = None
            if response_format == "json_object":
                resp_format = {"type": "json_object"}

            # Send chat request
            response = client.chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p < 1.0 else None,
                stop_sequences=stop_seq_list,
                response_format=resp_format
            )

            text = response.get("text", "")

            # Add assistant response to history
            messages.append({"role": "assistant", "content": text})

            print(f"[OpenAI] Chat response generated ({len(text)} characters)")

            return (text, messages)

        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIVision:
    """
    OpenAI Vision Analysis Node

    Uses OpenAI's vision capabilities to analyze images and answer questions about them.
    Supports single or multiple images.
    """

    # Vision-capable models
    VISION_MODELS = ["gpt-5.2", "gpt-5.2-pro", "gpt-5.1", "gpt-5", "gpt-5-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client from OpenAI API Config node"}
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
                    cls.VISION_MODELS,
                    {
                        "default": "gpt-4o",
                        "tooltip": "OpenAI model to use for vision analysis"
                    }
                ),
                "detail": (
                    ["auto", "low", "high"],
                    {
                        "default": "auto",
                        "tooltip": "Image detail level (low=faster/cheaper, high=more detailed)"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 4096,
                        "min": 256,
                        "max": 16384,
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
    CATEGORY = "ERPK/OpenAI"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always regenerate - disable caching for vision analysis
        return float("nan")

    def analyze(
        self,
        client: OpenAIClient,
        image,
        prompt: str,
        model: str = "gpt-4o",
        detail: str = "auto",
        max_tokens: int = 4096,
        temperature: float = 0.4,
    ):
        """
        Analyze image(s) using OpenAI's vision capabilities.

        Args:
            client: OpenAI API client
            image: Image tensor(s)
            prompt: Question or instruction about images
            model: OpenAI model to use
            detail: Image detail level (auto/low/high)
            max_tokens: Max output tokens
            temperature: Creativity level

        Returns:
            Tuple containing analysis text
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Convert tensor(s) to vision API format
            image_content = ImageConverter.tensors_to_vision_content(image, detail=detail)
            print(f"[OpenAI] Analyzing {len(image_content)} image(s)")

            # Generate content with images
            response = client.generate_content(
                prompt=prompt.strip(),
                images=image_content,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by content filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[OpenAI] Vision analysis completed ({len(text)} characters)")

            return (text,)

        except Exception as e:
            error_msg = f"Failed to analyze image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAISystemInstruction:
    """
    OpenAI System Instruction Node

    Sets a system-level instruction that persists across all requests
    for an OpenAI client. System instructions guide the model's behavior.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "OPENAI_API_CLIENT",
                    {"tooltip": "OpenAI API client to configure"}
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

    RETURN_TYPES = ("OPENAI_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "set_instruction"
    CATEGORY = "ERPK/OpenAI"

    def set_instruction(self, client: OpenAIClient, system_instruction: str):
        """
        Set system instruction for the client.

        Args:
            client: OpenAI API client
            system_instruction: System instruction text

        Returns:
            Tuple containing the updated client
        """
        try:
            instruction = system_instruction.strip() if system_instruction else None

            if instruction:
                client.update_config(system_instruction=instruction)
                print(f"[OpenAI] System instruction set ({len(instruction)} characters)")
            else:
                print("[OpenAI] Warning: Empty system instruction, skipping")

            return (client,)

        except Exception as e:
            error_msg = f"Failed to set system instruction: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


# Node registration
NODE_CLASS_MAPPINGS = {
    "OpenAIAPIConfig": OpenAIAPIConfig,
    "OpenAITextGeneration": OpenAITextGeneration,
    "OpenAIChat": OpenAIChat,
    "OpenAIVision": OpenAIVision,
    "OpenAISystemInstruction": OpenAISystemInstruction,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenAIAPIConfig": "OpenAI API Config",
    "OpenAITextGeneration": "OpenAI Text Generation",
    "OpenAIChat": "OpenAI Chat",
    "OpenAIVision": "OpenAI Vision",
    "OpenAISystemInstruction": "OpenAI System Instruction",
}
