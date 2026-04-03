# ABOUTME: ComfyUI V3 nodes for multi-turn Claude conversations with message history.
# ABOUTME: ClaudeConversation manages chat state; ClaudeConversationInfo displays conversation details.

from comfy_api.latest import IO


class ClaudeConversation(IO.ComfyNode):
    """Maintains a multi-turn conversation with Claude, preserving message history."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeConversation",
            display_name="Claude Conversation",
            category="ERPK/Claude",
            description="Multi-turn conversation with Claude, preserving message history across executions.",
            not_idempotent=True,
            inputs=[
                IO.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="Your message in the conversation",
                ),
                IO.Custom("CLAUDE_API_CLIENT").Input(
                    "client",
                    optional=True,
                    tooltip="Claude API client (optional if API key is configured in Settings)",
                ),
                IO.Custom("CLAUDE_CONVERSATION").Input(
                    "conversation_history",
                    optional=True,
                    tooltip="Previous conversation state (connect from previous conversation node)",
                ),
                IO.String.Input(
                    "system_prompt",
                    multiline=True,
                    default="",
                    optional=True,
                    tooltip="Optional system prompt (only used for new conversations)",
                ),
                IO.Boolean.Input(
                    "auto_trim",
                    default=True,
                    optional=True,
                    tooltip="Automatically trim old messages to fit context window",
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
                    max=1.0,
                    step=0.05,
                    optional=True,
                    tooltip="Creativity level",
                ),
                IO.Int.Input(
                    "max_tokens",
                    default=2048,
                    min=256,
                    max=4096,
                    step=128,
                    optional=True,
                    tooltip="Maximum length of response",
                ),
                IO.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=2**31 - 1,
                    control_after_generate=True,
                    tooltip="Seed for cache control. Randomizes by default to ensure fresh results each run.",
                ),
            ],
            outputs=[
                IO.String.Output("response"),
                IO.Custom("CLAUDE_CONVERSATION").Output("conversation_history"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.client import ClaudeClient
        from .claude_api.utils import TokenManager

        prompt = kwargs.get("prompt", "")
        client = kwargs.get("client")
        conversation_history = kwargs.get("conversation_history")
        system_prompt = kwargs.get("system_prompt", "")
        auto_trim = kwargs.get("auto_trim", True)
        reset_conversation = kwargs.get("reset_conversation", False)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2048)

        if client is None:
            client = ClaudeClient(api_key=None)

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            if reset_conversation or conversation_history is None:
                messages = []
                system = system_prompt.strip() if system_prompt and system_prompt.strip() else None
                print("[Claude] Starting new conversation")
            else:
                messages = conversation_history.get("messages", []).copy()
                system = conversation_history.get("system")
                print(f"[Claude] Continuing conversation ({len(messages)} messages in history)")

            messages.append({"role": "user", "content": prompt.strip()})

            if auto_trim:
                token_manager = TokenManager(model=client.model)
                messages, removed_count = token_manager.trim_messages_to_fit(
                    messages=messages,
                    system=system,
                    reserve_tokens=max_tokens + 1000,
                )
                if removed_count > 0:
                    print(f"[Claude] Trimmed {removed_count} old messages to fit context window")

            token_manager = TokenManager(model=client.model)
            messages = token_manager.consolidate_consecutive_messages(messages)

            if not token_manager.validate_message_roles(messages):
                print("[Claude] Warning: Message role pattern may be invalid, attempting to fix...")
                if messages[0].get("role") != "user":
                    messages = [{"role": "user", "content": "(Continuing conversation)"}] + messages
                messages = token_manager.consolidate_consecutive_messages(messages)

            response = client.send_request(
                messages=messages,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if hasattr(response, 'content') and len(response.content) > 0:
                response_text = response.content[0].text
            else:
                raise ValueError("Invalid response format from Claude API")

            messages.append({"role": "assistant", "content": response_text})

            updated_state = {
                "messages": messages,
                "system": system,
            }

            print(f"[Claude] Response generated ({len(response_text)} characters, {len(messages)} messages in history)")

            return IO.NodeOutput(response_text, updated_state)

        except Exception as e:
            error_msg = f"Failed in conversation: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)


class ClaudeConversationInfo(IO.ComfyNode):
    """Displays information about a conversation's state."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ClaudeConversationInfo",
            display_name="Claude Conversation Info",
            category="ERPK/Claude",
            description="Display information about a conversation's state and token usage.",
            is_output_node=True,
            inputs=[
                IO.Custom("CLAUDE_CONVERSATION").Input(
                    "conversation_history",
                    tooltip="Conversation state to inspect",
                ),
            ],
            outputs=[
                IO.String.Output("info"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        from .claude_api.utils import TokenManager

        conversation_history = kwargs.get("conversation_history")

        try:
            messages = conversation_history.get("messages", [])
            system = conversation_history.get("system")

            user_count = sum(1 for msg in messages if msg.get("role") == "user")
            assistant_count = sum(1 for msg in messages if msg.get("role") == "assistant")

            token_manager = TokenManager()
            total_tokens = token_manager.estimate_message_tokens(messages)
            if system:
                total_tokens += token_manager.estimate_tokens(system)

            info_str = f"""Conversation Information:
━━━━━━━━━━━━━━━━━━━━━━━━
Messages:
  User:      {user_count}
  Assistant: {assistant_count}
  Total:     {len(messages)}

System Prompt:
  {"Yes" if system else "No"}

Estimated Tokens:
  ~{total_tokens:,} tokens

Context Usage:
  ~{(total_tokens / 200000) * 100:.1f}% of 200k window
━━━━━━━━━━━━━━━━━━━━━━━━"""

            print(f"\n{info_str}\n")
            return IO.NodeOutput(info_str)

        except Exception as e:
            error_msg = f"Failed to get conversation info: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return IO.NodeOutput(error_msg)
