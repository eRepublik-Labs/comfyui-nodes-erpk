# ABOUTME: Picks one region's mask out of the Regional Prompt Builder's masks
# ABOUTME: batch by canvas region number, for targeting a single object downstream.

from comfy_api.latest import IO


def clamp_region_index(count, region):
    """Map a 1-based canvas region number to a safe 0-based batch index."""
    if count <= 0:
        return 0
    return max(0, min(count - 1, region - 1))


class RegionMask(IO.ComfyNode):
    """Selects a single region's mask from a masks batch."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="RegionMask",
            display_name="Region Mask",
            category="ERPK/utils",
            description="Pick one region's mask from the Regional Prompt "
                        "Builder's masks output by canvas region number.",
            inputs=[
                IO.Mask.Input(
                    "masks",
                    tooltip="Masks batch from the Regional Prompt Builder "
                            "(one mask per region, in region order).",
                ),
                IO.Int.Input(
                    "region",
                    default=1,
                    min=1,
                    max=1024,
                    tooltip="Canvas region number (1 = backmost). Out-of-range "
                            "numbers clamp to the batch.",
                ),
            ],
            outputs=[
                IO.Mask.Output(
                    "mask",
                    tooltip="The selected region's mask as a single-mask batch.",
                ),
            ],
        )

    @classmethod
    def execute(cls, **kwargs) -> IO.NodeOutput:
        masks = kwargs["masks"]
        region = kwargs.get("region", 1)
        index = clamp_region_index(len(masks), region)
        return IO.NodeOutput(masks[index:index + 1])
