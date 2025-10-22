"""
Core Claude API Nodes

Provides the fundamental nodes for Claude API integration in ComfyUI.
"""

from .claude_api.client import ClaudeClient


class ClaudeAPIClient:
    """
    Claude API Client Node

    Initializes and provides a Claude API client for use by other nodes.
    Handles API key configuration and client settings.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (
                    [
                        "claude-sonnet-4-5-20250929",
                        "claude-opus-4",
                        "claude-haiku-4-5",
                    ],
                    {
                        "default": "claude-sonnet-4-5-20250929",
                        "tooltip": "Claude model to use. Sonnet 4.5 offers best balance of performance and cost."
                    }
                ),
            },
            "optional": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Anthropic API key. If empty, will use ANTHROPIC_API_KEY env var or config.ini."
                    }
                ),
                "enable_streaming": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable streaming responses. Note: ComfyUI may not display streaming in real-time."
                    }
                ),
                "enable_caching": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Enable prompt caching for cost optimization (up to 90% savings on repeated prompts)."
                    }
                ),
            }
        }

    RETURN_TYPES = ("CLAUDE_API_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "create_client"
    CATEGORY = "ERPK/Claude"

    def create_client(
        self,
        model: str,
        api_key: str = "",
        enable_streaming: bool = False,
        enable_caching: bool = True
    ):
        """
        Create and return a Claude API client.

        Args:
            model: Claude model to use
            api_key: Optional API key
            enable_streaming: Enable streaming
            enable_caching: Enable prompt caching

        Returns:
            Tuple containing the client instance
        """
        try:
            client = ClaudeClient(
                api_key=api_key if api_key.strip() else None,
                model=model,
                enable_streaming=enable_streaming,
                enable_caching=enable_caching
            )

            print(f"[Claude] Client initialized with model: {model}")
            print(f"[Claude] Streaming: {'enabled' if enable_streaming else 'disabled'}")
            print(f"[Claude] Caching: {'enabled' if enable_caching else 'disabled'}")

            return (client,)

        except Exception as e:
            error_msg = f"Failed to create Claude client: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)


class ClaudeUsageStats:
    """
    Claude Usage Statistics Node

    Displays token usage and cost statistics for a Claude client.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("CLAUDE_API_CLIENT", {"tooltip": "Claude API client"}),
            },
            "optional": {
                "reset_stats": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Reset usage statistics after displaying"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("stats",)
    FUNCTION = "get_stats"
    CATEGORY = "ERPK/Claude"
    OUTPUT_NODE = True

    def get_stats(self, client: ClaudeClient, reset_stats: bool = False):
        """
        Get usage statistics from the client.

        Args:
            client: Claude API client
            reset_stats: Whether to reset stats after retrieving

        Returns:
            Tuple containing formatted stats string
        """
        try:
            stats = client.get_usage_stats()

            # Format stats as readable string
            stats_str = f"""Claude API Usage Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token Usage:
  Input Tokens:           {stats['input_tokens']:,}
  Output Tokens:          {stats['output_tokens']:,}
  Cache Read Tokens:      {stats['cache_read_tokens']:,}
  Cache Creation Tokens:  {stats['cache_creation_tokens']:,}

Cost (USD):
  Input Cost:       ${stats['input_cost_usd']:.4f}
  Output Cost:      ${stats['output_cost_usd']:.4f}
  Cache Savings:    ${stats['cache_savings_usd']:.4f}
  ─────────────────────────────────
  Total Cost:       ${stats['total_cost_usd']:.4f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            print(f"\n{stats_str}\n")

            if reset_stats:
                client.reset_usage_stats()
                print("[Claude] Usage statistics reset")

            return (stats_str,)

        except Exception as e:
            error_msg = f"Failed to get usage stats: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return (error_msg,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudeAPIClient": ClaudeAPIClient,
    "ClaudeUsageStats": ClaudeUsageStats,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeAPIClient": "Claude API Client",
    "ClaudeUsageStats": "Claude Usage Stats",
}
