# ABOUTME: Seedance V3 video nodes on BytePlus ModelArk: text, image (first/last frame) and
# ABOUTME: reference to video, plus a free node that reads back a task's result by its ID.

import asyncio
import re

from comfy_api.latest import IO

from .byteplus_api import emit, seedance
from .byteplus_api.client import BytePlusClient, task_failure_message
from .byteplus_api.media import SEEDANCE_IMAGE_LIMITS, images_to_data_uris
from .nodes import CLIENT_TOOLTIP, make_client, url_lines

# The poll deadline sits past execution_expires_after so ModelArk reports `expired` first.
_POLL_MARGIN_SECONDS = 600
_CATEGORY = "ERPK/BytePlus/Video"
_TASK_ID = re.compile(r"[A-Za-z0-9_-]+")


def _option_inputs(default_duration: int, reference: bool = False):
    inputs = [
        IO.Custom("BYTEPLUS_API_CLIENT").Input("client", optional=True, tooltip=CLIENT_TOOLTIP),
        IO.Combo.Input(
            "model", options=seedance.MODEL_IDS, default=seedance.DEFAULT_MODEL, optional=True,
            tooltip=(
                "Seedance model. 2.5 (480p-4k, 4-30 s, drafts, mov); 2.5 flash (480p/720p); 2.0 (480p-4k, "
                "4-15 s); 2.0 fast and 2.0 mini (480p/720p, 4-15 s; mini is the cheapest 2.x); 1.0 pro and "
                "1.0 pro fast (480p-1080p, 2-12 s, seed, camera_fixed, frames, flex; no references, and "
                "pro fast has no last frame). A combination the model rejects stops before any call."
            ),
        ),
        IO.String.Input(
            "endpoint_id", default="", optional=True,
            tooltip=("Custom ModelArk endpoint ID to call instead of the model ID. Accounts that get "
                     "ModelIDAccessDisabled must use one. The model widget still decides which options apply."),
        ),
        IO.Combo.Input(
            "resolution", options=seedance.RESOLUTIONS, default="720p", optional=True,
            tooltip="480p/720p on every model; 1080p on 2.5, 2.0 and 1.0; 4k on 2.5 and 2.0. Drafts are 480p.",
        ),
        IO.Combo.Input(
            "ratio", options=seedance.RATIOS, default="adaptive", optional=True,
            tooltip=("adaptive lets the model pick. 2.5 first-frame and first+last-frame tasks, and 2.5 video "
                     "edit/extend, accept adaptive only. 1.0 text-to-video needs a fixed ratio. A ratio unlike "
                     "the input image center-crops it."),
        ),
        IO.Int.Input(
            "duration", default=default_duration, min=-1, max=30, optional=True,
            tooltip=("Seconds. 2.5: 4-30; 2.0 series: 4-15; 1.0: 2-12. -1 lets a 2.x model pick (2.5 video "
                     "edit requires -1). ModelArk reports durations floored to whole seconds."),
        ),
        IO.Int.Input(
            "frames", default=0, min=0, max=seedance.FRAMES_MAX, optional=True,
            tooltip="1.0 only: exact frame count 29-289 in steps of 4 (25 + 4n) at 24 fps; overrides duration. 0 = off.",
        ),
        IO.Boolean.Input(
            "generate_audio", default=True, optional=True,
            tooltip="2.x only: synchronized stereo audio. Not sent to 1.0, which makes silent video.",
        ),
        IO.Boolean.Input("watermark", default=False, optional=True,
                         tooltip="Adds the 'AI Generated' mark in the lower-right corner. All models."),
        IO.Boolean.Input(
            "return_last_frame", default=False, optional=True,
            tooltip="Also return the final frame as a JPEG URL (no watermark) on the last_frame_url output.",
        ),
        IO.Combo.Input(
            "output_format", options=seedance.OUTPUT_FORMATS, default="mp4", optional=True,
            tooltip=("mov (H.264 yuv444p with PCM audio) is 2.5 and 2.5 flash only. 2.5 1080p/4k and 2.0 4k "
                     "are 10-bit HEVC, which some players cannot decode."),
        ),
        IO.Boolean.Input(
            "camera_fixed", default=False, optional=True,
            tooltip="1.0 only: keep the camera still. Turning it on with a 2.x model stops before any call.",
        ),
        IO.Combo.Input(
            "service_tier", options=seedance.SERVICE_TIERS, default="default", optional=True,
            tooltip="flex runs offline at half price and can take hours. Seedance 1.0 only.",
        ),
        IO.Int.Input(
            "priority", default=0, min=0, max=9, optional=True,
            tooltip="2.x only: queue order among tasks on the same endpoint (0-9). Not sent to 1.0 or when 0.",
        ),
        IO.Boolean.Input(
            "draft", default=False, optional=True,
            tooltip=("Seedance 2.5 only: a cheap 480p preview. Feed its task_id into draft_task_id to render "
                     "the final 1080p or 4k video."),
        ),
        IO.String.Input(
            "draft_task_id", default="", optional=True,
            tooltip=("Render this 2.5 draft at 1080p or 4k. The draft's prompt, inputs, duration, ratio and "
                     "audio are reused, so clear the prompt and disconnect every image, video and audio input."),
        ),
    ]
    if reference:
        inputs.append(IO.Combo.Input(
            "omni_reference_task_type", options=seedance.OMNI_TASK_TYPES, default="auto", optional=True,
            tooltip=("2.5 only. auto infers reference, edit or extend from the prompt; edit/extend are checked "
                     "before queueing. A 2.5 edit needs duration -1 and ratio adaptive. Not sent to 2.0."),
        ))
    inputs += [
        IO.Int.Input(
            "execution_expires_after", default=seedance.EXPIRES_DEFAULT, min=seedance.EXPIRES_MIN,
            max=seedance.EXPIRES_MAX, optional=True,
            tooltip="Seconds after creation before ModelArk expires a task still queued or running (1-72 h).",
        ),
        IO.String.Input("safety_identifier", default="", optional=True,
                        tooltip="Optional hashed end-user ID (max 64 characters) for ModelArk's abuse checks."),
        IO.Int.Input(
            "seed", default=-1, min=-1, max=seedance.SEED_MAX, optional=True, control_after_generate="randomize",
            tooltip=("On Seedance 1.0, 0 or more is sent as the generation seed. 2.x echoes a seed but does not "
                     "reproduce a video with it, so there it only controls ComfyUI's cache. -1 re-runs every queue; "
                     "a fixed value reuses the cached result, a video URL that expires after 24 h."),
        ),
    ]
    return inputs


