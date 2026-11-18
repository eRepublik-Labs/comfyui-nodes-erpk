# ABOUTME: Seedance video models on BytePlus ModelArk: one capability row per model, the
# ABOUTME: create-task body builder that enforces those rows, and the per-token price.

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SeedanceModel:
    """What one Seedance model accepts, from the ModelArk create-task reference."""

    model_id: str
    resolutions: Tuple[str, ...]
    duration_min: int
    duration_max: int
    max_reference_images: int
    max_reference_videos: int
    max_reference_audios: int
    first_last_frame: bool
    generate_audio: bool
    draft: bool
    output_formats: Tuple[str, ...]
    # Seed, camera_fixed, frames and the flex tier are documented for 1.0 only.
    seed: bool
    camera_fixed: bool
    frames: bool
    flex: bool
    # priority and omni_reference_task_type are 2.x / 2.5-series fields.
    priority: bool
    omni_task_type: bool
    # 2.0 series refuses an audio clip as the only reference; 2.5 accepts it.
    audio_only_reference: bool
    # 2.5 first-frame and first+last-frame tasks fail asynchronously with
    # InvalidParameter.TaskTypeConstraint unless ratio is adaptive.
    frame_tasks_need_adaptive_ratio: bool
    # 1.0 does not support ratio=adaptive for text-to-video.
    text_to_video_adaptive_ratio: bool
    # USD per million completion tokens, keyed by output resolution.
    price_per_million: Dict[str, float] = field(default_factory=dict)
    price_per_million_with_video_input: Dict[str, float] = field(default_factory=dict)
    flex_price_per_million: Optional[float] = None

    @property
    def references(self) -> bool:
        return self.max_reference_images > 0

    @property
    def duration_auto(self) -> bool:
        return not self.frames


def _price(low: float, p1080: Optional[float] = None, p4k: Optional[float] = None) -> Dict[str, float]:
    prices = {"480p": low, "720p": low}
    if p1080 is not None:
        prices["1080p"] = p1080
    if p4k is not None:
        prices["4k"] = p4k
    return prices


_TWO_FIVE = SeedanceModel(
    model_id="", resolutions=(), duration_min=4, duration_max=30,
    max_reference_images=0, max_reference_videos=0, max_reference_audios=0,
    first_last_frame=True, generate_audio=True, draft=False, output_formats=("mp4", "mov"),
    seed=False, camera_fixed=False, frames=False, flex=False, priority=True, omni_task_type=True,
    audio_only_reference=True, frame_tasks_need_adaptive_ratio=True, text_to_video_adaptive_ratio=True,
)
_TWO_ZERO = SeedanceModel(
    model_id="", resolutions=(), duration_min=4, duration_max=15,
    max_reference_images=9, max_reference_videos=3, max_reference_audios=3,
    first_last_frame=True, generate_audio=True, draft=False, output_formats=("mp4",),
    seed=False, camera_fixed=False, frames=False, flex=False, priority=True, omni_task_type=False,
    audio_only_reference=False, frame_tasks_need_adaptive_ratio=False, text_to_video_adaptive_ratio=True,
)
_ONE_ZERO = SeedanceModel(
    model_id="", resolutions=("480p", "720p", "1080p"), duration_min=2, duration_max=12,
    max_reference_images=0, max_reference_videos=0, max_reference_audios=0,
    first_last_frame=True, generate_audio=False, draft=False, output_formats=("mp4",),
    seed=True, camera_fixed=True, frames=True, flex=True, priority=False, omni_task_type=False,
    audio_only_reference=False, frame_tasks_need_adaptive_ratio=False, text_to_video_adaptive_ratio=False,
)

SEEDANCE_MODELS: Dict[str, SeedanceModel] = {m.model_id: m for m in (
    replace(
        _TWO_FIVE, model_id="dreamina-seedance-2-5-260628", resolutions=("480p", "720p", "1080p", "4k"),
        max_reference_images=30, max_reference_videos=10, max_reference_audios=10, draft=True,
        price_per_million=_price(10.70, 11.7, 4.7),
        price_per_million_with_video_input=_price(6.40, 7.0, 2.9),
    ),
    replace(
        _TWO_FIVE, model_id="dreamina-seedance-2-5-flash-261115", resolutions=("480p", "720p"),
        max_reference_images=10, max_reference_videos=5, max_reference_audios=5,
        price_per_million=_price(7.0), price_per_million_with_video_input=_price(4.3),
    ),
    replace(
        _TWO_ZERO, model_id="dreamina-seedance-2-0-260128", resolutions=("480p", "720p", "1080p", "4k"),
        price_per_million=_price(7.0, 7.7, 4.0),
        price_per_million_with_video_input=_price(4.3, 4.7, 2.4),
    ),
    replace(
        _TWO_ZERO, model_id="dreamina-seedance-2-0-fast-260128", resolutions=("480p", "720p"),
        price_per_million=_price(5.6), price_per_million_with_video_input=_price(3.3),
    ),
    replace(
        _TWO_ZERO, model_id="dreamina-seedance-2-0-mini-260615", resolutions=("480p", "720p"),
        price_per_million=_price(3.5), price_per_million_with_video_input=_price(2.1),
    ),
    replace(
        _ONE_ZERO, model_id="seedance-1-0-pro-250528",
        price_per_million=_price(2.5, 2.5), flex_price_per_million=1.25,
    ),
    replace(
        _ONE_ZERO, model_id="seedance-1-0-pro-fast-251015", first_last_frame=False,
        price_per_million=_price(1.0, 1.0), flex_price_per_million=0.5,
    ),
)}

