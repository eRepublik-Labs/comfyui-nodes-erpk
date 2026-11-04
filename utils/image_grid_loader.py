# ABOUTME: Image Grid Loader node: turns an ordered list of files in ComfyUI's input/ directory
# ABOUTME: into one IMAGE batch, letterboxing mixed sizes so the batch shares one height and width.

from comfy_api.latest import IO

from .image_grid import GridCap, grid_cap_for, grid_input, load_grid_images, register_grid_caps, resolve_grid_images

# The largest batch any edit node here accepts (Gemini Image Edit, 14).
MAX_GRID_IMAGES = 14
register_grid_caps("ImageGridLoader", {"*": MAX_GRID_IMAGES}, model_widget=None)
EMPTY_GRID = "Add at least one image"
# Mid-grey rather than black, so an edit model reads the bars as padding and
# not as dark content belonging to the picture.
LETTERBOX_GREY = 0.5


class ImageGridLoader(IO.ComfyNode):
    """Load the files picked or dropped onto the grid as one IMAGE batch, in grid order."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="ImageGridLoader",
            display_name="Image Grid Loader",
            category="ERPK/utils",
            description=(
                "Pick or drop image files onto the grid and get them back as one IMAGE "
                "batch in grid order, so cell 3 is Picture 3 for a multi-image edit node. "
                "Files are copied into ComfyUI's input folder; mixed sizes are letterboxed "
                "with mid-grey onto the largest height and width."
            ),
            inputs=[grid_input()],
            outputs=[IO.Image.Output(display_name="IMAGE")],
        )

    @classmethod
    def validate_inputs(cls, grid_images="[]"):
        import folder_paths

        try:
            paths = resolve_grid_images(grid_images, folder_paths.get_input_directory())
        except ValueError as e:
            return str(e)
        return True if paths else EMPTY_GRID

    @classmethod
    def execute(cls, grid_images="[]") -> IO.NodeOutput:
        pictures = load_grid_images(grid_images, GridCap("Image Grid Loader", grid_cap_for("ImageGridLoader", None)))
        if not pictures:
            raise ValueError(EMPTY_GRID)
        return IO.NodeOutput(_letterbox_batch([_to_tensor(picture) for picture in pictures]))


def _to_tensor(picture):
    import numpy as np
    import torch

    return torch.from_numpy(np.array(picture).astype(np.float32) / 255.0)


def _letterbox_batch(images):
    import torch

    height = max(image.shape[0] for image in images)
    width = max(image.shape[1] for image in images)
    batch = torch.full((len(images), height, width, 3), LETTERBOX_GREY, dtype=torch.float32)
    for index, image in enumerate(images):
        h, w = image.shape[:2]
        top, left = (height - h) // 2, (width - w) // 2
        batch[index, top:top + h, left:left + w] = image
    return batch
