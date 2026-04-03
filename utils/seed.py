# ABOUTME: ComfyUI V3 seed generator node with configurable range.
# ABOUTME: Outputs an INT seed that can be connected to any node's seed input.

from comfy_api.latest import IO


class Seed(IO.ComfyNode):
    """Generate a seed value with optional range clamping.

    Connect the output to any node's seed input to share
    a single seed across multiple nodes.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ERPK_Seed",
            display_name="Seed",
            category="ERPK/utils",
            description="Generate a seed value with optional min/max range.",
            inputs=[
                IO.Int.Input(
                    "seed",
                    default=-1,
                    min=-1,
                    max=2**31 - 1,
                    control_after_generate="randomize",
                    tooltip="Seed value. Use the control dropdown to randomize, increment, decrement, or fix.",
                ),
                IO.Int.Input(
                    "min_value",
                    default=0,
                    min=0,
                    max=2**31 - 1,
                    optional=True,
                    tooltip="Minimum seed value. Output is clamped to this lower bound.",
                ),
                IO.Int.Input(
                    "max_value",
                    default=2**31 - 1,
                    min=0,
                    max=2**31 - 1,
                    optional=True,
                    tooltip="Maximum seed value. Output is clamped to this upper bound.",
                ),
            ],
            outputs=[
                IO.Int.Output("seed"),
            ],
        )

    @classmethod
    def execute(cls, seed=0, min_value=0, max_value=2**31 - 1, **kwargs) -> IO.NodeOutput:
        clamped = max(min_value, min(seed, max_value))
        return IO.NodeOutput(clamped)
