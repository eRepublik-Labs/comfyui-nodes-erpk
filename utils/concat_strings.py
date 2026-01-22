# ABOUTME: ComfyUI node for concatenating multiple string inputs with configurable delimiters.
# ABOUTME: Supports up to 10 connectable text inputs, optional labels, and escape sequences.

MAX_INPUTS = 10


class ConcatenateStrings:
    """
    Concatenate multiple string inputs with configurable delimiter.
    Each input slot accepts connections from other nodes or manual text entry.
    """

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {},
            "optional": {
                "delimiter": ("STRING", {"default": "\\n", "multiline": False}),
                "include_labels": ("BOOLEAN", {"default": False}),
                "label_on_same_line": ("BOOLEAN", {"default": True}),
            },
        }

        # Add text and label input pairs
        for i in range(1, MAX_INPUTS + 1):
            inputs["optional"][f"text_{i}"] = ("STRING", {
                "default": "",
                "multiline": True,
            })
            inputs["optional"][f"label_{i}"] = ("STRING", {
                "default": "",
                "multiline": False,
            })

        return inputs

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "concatenate"
    CATEGORY = "ERPK/utils"
    DESCRIPTION = """
Concatenate multiple text inputs into a single output.

- Connect STRING outputs from other nodes to text_1, text_2, etc.
- Optionally set labels for each input (label_1, label_2, etc.)
- Enable **include_labels** to prefix values with their labels
- Set **delimiter** to control how values are joined (use \\n for newlines, \\t for tabs)
"""

    def concatenate(
        self,
        delimiter="\\n",
        include_labels=False,
        label_on_same_line=True,
        **kwargs
    ):
        # Handle escape sequences in delimiter (\n, \t, etc.)
        try:
            delimiter = delimiter.encode('utf-8').decode('unicode_escape')
        except (UnicodeDecodeError, ValueError):
            pass  # Keep delimiter as-is if escape processing fails

        parts = []
        for i in range(1, MAX_INPUTS + 1):
            text = kwargs.get(f"text_{i}", "")
            if not text:
                continue

            if include_labels:
                label = kwargs.get(f"label_{i}", "")
                if label:
                    if label_on_same_line:
                        parts.append(f"{label} {text}")
                    else:
                        parts.append(f"{label}\n{text}")
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
