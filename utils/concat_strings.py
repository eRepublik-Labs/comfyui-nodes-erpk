# ABOUTME: ComfyUI node for concatenating multiple string inputs with configurable delimiters.
# ABOUTME: Supports dynamic input count via JavaScript widgets, per-field naming, and various delimiter options.

import json


class ConcatenateStrings:
    """
    Concatenate multiple string inputs with configurable delimiter.
    Supports dynamic number of inputs with optional per-field names.
    UI is managed by JavaScript - see web/concat_strings.js
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {},
            "hidden": {
                "entries": "STRING",
                "delimiter": "STRING",
                "includeNames": "BOOLEAN",
                "labelOnSameLine": "BOOLEAN",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "concatenate"
    CATEGORY = "ERPK/utils"
    DESCRIPTION = """
Concatenate multiple text inputs into a single output.

- Click **+ Add Input** to add more text fields
- Each field has a **Label** and **Text** area
- Enable **Include Labels in Output** to prefix values with their labels
- Set the **Delimiter** to control how values are joined (use \\n for newlines)
"""

    def concatenate(self, entries=None, delimiter="\\n", includeNames=False, labelOnSameLine=True, **kwargs):
        # Parse entries from JSON if it's a string
        if isinstance(entries, str):
            try:
                entries = json.loads(entries)
            except (json.JSONDecodeError, TypeError):
                entries = []

        if not entries:
            entries = []

        # Handle escape sequences in delimiter (\n, \t, etc.)
        delimiter = delimiter.encode('utf-8').decode('unicode_escape')

        parts = []
        for entry in entries:
            text = entry.get("text", "")
            if not text:
                continue

            if includeNames:
                label = entry.get("label", "")
                if label:
                    if labelOnSameLine:
                        parts.append(f"{label}: {text}")
                    else:
                        parts.append(f"{label}:\n{text}")
                else:
                    parts.append(text)
            else:
                parts.append(text)

        return (delimiter.join(parts),)


NODE_CLASS_MAPPINGS = {
    "ERPK_ConcatenateStrings": ConcatenateStrings,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ERPK_ConcatenateStrings": "Concatenate Strings (ERPK)",
}
