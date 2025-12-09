"""
Claude Token Counter Node

Utility for counting tokens and estimating costs.
"""

import os
import json
from .claude_api.client import ClaudeClient
from .claude_api.utils import TokenManager


class ClaudeTokenCounter:
    """
    Claude Token Counter Node

    Counts tokens in text and provides cost estimates for Claude API usage.

    Useful for:
    - Checking if text fits in context window
    - Estimating API costs before requests
    - Optimizing prompt lengths
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text to count tokens for"
                    }
                ),
                "model": (
                    [
                        "claude-sonnet-4-5-20250929",
                        "claude-opus-4",
                        "claude-haiku-4-5",
                    ],
                    {
                        "default": "claude-sonnet-4-5-20250929",
                        "tooltip": "Model for token counting and cost estimation"
                    }
                ),
            },
            "optional": {
                "client": (
                    "CLAUDE_API_CLIENT",
                    {"tooltip": "Optional: Connect client for accurate API-based counting (otherwise uses ~4 chars/token estimation)"}
                ),
            }
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("token_count", "summary")
    FUNCTION = "count_tokens"
    CATEGORY = "ERPK/Claude"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False, False)

    @classmethod
    def load_pricing(cls):
        """Load pricing from pricing.json file."""
        try:
            pricing_file = os.path.join(os.path.dirname(__file__), "pricing.json")
            with open(pricing_file, 'r') as f:
                pricing_data = json.load(f)

            # Convert to simple dict format
            pricing = {}
            for model_id, model_data in pricing_data.get("models", {}).items():
                pricing[model_id] = {
                    "input": model_data.get("input_price_per_mtok", 0),
                    "output": model_data.get("output_price_per_mtok", 0)
                }

            return pricing, pricing_data.get("_last_updated", "Unknown")
        except Exception as e:
            print(f"[Claude] Warning: Could not load pricing.json, using fallback: {e}")
            # Fallback pricing
            return {
                "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
                "claude-opus-4": {"input": 15.0, "output": 75.0},
                "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
            }, "2025-10-22"

    def count_tokens(
        self,
        text: str,
        model: str,
        client: ClaudeClient = None
    ):
        """
        Count tokens in text and provide cost estimates.

        Args:
            text: Text to count
            model: Model to use for pricing
            client: Optional client for accurate counting

        Returns:
            Tuple of (token_count, formatted_summary)
        """
        if not text:
            return (0, "No text provided")

        try:
            # Count tokens (accurate with Anthropic API if client provided, estimated otherwise)
            if client:
                token_count = client.count_tokens([{"role": "user", "content": text}])
                counting_method = "Anthropic API (accurate)"
            else:
                token_manager = TokenManager(model=model)
                token_count = token_manager.estimate_tokens(text)
                counting_method = "Estimation (~4 chars/token)"

            # Get context window size
            token_manager = TokenManager(model=model)
            context_window = token_manager.context_window

            # Calculate percentages
            context_percentage = (token_count / context_window) * 100

            # Load pricing
            pricing_data, last_updated = self.load_pricing()
            pricing = pricing_data.get(model, pricing_data.get("claude-sonnet-4-5-20250929", {"input": 3.0, "output": 15.0}))

            # Calculate costs
            input_cost_per_1k = (token_count / 1_000_000) * pricing["input"]
            output_cost_per_1k = (token_count / 1_000_000) * pricing["output"]

            # Build summary
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

            # Warnings
            if context_percentage > 90:
                summary += "\n\n⚠️  WARNING: Using >90% of context window!"
            elif context_percentage > 75:
                summary += "\n\n⚠️  CAUTION: Using >75% of context window"

            print(f"\n{summary}\n")

            return (token_count, summary)

        except Exception as e:
            error_msg = f"Failed to count tokens: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return (0, error_msg)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudeTokenCounter": ClaudeTokenCounter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeTokenCounter": "Claude Token Counter",
}