MODEL_IDS: List[str] = list(SEEDANCE_MODELS)
DEFAULT_MODEL = "dreamina-seedance-2-0-mini-260615"
RESOLUTIONS = ["480p", "720p", "1080p", "4k"]
RATIOS = ["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"]
OUTPUT_FORMATS = ["mp4", "mov"]
SERVICE_TIERS = ["default", "flex"]
OMNI_TASK_TYPES = ["auto", "reference", "edit", "extend"]
DRAFT_RENDER_RESOLUTIONS = ("1080p", "4k")
EXPIRES_MIN, EXPIRES_MAX, EXPIRES_DEFAULT = 3600, 259200, 172800
FRAMES_MIN, FRAMES_MAX = 29, 289
SAFETY_IDENTIFIER_MAX = 64
SEED_MAX = 2147483647

_IMAGE_URL_PREFIXES = ("https://", "http://", "asset://", "data:image/")
_VIDEO_URL_PREFIXES = ("https://", "http://", "asset://")
_AUDIO_URL_PREFIXES = ("https://", "http://", "asset://", "data:audio/")


class Mode(Enum):
    TEXT = "text-to-video"
    FIRST_FRAME = "first-frame"
    FIRST_LAST_FRAME = "first+last-frame"
    REFERENCE = "reference-to-video"
    DRAFT_RENDER = "draft render"


@dataclass(frozen=True)
class VideoMedia:
    """Image, video and audio inputs, each a URL, data URI or asset:// ID."""

    first_frame: Optional[str] = None
    last_frame: Optional[str] = None
    reference_images: Tuple[str, ...] = ()
    reference_videos: Tuple[str, ...] = ()
    reference_audios: Tuple[str, ...] = ()
    draft_task_id: str = ""

    def mode(self) -> Mode:
        frames = self.first_frame is not None or self.last_frame is not None
        references = bool(self.reference_images or self.reference_videos or self.reference_audios)
        if self.draft_task_id:
            if frames or references:
                raise ValueError("A draft render reuses the draft's inputs: disconnect every image, "
                                 "video and audio input, or clear draft_task_id.")
            return Mode.DRAFT_RENDER
        if frames and references:
            raise ValueError("First/last frames and reference inputs cannot be mixed in one Seedance request.")
        if self.last_frame is not None and self.first_frame is None:
            raise ValueError("A last frame needs a first frame.")
        if self.last_frame is not None:
            return Mode.FIRST_LAST_FRAME
        if self.first_frame is not None:
            return Mode.FIRST_FRAME
        if references:
            return Mode.REFERENCE
        return Mode.TEXT


@dataclass(frozen=True)
class VideoOptions:
    resolution: str = "720p"
    ratio: str = "adaptive"
    duration: int = 5
    frames: int = 0
    seed: int = -1
    camera_fixed: bool = False
    watermark: bool = False
    generate_audio: bool = True
    return_last_frame: bool = False
    output_format: str = "mp4"
    draft: bool = False
    service_tier: str = "default"
    priority: int = 0
    execution_expires_after: int = EXPIRES_DEFAULT
    omni_reference_task_type: str = "auto"
    safety_identifier: str = ""


def get_model(model_id: str) -> SeedanceModel:
    try:
        return SEEDANCE_MODELS[model_id]
    except KeyError:
        raise ValueError(f"Unknown Seedance model {model_id!r}. Known: {', '.join(MODEL_IDS)}") from None


def _check_urls(kind: str, urls: Tuple[str, ...], prefixes: Tuple[str, ...]) -> None:
    for url in urls:
        if not url.startswith(prefixes):
            raise ValueError(f"{kind} {url[:80]!r} must start with one of {', '.join(prefixes)}")


