# ABOUTME: ComfyUI V3 node for counting tokens and estimating Claude API costs.
# ABOUTME: Supports API-based accurate counting or estimation, with pricing from pricing.json.

import os
import json
from comfy_api.latest import IO


class ClaudeTokenCounter(IO.ComfyNode):
    """Counts tokens in text and provides cost estimates for Claude API usage."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeTokenCounter",
            display_name="Claude Token Counter",
            category="ERPK/Claude",
            description="Count tokens and estimate API costs for Claude models.",
            is_output_node=True,
            inputs=[
                IO.String.Input(
                    "text",
                    multiline=True,
                    default="",
                    tooltip="Text to count tokens for",
                ),
                IO.Combo.Input(
                    "model",
                    options=[
                        "claude-sonnet-4-6",
                        "claude-opus-4-6",
                        "claude-haiku-4-5-20251001",
                        "claude-sonnet-4-5-20250929",
                    ],
                    default="claude-sonnet-4-6",
                    tooltip="Model for token counting and cost estimation",
                ),
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Optional: Connect client for accurate API-based counting (otherwise uses ~4 chars/token estimation)",
                ),
            ],
            outputs=[
                IO.Int.Output("token_count"),
                IO.String.Output("summary"),
            ],
        )

    @classmethod
    def load_pricing(cls):
        """Load pricing from pricing.json file."""
        try:
            pricing_file = os.path.join(os.path.dirname(__file__), "pricing.json")
            with open(pricing_file, 'r') as f:
                pricing_data = json.load(f)

            pricing = {}
            for model_id, model_data in pricing_data.get("models", {}).items():
                pricing[model_id] = {
                    "input": model_data.get("input_price_per_mtok", 0),
                    "output": model_data.get("output_price_per_mtok", 0),
                }

            return pricing, pricing_data.get("_last_updated", "Unknown")
        except Exception as e:
            print(f"[Claude] Warning: Could not load pricing.json, using fallback: {e}")
            return {
                "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
                "claude-opus-4-6": {"input": 5.0, "output": 25.0},
                "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
                "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
            }, "2026-02-20"

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.utils import TokenManager

        text = kwargs.get("text", "")
        model = kwargs.get("model", "claude-sonnet-4-6")
        client = kwargs.get("client")

        if not text:
            return IO.NodeOutput(0, "No text provided")

        try:
            if client:
                token_count = client.count_tokens([{"role": "user", "content": text}])
                counting_method = "Anthropic API (accurate)"
            else:
                token_manager = TokenManager(model=model)
                token_count = token_manager.estimate_tokens(text)
                counting_method = "Estimation (~4 chars/token)"

            token_manager = TokenManager(model=model)
            context_window = token_manager.context_window

            context_percentage = (token_count / context_window) * 100

            pricing_data, last_updated = cls.load_pricing()
            pricing = pricing_data.get(model, pricing_data.get("claude-sonnet-4-6", {"input": 3.0, "output": 15.0}))

            input_cost_per_1k = (token_count / 1_000_000) * pricing["input"]
            output_cost_per_1k = (token_count / 1_000_000) * pricing["output"]

            summary = f"""Token Count Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Text Length:      {len(text):,} characters
Token Count:      {token_count:,} tokens
Counting Method:  {counting_method}

Model:            {model}
Context Window:   {context_window:,} tokens
Context Usage:    {context_percentage:.1f}%

Cost Estimates (USD):
  As Input:    ${input_cost_per_1k:.6f}
  As Output:   ${output_cost_per_1k:.6f}

Per 1K Repetitions:
  As Input:    ${input_cost_per_1k * 1000:.4f}
  As Output:   ${output_cost_per_1k * 1000:.4f}

Pricing last updated: {last_updated}
Source: anthropic.com/pricing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            if context_percentage > 90:
                summary += "\n\nWARNING: Using >90% of context window!"
            elif context_percentage > 75:
                summary += "\n\nCAUTION: Using >75% of context window"

            print(f"\n{summary}\n")
            return IO.NodeOutput(token_count, summary)

        except Exception as e:
            error_msg = f"Failed to count tokens: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return IO.NodeOutput(0, error_msg)
