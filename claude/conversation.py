"""
Claude Conversation Node

Maintains multi-turn conversations with message history.
"""

from .claude_api.client import ClaudeClient
from .claude_api.utils import TokenManager


class ClaudeConversation:
    """
    Claude Conversation Node

    Maintains a multi-turn conversation with Claude, preserving message history
    across multiple node executions.

    Features:
    - Message history management
    - Automatic context window trimming
    - Conversation state preservation
    - Token usage tracking
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": (
                    "CLAUDE_API_CLIENT",
                    {"tooltip": "Claude API client from Claude API Client node"}
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
                "conversation_history": (
                    "CLAUDE_CONVERSATION",
                    {"tooltip": "Previous conversation state (connect from previous conversation node)"}
                ),
                "system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional system prompt (only used for new conversations)"
                    }
                ),
                "auto_trim": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Automatically trim old messages to fit context window"
                    }
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
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Creativity level"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 2048,
                        "min": 256,
                        "max": 4096,
                        "step": 128,
                        "tooltip": "Maximum length of response"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "CLAUDE_CONVERSATION")
    RETURN_NAMES = ("response", "conversation_history")
    FUNCTION = "chat"
    CATEGORY = "ERPK/Claude"

    def chat(
        self,
        client: ClaudeClient,
        prompt: str,
        conversation_history=None,
        system_prompt: str = "",
        auto_trim: bool = True,
        reset_conversation: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Continue or start a conversation with Claude.

        Args:
            client: Claude API client
            prompt: User message
            conversation_history: Previous conversation state
            system_prompt: Optional system prompt (for new conversations)
            auto_trim: Auto-trim to context window
            reset_conversation: Start new conversation
            temperature: Creativity level
            max_tokens: Max output tokens

        Returns:
            Tuple of (response_text, updated_conversation_state)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Initialize or continue conversation
            if reset_conversation or conversation_history is None:
                messages = []
                system = system_prompt.strip() if system_prompt and system_prompt.strip() else None
                print("[Claude] Starting new conversation")
            else:
                messages = conversation_history.get("messages", []).copy()
                system = conversation_history.get("system")
                print(f"[Claude] Continuing conversation ({len(messages)} messages in history)")

            # Add user message
            messages.append({"role": "user", "content": prompt.strip()})

            # Trim messages if needed
            if auto_trim:
                token_manager = TokenManager(model=client.model)
                messages, removed_count = token_manager.trim_messages_to_fit(
                    messages=messages,
                    system=system,
                    reserve_tokens=max_tokens + 1000  # Reserve space for response + buffer
                )
                if removed_count > 0:
                    print(f"[Claude] Trimmed {removed_count} old messages to fit context window")

            # Consolidate consecutive messages from same role
            token_manager = TokenManager(model=client.model)
            messages = token_manager.consolidate_consecutive_messages(messages)

            # Validate messages
            if not token_manager.validate_message_roles(messages):
                print("[Claude] Warning: Message role pattern may be invalid, attempting to fix...")
                # Ensure it starts with user and consolidate
                if messages[0].get("role") != "user":
                    # Prepend a user message if needed
                    messages = [{"role": "user", "content": "(Continuing conversation)"}] + messages
                messages = token_manager.consolidate_consecutive_messages(messages)

            # Send request
            response = client.send_request(
                messages=messages,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract response text
            if hasattr(response, 'content') and len(response.content) > 0:
                response_text = response.content[0].text
            else:
                raise ValueError("Invalid response format from Claude API")

            # Add assistant response to history
            messages.append({"role": "assistant", "content": response_text})

            # Build updated conversation state
            updated_state = {
                "messages": messages,
                "system": system
            }

            print(f"[Claude] Response generated ({len(response_text)} characters, {len(messages)} messages in history)")

            return (response_text, updated_state)

        except Exception as e:
            error_msg = f"Failed in conversation: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)


class ClaudeConversationInfo:
    """
    Claude Conversation Info Node

    Displays information about a conversation's state.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conversation_history": (
                    "CLAUDE_CONVERSATION",
                    {"tooltip": "Conversation state to inspect"}
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("info",)
    FUNCTION = "get_info"
    CATEGORY = "ERPK/Claude"
    OUTPUT_NODE = True

    def get_info(self, conversation_history):
        """
        Get information about conversation state.

        Args:
            conversation_history: Conversation state

        Returns:
            Tuple containing formatted info string
        """
        try:
            messages = conversation_history.get("messages", [])
            system = conversation_history.get("system")

            # Count messages by role
            user_count = sum(1 for msg in messages if msg.get("role") == "user")
            assistant_count = sum(1 for msg in messages if msg.get("role") == "assistant")

            # Estimate tokens
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

            return (info_str,)

        except Exception as e:
            error_msg = f"Failed to get conversation info: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            return (error_msg,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudeConversation": ClaudeConversation,
    "ClaudeConversationInfo": ClaudeConversationInfo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudeConversation": "Claude Conversation",
    "ClaudeConversationInfo": "Claude Conversation Info",
}
