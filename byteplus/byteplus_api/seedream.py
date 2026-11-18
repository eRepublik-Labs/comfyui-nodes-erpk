# ABOUTME: Seedream image models on BytePlus ModelArk: one capability row per model, the
# ABOUTME: /images/generations body builder that enforces those rows, and the per-image price.

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .seedance import check_urls


@dataclass(frozen=True)
class SeedreamModel:
    """What one Seedream model accepts, from the ModelArk image-generation reference."""

    model_id: str
    max_reference_images: int
    size_presets: Tuple[str, ...]
    min_pixels: int
    max_pixels: int
    sequential: bool
    layer_decomposition: bool
    layer_options: bool
    # Empty when the model takes no output_format field (4.5 and 4.0 are jpeg only).
    output_formats: Tuple[str, ...]
    backgrounds: Tuple[str, ...]
    # 5.5 makes transparent images from text or up to 10 references; 5.0 pro and
    # flash only from exactly one reference that carries alpha.
    transparent_from_text: bool
    fast_prompt_mode: bool
    safety_identifier: bool
    # (inclusive pixel ceiling, USD per output image), ascending.
    output_price_tiers: Tuple[Tuple[float, float], ...]
    layer_price_tiers: Tuple[Tuple[float, float], ...]
    input_image_price: float
    free_input_images: int


_FIVE_X_PRESETS = ("1K", "1.5K", "2K")

SEEDREAM_MODELS: Dict[str, SeedreamModel] = {m.model_id: m for m in (
    SeedreamModel(
        model_id="dola-seedream-5-5-261028", max_reference_images=10, size_presets=_FIVE_X_PRESETS,
        min_pixels=921_600, max_pixels=4_624_220, sequential=False,
        layer_decomposition=True, layer_options=True, output_formats=("png", "jpeg"),
        backgrounds=("auto", "transparent", "opaque"), transparent_from_text=True, fast_prompt_mode=False,
        safety_identifier=True, output_price_tiers=((2_601_123.84, 0.020), (4_624_220.16, 0.035)),
        layer_price_tiers=((2_601_123.84, 0.020), (4_624_220.16, 0.035)),
        input_image_price=0.008, free_input_images=0,
    ),
    SeedreamModel(
        model_id="dola-seedream-5-0-pro-260628", max_reference_images=10, size_presets=_FIVE_X_PRESETS,
        min_pixels=921_600, max_pixels=4_624_220, sequential=False,
        layer_decomposition=True, layer_options=False, output_formats=("jpeg", "png"),
        backgrounds=("opaque", "transparent"), transparent_from_text=False, fast_prompt_mode=True,
        safety_identifier=True, output_price_tiers=((2_610_000, 0.045), (4_624_220.16, 0.09)),
        layer_price_tiers=((2_610_000, 0.0225), (4_624_220.16, 0.045)),
        input_image_price=0.003, free_input_images=1,
    ),
    SeedreamModel(
        model_id="dola-seedream-5-0-flash-260915", max_reference_images=10, size_presets=_FIVE_X_PRESETS,
        min_pixels=921_600, max_pixels=4_624_220, sequential=False,
        layer_decomposition=True, layer_options=False, output_formats=("jpeg", "png"),
        backgrounds=("opaque", "transparent"), transparent_from_text=False, fast_prompt_mode=False,
        safety_identifier=True, output_price_tiers=((4_624_220.16, 0.018),),
        layer_price_tiers=((4_624_220.16, 0.018),), input_image_price=0.0, free_input_images=0,
    ),
    SeedreamModel(
        model_id="seedream-5-0-260128", max_reference_images=14, size_presets=("2K", "3K", "4K"),
        min_pixels=3_686_400, max_pixels=16_777_216, sequential=True,
        layer_decomposition=False, layer_options=False, output_formats=("jpeg", "png"),
        backgrounds=(), transparent_from_text=False, fast_prompt_mode=False, safety_identifier=False,
        output_price_tiers=((16_777_216, 0.035),), layer_price_tiers=(),
        input_image_price=0.0, free_input_images=0,
    ),
    SeedreamModel(
        model_id="seedream-4-5-251128", max_reference_images=14, size_presets=("2K", "4K"),
        min_pixels=3_686_400, max_pixels=16_777_216, sequential=True,
        layer_decomposition=False, layer_options=False, output_formats=(),
        backgrounds=(), transparent_from_text=False, fast_prompt_mode=False, safety_identifier=False,
        output_price_tiers=((16_777_216, 0.04),), layer_price_tiers=(),
        input_image_price=0.0, free_input_images=0,
    ),
    SeedreamModel(
        model_id="seedream-4-0-250828", max_reference_images=14, size_presets=("1K", "2K", "4K"),
        min_pixels=921_600, max_pixels=16_777_216, sequential=True,
        layer_decomposition=False, layer_options=False, output_formats=(),
        backgrounds=(), transparent_from_text=False, fast_prompt_mode=True, safety_identifier=False,
        output_price_tiers=((16_777_216, 0.03),), layer_price_tiers=(),
        input_image_price=0.0, free_input_images=0,
    ),
)}

