# ABOUTME: ComfyUI V3 node for concatenating multiple string inputs with configurable delimiters.
# ABOUTME: Supports up to 10 connectable text inputs, optional labels, and escape sequences.

from comfy_api.latest import IO

MAX_INPUTS = 10


class ConcatenateStrings(IO.ComfyNode):
    """Concatenate multiple string inputs with configurable delimiter."""

    @classmethod
    def define_schema(cls):
        inputs = [
            IO.String.Input("Delimiter", default="\\n", optional=True,
                            tooltip="Separator between texts. Use \\\\n for newlines, \\\\t for tabs."),
            IO.Boolean.Input("Include Labels", default=False, optional=True,
                             tooltip="Prefix each text with its label."),
            IO.Boolean.Input("Label on Same Line", default=True, optional=True,
                             tooltip="Place label on same line as text, or on a separate line."),
        ]

        for i in range(1, MAX_INPUTS + 1):
            inputs.append(IO.String.Input(f"Label {i}", default="", optional=True))
            inputs.append(IO.String.Input(f"Text {i}", default="", multiline=True, optional=True))

        return IO.Schema(
            node_id="ERPK_ConcatenateStrings",
            display_name="Concatenate Strings (ERPK)",
            category="ERPK/utils",
            description=(
                "Concatenate multiple text inputs into a single output. "
                "Connect STRING outputs from other nodes to Text 1, Text 2, etc. "
                "Set delimiter to control joining (use \\\\n for newlines, \\\\t for tabs)."
            ),
            inputs=inputs,
            outputs=[
                IO.String.Output(display_name="STRING"),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        # Handle escape sequences in delimiter (\n, \t, etc.)
        delimiter = kwargs.get("Delimiter", "\\n")
        try:
            delimiter = delimiter.encode('utf-8').decode('unicode_escape')
        except (UnicodeDecodeError, ValueError):
            pass  # Keep delimiter as-is if escape processing fails

        include_labels = kwargs.get("Include Labels", False)
        label_on_same_line = kwargs.get("Label on Same Line", True)

        parts = []
        for i in range(1, MAX_INPUTS + 1):
            text = kwargs.get(f"Text {i}", "")
            if not text:
                continue

            if include_labels:
                label = kwargs.get(f"Label {i}", "")
                if label:
                    if label_on_same_line:
                        parts.append(f"{label} {text}")
                    else:
                        parts.append(f"{label}\n{text}")
                else:
                    parts.append(text)
            else:
                parts.append(text)

        return IO.NodeOutput(delimiter.join(parts))
