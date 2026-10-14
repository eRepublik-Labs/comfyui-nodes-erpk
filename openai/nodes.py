# ABOUTME: ComfyUI V3 nodes for OpenAI API integration
# ABOUTME: Provides text generation, vision, chat, and configuration nodes

import json

from comfy_api.latest import IO
from .openai_api.client import OpenAIClient

TEXT_MODELS = list(OpenAIClient.MODELS.keys())
VISION_MODELS = [m for m in TEXT_MODELS if not m.startswith("o")]

REASONING_EFFORT_OPTIONS = ["default", "none", "minimal", "low", "medium", "high", "xhigh"]
REASONING_EFFORT_TOOLTIP = (
    "Reasoning depth for the gpt-5.6 and gpt-6.x models. 'default' sends nothing, so "
    "the model reasons at its own default (medium). 'none' turns reasoning off on "
    "gpt-6-sol, gpt-6-luna and the gpt-5.6 tiers; gpt-6.1-sol and gpt-6-astra cannot "
    "turn it off, so there 'none' acts like 'default'. 'minimal' is rejected by every "
    "current model and is sent as 'low'. Ignored by chat-latest."
)

# temperature and top_p 400 on every current model unless reasoning is off.
SAMPLING_NOTE = (
    "Sent only when reasoning_effort is 'none' on gpt-6-sol, gpt-6-luna or a gpt-5.6 "
    "tier; every other model and effort accepts only the default, so it is dropped."
)

VERBOSITY_OPTIONS = ["default", "low", "medium", "high"]
VERBOSITY_TOOLTIP = (
    "Output verbosity for the gpt-5.6 and gpt-6.x models. 'low' produces terse responses, "
    "'high' produces more detailed ones. Distinct from max_tokens — shapes "
    "style, not the hard length cap. 'default' lets the model choose. "
    "Not sent to chat-latest, which accepts the field but ignores it."
)

RESPONSE_FORMAT_OPTIONS = ["default", "json_object", "json_schema"]
RESPONSE_FORMAT_TOOLTIP = (
    "Output format. json_object is JSON mode; json_schema is strict Structured "
    "Outputs, which forces the reply to match the JSON Schema in the json_schema input."
)


def json_schema_input():
    """The JSON Schema String for response_format json_schema, appended last."""
    return IO.String.Input(
        "json_schema",
        default="",
        multiline=True,
        optional=True,
        tooltip=(
            "JSON Schema the reply must match when response_format is json_schema "
            "(sent with strict: true). Strict mode needs every property listed in "
            "required and additionalProperties set to false on each object."
        ),
    )


def build_response_format(response_format, json_schema):
    """The chat.completions response_format for the node's widgets, or None."""
    if response_format == "json_object":
        return {"type": "json_object"}
    if response_format != "json_schema":
        return None
    if not json_schema or not json_schema.strip():
        raise ValueError("response_format 'json_schema' needs a JSON Schema in the json_schema input")
    try:
        schema = json.loads(json_schema)
    except json.JSONDecodeError as e:
        raise ValueError(f"json_schema is not valid JSON: {e}") from e
    if not isinstance(schema, dict):
        raise ValueError(f"json_schema must be a JSON object (a JSON Schema), got {type(schema).__name__}")
    return {
        "type": "json_schema",
        "json_schema": {"name": "response", "strict": True, "schema": schema},
    }


