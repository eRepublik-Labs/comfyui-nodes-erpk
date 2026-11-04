# ABOUTME: Image Grid Loader node: turns an ordered list of files in ComfyUI's input/ directory
# ABOUTME: into one IMAGE batch, letterboxing mixed sizes so the batch shares one height and width.

import json
import os

from comfy_api.latest import IO

# The largest batch any edit node here accepts (Gemini Image Edit, 14).
MAX_GRID_IMAGES = 14
DEFAULT_MAX_IMAGES = 10
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
            inputs=[
                IO.String.Input(
                    "images",
                    default="[]",
                    socketless=True,
                    tooltip="Managed by the grid; JSON list of filenames in ComfyUI's input folder.",
                ),
                IO.Int.Input(
                    "max_images",
                    default=DEFAULT_MAX_IMAGES,
                    min=1,
                    max=MAX_GRID_IMAGES,
                    step=1,
                    tooltip="Most images the grid accepts. Seedream edit nodes take up to 10, "
                            "Gemini Image Edit up to 14.",
                ),
            ],
            outputs=[IO.Image.Output(display_name="IMAGE")],
        )

    @classmethod
    def validate_inputs(cls, images):
        # max_images stays out of this signature: naming it here would switch off
        # ComfyUI's own min/max check for it. The cap is enforced in execute.
        import folder_paths

        try:
            resolve_grid_images(images, folder_paths.get_input_directory())
        except ValueError as e:
            return str(e)
        return True

    @classmethod
    def execute(cls, images, max_images) -> IO.NodeOutput:
        import folder_paths

        paths = resolve_grid_images(images, folder_paths.get_input_directory())
        if len(paths) > max_images:
            raise ValueError(
                f"The grid holds {len(paths)} images but max_images is {max_images}; "
                f"remove {len(paths) - max_images} or raise max_images")
        return IO.NodeOutput(_letterbox_batch([_load_rgb(path) for path in paths]))


def _load_rgb(path):
    import numpy as np
    import torch
    from PIL import Image, ImageOps

    with Image.open(path) as img:
        rgb = ImageOps.exif_transpose(img).convert("RGB")
    return torch.from_numpy(np.array(rgb).astype(np.float32) / 255.0)


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


def resolve_grid_images(raw, input_dir):
    """Parse the `images` widget JSON into absolute paths of files under input_dir."""
    names = _parse_names(raw)
    root = os.path.realpath(input_dir)
    return [_resolve_input_file(position, name, root)
            for position, name in enumerate(names, start=1)]


def _parse_names(raw):
    try:
        names = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"images must be a JSON list of filenames, got {raw!r}") from None
    if not isinstance(names, list):
        raise ValueError(f"images must be a JSON list of filenames, got {names!r}")
    if not names:
        raise ValueError("Add at least one image")
    for position, name in enumerate(names, start=1):
        if not isinstance(name, str) or not name:
            raise ValueError(f"images entry {position} is not a filename: {name!r}")
    return names


def _resolve_input_file(position, name, root):
    # realpath follows symlinks, so a link inside input/ that points elsewhere
    # is judged by where it lands, not where it sits.
    path = os.path.realpath(os.path.join(root, name)) if "\x00" not in name else None
    if path is None or os.path.isabs(name) or os.path.commonpath((root, path)) != root:
        raise ValueError(
            f"images entry {position} is outside ComfyUI's input directory: {name!r}")
    if not os.path.isfile(path):
        raise ValueError(
            f"images entry {position} not found in ComfyUI's input directory: {name!r}")
    return path
