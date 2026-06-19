# ABOUTME: ComfyUI V3 nodes for Google Gemini API integration.
# ABOUTME: Provides text generation, vision, chat, image gen/edit, and configuration nodes.

import asyncio
import json
import math

from comfy_api.latest import IO

from .gemini_api.client import GeminiClient

# Degenerate-box floor for detections, mirroring utils/regional_prompt's
# MIN_REGION_EXTENT (the regions contract). It is duplicated rather than imported
# because this module is imported as a top-level package in the test harness,
# where a module-level cross-package relative import ("from ..utils ...") raises
# "beyond top-level package". test_gemini_detect asserts the two stay in sync.
MIN_REGION_EXTENT = 0.005

GEMINI_MAX_STOP_SEQUENCES = 5


def _parse_stop_sequences(text):
    """Parse newline-separated stop sequences, enforcing the Gemini API limit."""
    if not text or not text.strip():
        return None
    sequences = [s.strip() for s in text.strip().split('\n') if s.strip()]
    if not sequences:
        return None
    if len(sequences) > GEMINI_MAX_STOP_SEQUENCES:
        print(f"[Gemini] Warning: {len(sequences)} stop sequences provided, "
              f"truncating to {GEMINI_MAX_STOP_SEQUENCES} (Gemini API limit)")
        sequences = sequences[:GEMINI_MAX_STOP_SEQUENCES]
    return sequences


def _is_gemini_3x(model: str) -> bool:
    """Return True when the model string belongs to the Gemini 3.x generation."""
    return model.startswith("gemini-3")


_FINISH_REASON_HINTS = {
    "IMAGE_OTHER": (
        "Gemini soft-refused image generation without a specific reason. "
        "Try lower image_size (2K instead of 4K), simpler prompts, "
        "disabling enable_google_search for image edits, or splitting "
        "multi-constraint edits into single-change steps."
    ),
    "IMAGE_SAFETY": (
        "Output was blocked by Gemini's image safety filters. "
        "Rephrase the prompt to avoid sensitive content."
    ),
    "IMAGE_PROHIBITED_CONTENT": (
        "Output was blocked under prohibited-content rules. "
        "Rephrase or remove the disallowed element."
    ),
    "IMAGE_RECITATION": (
        "Output was blocked because it resembled training data too closely. "
        "Rephrase the prompt to be more original."
    ),
    "SAFETY": "Response was blocked by content safety filters. Rephrase the prompt.",
    "RECITATION": "Response was blocked due to recitation policies. Rephrase to be more original.",
    "PROHIBITED_CONTENT": "Response was blocked under prohibited-content rules.",
    "BLOCKLIST": "Response contains terms from Gemini's blocklist. Rephrase the prompt.",
    "SPII": "Response contained sensitive personally identifiable information.",
    "MAX_TOKENS": "Response hit the token limit before completing. Increase max_tokens or shorten the prompt.",
    "MALFORMED_FUNCTION_CALL": "Model produced a malformed function/tool call. Usually retryable.",
}


def _finish_reason_hint(finish_reason):
    """Map a Gemini finish_reason enum value to a short remediation hint."""
    if finish_reason is None:
        return None
    name = str(finish_reason).split(".")[-1].upper()
    return _FINISH_REASON_HINTS.get(name)


def _dump_response_payload(response, label="response"):
    """Print the full Gemini response object to console for post-mortem debugging.

    Tries Pydantic's model_dump_json first; falls back to repr if the response
    isn't a Pydantic model (older SDK versions).
    """
    print(f"[Gemini] Full {label} payload on failure:")
    try:
        print(response.model_dump_json(indent=2))
    except Exception:
        try:
            print(response.model_dump(mode="json"))
        except Exception:
            print(repr(response))


def _build_thinking_config(thinking_level, model):
    """Build a ThinkingConfig tailored to the model's generation.

    Gemini 3.x accepts the semantic enum (thinking_level). Gemini 2.5 expects
    an integer thinking_budget, so the enum is mapped to an approximate budget.
    Pro 2.5 cannot disable thinking, so minimal is clamped up to a 128 minimum.
    """
    if thinking_level == "none":
        return None
    from google.genai import types as genai_types
    if not hasattr(genai_types, 'ThinkingConfig'):
        print("[Gemini] Warning: ThinkingConfig not supported by SDK, ignoring")
        return None
    if _is_gemini_3x(model):
        return genai_types.ThinkingConfig(thinking_level=thinking_level.upper())
    budget_map = {"minimal": 0, "low": 512, "medium": 4096, "high": 16384}
    budget = budget_map.get(thinking_level, 0)
    if model == "gemini-2.5-pro" and budget < 128:
        budget = 128
    return genai_types.ThinkingConfig(thinking_budget=budget)


