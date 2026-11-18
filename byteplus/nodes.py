# ABOUTME: BytePlus ModelArk V3 nodes: the optional API Client config node and the Seedream
# ABOUTME: text-to-image and image-edit nodes, which output an IMAGE batch plus its alpha.

import asyncio
import threading
from typing import Callable, List, Optional

from comfy_api.latest import IO

from .byteplus_api import client as client_module
from .byteplus_api import emit, seedream
from .byteplus_api.client import BytePlusClient
from .byteplus_api.media import (
    SEEDREAM_IMAGE_LIMITS, SEEDREAM_LAYER_IMAGE_LIMITS, compose, decode_items, images_to_data_uris,
    save_recovered_images,
)

CLIENT_TOOLTIP = ("BytePlus API client from the BytePlus API Client node. If not connected, the key comes "
                  "from ComfyUI Settings or byteplus/config.ini.")
_CATEGORY = "ERPK/BytePlus"


def make_client(client_dict: Optional[dict]) -> BytePlusClient:
    """A client from the API Client node's output, or one resolving the key itself."""
    if client_dict is not None:
        return BytePlusClient(api_key=client_dict["api_key"])
    return BytePlusClient()


def url_lines(text: str) -> List[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


class BytePlusAPIClient(IO.ComfyNode):
    """Provides a BytePlus ModelArk API key to the BytePlus nodes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusAPIClient",
            display_name="BytePlus API Client",
            category=_CATEGORY,
            description=("BytePlus ModelArk API key for the Seedance and Seedream nodes. Optional: leave it out "
                         "and the nodes read ComfyUI Settings or byteplus/config.ini."),
            inputs=[
                IO.String.Input(
                    "api_key", default="", optional=True,
                    tooltip=("ModelArk API key from the ap-southeast-1 (Johor) console. ComfyUI Settings take "
                             "priority; if empty, byteplus/config.ini is read."),
                ),
            ],
            outputs=[IO.Custom("BYTEPLUS_API_CLIENT").Output("client")],
        )

    @classmethod
    def execute(cls, api_key: str = "", **kwargs) -> IO.NodeOutput:
        client = BytePlusClient(api_key=api_key.strip() or None)
        return IO.NodeOutput({"api_key": client.api_key})


def _image_option_inputs(edit: bool):
    inputs = [
        IO.Custom("BYTEPLUS_API_CLIENT").Input("client", optional=True, tooltip=CLIENT_TOOLTIP),
        IO.Combo.Input(
            "model", options=seedream.MODEL_IDS, default=seedream.DEFAULT_MODEL, optional=True,
            tooltip=("Seedream model. 5.5 (transparent output, up to 99 layers); 5.0 pro and 5.0 flash (layers, "
                     "transparent from one alpha reference); 5.0 lite, 4.5 and 4.0 (batches of up to 15 via "
                     "sequential, 14 references). A combination the model rejects stops before any call."),
        ),
        IO.String.Input(
            "endpoint_id", default="", optional=True,
            tooltip=("Custom ModelArk endpoint ID to call instead of the model ID. The model widget still "
                     "decides which options apply."),
        ),
        IO.Combo.Input(
            "size", options=seedream.EDIT_SIZES if edit else seedream.SIZES, default="2K", optional=True,
            tooltip=("Preset (the model picks the aspect from the prompt): 1K/1.5K/2K on 5.5, 5.0 pro, 5.0 "
                     "flash; 2K/3K/4K on 5.0 lite; 2K/4K on 4.5; 1K/2K/4K on 4.0. custom sends width x height."
                     + (" auto is for layer decomposition." if edit else "")),
        ),
        IO.Int.Input(
            "width", default=2048, min=15, max=8192, optional=True,
            tooltip=("Used when size is custom. Total pixels: 921,600-4,624,220 on 5.5/5.0 pro/5.0 flash, "
                     "3,686,400-16,777,216 on 5.0 lite and 4.5, 921,600-16,777,216 on 4.0."),
        ),
        IO.Int.Input("height", default=2048, min=15, max=8192, optional=True,
                     tooltip="Used when size is custom. Every model needs an aspect ratio within 1:16-16:1."),
        IO.Combo.Input(
            "sequential", options=seedream.SEQUENTIAL_MODES, default="disabled", optional=True,
            tooltip=("auto lets 5.0 lite, 4.5 and 4.0 return a related set of up to max_images images. "
                     "5.x pro/flash/5.5 return one image per request."),
        ),
        IO.Int.Input(
            "max_images", default=15, min=1, max=15, optional=True,
            tooltip=("Upper bound for sequential auto. ModelArk allows 15 reference plus generated images, so "
                     "next to references the node sends at most 15 minus their count and logs it. Rate limits "
                     "are reserved for the max_images sent, up front; billing counts images returned."),
        ),
        IO.Combo.Input(
            "output_format", options=seedream.OUTPUT_FORMATS, default=seedream.MODEL_DEFAULT, optional=True,
            tooltip="5.5 defaults to png, 5.0 models to jpeg. 4.5 and 4.0 make jpeg only. Layers are always png.",
        ),
        IO.Combo.Input(
            "background", options=seedream.BACKGROUNDS, default=seedream.MODEL_DEFAULT, optional=True,
            tooltip=("5.5: auto/transparent/opaque. 5.0 pro and flash: opaque/transparent, transparent from "
                     "exactly one reference image with alpha (connect a mask). Transparent needs png. Not with "
                     "layer decomposition. The alpha output carries the transparency."),
        ),
        IO.Combo.Input(
            "optimize_prompt_mode", options=seedream.PROMPT_MODES, default="standard", optional=True,
            tooltip="Prompt optimization. fast trades quality for speed on 5.0 pro and 4.0 only.",
        ),
        IO.Combo.Input(
            "response_format", options=seedream.RESPONSE_FORMATS, default="url", optional=True,
            tooltip="How ModelArk returns images: url (downloaded here, valid 24 h) or b64_json (inline).",
        ),
        IO.Boolean.Input("watermark", default=False, optional=True,
                         tooltip="Adds the 'AI-generated' mark. ModelArk's own default is on; this node sends off."),
        IO.Boolean.Input(
            "fail_on_partial", default=False, optional=True,
            tooltip=("In a sequential batch one image can fail moderation while the others succeed. Off: return "
                     "the images that succeeded and log the refusals. On: raise, after saving the billed images "
                     "to output/byteplus_recovered."),
        ),
    ]
    if edit:
        inputs += [
            IO.Boolean.Input(
                "layer_decomposition", default=False, optional=True,
                tooltip=("5.5, 5.0 pro, 5.0 flash: split one image into a base plus transparent layers. The "
                         "images output is the base then each layer on the base canvas; alpha holds each "
                         "layer's transparency. Any failed layer fails the request."),
            ),
            IO.Int.Input(
                "layer_max_images", default=30, min=seedream.LAYER_MAX_IMAGES_MIN,
                max=seedream.LAYER_MAX_IMAGES_MAX, optional=True,
                tooltip=("5.5 only: most images to return, base included (2-100). Rate limits reserve this "
                         "count up front. 5.0 pro and flash return up to 1 base + 16 layers."),
            ),
            IO.Boolean.Input("text_recognition", default=False, optional=True,
                             tooltip="5.5 layer decomposition only: rich-text OCR on text layers."),
        ]
    inputs += [
        IO.String.Input("safety_identifier", default="", optional=True,
                        tooltip="Optional hashed end-user ID (max 64 characters). Sent to 5.5, 5.0 pro and 5.0 flash."),
        IO.Int.Input(
            "seed", default=-1, min=-1, max=2**31 - 1, optional=True, control_after_generate="randomize",
            tooltip=("Cache control only, not sent: Seedream echoes a seed but does not reproduce an image with it. -1 "
                     "re-runs every queue; a fixed value reuses the cached result."),
        ),
    ]
    return inputs


def _image_outputs(edit: bool):
    images_tip = "Generated images as one batch (with layers: base first)." if edit else "Generated images as one batch."
    return [
        IO.Image.Output("images", tooltip=images_tip),
        IO.Mask.Output("alpha", tooltip=("Per-image alpha, 1 = opaque, 0 = transparent. Invert it (InvertMask) "
                                         "before feeding a mask input that uses the LoadImage convention.")),
    ]


def _image_options(kwargs) -> seedream.ImageOptions:
    return seedream.ImageOptions(
        size=kwargs.get("size", "2K"),
        width=kwargs.get("width", 2048),
        height=kwargs.get("height", 2048),
        sequential=kwargs.get("sequential", "disabled"),
        max_images=kwargs.get("max_images", 15),
        response_format=kwargs.get("response_format", "url"),
        output_format=kwargs.get("output_format", seedream.MODEL_DEFAULT),
        background=kwargs.get("background", seedream.MODEL_DEFAULT),
        optimize_prompt_mode=kwargs.get("optimize_prompt_mode", "standard"),
        watermark=kwargs.get("watermark", False),
        safety_identifier=kwargs.get("safety_identifier", "").strip(),
        layer_decomposition=kwargs.get("layer_decomposition", False),
        layer_max_images=kwargs.get("layer_max_images", 30),
        text_recognition=kwargs.get("text_recognition", False),
    )


async def _generate(kwargs, images: List[str]) -> IO.NodeOutput:
    model_id = kwargs.get("model", seedream.DEFAULT_MODEL)
    options = _image_options(kwargs)
    body = seedream.build_image_body(model_id, kwargs.get("prompt", ""), images, options,
                                     kwargs.get("endpoint_id", ""))
    sent_max = body.get("sequential_image_generation_options", {}).get("max_images", options.max_images)
    if sent_max != options.max_images:
        emit(f"ModelArk allows {seedream.MAX_SEQUENTIAL_TOTAL} reference plus generated images, so "
             f"max_images {options.max_images} is sent as {sent_max} next to {len(images)} reference "
             f"image{'' if len(images) == 1 else 's'}.")
    client = make_client(kwargs.get("client"))
    emit(f"Seedream request: model={body['model']}, size={body['size']}, "
         f"reference images={len(images)}")
    handoff = _Handoff()
    try:
        image_tensor, alpha = await asyncio.to_thread(
            _generate_sync, client, body, model_id, options, len(images), kwargs.get("fail_on_partial", False),
            handoff)
    except asyncio.CancelledError:
        handoff.abandon()
        raise
    return IO.NodeOutput(image_tensor, alpha)


class _Handoff:
    """Hands a worker thread's billed result to its node, or to the worker's fallback when ComfyUI
    cancelled the node first. Whichever side comes second runs the fallback, so it runs at most once."""

    def __init__(self):
        self._lock = threading.Lock()
        self._abandoned = False
        self._fallback: Optional[Callable[[], None]] = None

    def finish(self, fallback: Callable[[], None]) -> None:
        """Worker: done; `fallback` saves or prints the result if the node never receives it."""
        with self._lock:
            if not self._abandoned:
                self._fallback = fallback
                return
        fallback()

    def abandon(self) -> None:
        """Node: cancelled, so it will not receive the result."""
        with self._lock:
            self._abandoned = True
            fallback, self._fallback = self._fallback, None
        if fallback is not None:
            fallback()


def _generate_sync(client: BytePlusClient, body: dict, model_id: str, options: seedream.ImageOptions,
                   input_images: int, fail_on_partial: bool, handoff: _Handoff):
    """POST, decode and compose in one worker thread. ComfyUI cancels a pending node when another
    node fails, but this thread runs to the end, so images billed after the cancel still reach disk.
    Cancel pressed while only this node runs raises at the next node instead, after this node has
    returned, so images that arrive with Cancel pressed are saved here too."""
    response = client.generate_images(body)
    try:
        output, decoded = _images_from_response(response, model_id, options, input_images, fail_on_partial)
    except Exception as e:
        message = str(e)
        handoff.finish(lambda: emit(message))
        raise
    saved = None
    if client_module._resolve_interrupt_checker()():
        saved = _recover(decoded)
        emit("Cancel was pressed while Seedream was generating, so the run stops before the next "
             f"node. {saved}")
    handoff.finish(lambda: emit("The ComfyUI run ended before Seedream's images were returned. "
                                f"{saved or _recover(decoded)}"))
    return output


def _images_from_response(response: dict, model_id: str, options: seedream.ImageOptions, input_images: int,
                          fail_on_partial: bool):
    """((IMAGE, alpha), decoded images) from a Seedream response; every raise after billing first
    saves the decoded images and names them."""
    items = [item for item in response.get("data") or [] if isinstance(item, dict)]
    failed = [item["error"] for item in items if item.get("error")]
    succeeded = [item for item in items if not item.get("error")]
    urls = [item["url"] for item in succeeded if isinstance(item.get("url"), str)]
    if urls:
        emit(f"Seedream result URLs (valid 24 h): {' '.join(urls)}")
    if not succeeded:
        raise ValueError(f"Seedream returned no images: {str(response)[:300]}")
    reasons = "; ".join(_error_reason(e) for e in failed)
    if failed:
        emit(f"Seedream refused {len(failed)} of {len(items)} images: {reasons}")

    # Every image from here on is billed: no failure below may discard one.
    decoded, decode_errors = decode_items(succeeded)
    problem = None
    if decode_errors:
        problem = f"Seedream images could not be decoded: {'; '.join(decode_errors)}."
    elif failed and fail_on_partial:
        problem = f"Seedream returned {len(succeeded)} of {len(items)} images; failures: {reasons}."
    else:
        try:
            output = compose(succeeded, decoded, options.layer_decomposition)
        except Exception as e:
            problem = str(e) or type(e).__name__
    if problem:
        raise ValueError(f"{problem} {_recover(decoded)}")

    try:
        cost = seedream.image_cost_usd(model_id, [image.size for image in decoded], input_images=input_images,
                                       layers=options.layer_decomposition)
        emit(f"Seedream returned {len(decoded)} image(s), about ${cost:.4f}")
    except ValueError as e:
        # The images are already billed; a gap in the price list must not discard them.
        emit(f"Seedream returned {len(decoded)} image(s); cost unknown: {e}")
    return output, decoded


def _error_reason(error) -> str:
    if isinstance(error, dict):
        return f"{error.get('code')}: {error.get('message', '')}"
    return str(error)


def _recover(decoded) -> str:
    """Save the decoded images and say where, for the error that is about to discard them."""
    keep = [image for image in decoded if image is not None]
    if not keep:
        return "No image decoded, so none could be saved."
    try:
        saved, errors = save_recovered_images(keep)
    except Exception as e:
        return f"Saving the billed images to ComfyUI's output folder failed: {e}"
    parts = [f"The billed images are saved as {', '.join(saved)}"] if saved else []
    return ". ".join(parts + errors)


def _seed_fingerprint(kwargs):
    seed = kwargs.get("seed", -1)
    return float("NaN") if seed == -1 else seed


class BytePlusSeedreamTextToImage(IO.ComfyNode):
    """Seedream text-to-image on BytePlus ModelArk."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedreamTextToImage",
            display_name="BytePlus Seedream Text to Image",
            category=_CATEGORY,
            description="Generate images from a text prompt with Seedream on your own BytePlus ModelArk key.",
            not_idempotent=True,
            inputs=[
                IO.String.Input("prompt", multiline=True, default="", tooltip="What the image shows."),
                *_image_option_inputs(edit=False),
            ],
            outputs=_image_outputs(edit=False),
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        return await _generate(kwargs, [])


class BytePlusSeedreamImageEdit(IO.ComfyNode):
    """Seedream image editing and layer decomposition from reference images."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedreamImageEdit",
            display_name="BytePlus Seedream Image Edit",
            category=_CATEGORY,
            description=("Edit or combine reference images, or split one into layers, with Seedream on your "
                         "own BytePlus ModelArk key."),
            not_idempotent=True,
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="The edit to make. Optional for layer decomposition."),
                IO.Image.Input("images", optional=True,
                               tooltip=("Reference image batch, sent inline. Max 10 on 5.5/5.0 pro/5.0 flash, 14 "
                                        "on 5.0 lite/4.5/4.0, counted together with images_url.")),
                IO.String.Input("images_url", multiline=True, default="", optional=True,
                                tooltip=("More reference images, one https URL or data:image/ URI per line, "
                                         "after the batch.")),
                IO.Mask.Input("mask", optional=True,
                              tooltip=("Alpha for the connected images (LoadImage convention, 1 = transparent): "
                                       "they are sent as PNG with that transparency. 5.0 pro and flash need it "
                                       "for a transparent background. The alpha output of a Seedream node is "
                                       "the inverse: pass it through InvertMask first.")),
                *_image_option_inputs(edit=True),
            ],
            outputs=_image_outputs(edit=True),
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        batch = kwargs.get("images")
        if kwargs.get("mask") is not None and batch is None:
            raise ValueError("The mask applies to the images input; connect images too.")
        limits = SEEDREAM_LAYER_IMAGE_LIMITS if kwargs.get("layer_decomposition") else SEEDREAM_IMAGE_LIMITS
        inline = (await asyncio.to_thread(images_to_data_uris, batch, limits, "images", kwargs.get("mask"))
                  if batch is not None else [])
        images = inline + url_lines(kwargs.get("images_url", ""))
        if not images:
            raise ValueError("Connect images or enter at least one image URL.")
        return await _generate(kwargs, images)
