# ABOUTME: Builds a MiniMax H3 LoRA stack (up to 3 path/scale pairs) for the H3 nodes.
# ABOUTME: Connecting its output routes any H3 node to the endpoint's -lora twin.

from comfy_api.latest import IO


class MinimaxH3LoraStackNode(IO.ComfyNode):
    """
    MiniMax H3 LoRA Stack Node

    Collects up to three LoRA weights as {path, scale} pairs. Connect the
    output to the `loras` socket of any MiniMax H3 node and that node calls
    the endpoint's `-lora` twin. A config node: it calls no API and takes no
    seed, so ComfyUI caches it like any other pure input.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="MinimaxH3LoraStackNode",
            display_name="MiniMax H3 LoRA Stack",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("lora_1_path",
                                tooltip="URL of the first LoRA file (required)"),
                IO.Float.Input("lora_1_scale", default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale for the first LoRA. WaveSpeed documents no range for H3; 0.0-4.0 follows the Qwen LoRA nodes."),
                IO.String.Input("lora_2_path", optional=True, default="",
                                tooltip="URL of the second LoRA file (optional)"),
                IO.Float.Input("lora_2_scale", optional=True, default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale for the second LoRA"),
                IO.String.Input("lora_3_path", optional=True, default="",
                                tooltip="URL of the third LoRA file (optional)"),
                IO.Float.Input("lora_3_scale", optional=True, default=1.0, min=0.0, max=4.0, step=0.1,
                               tooltip="Scale for the third LoRA"),
            ],
            outputs=[
                IO.Custom("MINIMAX_H3_LORAS").Output("loras"),
            ],
        )

    @staticmethod
    def _build_loras(lora_1_path, lora_1_scale, lora_2_path, lora_2_scale,
                     lora_3_path, lora_3_scale):
        loras = []
        for path, scale in ((lora_1_path, lora_1_scale),
                            (lora_2_path, lora_2_scale),
                            (lora_3_path, lora_3_scale)):
            if path and path.strip():
                loras.append({"path": path.strip(), "scale": scale})
        if not loras:
            raise ValueError("At least one LoRA path is required")
        return loras

    @classmethod
    def execute(cls, lora_1_path="", lora_1_scale=1.0, lora_2_path="", lora_2_scale=1.0,
                lora_3_path="", lora_3_scale=1.0, **kwargs):
        return IO.NodeOutput(cls._build_loras(lora_1_path, lora_1_scale, lora_2_path,
                                              lora_2_scale, lora_3_path, lora_3_scale))