# --- Model lists for COMBO inputs ---
TEXT_MODELS = list(GeminiClient.MODELS.keys())
IMAGE_MODELS = GeminiClient.IMAGE_MODELS


# Structured-output schema for object detection: a flat list of boxes, each on
# Gemini's 0-1000 grid as box_2d = [ymin, xmin, ymax, xmax] plus a short label.
DETECTION_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "box_2d": {"type": "ARRAY", "items": {"type": "INTEGER"}},
            "label": {"type": "STRING"},
        },
        "required": ["box_2d", "label"],
    },
}


def detection_prompt(objects, max_objects):
    """Build the detection request prompt from the objects widget text.

    The list-restriction sentence only applies when the user named objects;
    in detect-everything mode it would contradict the opening instruction.
    """
    labels = [line.strip() for line in objects.split("\n") if line.strip()]
    if labels:
        prompt = f"Detect the following objects in the image: {', '.join(labels)}. "
        restriction = " Only include objects from the list and omit anything not present."
    else:
        prompt = "Detect all prominent objects in the image. "
        restriction = ""
    return prompt + (
        "For each detected instance, return its 2D bounding box as "
        "box_2d = [ymin, xmin, ymax, xmax] on a 0-1000 grid with the origin "
        "at the top-left, and a short label naming the object. Detect at most "
        f"{max_objects} instances total." + restriction
    )


def detections_to_regions(text, max_objects):
    """Convert Gemini's detection JSON into clamped, normalized region dicts.

    Input is the model's structured output: a list of {box_2d, label} where
    box_2d is [ymin, xmin, ymax, xmax] on a 0-1000 grid (top-left origin).
    Output dicts match utils/regional_prompt.parse_regions exactly. An empty
    list is valid (model found nothing); malformed or non-list JSON raises.
    """
    try:
        raw = json.loads(text)
    except (TypeError, ValueError):
        raise ValueError("Gemini returned malformed detection JSON")
    if not isinstance(raw, list):
        raise ValueError("Gemini returned malformed detection JSON")
    regions = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        box = entry.get("box_2d")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        try:
            values = [float(value) for value in box]
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in values):
            continue
        ymin, xmin, ymax, xmax = (value / 1000.0 for value in values)
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin
        xmin = max(0.0, min(1.0, xmin))
        xmax = max(0.0, min(1.0, xmax))
        ymin = max(0.0, min(1.0, ymin))
        ymax = max(0.0, min(1.0, ymax))
        x, y, w, h = xmin, ymin, xmax - xmin, ymax - ymin
        if w <= MIN_REGION_EXTENT or h <= MIN_REGION_EXTENT:
            continue
        label = entry.get("label")
        desc = label.strip() if isinstance(label, str) else ""
        regions.append({"x": x, "y": y, "w": w, "h": h,
                        "kind": "object", "desc": desc, "text": ""})
    return regions[:max_objects]