def _check_references(model: SeedanceModel, media: VideoMedia) -> None:
    if not model.references:
        raise ValueError(f"{model.model_id} does not take reference images, videos or audio. "
                         "Use a Seedance 2.0 or 2.5 model.")
    counts = (
        ("reference images", len(media.reference_images), model.max_reference_images),
        ("reference videos", len(media.reference_videos), model.max_reference_videos),
        ("reference audio clips", len(media.reference_audios), model.max_reference_audios),
    )
    for kind, count, cap in counts:
        if count > cap:
            raise ValueError(f"{model.model_id} takes at most {cap} {kind}, got {count}.")
    if media.reference_audios and not (media.reference_images or media.reference_videos) \
            and not model.audio_only_reference:
        raise ValueError(f"{model.model_id} needs a reference image or video alongside reference audio.")
    _check_urls("Reference image", media.reference_images, _IMAGE_URL_PREFIXES)
    _check_urls("Reference video", media.reference_videos, _VIDEO_URL_PREFIXES)
    _check_urls("Reference audio", media.reference_audios, _AUDIO_URL_PREFIXES)


def _content(prompt: str, media: VideoMedia, mode: Mode) -> List[dict]:
    content: List[dict] = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    if mode in (Mode.FIRST_FRAME, Mode.FIRST_LAST_FRAME):
        content.append({"type": "image_url", "image_url": {"url": media.first_frame}, "role": "first_frame"})
    if mode is Mode.FIRST_LAST_FRAME:
        content.append({"type": "image_url", "image_url": {"url": media.last_frame}, "role": "last_frame"})
    for url in media.reference_images:
        content.append({"type": "image_url", "image_url": {"url": url}, "role": "reference_image"})
    for url in media.reference_videos:
        content.append({"type": "video_url", "video_url": {"url": url}, "role": "reference_video"})
    for url in media.reference_audios:
        content.append({"type": "audio_url", "audio_url": {"url": url}, "role": "reference_audio"})
    return content


def _check_common(model: SeedanceModel, options: VideoOptions) -> None:
    if options.resolution not in model.resolutions:
        raise ValueError(f"{model.model_id} renders {', '.join(model.resolutions)}, not {options.resolution}.")
    if options.output_format not in model.output_formats:
        raise ValueError(f"{model.model_id} outputs {', '.join(model.output_formats)} only, "
                         f"not {options.output_format}.")
    if options.service_tier == "flex" and not model.flex:
        raise ValueError(f"{model.model_id} has no flex tier: ModelArk offers flex on Seedance 1.0 only.")
    if not EXPIRES_MIN <= options.execution_expires_after <= EXPIRES_MAX:
        raise ValueError(f"execution_expires_after must be {EXPIRES_MIN}-{EXPIRES_MAX} s, "
                         f"got {options.execution_expires_after}.")
    if len(options.safety_identifier) > SAFETY_IDENTIFIER_MAX:
        raise ValueError(f"safety_identifier is at most {SAFETY_IDENTIFIER_MAX} characters, "
                         f"got {len(options.safety_identifier)}.")


def _output_fields(model: SeedanceModel, options: VideoOptions) -> dict:
    """Fields a draft render may still carry, per the Seedance 2.5 draft rules."""
    body = {
        "watermark": options.watermark,
        "return_last_frame": options.return_last_frame,
        "execution_expires_after": options.execution_expires_after,
    }
    if len(model.output_formats) > 1:
        body["output_format"] = options.output_format
    if options.service_tier == "flex":
        body["service_tier"] = "flex"
    if model.priority and options.priority:
        body["priority"] = options.priority
    if options.safety_identifier:
        body["safety_identifier"] = options.safety_identifier
    return body


def _build_draft_render(model: SeedanceModel, prompt: str, media: VideoMedia, options: VideoOptions) -> dict:
    if not model.draft:
        raise ValueError(f"{model.model_id} has no draft mode; only Seedance 2.5 renders drafts.")
    if options.draft:
        raise ValueError("Turn draft off to render a draft: the final render is a full-resolution task.")
    if prompt:
        raise ValueError("A draft render reuses the draft's prompt; clear the prompt.")
    if options.resolution not in DRAFT_RENDER_RESOLUTIONS:
        raise ValueError(f"A draft render needs resolution 1080p or 4k, got {options.resolution}.")
    return {"content": [{"type": "draft_task", "draft_task": {"id": media.draft_task_id}}],
            "resolution": options.resolution, **_output_fields(model, options)}


def _duration_fields(model: SeedanceModel, options: VideoOptions) -> dict:
    if options.frames:
        if not model.frames:
            raise ValueError(f"{model.model_id} takes no frames count; set frames to 0 and use duration.")
        if not FRAMES_MIN <= options.frames <= FRAMES_MAX or (options.frames - 25) % 4:
            raise ValueError(f"frames must be 25 + 4n within {FRAMES_MIN}-{FRAMES_MAX}, got {options.frames}.")
        return {"frames": options.frames}
    if options.duration == -1:
        if not model.duration_auto:
            raise ValueError(f"{model.model_id} cannot pick its own duration; "
                             f"set {model.duration_min}-{model.duration_max} s.")
        return {"duration": -1}
    if not model.duration_min <= options.duration <= model.duration_max:
        auto = " or -1" if model.duration_auto else ""
        raise ValueError(f"{model.model_id} takes a duration of {model.duration_min}-{model.duration_max} s"
                         f"{auto}, got {options.duration}.")
    return {"duration": options.duration}


