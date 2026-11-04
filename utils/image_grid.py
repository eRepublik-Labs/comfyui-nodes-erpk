# ABOUTME: Server side of the image grid, shared by Image Grid Loader and the edit nodes that embed it:
# ABOUTME: the input every grid node declares, each node's per-model image caps, and loading the files.

import json
import os
from typing import NamedTuple

from comfy_api.latest import IO

NO_GRID_IMAGE = "Connect an image or add images to the grid"
ANY_MODEL = "*"


class GridCap(NamedTuple):
    """The most images a grid holds, and what an over-cap error names as setting it:
    the selected model on a node with a model choice, else the node."""

    name: str
    cap: int


# node_id -> {"model_widget": combo name or None, "caps": {model id or "*": most images}}.
# Each grid node's module fills it at import; /erpk/grid_caps serves it to the grid.
GRID_CAPS = {}


def register_grid_caps(node_id, caps, model_widget):
    """Record the most images each model on `node_id` takes; "*" covers models not listed.

    `model_widget` names the node's model combo, or is None for a node with no model
    choice, whose caps are then {"*": n} alone.
    """
    if not caps or any(not isinstance(n, int) or n < 1 for n in caps.values()):
        raise ValueError(f"Grid caps for {node_id} must map models to positive counts, got {caps!r}")
    if model_widget is None and set(caps) != {ANY_MODEL}:
        raise ValueError(f"{node_id} has no model widget, so its grid caps must be {{'*': n}}, got {caps!r}")
    GRID_CAPS[node_id] = {"model_widget": model_widget, "caps": dict(caps)}


def grid_cap_for(node_id, model):
    """The most images `model` on `node_id` takes: its own entry, else "*", else the node's largest."""
    entry = GRID_CAPS.get(node_id)
    if entry is None:
        raise ValueError(f"No grid caps registered for {node_id}")
    caps = entry["caps"]
    return caps.get(model, caps.get(ANY_MODEL, max(caps.values())))


def model_grid_cap(node_id, model):
    """The cap `model` sets on `node_id`'s grid, named by the model."""
    return GridCap(model, grid_cap_for(node_id, model))


def grid_input():
    """The `grid_images` list the grid writes, declared after every other input.

    It is optional because the frontend lays out required widgets before optional
    ones and widgets_values is positional: a required grid input on a node that
    already has optional widgets would land mid-list and shift every saved value
    after it.
    """
    return IO.String.Input(
        "grid_images",
        default="[]",
        socketless=True,
        optional=True,
        tooltip="Managed by the grid; JSON list of filenames in ComfyUI's input folder.",
    )


def validate_grid(raw):
    """A validate_inputs answer for the `grid_images` list: True, or why its files cannot load.

    An empty list passes, for nodes where a connected socket can stand in for the grid.
    """
    import folder_paths

    try:
        resolve_grid_images(raw, folder_paths.get_input_directory())
    except ValueError as e:
        return str(e)
    return True


def load_grid_images(raw, cap):
    """The grid's files as upright RGB PIL images in grid order; an empty grid gives [].

    More files than `cap.cap` is an error naming `cap.name`.
    """
    import folder_paths

    paths = resolve_grid_images(raw, folder_paths.get_input_directory())
    count = len(paths)
    if count > cap.cap:
        noun = "image" if cap.cap == 1 else "images"
        raise ValueError(
            f"The grid holds {count} images but {cap.name} takes up to {cap.cap} {noun}; "
            f"remove {count - cap.cap}")
    return [_load_upright_rgb(path) for path in paths]


def _load_upright_rgb(path):
    from PIL import Image, ImageOps

    with Image.open(path) as img:
        return ImageOps.exif_transpose(img).convert("RGB")


def resolve_grid_images(raw, input_dir):
    """Parse the `grid_images` widget JSON into absolute paths of files under input_dir."""
    names = _parse_names(raw)
    root = os.path.realpath(input_dir)
    return [_resolve_input_file(position, name, root)
            for position, name in enumerate(names, start=1)]


def _parse_names(raw):
    try:
        names = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"grid_images must be a JSON list of filenames, got {raw!r}") from None
    if not isinstance(names, list):
        raise ValueError(f"grid_images must be a JSON list of filenames, got {names!r}")
    for position, name in enumerate(names, start=1):
        if not isinstance(name, str) or not name:
            raise ValueError(f"grid_images entry {position} is not a filename: {name!r}")
    return names


def _resolve_input_file(position, name, root):
    # realpath follows symlinks, so a link inside input/ that points elsewhere
    # is judged by where it lands, not where it sits.
    path = os.path.realpath(os.path.join(root, name)) if "\x00" not in name else None
    if path is None or os.path.isabs(name) or os.path.commonpath((root, path)) != root:
        raise ValueError(
            f"grid_images entry {position} is outside ComfyUI's input directory: {name!r}")
    if not os.path.isfile(path):
        raise ValueError(
            f"grid_images entry {position} not found in ComfyUI's input directory: {name!r}")
    return path