_OUTPUTS = [
    IO.String.Output("video_url", tooltip="MP4/MOV URL, valid 24 h (2.5: at most 100 downloads)."),
    IO.String.Output("last_frame_url", tooltip="Final-frame JPEG URL when return_last_frame is on, else empty."),
    IO.String.Output("task_id", tooltip="ModelArk task ID; a draft's ID feeds draft_task_id."),
]


def _options(kwargs) -> seedance.VideoOptions:
    return seedance.VideoOptions(
        resolution=kwargs.get("resolution", "720p"),
        ratio=kwargs.get("ratio", "adaptive"),
        duration=kwargs.get("duration", 5),
        frames=kwargs.get("frames", 0),
        seed=kwargs.get("seed", -1),
        camera_fixed=kwargs.get("camera_fixed", False),
        watermark=kwargs.get("watermark", False),
        generate_audio=kwargs.get("generate_audio", True),
        return_last_frame=kwargs.get("return_last_frame", False),
        output_format=kwargs.get("output_format", "mp4"),
        draft=kwargs.get("draft", False),
        service_tier=kwargs.get("service_tier", "default"),
        priority=kwargs.get("priority", 0),
        execution_expires_after=kwargs.get("execution_expires_after", seedance.EXPIRES_DEFAULT),
        omni_reference_task_type=kwargs.get("omni_reference_task_type", "auto"),
        safety_identifier=kwargs.get("safety_identifier", "").strip(),
    )


async def _single_image(image, url: str, name: str):
    """A connected IMAGE (one frame) takes precedence over the URL field."""
    if image is not None:
        if image.shape[0] != 1:
            raise ValueError(f"{name} takes one image, got a batch of {image.shape[0]}.")
        return (await asyncio.to_thread(images_to_data_uris, image, SEEDANCE_IMAGE_LIMITS, name))[0]
    return url.strip() or None


def _task_urls(task: dict):
    """(video_url, last_frame_url) of a task, each "" when absent or null."""
    content = task.get("content") or {}
    return content.get("video_url") or "", content.get("last_frame_url") or ""


