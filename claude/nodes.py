# ABOUTME: ComfyUI V3 nodes for Claude API client initialization and usage statistics.
# ABOUTME: ClaudeAPIClient creates the client; ClaudeUsageStats displays token/cost info.

from comfy_api.latest import IO


class ClaudeAPIClient(IO.ComfyNode):
    """Initializes and provides a Claude API client for use by other nodes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeAPIClient",
            display_name="Claude API Client",
            category="ERPK/Claude",
            description="Initialize a Claude API client with model and settings.",
            inputs=[
                IO.Combo.Input(
                    "model",
                    options=[
                        "claude-sonnet-4-6",
                        "claude-opus-4-6",
                        "claude-haiku-4-5-20251001",
                        "claude-sonnet-4-5-20250929",
                    ],
                    default="claude-sonnet-4-6",
                    tooltip="Claude model to use. Sonnet 4.6 offers best balance of performance and cost.",
                ),
                IO.String.Input(
                    "api_key",
                    default="",
                    optional=True,
                    tooltip="Anthropic API key. If empty, will use ANTHROPIC_API_KEY env var or config.ini.",
                ),
                IO.Boolean.Input(
                    "enable_streaming",
                    default=False,
                    optional=True,
                    tooltip="Enable streaming responses. Note: ComfyUI may not display streaming in real-time.",
                ),
                IO.Boolean.Input(
                    "enable_caching",
                    default=True,
                    optional=True,
                    tooltip="Enable prompt caching for cost optimization (up to 90% savings on repeated prompts).",
                ),
            ],
            outputs=[
                IO.Custom("CLAUDE_API_CLIENT").Output("client"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.client import ClaudeClient

        model = kwargs.get("model", "claude-sonnet-4-6")
        api_key = kwargs.get("api_key", "")
        enable_streaming = kwargs.get("enable_streaming", False)
        enable_caching = kwargs.get("enable_caching", True)

        try:
            client = ClaudeClient(
                api_key=api_key if api_key.strip() else None,
                model=model,
                enable_streaming=enable_streaming,
                enable_caching=enable_caching,
            )

            print(f"[Claude] Client initialized with model: {model}")
            print(f"[Claude] Streaming: {'enabled' if enable_streaming else 'disabled'}")
            print(f"[Claude] Caching: {'enabled' if enable_caching else 'disabled'}")

            return IO.NodeOutput(client)

        except Exception as e:
            error_msg = f"Failed to create Claude client: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)


class ClaudeUsageStats(IO.ComfyNode):
    """Displays token usage and cost statistics for a Claude client."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeUsageStats",
            display_name="Claude Usage Stats",
            category="ERPK/Claude",
            description="Display token usage and cost statistics for a Claude client.",
            is_output_node=True,
            inputs=[
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    tooltip="Claude API client",
                ),
                IO.Boolean.Input(
                    "reset_stats",
                    default=False,
                    optional=True,
                    tooltip="Reset usage statistics after displaying",
                ),
            ],
            outputs=[
                IO.String.Output("stats"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        client = kwargs.get("client")
        reset_stats = kwargs.get("reset_stats", False)

        try:
            stats = client.get_usage_stats()

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

            return IO.NodeOutput(stats_str)

        except Exception as e:
            error_msg = f"Failed to get usage stats: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return IO.NodeOutput(error_msg)