MODEL_IDS: List[str] = list(SEEDREAM_MODELS)
DEFAULT_MODEL = "dola-seedream-5-5-261028"
SIZES = ["2K", "1K", "1.5K", "3K", "4K", "custom"]
# auto is a layer-decomposition size, so only Image Edit offers it.
EDIT_SIZES = SIZES[:-1] + ["auto", "custom"]
MODEL_DEFAULT = "(model default)"
OUTPUT_FORMATS = [MODEL_DEFAULT, "png", "jpeg"]
BACKGROUNDS = [MODEL_DEFAULT, "auto", "transparent", "opaque"]
RESPONSE_FORMATS = ["url", "b64_json"]
PROMPT_MODES = ["standard", "fast"]
SEQUENTIAL_MODES = ["disabled", "auto"]
# image-generation-api, max_images: reference images + generated images <= 15. max_images is only an upper
# bound, so the body sends at most what the references leave.
MAX_SEQUENTIAL_TOTAL = 15
# Every model's explicit width x height must keep width / height within [1/16, 16].
ASPECT_RATIO_LIMIT = 16
IMAGE_URL_PREFIXES = ("https://", "http://", "data:image/")
LAYER_MAX_IMAGES_MIN, LAYER_MAX_IMAGES_MAX = 2, 100
SAFETY_IDENTIFIER_MAX = 64


@dataclass(frozen=True)
class ImageOptions:
    size: str = "2K"
    width: int = 2048
    height: int = 2048
    sequential: str = "disabled"
    max_images: int = 15
    response_format: str = "url"
    output_format: str = MODEL_DEFAULT
    background: str = MODEL_DEFAULT
    optimize_prompt_mode: str = "standard"
    watermark: bool = False
    safety_identifier: str = ""
    layer_decomposition: bool = False
    layer_max_images: int = 30
    text_recognition: bool = False


def get_model(model_id: str) -> SeedreamModel:
    try:
        return SEEDREAM_MODELS[model_id]
    except KeyError:
        raise ValueError(f"Unknown Seedream model {model_id!r}. Known: {', '.join(MODEL_IDS)}") from None


def _size(model: SeedreamModel, options: ImageOptions) -> str:
    if options.size == "auto":
        if not options.layer_decomposition:
            raise ValueError("Size auto is for layer decomposition only.")
        return "auto"
    if options.size == "custom":
        if options.layer_decomposition:
            raise ValueError("Layer decomposition takes a size preset or auto, not a custom size.")
        w, h = options.width, options.height
        pixels = w * h
        if not model.min_pixels <= pixels <= model.max_pixels:
            raise ValueError(f"{model.model_id} needs {model.min_pixels}-{model.max_pixels} total pixels, "
                             f"got {w}x{h} = {pixels}.")
        if not 1 / ASPECT_RATIO_LIMIT <= w / h <= ASPECT_RATIO_LIMIT:
            raise ValueError(f"{model.model_id} needs an aspect ratio within 1/{ASPECT_RATIO_LIMIT}-"
                             f"{ASPECT_RATIO_LIMIT}, got {w}x{h}.")
        return f"{w}x{h}"
    if options.size not in model.size_presets:
        raise ValueError(f"{model.model_id} takes size {', '.join(model.size_presets)} or custom, "
                         f"not {options.size}.")
    return options.size


def _check_output_format(model: SeedreamModel, options: ImageOptions) -> None:
    fmt = options.output_format
    if fmt != MODEL_DEFAULT and model.output_formats and fmt not in model.output_formats:
        raise ValueError(f"{model.model_id} outputs {', '.join(model.output_formats)}, not {fmt}.")
    if not model.output_formats and fmt not in (MODEL_DEFAULT, "jpeg"):
        raise ValueError(f"{model.model_id} outputs jpeg only, not {fmt}.")


def _check_background(model: SeedreamModel, options: ImageOptions, images: Sequence[str]) -> None:
    background = options.background
    if background == MODEL_DEFAULT:
        return
    if options.layer_decomposition:
        raise ValueError("Layer decomposition does not take a background option.")
    if not model.backgrounds:
        raise ValueError(f"{model.model_id} has no background option.")
    if background not in model.backgrounds:
        raise ValueError(f"{model.model_id} takes background {' or '.join(model.backgrounds)}, not {background}.")
    if background != "transparent":
        return
    if not model.transparent_from_text:
        if len(images) != 1:
            raise ValueError(f"{model.model_id} makes transparent images only from exactly one reference "
                             "image with alpha.")
        if images[0].startswith("data:image/jpeg"):
            raise ValueError(f"{model.model_id} makes a transparent image only from a reference that carries "
                             "alpha, and an inline image without a mask is sent as JPEG. Connect a mask to images.")
    fmt = options.output_format if options.output_format != MODEL_DEFAULT else model.output_formats[0]
    if fmt != "png":
        raise ValueError(f"A transparent background needs png output, not {fmt}.")