class GeminiAPIConfig(IO.ComfyNode):
    """Initializes and provides a Gemini API client for use by other nodes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiAPIConfig",
            display_name="Gemini API Config",
            category="ERPK/Gemini",
            description="Initialize a Gemini API client. Each node selects its own model.",
            inputs=[],
            outputs=[
                IO.Custom("GEMINI_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        try:
            client = GeminiClient(api_key=None)
            print(f"[Gemini] Client initialized")
            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to create Gemini client: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiTextGeneration(IO.ComfyNode):
    """General-purpose text generation for various tasks including completion,
    creative writing, transformation, and content generation."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiTextGeneration",
            display_name="Gemini Text Generation",
            category="ERPK/Gemini",
            description="Generate text using Gemini models.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Text prompt for Gemini",
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GeminiClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="Gemini model to use for generation",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.7,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level (0.0=focused, 2.0=very creative)",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=8192,
                    min=256,
                    max=65536,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Float.Input(
                    "top_p",
                    default=0.95,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Nucleus sampling - cumulative probability threshold (0.0=disabled)",
                ),
                IO.Int.Input(
                    "top_k",
                    default=40,
                    min=-1,
                    max=100,
                    step=1,
                    optional=True,
                    tooltip="Top-k sampling - limit token selection (0=disabled)",
                ),
                IO.String.Input(
                    "stop_sequences",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="Stop generation at these sequences (one per line, leave empty to disable)",
                ),
                IO.Combo.Input(
                    "response_mime_type",
                    options=["default", "text/plain", "application/json"],
                    default="default",
                    optional=True,
                    tooltip="Output format (use application/json for JSON mode)",
                ),
                IO.String.Input(
                    "response_schema",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="JSON schema for structured output (only used with application/json, leave empty for free-form JSON)",
                ),
                IO.Combo.Input(
                    "thinking_level",
                    options=["none", "minimal", "low", "medium", "high"],
                    default="none",
                    optional=True,
                    tooltip="Reasoning depth. Works on Gemini 2.5 and 3.x; the node translates to thinking_budget (2.5) or thinking_level enum (3.x) automatically.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs. Randomizes by default.",
                ),
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
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 8192)
        top_p = kwargs.get("top_p", 0.95)
        top_k = kwargs.get("top_k", 40)
        stop_sequences = kwargs.get("stop_sequences", "")
        response_mime_type = kwargs.get("response_mime_type", "default")
        response_schema = kwargs.get("response_schema", "")
        thinking_level = kwargs.get("thinking_level", "none")
        seed = kwargs.get("seed", -1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if client is None:
            client = GeminiClient(api_key=None)

        if model is None:
            model = GeminiClient.DEFAULT_MODEL

        stop_seq_list = _parse_stop_sequences(stop_sequences)

        schema_obj = None
        if response_schema and response_schema.strip():
            import json
            try:
                schema_obj = json.loads(response_schema.strip())
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON schema: {str(e)}")

        thinking_cfg = _build_thinking_config(thinking_level, model)

        try:
            response = await client.generate_content(
                prompt=prompt.strip(),
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p > 0.0 else None,
                top_k=top_k if top_k > 0 else None,
                stop_sequences=stop_seq_list,
                response_mime_type=response_mime_type if response_mime_type != "default" else None,
                response_schema=schema_obj,
                thinking_config=thinking_cfg,
                seed=seed if seed != -1 else None,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by safety filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[Gemini] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[Gemini] Text generated successfully ({len(text)} characters)")

            return IO.NodeOutput(text)

        except Exception as e:
            error_msg = f"Failed to generate text: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiChat(IO.ComfyNode):
    """Maintains multi-turn conversations with Gemini, preserving message history
    across multiple node executions."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiChat",
            display_name="Gemini Chat",
            category="ERPK/Gemini",
            description="Multi-turn conversation with Gemini.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Your message in the conversation",
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GeminiClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="Gemini model to use for chat",
                ),
                IO.Custom("GEMINI_CHAT_SESSION").Input(
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
                    tooltip="Creativity level",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=8192,
                    min=256,
                    max=65536,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Float.Input(
                    "top_p",
                    default=0.95,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Nucleus sampling - cumulative probability threshold (0.0=disabled)",
                ),
                IO.Int.Input(
                    "top_k",
                    default=40,
                    min=-1,
                    max=100,
                    step=1,
                    optional=True,
                    tooltip="Top-k sampling - limit token selection (0=disabled)",
                ),
                IO.String.Input(
                    "stop_sequences",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="Stop generation at these sequences (one per line, leave empty to disable)",
                ),
                IO.Combo.Input(
                    "response_mime_type",
                    options=["default", "text/plain", "application/json"],
                    default="default",
                    optional=True,
                    tooltip="Output format (use application/json for JSON mode)",
                ),
                IO.String.Input(
                    "response_schema",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="JSON schema for structured output (only used with application/json, leave empty for free-form JSON)",
                ),
                IO.Combo.Input(
                    "thinking_level",
                    options=["none", "minimal", "low", "medium", "high"],
                    default="none",
                    optional=True,
                    tooltip="Reasoning depth. Works on Gemini 2.5 and 3.x; the node translates to thinking_budget (2.5) or thinking_level enum (3.x) automatically.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs. Randomizes by default.",
                ),
            ],
            outputs=[
                IO.String.Output("response"),
                IO.Custom("GEMINI_CHAT_SESSION").Output("chat_session"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        model = kwargs.get("model")
        chat_session = kwargs.get("chat_session")
        reset_conversation = kwargs.get("reset_conversation", False)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 8192)
        top_p = kwargs.get("top_p", 0.95)
        top_k = kwargs.get("top_k", 40)
        stop_sequences = kwargs.get("stop_sequences", "")
        response_mime_type = kwargs.get("response_mime_type", "default")
        response_schema = kwargs.get("response_schema", "")
        thinking_level = kwargs.get("thinking_level", "none")
        seed = kwargs.get("seed", -1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if client is None:
            client = GeminiClient(api_key=None)

        if model is None:
            model = GeminiClient.DEFAULT_MODEL

        thinking_cfg = _build_thinking_config(thinking_level, model)

        try:
            if reset_conversation or chat_session is None:
                chat_session = client.start_chat(model=model, thinking_config=thinking_cfg)
                print(f"[Gemini] Started new conversation with {model}")
            else:
                print(f"[Gemini] Continuing conversation")

            from google.genai import types
            import json

            stop_seq_list = _parse_stop_sequences(stop_sequences)

            schema_obj = None
            if response_schema and response_schema.strip():
                try:
                    schema_obj = json.loads(response_schema.strip())
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON schema: {str(e)}")

            config_params = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
            if seed != -1:
                config_params["seed"] = seed
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
            if thinking_cfg is not None:
                config.thinking_config = thinking_cfg
            response = await asyncio.to_thread(
                chat_session.send_message,
                prompt.strip(),
                config=config,
            )

            text = response.text
            print(f"[Gemini] Chat response generated ({len(text)} characters)")

            return IO.NodeOutput(text, chat_session)

        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiVision(IO.ComfyNode):
    """Uses Gemini's vision capabilities to analyze images and answer questions about them."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiVision",
            display_name="Gemini Vision",
            category="ERPK/Gemini",
            description="Analyze images using Gemini's vision capabilities.",
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
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GeminiClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="Gemini model to use for vision analysis",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=8192,
                    min=256,
                    max=65536,
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
                    tooltip="Creativity level (lower=more factual)",
                ),
                IO.Float.Input(
                    "top_p",
                    default=0.95,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Nucleus sampling - cumulative probability threshold (0.0=disabled)",
                ),
                IO.Int.Input(
                    "top_k",
                    default=40,
                    min=-1,
                    max=100,
                    step=1,
                    optional=True,
                    tooltip="Top-k sampling - limit token selection (0=disabled)",
                ),
                IO.String.Input(
                    "stop_sequences",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="Stop generation at these sequences (one per line, leave empty to disable)",
                ),
                IO.Combo.Input(
                    "response_mime_type",
                    options=["default", "text/plain", "application/json"],
                    default="default",
                    optional=True,
                    tooltip="Output format (use application/json for JSON mode)",
                ),
                IO.String.Input(
                    "response_schema",
                    default="",
                    multiline=True,
                    optional=True,
                    tooltip="JSON schema for structured output (only used with application/json, leave empty for free-form JSON)",
                ),
                IO.Combo.Input(
                    "thinking_level",
                    options=["none", "minimal", "low", "medium", "high"],
                    default="none",
                    optional=True,
                    tooltip="Reasoning depth. Works on Gemini 2.5 and 3.x; the node translates to thinking_budget (2.5) or thinking_level enum (3.x) automatically.",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs. Randomizes by default.",
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
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.utils import ImageConverter

        image = kwargs.get("image")
        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        model = kwargs.get("model")
        max_tokens = kwargs.get("max_tokens", 8192)
        temperature = kwargs.get("temperature", 0.4)
        top_p = kwargs.get("top_p", 0.95)
        top_k = kwargs.get("top_k", 40)
        stop_sequences = kwargs.get("stop_sequences", "")
        response_mime_type = kwargs.get("response_mime_type", "default")
        response_schema = kwargs.get("response_schema", "")
        thinking_level = kwargs.get("thinking_level", "none")
        seed = kwargs.get("seed", -1)

        if model is None:
            model = GeminiClient.DEFAULT_MODEL
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if client is None:
            client = GeminiClient(api_key=None)

        try:
            pil_images = ImageConverter.tensors_to_pil_list(image)
            print(f"[Gemini] Analyzing {len(pil_images)} image(s)")

            stop_seq_list = _parse_stop_sequences(stop_sequences)

            schema_obj = None
            if response_schema and response_schema.strip():
                import json
                try:
                    schema_obj = json.loads(response_schema.strip())
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON schema: {str(e)}")

            thinking_cfg = _build_thinking_config(thinking_level, model)

            response = await client.generate_content(
                prompt=prompt.strip(),
                images=pil_images,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                top_p=top_p if top_p > 0.0 else None,
                top_k=top_k if top_k > 0 else None,
                stop_sequences=stop_seq_list,
                response_mime_type=response_mime_type if response_mime_type != "default" else None,
                response_schema=schema_obj,
                thinking_config=thinking_cfg,
                seed=seed if seed != -1 else None,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by safety filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[Gemini] Warning: {error_msg}")
                raise ValueError(error_msg)

            text = response.get("text", "")
            print(f"[Gemini] Vision analysis completed ({len(text)} characters)")

            return IO.NodeOutput(text)

        except Exception as e:
            error_msg = f"Failed to analyze image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiDetect(IO.ComfyNode):
    """Detects objects in an image and emits their bounding boxes as ERPK_REGIONS."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiDetect",
            display_name="Gemini Detect",
            category="ERPK/Gemini",
            description="Detect objects in an image and emit their bounding boxes "
                        "as regions for the Regional Prompt Builder.",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip="Image to detect objects in (ComfyUI tensor)",
                ),
                IO.String.Input(
                    "objects",
                    multiline=True,
                    default="",
                    tooltip="Objects to detect, one per line (e.g. 'red car'). "
                            "Leave empty to detect all prominent objects.",
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (optional if API key is configured in Settings)",
                ),
                IO.Combo.Input(
                    "model",
                    options=TEXT_MODELS,
                    default=GeminiClient.DEFAULT_MODEL,
                    optional=True,
                    tooltip="Gemini model to use for detection",
                ),
                IO.Float.Input(
                    "temperature",
                    default=0.0,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    optional=True,
                    tooltip="Lower = more deterministic detection",
                ),
                IO.Int.Input(
                    "max_objects",
                    default=20,
                    min=1,
                    max=100,
                    step=1,
                    optional=True,
                    tooltip="Maximum number of regions to return",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible detection. Randomizes by default.",
                ),
            ],
            outputs=[
                IO.Custom("ERPK_REGIONS").Output(
                    "regions",
                    tooltip="Detected regions as JSON for the Regional Prompt Builder's regions input.",
                ),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.utils import ImageConverter

        image = kwargs.get("image")
        objects = kwargs.get("objects", "")
        client = kwargs.get("client")
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.0)
        max_objects = kwargs.get("max_objects", 20)
        seed = kwargs.get("seed", -1)

        if model is None:
            model = GeminiClient.DEFAULT_MODEL
        if client is None:
            client = GeminiClient(api_key=None)

        prompt = detection_prompt(objects, max_objects)

        try:
            pil_images = [ImageConverter.tensor_to_pil(image)]

            response = await client.generate_content(
                prompt=prompt,
                images=pil_images,
                temperature=temperature,
                model=model,
                response_mime_type="application/json",
                response_schema=DETECTION_SCHEMA,
                seed=seed if seed != -1 else None,
            )

            if response.get("blocked", False):
                error_msg = f"Response blocked by safety filters. Reason: {response.get('finish_reason', 'UNKNOWN')}"
                print(f"[Gemini] Warning: {error_msg}")
                raise ValueError(error_msg)

            regions = detections_to_regions(response.get("text", ""), max_objects)
            print(f"[Gemini] Detected {len(regions)} region(s)")

            return IO.NodeOutput(json.dumps(regions))

        except Exception as e:
            error_msg = f"Failed to detect objects: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiSystemInstruction(IO.ComfyNode):
    """Sets a system-level instruction that persists across all requests for a Gemini client."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiSystemInstruction",
            display_name="Gemini System Instruction",
            category="ERPK/Gemini",
            description="Set a system-level instruction to guide model behavior.",
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    tooltip="Gemini API client to configure",
                ),
                IO.String.Input(
                    "system_instruction",
                    multiline=True,
                    default="",
                    tooltip="System-level instruction to guide model behavior",
                ),
            ],
            outputs=[
                IO.Custom("GEMINI_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        client = kwargs.get("client")
        system_instruction = kwargs.get("system_instruction", "")

        try:
            instruction = system_instruction.strip() if system_instruction else None

            if instruction:
                client.update_config(system_instruction=instruction)
                print(f"[Gemini] System instruction set ({len(instruction)} characters)")
            else:
                print("[Gemini] Warning: Empty system instruction, skipping")

            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to set system instruction: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiSafetySettings(IO.ComfyNode):
    """Configures content safety filters for Gemini API requests."""

    @classmethod
    def define_schema(cls):
        threshold_options = ["none", "low", "medium", "high"]
        return IO.Schema(
            node_id="GeminiSafetySettings",
            display_name="Gemini Safety Settings",
            category="ERPK/Gemini",
            description="Configure content safety filters for Gemini API requests.",
            inputs=[
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    tooltip="Gemini API client to configure",
                ),
                IO.Combo.Input(
                    "preset",
                    options=["balanced", "strict", "permissive", "custom"],
                    default="balanced",
                    optional=True,
                    tooltip="Safety preset or custom configuration",
                ),
                IO.Combo.Input(
                    "harassment",
                    options=threshold_options,
                    default="medium",
                    optional=True,
                    tooltip="Threshold for harassment content (only used if preset=custom)",
                ),
                IO.Combo.Input(
                    "hate_speech",
                    options=threshold_options,
                    default="medium",
                    optional=True,
                    tooltip="Threshold for hate speech (only used if preset=custom)",
                ),
                IO.Combo.Input(
                    "sexually_explicit",
                    options=threshold_options,
                    default="medium",
                    optional=True,
                    tooltip="Threshold for sexually explicit content (only used if preset=custom)",
                ),
                IO.Combo.Input(
                    "dangerous_content",
                    options=threshold_options,
                    default="medium",
                    optional=True,
                    tooltip="Threshold for dangerous content (only used if preset=custom)",
                ),
            ],
            outputs=[
                IO.Custom("GEMINI_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.utils import SafetySettings

        client = kwargs.get("client")
        preset = kwargs.get("preset", "balanced")
        harassment = kwargs.get("harassment", "medium")
        hate_speech = kwargs.get("hate_speech", "medium")
        sexually_explicit = kwargs.get("sexually_explicit", "medium")
        dangerous_content = kwargs.get("dangerous_content", "medium")

        try:
            if preset == "custom":
                safety_settings = SafetySettings.create_settings(
                    harassment=harassment,
                    hate_speech=hate_speech,
                    sexually_explicit=sexually_explicit,
                    dangerous_content=dangerous_content,
                )
                print(f"[Gemini] Custom safety settings configured")
            else:
                safety_settings = SafetySettings.get_preset(preset)
                print(f"[Gemini] Safety preset '{preset}' configured")

            client.update_config(safety_settings=safety_settings)

            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to configure safety settings: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiImageGeneration(IO.ComfyNode):
    """Generates images using Gemini's image generation models."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiImageGeneration",
            display_name="Gemini Image Generation",
            category="ERPK/Gemini",
            description="Generate images using Gemini's image generation models.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Description of the image to generate",
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (uses API key from config)",
                ),
                IO.Combo.Input(
                    "model",
                    options=IMAGE_MODELS,
                    default="gemini-3.1-flash-image-preview",
                    optional=True,
                    tooltip="Image generation model (overrides client model)",
                ),
                IO.Float.Input(
                    "temperature",
                    default=1.0,
                    min=0.0,
                    max=2.0,
                    step=0.1,
                    optional=True,
                    tooltip="Creativity level (higher = more creative)",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=["default", "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
                             "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"],
                    default="default",
                    optional=True,
                    tooltip="Image aspect ratio (all 14 ratios for 3.1 Flash; 10 for 3 Pro and 2.5 Flash)",
                ),
                IO.Combo.Input(
                    "image_size",
                    options=["default", "1K", "2K", "4K"],
                    default="default",
                    optional=True,
                    tooltip="Image resolution (1K-4K for 3.1 Flash and 3 Pro; 2.5 Flash fixed at 1024px)",
                ),
                IO.Combo.Input(
                    "response_modalities",
                    options=["IMAGE", "TEXT+IMAGE"],
                    default="IMAGE",
                    optional=True,
                    tooltip="What to return - image only or both text description and image",
                ),
                IO.Boolean.Input(
                    "enable_google_search",
                    default=False,
                    optional=True,
                    tooltip="Enable Google Search grounding (Gemini 3 models only, not 2.5 Flash)",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs. Randomizes by default.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.String.Output("description"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.utils import ImageConverter

        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        model = kwargs.get("model", "gemini-3.1-flash-image-preview")
        temperature = kwargs.get("temperature", 1.0)
        aspect_ratio = kwargs.get("aspect_ratio", "default")
        image_size = kwargs.get("image_size", "default")
        response_modalities = kwargs.get("response_modalities", "IMAGE")
        enable_google_search = kwargs.get("enable_google_search", False)
        seed = kwargs.get("seed", -1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            if client is not None:
                image_client = GeminiClient(
                    api_key=client.api_key,
                    model=model,
                )
                if client.safety_settings:
                    image_client.safety_settings = client.safety_settings
                if client.system_instruction:
                    image_client.system_instruction = client.system_instruction
            else:
                image_client = GeminiClient(
                    api_key=None,
                    model=model,
                )

            print(f"[Gemini] Generating image with model: {model}")
            print(f"[Gemini] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            if aspect_ratio != "default":
                print(f"[Gemini] Aspect ratio: {aspect_ratio}")
            if image_size != "default":
                print(f"[Gemini] Image size: {image_size}")

            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
                seed=seed if seed != -1 else None,
            )

            if response_modalities == "TEXT+IMAGE":
                config.response_modalities = ["TEXT", "IMAGE"]
            else:
                config.response_modalities = ["IMAGE"]

            if enable_google_search and model != "gemini-2.5-flash-image":
                config.tools = [{"google_search": {}}]
                print(f"[Gemini] Google Search grounding enabled")
            else:
                config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)

            image_config_params = {}
            if aspect_ratio != "default":
                image_config_params["aspect_ratio"] = aspect_ratio
            if image_size != "default" and model != "gemini-2.5-flash-image":
                if "image_size" in types.ImageConfig.model_fields:
                    image_config_params["image_size"] = image_size
                else:
                    print(f"[Gemini] Warning: image_size not supported by SDK, ignoring")

            if image_config_params:
                config.image_config = types.ImageConfig(**image_config_params)

            from .gemini_api.cooperative_call import call_with_retry
            response = await asyncio.to_thread(
                call_with_retry,
                image_client.client.models.generate_content,
                model=image_client.model_name,
                contents=[prompt.strip()],
                config=config,
            )

            image_tensor = None
            description_text = ""

            parts = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts = candidate.content.parts

            for part in (parts or []):
                if hasattr(part, 'text') and part.text:
                    description_text = part.text

                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image generated successfully: {image_tensor.shape}")
                    elif isinstance(image_data, str):
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image generated successfully: {image_tensor.shape}")

            if image_tensor is None:
                error_parts = ["No image was generated."]
                finish_reason = None

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            error_parts.append(f"Model returned text: {part.text}")

                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    error_parts.append(f"Finish reason: {finish_reason}")

                if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                    error_parts.append(f"Blocked: {response.prompt_feedback.block_reason}")

                hint = _finish_reason_hint(finish_reason)
                if hint:
                    error_parts.append(f"Hint: {hint}")

                _dump_response_payload(response)

                raise ValueError(" ".join(error_parts))

            if description_text:
                print(f"[Gemini] Also got description: {description_text[:100]}...")

            from ..utils.inline_preview import inline_preview_image
            ui = inline_preview_image(cls, image_tensor, slot=0)
            return IO.NodeOutput(image_tensor, description_text, ui=ui)

        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)


class GeminiImageEdit(IO.ComfyNode):
    """Uses Gemini's image generation models to edit/modify existing images based on text prompts.
    Gemini 3 Pro supports up to 14 reference images (up to 6 objects, up to 5 humans)."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="GeminiImageEdit",
            display_name="Gemini Image Edit",
            category="ERPK/Gemini",
            description="Edit images using Gemini's image generation models.",
            not_idempotent=True,
            inputs=[
                IO.Image.Input(
                    "image",
                    tooltip="Reference image(s) to edit. Use Batch Images node to combine multiple images (up to 14).",
                ),
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Describe the edit. Reference images by order (first/second), content (the logo), or role (the style reference)",
                ),
                IO.Custom("GEMINI_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Gemini API client from Gemini API Config node (uses API key from config)",
                ),
                IO.Combo.Input(
                    "model",
                    options=IMAGE_MODELS,
                    default="gemini-3.1-flash-image-preview",
                    optional=True,
                    tooltip="Image generation model (overrides client model)",
                ),
                IO.Float.Input(
                    "temperature",
                    default=1.0,
                    min=0.0,
                    max=2.0,
                    step=0.1,
                    optional=True,
                    tooltip="Creativity level (higher = more creative)",
                ),
                IO.Combo.Input(
                    "aspect_ratio",
                    options=["default", "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
                             "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"],
                    default="default",
                    optional=True,
                    tooltip="Image aspect ratio (all 14 ratios for 3.1 Flash; 10 for 3 Pro and 2.5 Flash)",
                ),
                IO.Combo.Input(
                    "image_size",
                    options=["default", "1K", "2K", "4K"],
                    default="default",
                    optional=True,
                    tooltip="Image resolution (1K-4K for 3.1 Flash and 3 Pro; 2.5 Flash fixed at 1024px)",
                ),
                IO.Combo.Input(
                    "response_modalities",
                    options=["IMAGE", "TEXT+IMAGE"],
                    default="IMAGE",
                    optional=True,
                    tooltip="What to return - image only or both text description and image",
                ),
                IO.Boolean.Input(
                    "enable_google_search",
                    default=False,
                    optional=True,
                    tooltip="Enable Google Search grounding (Gemini 3 models only, not 2.5 Flash)",
                ),
                IO.Image.Input(
                    "additional_images",
                    optional=True,
                    tooltip="Optional additional reference images (combined with primary image input, up to 14 total)",
                ),
                IO.Custom("ERPK_IMAGE_REFS").Input(
                    "image_refs",
                    optional=True,
                    tooltip="Ordered reference images from a Regional Prompt "
                            "Builder; sent right after the primary image so "
                            "the prompt's image numbers line up",
                ),
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed for reproducible outputs. Randomizes by default.",
                ),
            ],
            outputs=[
                IO.Image.Output("image"),
                IO.String.Output("description"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        from .gemini_api.utils import ImageConverter

        image = kwargs.get("image")
        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        model = kwargs.get("model", "gemini-3.1-flash-image-preview")
        temperature = kwargs.get("temperature", 1.0)
        aspect_ratio = kwargs.get("aspect_ratio", "default")
        image_size = kwargs.get("image_size", "default")
        response_modalities = kwargs.get("response_modalities", "IMAGE")
        enable_google_search = kwargs.get("enable_google_search", False)
        additional_images = kwargs.get("additional_images")
        image_refs = kwargs.get("image_refs")
        seed = kwargs.get("seed", -1)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            if client is not None:
                image_client = GeminiClient(
                    api_key=client.api_key,
                    model=model,
                )
                if client.safety_settings:
                    image_client.safety_settings = client.safety_settings
                if client.system_instruction:
                    image_client.system_instruction = client.system_instruction
            else:
                image_client = GeminiClient(
                    api_key=None,
                    model=model,
                )

            pil_images = ImageConverter.tensors_to_pil_list(image)
            # Refs precede additional_images so the prompt's image numbering
            # (base image is 1, refs follow in region order) holds.
            for ref in image_refs or []:
                pil_images.extend(ImageConverter.tensors_to_pil_list(ref))
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

            if num_images > 14:
                print(f"[Gemini] Warning: Using {num_images} images. Gemini 3 Pro supports up to 14 reference images.")

            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature,
                seed=seed if seed != -1 else None,
            )

            if response_modalities == "TEXT+IMAGE":
                config.response_modalities = ["TEXT", "IMAGE"]
            else:
                config.response_modalities = ["IMAGE"]

            if enable_google_search and model != "gemini-2.5-flash-image":
                config.tools = [{"google_search": {}}]
                print(f"[Gemini] Google Search grounding enabled")
            else:
                config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)

            image_config_params = {}
            if aspect_ratio != "default":
                image_config_params["aspect_ratio"] = aspect_ratio
            if image_size != "default" and model != "gemini-2.5-flash-image":
                if "image_size" in types.ImageConfig.model_fields:
                    image_config_params["image_size"] = image_size
                else:
                    print(f"[Gemini] Warning: image_size not supported by SDK, ignoring")

            if image_config_params:
                config.image_config = types.ImageConfig(**image_config_params)

            contents = pil_images + [prompt.strip()]

            from .gemini_api.cooperative_call import call_with_retry
            response = await asyncio.to_thread(
                call_with_retry,
                image_client.client.models.generate_content,
                model=image_client.model_name,
                contents=contents,
                config=config,
            )

            image_tensor = None
            description_text = ""

            parts = None
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts = candidate.content.parts

            for part in (parts or []):
                if hasattr(part, 'text') and part.text:
                    description_text = part.text

                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data

                    if not image_data or (hasattr(image_data, '__len__') and len(image_data) == 0):
                        continue

                    if isinstance(image_data, bytes):
                        image_tensor = ImageConverter.bytes_to_tensor(image_data)
                        print(f"[Gemini] Image edited successfully: {image_tensor.shape}")
                    elif isinstance(image_data, str):
                        import base64
                        decoded_data = base64.b64decode(image_data)
                        if len(decoded_data) > 0:
                            image_tensor = ImageConverter.bytes_to_tensor(decoded_data)
                            print(f"[Gemini] Image edited successfully: {image_tensor.shape}")

            if image_tensor is None:
                error_parts = ["No image was generated."]
                finish_reason = None

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            error_parts.append(f"Model returned text: {part.text}")

                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    error_parts.append(f"Finish reason: {finish_reason}")

                if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                    error_parts.append(f"Blocked: {response.prompt_feedback.block_reason}")

                hint = _finish_reason_hint(finish_reason)
                if hint:
                    error_parts.append(f"Hint: {hint}")

                _dump_response_payload(response)

                raise ValueError(" ".join(error_parts))

            if description_text:
                print(f"[Gemini] Also got description: {description_text[:100]}...")

            from ..utils.inline_preview import inline_preview_image
            ui = inline_preview_image(cls, image_tensor, slot=0)
            return IO.NodeOutput(image_tensor, description_text, ui=ui)

        except Exception as e:
            error_msg = f"Failed to edit image: {str(e)}"
            print(f"[Gemini] Error: {error_msg}")
            raise ValueError(error_msg)