async def _run(kwargs, media: seedance.VideoMedia) -> IO.NodeOutput:
    model_id = kwargs.get("model", seedance.DEFAULT_MODEL)
    options = _options(kwargs)
    body = seedance.build_video_body(model_id, kwargs.get("prompt", ""), media, options,
                                     kwargs.get("endpoint_id", ""))
    client: BytePlusClient = make_client(kwargs.get("client"))
    emit(f"Seedance {media.mode().value} request: model={body['model']}, "
         f"resolution={options.resolution}")
    task_id = await client.create_video_task(body)
    task = await client.wait_for_video_task(task_id, options.execution_expires_after + _POLL_MARGIN_SECONDS)

    video_url, last_frame_url = _task_urls(task)
    if not video_url:
        raise ValueError(f"Seedance task {task_id} succeeded without a video_url: {str(task)[:300]}")
    if options.return_last_frame and not last_frame_url:
        emit(f"Task {task_id} returned no last_frame_url although return_last_frame was on; "
             "returning the video without it.")
    tokens = (task.get("usage") or {}).get("completion_tokens")
    if isinstance(tokens, int) and tokens > 0:
        try:
            cost = seedance.video_cost_usd(model_id, options.resolution, tokens,
                                           has_video_input=bool(media.reference_videos),
                                           flex=options.service_tier == "flex")
            emit(f"Task {task_id}: {tokens} tokens, about ${cost:.4f}")
        except ValueError as e:
            # The video is already billed; a gap in the price list must not discard it.
            emit(f"Task {task_id}: {tokens} tokens; cost unknown: {e}")
    emit(f"Video URL: {video_url}")
    return IO.NodeOutput(video_url, last_frame_url, task_id)


def _seed_fingerprint(kwargs):
    seed = kwargs.get("seed", -1)
    return float("NaN") if seed == -1 else seed


class BytePlusSeedanceTextToVideo(IO.ComfyNode):
    """Seedance text-to-video on BytePlus ModelArk; also renders a 2.5 draft by task ID."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedanceTextToVideo",
            display_name="BytePlus Seedance Text to Video",
            category=_CATEGORY,
            description="Generate a video from a text prompt with Seedance on your own BytePlus ModelArk key.",
            not_idempotent=True,
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="What the video shows. Leave empty only to render a draft."),
                *_option_inputs(default_duration=5),
            ],
            outputs=_OUTPUTS,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        return await _run(kwargs, seedance.VideoMedia(draft_task_id=kwargs.get("draft_task_id", "").strip()))


class BytePlusSeedanceImageToVideo(IO.ComfyNode):
    """Seedance image-to-video from a start frame and an optional end frame."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedanceImageToVideo",
            display_name="BytePlus Seedance Image to Video",
            category=_CATEGORY,
            description=("Animate a start frame, optionally toward an end frame, with Seedance on your own "
                         "BytePlus ModelArk key."),
            not_idempotent=True,
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip="Optional description of the motion."),
                IO.Image.Input("first_frame", optional=True,
                               tooltip=("Start frame (one image), sent inline as JPEG. 300-6000 px per side, "
                                        "aspect ratio 0.4-2.5. Takes precedence over first_frame_url.")),
                IO.String.Input("first_frame_url", default="", optional=True,
                                tooltip="Start frame as an https URL or asset://ID, used when first_frame is not connected."),
                IO.Image.Input("last_frame", optional=True,
                               tooltip=("End frame (one image). Not on 1.0 pro fast. If its aspect ratio differs "
                                        "from the start frame, it is cropped to match.")),
                IO.String.Input("last_frame_url", default="", optional=True,
                                tooltip="End frame as an https URL or asset://ID, used when last_frame is not connected."),
                *_option_inputs(default_duration=5),
            ],
            outputs=_OUTPUTS,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        media = seedance.VideoMedia(
            first_frame=await _single_image(kwargs.get("first_frame"), kwargs.get("first_frame_url", ""), "first_frame"),
            last_frame=await _single_image(kwargs.get("last_frame"), kwargs.get("last_frame_url", ""), "last_frame"),
            draft_task_id=kwargs.get("draft_task_id", "").strip(),
        )
        if media.first_frame is None and media.last_frame is None and not media.draft_task_id:
            raise ValueError("Connect a first_frame image or enter first_frame_url.")
        return await _run(kwargs, media)