def _check_layers(model: SeedreamModel, options: ImageOptions, image_count: int) -> None:
    if not model.layer_decomposition:
        raise ValueError(f"{model.model_id} has no layer decomposition; use Seedream 5.5, 5.0 pro or 5.0 flash.")
    if image_count != 1:
        raise ValueError(f"Layer decomposition takes exactly one image, got {image_count}.")
    if options.text_recognition and not model.layer_options:
        raise ValueError(f"{model.model_id} has no layer text recognition; it is on Seedream 5.5 only.")
    if not LAYER_MAX_IMAGES_MIN <= options.layer_max_images <= LAYER_MAX_IMAGES_MAX:
        raise ValueError(f"layer_max_images must be {LAYER_MAX_IMAGES_MIN}-{LAYER_MAX_IMAGES_MAX}, "
                         f"got {options.layer_max_images}.")


def _check_sequential(model: SeedreamModel, options: ImageOptions, image_count: int) -> None:
    if not model.sequential:
        raise ValueError(f"{model.model_id} has no sequential generation; it returns one image per request.")
    if not 1 <= options.max_images <= MAX_SEQUENTIAL_TOTAL:
        raise ValueError(f"max_images must be 1-{MAX_SEQUENTIAL_TOTAL}, got {options.max_images}.")
    if image_count >= MAX_SEQUENTIAL_TOTAL:
        raise ValueError(f"Sequential generation needs fewer than {MAX_SEQUENTIAL_TOTAL} reference images, "
                         f"got {image_count}.")


def build_image_body(model_id: str, prompt: str, images: Sequence[str], options: ImageOptions,
                     endpoint_id: str = "") -> dict:
    """Return the POST /images/generations body, or raise ValueError on a combination the
    selected model rejects. Options a model ignores are left out of the body."""
    model = get_model(model_id)
    prompt = prompt.strip()
    count = len(images)
    if count > model.max_reference_images:
        raise ValueError(f"{model.model_id} takes at most {model.max_reference_images} reference images, "
                         f"got {count}.")
    if not prompt and not options.layer_decomposition:
        raise ValueError("Image generation needs a prompt.")
    if options.optimize_prompt_mode == "fast" and not model.fast_prompt_mode:
        raise ValueError(f"{model.model_id} has no fast prompt optimization; it is on 5.0 pro and 4.0 only.")
    if len(options.safety_identifier) > SAFETY_IDENTIFIER_MAX:
        raise ValueError(f"safety_identifier is at most {SAFETY_IDENTIFIER_MAX} characters, "
                         f"got {len(options.safety_identifier)}.")
    _check_output_format(model, options)
    check_urls("Reference image", images, IMAGE_URL_PREFIXES)
    _check_background(model, options, images)
    if options.layer_decomposition:
        _check_layers(model, options, count)
    if options.sequential == "auto":
        _check_sequential(model, options, count)

    body: dict = {"model": endpoint_id.strip() or model.model_id}
    if prompt:
        body["prompt"] = prompt
    body.update({
        "size": _size(model, options),
        "response_format": options.response_format,
        "watermark": options.watermark,
        "optimize_prompt_options": {"mode": options.optimize_prompt_mode},
    })
    if options.layer_decomposition:
        body["image"] = images[0]
        body["layer_decomposition"] = True
        if model.layer_options:
            body["layer_decomposition_options"] = {"max_images": options.layer_max_images,
                                                   "text_recognition": options.text_recognition}
    elif images:
        body["image"] = list(images)
    if options.sequential == "auto":
        body["sequential_image_generation"] = "auto"
        body["sequential_image_generation_options"] = {
            "max_images": min(options.max_images, MAX_SEQUENTIAL_TOTAL - count)}
    if options.output_format != MODEL_DEFAULT and model.output_formats:
        body["output_format"] = options.output_format
    if options.background != MODEL_DEFAULT:
        body["background"] = options.background
    if options.safety_identifier and model.safety_identifier:
        body["safety_identifier"] = options.safety_identifier
    return body


def _tier_price(tiers: Tuple[Tuple[float, float], ...], pixels: int, model_id: str) -> float:
    for ceiling, price in tiers:
        if pixels <= ceiling:
            return price
    raise ValueError(f"{model_id} has no price for a {pixels}-pixel image.")


def image_cost_usd(model_id: str, output_sizes: Sequence[Tuple[int, int]], input_images: int,
                   layers: bool = False) -> float:
    """USD charged for one request: priced inputs plus each returned image at its pixel tier."""
    model = get_model(model_id)
    tiers = model.layer_price_tiers if layers else model.output_price_tiers
    outputs = sum(_tier_price(tiers, w * h, model_id) for w, h in output_sizes)
    priced_inputs = max(0, input_images - model.free_input_images)
    return outputs + priced_inputs * model.input_image_price
