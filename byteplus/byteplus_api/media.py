# ABOUTME: Media conversion for BytePlus ModelArk: ComfyUI IMAGE/MASK to data URIs within the
# ABOUTME: documented input limits, Seedream response items back to IMAGE plus alpha, and billed-image recovery.

import base64
import http.client
import io
import os
import time
import urllib.error
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from . import emit

MAX_IMAGE_BYTES = 30 * 1024 * 1024
# Seconds to wait before the second and third attempt at a free result download.
DOWNLOAD_RETRY_DELAYS = (1.0, 3.0)


@dataclass(frozen=True)
class ImageLimits:
    min_side: int
    max_side: Optional[int]
    min_aspect: float
    max_aspect: float
    min_pixels: int
    max_pixels: Optional[int]


SEEDANCE_IMAGE_LIMITS = ImageLimits(min_side=300, max_side=6000, min_aspect=0.4, max_aspect=2.5,
                                    min_pixels=0, max_pixels=None)
SEEDREAM_IMAGE_LIMITS = ImageLimits(min_side=15, max_side=None, min_aspect=1 / 16, max_aspect=16,
                                    min_pixels=196, max_pixels=36_000_000)
# Layer decomposition needs at least 512x512 worth of pixels in its single input.
SEEDREAM_LAYER_IMAGE_LIMITS = ImageLimits(min_side=15, max_side=None, min_aspect=1 / 16, max_aspect=16,
                                          min_pixels=262_144, max_pixels=36_000_000)


def _check_limits(width: int, height: int, limits: ImageLimits, label: str) -> None:
    side_ok = min(width, height) >= limits.min_side and (limits.max_side is None
                                                         or max(width, height) <= limits.max_side)
    if not side_ok:
        upper = f"-{limits.max_side}" if limits.max_side is not None else " or more"
        raise ValueError(f"{label} is {width}x{height}; width and height must be {limits.min_side}{upper} px.")
    if not limits.min_aspect <= width / height <= limits.max_aspect:
        raise ValueError(f"{label} is {width}x{height}; the aspect ratio must be "
                         f"{limits.min_aspect:g}-{limits.max_aspect:g}.")
    pixels = width * height
    if pixels < limits.min_pixels or (limits.max_pixels is not None and pixels > limits.max_pixels):
        raise ValueError(f"{label} is {width}x{height} = {pixels} pixels; it must be "
                         f"{limits.min_pixels}-{limits.max_pixels or 'unlimited'}.")


def images_to_data_uris(images, limits: ImageLimits, input_name: str, mask=None) -> List[str]:
    """Encode each image of a ComfyUI IMAGE batch as a data URI ModelArk accepts.

    Opaque images go as JPEG quality 95. With a MASK (LoadImage convention, 1 = transparent)
    the image goes as PNG with alpha = 1 - mask, for Seedream's transparent-background edits.
    """
    import numpy as np
    from PIL import Image

    out: List[str] = []
    for index in range(images.shape[0]):
        array = (images[index].detach().cpu().numpy().clip(0, 1) * 255).round().astype("uint8")
        height, width = array.shape[0], array.shape[1]
        _check_limits(width, height, limits, f"{input_name} image {index + 1}")
        pil = Image.fromarray(array[..., :3])
        buffer = io.BytesIO()
        if mask is not None:
            layer = mask[min(index, mask.shape[0] - 1)].detach().cpu().numpy()
            if layer.shape != (height, width):
                raise ValueError(f"The mask is {layer.shape[1]}x{layer.shape[0]} but {input_name} image "
                                 f"{index + 1} is {width}x{height}.")
            pil.putalpha(Image.fromarray(((1.0 - layer.clip(0, 1)) * 255).round().astype(np.uint8)))
            pil.save(buffer, format="PNG")
            mime = "png"
        else:
            pil.save(buffer, format="JPEG", quality=95)
            mime = "jpeg"
        data = buffer.getvalue()
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError(f"{input_name} image {index + 1} encodes to {len(data)} bytes; "
                             f"ModelArk accepts at most {MAX_IMAGE_BYTES} per image.")
        out.append(f"data:image/{mime};base64,{base64.b64encode(data).decode('ascii')}")
    return out


def _item_image(item: dict):
    from PIL import Image

    from ...utils.safe_fetch import fetch_remote_bytes, safe_image_decode

    if item.get("b64_json"):
        data = base64.b64decode(item["b64_json"])
    elif item.get("url"):
        if not isinstance(item["url"], str):
            raise ValueError(f"Seedream returned a url that is not text: {str(item['url'])[:100]}")
        data = _download(item["url"], fetch_remote_bytes)
    else:
        raise ValueError(f"Seedream returned an image with neither url nor b64_json: {sorted(item)}")
    with safe_image_decode():
        try:
            image = Image.open(io.BytesIO(data))
        except Image.UnidentifiedImageError as e:
            # PIL's own message names a buffer's memory address, which tells the user nothing.
            raise ValueError("the data is not an image PIL can read") from e
        image.load()
    return image.convert("RGBA")


def _transient(error: Exception) -> bool:
    if isinstance(error, urllib.error.HTTPError):
        return error.code == 429 or error.code >= 500
    return isinstance(error, (urllib.error.URLError, ConnectionError, TimeoutError, http.client.IncompleteRead))