class BytePlusSeedanceReferenceToVideo(IO.ComfyNode):
    """Seedance 2.x omni-reference video from reference images, videos and audio."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedanceReferenceToVideo",
            display_name="BytePlus Seedance Reference to Video",
            category=_CATEGORY,
            description=("Generate, edit or extend a video from reference images, videos and audio with "
                         "Seedance 2.x on your own BytePlus ModelArk key."),
            not_idempotent=True,
            inputs=[
                IO.String.Input("prompt", multiline=True, default="",
                                tooltip=("How to use the references. On 2.5, edit or extend wording ('replace', "
                                         "'extend forward') makes the task an edit or extend.")),
                IO.Image.Input("reference_images", optional=True,
                               tooltip=("Reference image batch, sent inline as JPEG. Max 30 on 2.5, 10 on 2.5 "
                                        "flash, 9 on 2.0 series, counted together with reference_images_url. "
                                        "Real human faces are rejected on 2.x.")),
                IO.String.Input("reference_images_url", multiline=True, default="", optional=True,
                                tooltip="More reference images, one https URL or asset://ID per line, after the batch."),
                IO.String.Input("reference_videos_url", multiline=True, default="", optional=True,
                                tooltip=("Reference videos, one https URL or asset://ID per line (ModelArk takes "
                                         "no inline video). mp4/mov, 2-30 s each on 2.5 (2-15 s on 2.0), "
                                         "max 10 / 5 / 3 on 2.5 / 2.5 flash / 2.0 series. Video input bills at "
                                         "the lower with-video rate plus a minimum token charge.")),
                IO.String.Input("reference_audios_url", multiline=True, default="", optional=True,
                                tooltip=("Reference audio, one https URL or asset://ID per line. wav/mp3, max 10 / "
                                         "5 / 3. Audio alone is allowed on 2.5 only.")),
                *_option_inputs(default_duration=-1, reference=True),
            ],
            outputs=_OUTPUTS,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, **kwargs) -> IO.NodeOutput:
        batch = kwargs.get("reference_images")
        inline = (await asyncio.to_thread(images_to_data_uris, batch, SEEDANCE_IMAGE_LIMITS, "reference_images")
                  if batch is not None else [])
        media = seedance.VideoMedia(
            reference_images=tuple(inline + url_lines(kwargs.get("reference_images_url", ""))),
            reference_videos=tuple(url_lines(kwargs.get("reference_videos_url", ""))),
            reference_audios=tuple(url_lines(kwargs.get("reference_audios_url", ""))),
            draft_task_id=kwargs.get("draft_task_id", "").strip(),
        )
        if media.mode() is seedance.Mode.TEXT:
            raise ValueError("Connect reference_images or enter at least one reference URL.")
        return await _run(kwargs, media)


class BytePlusSeedanceTaskResult(IO.ComfyNode):
    """Reads a Seedance task's status and result URLs by ID; a GET, so it bills nothing."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="BytePlusSeedanceTaskResult",
            display_name="BytePlus Seedance Task Result",
            category=_CATEGORY,
            description=("Fetch a Seedance task's video URL, last-frame URL and status by task ID, for example "
                         "after a run was cancelled or lost. Reading a task is free."),
            not_idempotent=True,
            inputs=[
                IO.String.Input("task_id", default="",
                                tooltip="ModelArk task ID (cgt-...), from a Seedance node's task_id output or the console."),
                IO.Custom("BYTEPLUS_API_CLIENT").Input("client", optional=True, tooltip=CLIENT_TOOLTIP),
                IO.Boolean.Input(
                    "wait", default=True, optional=True,
                    tooltip=("On: poll until the task finishes and raise if it failed. Off: read the status once; "
                             "the URLs are empty until it succeeds. Keep seed on randomize while the task is "
                             "unfinished, or a cached queued or running status is served again."),
                ),
                IO.Int.Input(
                    "seed", default=-1, min=-1, max=seedance.SEED_MAX, optional=True,
                    control_after_generate="randomize",
                    tooltip=("Cache control only, never sent. Randomize reads the task again on every queue; a "
                             "fixed value reuses the last answer, even a queued or running status from before "
                             "the task finished."),
                ),
            ],
            outputs=[
                IO.String.Output("video_url", tooltip="Video URL once the task succeeded, else empty. Valid 24 h."),
                IO.String.Output("last_frame_url",
                                 tooltip="Final-frame URL if the task was created with return_last_frame, else empty."),
                IO.String.Output("status", tooltip="queued, running, succeeded, failed, expired or cancelled."),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return _seed_fingerprint(kwargs)

    @classmethod
    async def execute(cls, task_id: str = "", **kwargs) -> IO.NodeOutput:
        task_id = task_id.strip()
        if not _TASK_ID.fullmatch(task_id):
            raise ValueError(f"task_id must be a ModelArk task ID such as cgt-20261119021437-q68pg, got {task_id!r}.")
        client = make_client(kwargs.get("client"))
        if kwargs.get("wait", True):
            # ModelArk expires any task within EXPIRES_MAX of its creation, so this bound always ends the wait.
            task = await client.wait_for_video_task(task_id, seedance.EXPIRES_MAX + _POLL_MARGIN_SECONDS,
                                                    cancel_on_interrupt=False)
        else:
            task = await client.get_video_task(task_id)
        status = task.get("status") or ""
        if status not in ("queued", "running", "succeeded"):
            emit(task_failure_message(task_id, task))
        video_url, last_frame_url = _task_urls(task)
        if video_url:
            emit(f"Video URL: {video_url}")
        return IO.NodeOutput(video_url, last_frame_url, status)
