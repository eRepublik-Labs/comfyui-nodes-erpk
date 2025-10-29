# ABOUTME: Google Gemini API client using the new google-genai SDK
# ABOUTME: Handles authentication, requests, and error handling

import os
import configparser
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


class GeminiClient:
    """
    Client for interacting with Google Gemini API using google-genai SDK.

    Features:
    - Multi-source API key management (input → env → config)
    - All Gemini models support
    - Text generation and vision capabilities
    - Safety settings configuration
    - System instructions support
    """

    # Available models
    MODELS = {
        "gemini-2.5-pro-latest": "Gemini 2.5 Pro Latest (Always newest stable)",
        "gemini-2.5-pro": "Gemini 2.5 Pro (State-of-the-art thinking model)",
        "gemini-2.5-flash-latest": "Gemini 2.5 Flash Latest (Always newest stable)",
        "gemini-2.5-flash": "Gemini 2.5 Flash (Best price-performance)",
        "gemini-2.5-flash-preview": "Gemini 2.5 Flash Preview (Experimental features)",
        "gemini-2.5-flash-image": "Gemini 2.5 Flash Image (Image generation)",
        "gemini-2.5-flash-image-preview": "Gemini 2.5 Flash Image Preview (Experimental image gen)",
        "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite (Fastest, most cost-efficient)",
        "gemini-2.5-flash-lite-preview": "Gemini 2.5 Flash-Lite Preview (Experimental)",
        "gemini-2.0-flash-exp": "Gemini 2.0 Flash Experimental (Cutting edge)",
    }

    # Default configuration
    DEFAULT_MODEL = "gemini-2.5-flash"
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_TEMPERATURE = 0.7

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        config_path: Optional[str] = None
    ):
        """
        Initialize Gemini API client.

        Args:
            api_key: Google API key (optional, will check env/config)
            model: Gemini model to use
            config_path: Path to config.ini file
        """
        self.model_name = model

        # Resolve API key from multiple sources
        self.api_key = self._resolve_api_key(api_key, config_path)

        # Initialize the client
        self.client = genai.Client(api_key=self.api_key)

        # Store configuration for later use
        self.system_instruction = None
        self.safety_settings = None

    def _resolve_api_key(self, api_key: Optional[str], config_path: Optional[str]) -> str:
        """
        Resolve API key from multiple sources in order of priority:
        1. Provided api_key parameter
        2. GOOGLE_API_KEY or GEMINI_API_KEY environment variable
        3. config.ini file

        Args:
            api_key: API key provided directly
            config_path: Path to config.ini

        Returns:
            Resolved API key

        Raises:
            ValueError: If no API key found
        """
        # Priority 1: Direct parameter
        if api_key and api_key.strip():
            return api_key.strip()

        # Priority 2: Environment variable
        env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if env_key:
            return env_key

        # Priority 3: Config file
        if config_path is None:
            # Default to config.ini in same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(current_dir), "config.ini")

        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            if "gemini" in config and "api_key" in config["gemini"]:
                return config["gemini"]["api_key"]

        raise ValueError(
            "No API key found. Please provide via:\\n"
            "1. api_key parameter\\n"
            "2. GOOGLE_API_KEY or GEMINI_API_KEY environment variable\\n"
            "3. config.ini file in gemini/ directory"
        )

    def update_config(
        self,
        system_instruction: Optional[str] = None,
        safety_settings: Optional[Dict] = None
    ):
        """
        Update client configuration.

        Args:
            system_instruction: System-level instruction for the model
            safety_settings: Safety settings configuration
        """
        if system_instruction:
            self.system_instruction = system_instruction
        if safety_settings:
            self.safety_settings = safety_settings

    def generate_content(
        self,
        prompt: str,
        images: Optional[List[Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini API.

        Args:
            prompt: Text prompt
            images: Optional list of PIL Images for vision tasks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            **kwargs: Additional parameters

        Returns:
            Response dict with 'text' and metadata
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        # Build generation config
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        # Add system instruction if set
        if self.system_instruction:
            config.system_instruction = self.system_instruction

        # Add safety settings if set
        if self.safety_settings:
            config.safety_settings = self.safety_settings

        # Build content list (images + text)
        contents = []
        if images:
            contents.extend(images)
        contents.append(prompt)

        # Generate content
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

        # Extract text from response
        try:
            text = response.text
            return {
                "text": text,
                "blocked": False,
                "finish_reason": response.candidates[0].finish_reason if response.candidates else "STOP"
            }
        except Exception as e:
            # Response was blocked or error occurred
            return {
                "text": "",
                "blocked": True,
                "finish_reason": response.candidates[0].finish_reason if response.candidates else "ERROR",
                "error": str(e)
            }

    def start_chat(self, history: Optional[List[Dict[str, str]]] = None):
        """
        Start a chat session for multi-turn conversations.

        Args:
            history: Optional chat history

        Returns:
            Chat session object
        """
        # Build config
        config = types.GenerateContentConfig()
        if self.system_instruction:
            config.system_instruction = self.system_instruction
        if self.safety_settings:
            config.safety_settings = self.safety_settings

        # Create chat
        return self.client.chats.create(
            model=self.model_name,
            config=config
        )