def _download(url: str, fetch) -> bytes:
    """GET a result URL, retrying connection errors, timeouts, 429 and 5xx: a download is free."""
    attempts = len(DOWNLOAD_RETRY_DELAYS) + 1
    for attempt in range(1, attempts + 1):
        try:
            return fetch(url, max_bytes=100 * 1024 * 1024, timeout=60, user_agent="ERPK-BytePlus/1.0")
        except Exception as e:
            if not _transient(e):
                raise ValueError(f"Downloading {url} failed: {e}") from e
            if attempt == attempts:
                raise ValueError(f"Downloading {url} failed after {attempts} attempts: {e}") from e
            emit(f"Downloading {url} failed ({e}); retrying.")
            time.sleep(DOWNLOAD_RETRY_DELAYS[attempt - 1])


def decode_items(data: Sequence[dict]) -> Tuple[List, List[str]]:
    """Decode every successful response item to RGBA, one at a time, so a bad item never
    costs the others. Returns the images (None where decoding failed) and one error per failure."""
    images: List = []
    errors: List[str] = []
    for index, item in enumerate(data):
        try:
            images.append(_item_image(item))
        except Exception as e:
            images.append(None)
            errors.append(f"image {index + 1} of {len(data)}: {e}")
    return images, errors


def _to_tensors(rgba_images: Sequence) -> Tuple:
    import numpy as np
    import torch

    stacked = np.stack([np.asarray(image, dtype=np.float32) / 255.0 for image in rgba_images])
    tensor = torch.from_numpy(stacked)
    return tensor[..., :3].contiguous(), tensor[..., 3].contiguous()


def _place_layer(layer, canvas_size: Tuple[int, int], bounding_box: Optional[dict]):
    from PIL import Image

    absolute = (bounding_box or {}).get("absolute")
    if not absolute:
        if layer.size != canvas_size:
            raise ValueError(f"A Seedream layer is {layer.size[0]}x{layer.size[1]} with no bounding box "
                             f"on a {canvas_size[0]}x{canvas_size[1]} base.")
        return layer
    left, top, right, bottom = (int(round(v)) for v in absolute)
    if right <= left or bottom <= top:
        raise ValueError(f"A Seedream layer has an empty bounding box {list(absolute)}.")
    if layer.size != (right - left, bottom - top):
        layer = layer.resize((right - left, bottom - top), Image.LANCZOS)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.paste(layer, (left, top))
    return canvas


def _letterbox(images: List) -> List:
    """Center each image on the largest width and height, with mid-grey, fully transparent bars,
    as the Image Grid Loader letterboxes mixed sizes."""
    from PIL import Image

    width = max(image.size[0] for image in images)
    height = max(image.size[1] for image in images)
    listed = ", ".join(f"{w}x{h}" for w, h in sorted({image.size for image in images}))
    emit(f"Seedream returned images of different sizes ({listed}); letterboxed onto {width}x{height}.")
    boxed = []
    for image in images:
        canvas = Image.new("RGBA", (width, height), (128, 128, 128, 0))
        canvas.paste(image, ((width - image.size[0]) // 2, (height - image.size[1]) // 2))
        boxed.append(canvas)
    return boxed


def compose(data: Sequence[dict], images: Sequence, layers: bool) -> Tuple:
    """Return (IMAGE batch, alpha batch with 1 = opaque) from decoded response items.

    With layers, the base is the item with z_index 0 (else the first), and every other item
    is scaled to its bounding box on a canvas of the base's size, in ascending z_index.
    Mixed sizes are letterboxed onto the largest.
    """
    images = list(images)
    if layers:
        pairs = list(zip(images, data))
        base_index = next((i for i, item in enumerate(data) if item.get("z_index") == 0), 0)
        base = images[base_index]
        rest = sorted((pair for i, pair in enumerate(pairs) if i != base_index),
                      key=lambda pair: pair[1].get("z_index", 0))
        images = [base] + [_place_layer(image, base.size, item.get("bounding_box")) for image, item in rest]
    if len({image.size for image in images}) > 1:
        images = _letterbox(images)
    return _to_tensors(images)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _create_new(directory: str, stem: str):
    """Open a new PNG for writing without ever replacing an existing file."""
    attempt = 0
    while True:
        path = os.path.join(directory, f"{stem}{f'-{attempt}' if attempt else ''}.png")
        try:
            return path, open(path, "xb")
        except FileExistsError:
            attempt += 1


def save_recovered_images(images: Sequence) -> Tuple[List[str], List[str]]:
    """Write billed images as PNG under ComfyUI's output/byteplus_recovered. Returns the paths
    written and one error per image that could not be written; a failed write leaves no file.
    Names come from the local clock and the index, never from response data."""
    import folder_paths

    directory = os.path.join(folder_paths.get_output_directory(), "byteplus_recovered")
    os.makedirs(directory, exist_ok=True)
    stamp = _timestamp()
    paths: List[str] = []
    errors: List[str] = []
    for index, image in enumerate(images, 1):
        try:
            path, handle = _create_new(directory, f"{stamp}-{index:02d}")
        except OSError as e:
            errors.append(f"Saving image {index} of {len(images)} failed: {e}")
            continue
        try:
            with handle:
                image.save(handle, format="PNG")
        except Exception as e:
            error = f"Saving image {index} of {len(images)} failed: {e}"
            try:
                os.remove(path)
            except OSError as remove_error:
                error += f"; the partial file {path} could not be removed ({remove_error})"
            errors.append(error)
            continue
        paths.append(path)
    return paths, errors