def _check_ratio(model: SeedanceModel, options: VideoOptions, mode: Mode) -> None:
    if mode is Mode.TEXT and options.ratio == "adaptive" and not model.text_to_video_adaptive_ratio:
        raise ValueError(f"{model.model_id} cannot use ratio adaptive for text-to-video; pick a fixed ratio.")
    if mode in (Mode.FIRST_FRAME, Mode.FIRST_LAST_FRAME) and model.frame_tasks_need_adaptive_ratio \
            and options.ratio != "adaptive":
        raise ValueError(f"{model.model_id} {mode.value} tasks accept only ratio adaptive, got {options.ratio}.")
    task_type = options.omni_reference_task_type
    if mode is Mode.REFERENCE and model.omni_task_type and task_type in ("edit", "extend") \
            and options.ratio != "adaptive":
        raise ValueError(f"A Seedance 2.5 video {task_type} accepts only ratio adaptive, got {options.ratio}.")


def build_video_body(model_id: str, prompt: str, media: VideoMedia, options: VideoOptions,
                     endpoint_id: str = "") -> dict:
    """Return the POST /contents/generations/tasks body, or raise ValueError on a combination
    the selected model rejects. Options a model ignores are left out of the body."""
    model = get_model(model_id)
    prompt = prompt.strip()
    mode = media.mode()
    _check_common(model, options)
    sent_model = endpoint_id.strip() or model.model_id

    if mode is Mode.DRAFT_RENDER:
        return {"model": sent_model, **_build_draft_render(model, prompt, media, options)}

    if mode is Mode.TEXT and not prompt:
        raise ValueError("Text-to-video needs a prompt.")
    if mode is Mode.FIRST_LAST_FRAME and not model.first_last_frame:
        raise ValueError(f"{model.model_id} does not support a last frame; use a first frame only or "
                         "pick another model.")
    if mode is Mode.REFERENCE:
        _check_references(model, media)
    if mode in (Mode.FIRST_FRAME, Mode.FIRST_LAST_FRAME):
        frames = (media.first_frame,) + ((media.last_frame,) if media.last_frame else ())
        _check_urls("Frame image", frames, _IMAGE_URL_PREFIXES)
    _check_ratio(model, options, mode)
    if options.draft:
        if not model.draft:
            raise ValueError(f"{model.model_id} has no draft mode; only Seedance 2.5 makes drafts.")
        if options.resolution != "480p":
            raise ValueError(f"A draft renders at 480p only, got {options.resolution}.")
    if mode is Mode.REFERENCE and model.omni_task_type and options.omni_reference_task_type == "edit" \
            and options.duration != -1:
        raise ValueError(f"A Seedance 2.5 video edit needs duration -1, got {options.duration}.")
    if options.seed != -1 and not 0 <= options.seed <= SEED_MAX:
        raise ValueError(f"seed must be -1 or 0-{SEED_MAX}, got {options.seed}.")

    body = {
        "model": sent_model,
        "content": _content(prompt, media, mode),
        "resolution": options.resolution,
        "ratio": options.ratio,
        **_duration_fields(model, options),
        **_output_fields(model, options),
    }
    if model.generate_audio:
        body["generate_audio"] = options.generate_audio
    if model.seed and options.seed >= 0:
        body["seed"] = options.seed
    if model.camera_fixed and mode is not Mode.REFERENCE:
        body["camera_fixed"] = options.camera_fixed
    if model.draft:
        body["draft"] = options.draft
    if mode is Mode.REFERENCE and model.omni_task_type:
        body["omni_reference_task_type"] = options.omni_reference_task_type
    return body


def video_cost_usd(model_id: str, resolution: str, completion_tokens: int,
                   has_video_input: bool = False, flex: bool = False) -> float:
    """USD charged for a finished task: completion tokens x the model's per-million rate."""
    model = get_model(model_id)
    if flex:
        rate = model.flex_price_per_million
    elif has_video_input:
        rate = model.price_per_million_with_video_input.get(resolution)
    else:
        rate = model.price_per_million.get(resolution)
    if rate is None:
        tier = "flex " if flex else "with-video " if has_video_input else ""
        raise ValueError(f"{model_id} has no {tier}price for {resolution}.")
    return completion_tokens * rate / 1_000_000