class OpenAIAPIConfig(IO.ComfyNode):
    """Initializes and provides an OpenAI API client for use by other nodes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIAPIConfig",
            display_name="OpenAI API Config",
            category="ERPK/OpenAI",
            inputs=[],
            outputs=[
                IO.Custom("OPENAI_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        try:
            client = OpenAIClient(
                api_key=None
            )

            print(f"[OpenAI] Client initialized")

            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to create OpenAI client: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAITextGeneration(IO.ComfyNode):
    """General-purpose text generation for various tasks."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAITextGeneration",
            display_name="OpenAI Text Generation",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text prompt for OpenAI",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=OpenAIClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="OpenAI model to use for generation",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level (0.0=focused, 2.0=very creative). " + SAMPLING_NOTE,
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=128000,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Float.Input(
                    "top_p",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Nucleus sampling - cumulative probability threshold (1.0=disabled). " + SAMPLING_NOTE,
                ),
                IO.String.Input(
                    "stop_sequences",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="Stop generation at these sequences (one per line, leave empty to disable). Ignored by every current model.",
                ),
                IO.Combo.Input(
                    "response_format",
                    options=RESPONSE_FORMAT_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=RESPONSE_FORMAT_TOOLTIP,
                ),
                IO.Combo.Input(
                    "reasoning_effort",
                    options=REASONING_EFFORT_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=REASONING_EFFORT_TOOLTIP,
                ),
                IO.Combo.Input(
                    "verbosity",
                    options=VERBOSITY_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=VERBOSITY_TOOLTIP,
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
                json_schema_input(),
            ],
            outputs=[
                IO.String.Output("response"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        client = kwargs.get("client")
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        top_p = kwargs.get("top_p", 1.0)
        stop_sequences = kwargs.get("stop_sequences", "")
        response_format = kwargs.get("response_format", "default")
        reasoning_effort = kwargs.get("reasoning_effort", "default")
        verbosity = kwargs.get("verbosity", "default")
        seed = kwargs.get("seed", -1)
        json_schema = kwargs.get("json_schema", "")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        resp_format = build_response_format(response_format, json_schema)

        if client is None:
            client = OpenAIClient(api_key=None)

        if model is None:
            model = OpenAIClient.DEFAULT_MODEL

        # Parse stop sequences (one per line)
        stop_seq_list = None
        if stop_sequences and stop_sequences.strip():
            stop_seq_list = [s.strip() for s in stop_sequences.strip().split('\n') if s.strip()]


        try:
            response = await client.generate_content(
                prompt=prompt.strip(),
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p < 1.0 else None,
                stop_sequences=stop_seq_list,
                response_format=resp_format,
                seed=seed if seed != -1 else None,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity if verbosity and verbosity != "default" else None,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by content filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[OpenAI] Text generated successfully ({len(text)} characters)")

            return IO.NodeOutput(text)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIChat(IO.ComfyNode):
    """Maintains multi-turn conversations with OpenAI, preserving message history."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIChat",
            display_name="OpenAI Chat",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Your message in the conversation",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=OpenAIClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="OpenAI model to use for chat",
                ),
                IO.Custom("OPENAI_CHAT_SESSION").Input(
                    "chat_session",
                    optional=True,
                    tooltip="Previous chat session (connect from previous chat node)",
                ),
                IO.Boolean.Input(
                    "reset_conversation",
                    default=False,
                    optional=True,
                    tooltip="Start a new conversation, discarding history",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level. " + SAMPLING_NOTE,
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=128000,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Float.Input(
                    "top_p",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Nucleus sampling - cumulative probability threshold (1.0=disabled). " + SAMPLING_NOTE,
                ),
                IO.String.Input(
                    "stop_sequences",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="Stop generation at these sequences (one per line, leave empty to disable). Ignored by every current model.",
                ),
                IO.Combo.Input(
                    "response_format",
                    options=RESPONSE_FORMAT_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=RESPONSE_FORMAT_TOOLTIP,
                ),
                IO.Combo.Input(
                    "reasoning_effort",
                    options=REASONING_EFFORT_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=REASONING_EFFORT_TOOLTIP,
                ),
                IO.Combo.Input(
                    "verbosity",
                    options=VERBOSITY_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=VERBOSITY_TOOLTIP,
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
                json_schema_input(),
            ],
            outputs=[
                IO.String.Output("response"),
                IO.Custom("OPENAI_CHAT_SESSION").Output("chat_session"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, prompt, **kwargs) -> IO.NodeOutput:
        client = kwargs.get("client")
        model = kwargs.get("model")
        chat_session = kwargs.get("chat_session")
        reset_conversation = kwargs.get("reset_conversation", False)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        top_p = kwargs.get("top_p", 1.0)
        stop_sequences = kwargs.get("stop_sequences", "")
        response_format = kwargs.get("response_format", "default")
        reasoning_effort = kwargs.get("reasoning_effort", "default")
        verbosity = kwargs.get("verbosity", "default")
        seed = kwargs.get("seed", -1)
        json_schema = kwargs.get("json_schema", "")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        resp_format = build_response_format(response_format, json_schema)

        if client is None:
            client = OpenAIClient(api_key=None)

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


            # Send chat request
            response = await client.chat(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p < 1.0 else None,
                stop_sequences=stop_seq_list,
                response_format=resp_format,
                seed=seed if seed != -1 else None,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity if verbosity and verbosity != "default" else None,
            )

            text = response.get("text", "")

            # Add assistant response to history
            messages.append({"role": "assistant", "content": text})

            print(f"[OpenAI] Chat response generated ({len(text)} characters)")

            return IO.NodeOutput(text, messages)

        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAIVision(IO.ComfyNode):
    """Uses OpenAI's vision capabilities to analyze images and answer questions about them."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAIVision",
            display_name="OpenAI Vision",
            category="ERPK/OpenAI",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip="Image(s) to analyze (ComfyUI tensor)",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="Describe this image in detail.",
                    tooltip="Question or instruction about the image(s)",
                ),
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="OpenAI API client from OpenAI API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=VISION_MODELS,
                    default=OpenAIClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="OpenAI model to use for vision analysis",
                ),
                IO.Combo.Input(
                    "detail",
                    options=["auto", "low", "high", "original"],
                    default="auto",
                    optional=True,
                    tooltip=(
                        "Image detail level (low=faster/cheaper, high=more detailed, "
                        "original=full resolution without downscaling). On gpt-6-astra and "
                        "the gpt-5.6 tiers, auto already behaves as original."
                    ),
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=4096,
                    min=256,
                    max=128000,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of analysis",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.4,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level (lower=more factual). " + SAMPLING_NOTE,
                ),
                IO.Combo.Input(
                    "reasoning_effort",
                    options=REASONING_EFFORT_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=REASONING_EFFORT_TOOLTIP,
                ),
                IO.Combo.Input(
                    "verbosity",
                    options=VERBOSITY_OPTIONS,
                    default="default",
                    optional=True,
                    tooltip=VERBOSITY_TOOLTIP,
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs (best-effort). Randomizes by default.",
                ),
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
    async def execute(cls, image, prompt, **kwargs) -> IO.NodeOutput:
        from .openai_api.utils import ImageConverter

        client = kwargs.get("client")
        model = kwargs.get("model", OpenAIClient.DEFAULT_MODEL)
        detail = kwargs.get("detail", "auto")
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.4)
        reasoning_effort = kwargs.get("reasoning_effort", "default")
        verbosity = kwargs.get("verbosity", "default")
        seed = kwargs.get("seed", -1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if client is None:
            client = OpenAIClient(api_key=None)

        try:
            # Convert tensor(s) to vision API format
            image_content = ImageConverter.tensors_to_vision_content(image, detail=detail)
            print(f"[OpenAI] Analyzing {len(image_content)} image(s)")


            # Generate content with images
            response = await client.generate_content(
                prompt=prompt.strip(),
                images=image_content,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                seed=seed if seed != -1 else None,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity if verbosity and verbosity != "default" else None,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by content filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[OpenAI] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[OpenAI] Vision analysis completed ({len(text)} characters)")

            return IO.NodeOutput(text)

        except Exception as e:
            error_msg = f"Failed to analyze image: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)


class OpenAISystemInstruction(IO.ComfyNode):
    """Sets a system-level instruction that persists across all requests for an OpenAI client."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="OpenAISystemInstruction",
            display_name="OpenAI System Instruction",
            category="ERPK/OpenAI",
            inputs=[
                IO.Custom("OPENAI_API_CLIENT").Input(
                    "client",
                    tooltip="OpenAI API client to configure",
                ),
                IO.String.Input(
                    "system_instruction",
                    multiline=True,
                    default="",
                    tooltip="System-level instruction to guide model behavior",
                ),
            ],
            outputs=[
                IO.Custom("OPENAI_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    def execute(cls, client, system_instruction, **kwargs) -> IO.NodeOutput:
        try:
            instruction = system_instruction.strip() if system_instruction else None

            if instruction:
                client.update_config(system_instruction=instruction)
                print(f"[OpenAI] System instruction set ({len(instruction)} characters)")
            else:
                print("[OpenAI] Warning: Empty system instruction, skipping")

            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to set system instruction: {str(e)}"
            print(f"[OpenAI] Error: {error_msg}")
            raise ValueError(error_msg)
