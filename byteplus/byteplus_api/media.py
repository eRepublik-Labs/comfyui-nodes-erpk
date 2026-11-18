# ABOUTME: Media conversion for BytePlus ModelArk: ComfyUI IMAGE/MASK to data URIs within the
# ABOUTME: documented input limits, and Seedream response items back to IMAGE plus alpha tensors.

import base64
import io
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

MAX_IMAGE_BYTES = 30 * 1024 * 1024


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
        data = fetch_remote_bytes(item["url"], max_bytes=100 * 1024 * 1024, timeout=60,
                                  user_agent="ERPK-BytePlus/1.0")
    else:
        raise ValueError(f"Seedream returned an image with neither url nor b64_json: {sorted(item)}")
    with safe_image_decode():
        image = Image.open(io.BytesIO(data))
        image.load()
    return image.convert("RGBA")


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
    if layer.size != (right - left, bottom - top):
        layer = layer.resize((right - left, bottom - top), Image.LANCZOS)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.paste(layer, (left, top))
    return canvas


def response_to_images(data: Sequence[dict], layers: bool) -> Tuple:
    """Return (IMAGE batch, alpha batch with 1 = opaque) for the successful response items.

    With layers, item 0 is the base image and every later item is placed on a canvas of
    the base's size at its bounding box, ordered by z_index.
    """
    images = [_item_image(item) for item in data]
    if layers:
        base, rest = images[0], list(zip(images[1:], data[1:]))
        rest.sort(key=lambda pair: pair[1].get("z_index", 0))
        images = [base] + [_place_layer(image, base.size, item.get("bounding_box")) for image, item in rest]
    sizes = sorted({image.size for image in images})
    if len(sizes) > 1:
        listed = ", ".join(f"{w}x{h}" for w, h in sizes)
        raise ValueError(f"Seedream returned images of different sizes ({listed}); "
                         "they cannot share one IMAGE batch.")
    return _to_tensors(images)
