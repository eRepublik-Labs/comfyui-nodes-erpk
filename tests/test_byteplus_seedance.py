# ABOUTME: Seedance create-task bodies per mode and per-model gating, against the ModelArk docs.
# ABOUTME: Expected bodies and prices are literals from the API study, not recomputed by the builder.

import pytest

from erpk.byteplus.byteplus_api.seedance import (
    VideoMedia, VideoOptions, build_video_body, video_cost_usd,
)

MINI = "dreamina-seedance-2-0-mini-260615"
TWO_FIVE = "dreamina-seedance-2-5-260628"
PRO = "seedance-1-0-pro-250528"
PRO_FAST = "seedance-1-0-pro-fast-251015"
IMG_A = "https://example.com/a.png"
IMG_B = "https://example.com/b.png"


def test_text_to_video_on_2_0_mini_sends_audio_and_omits_1_0_fields():
    body = build_video_body(MINI, "  a fox runs  ", VideoMedia(), VideoOptions(seed=7))
    assert body == {
        "model": MINI,
        "content": [{"type": "text", "text": "a fox runs"}],
        "resolution": "720p",
        "ratio": "adaptive",
        "duration": 5,
        "watermark": False,
        "return_last_frame": False,
        "execution_expires_after": 172800,
        "generate_audio": True,
    }


def test_first_frame_on_1_0_pro_sends_seed_camera_fixed_and_flex():
    options = VideoOptions(resolution="480p", ratio="16:9", duration=5, seed=11, camera_fixed=True,
                           service_tier="flex", return_last_frame=True)
    body = build_video_body(PRO, "", VideoMedia(first_frame=IMG_A), options)
    assert body == {
        "model": PRO,
        "content": [{"type": "image_url", "image_url": {"url": IMG_A}, "role": "first_frame"}],
        "resolution": "480p",
        "ratio": "16:9",
        "duration": 5,
        "watermark": False,
        "return_last_frame": True,
        "execution_expires_after": 172800,
        "service_tier": "flex",
        "seed": 11,
        "camera_fixed": True,
    }


def test_first_last_frame_on_2_5_with_frames_count_on_1_0_and_endpoint_id():
    body = build_video_body(TWO_FIVE, "turn", VideoMedia(first_frame=IMG_A, last_frame=IMG_B),
                            VideoOptions(duration=-1, output_format="mov", priority=3, draft=False),
                            endpoint_id=" ep-20261118-abc ")
    assert body == {
        "model": "ep-20261118-abc",
        "content": [
            {"type": "text", "text": "turn"},
            {"type": "image_url", "image_url": {"url": IMG_A}, "role": "first_frame"},
            {"type": "image_url", "image_url": {"url": IMG_B}, "role": "last_frame"},
        ],
        "resolution": "720p",
        "ratio": "adaptive",
        "duration": -1,
        "watermark": False,
        "return_last_frame": False,
        "execution_expires_after": 172800,
        "output_format": "mov",
        "priority": 3,
        "generate_audio": True,
        "draft": False,
    }
    frames_body = build_video_body(PRO, "", VideoMedia(first_frame=IMG_A, last_frame=IMG_B),
                                   VideoOptions(frames=121))
    assert frames_body["frames"] == 121 and "duration" not in frames_body


def test_reference_images_video_and_audio_on_2_5():
    media = VideoMedia(reference_images=("data:image/jpeg;base64,AAAA", "asset://asset-1"),
                       reference_videos=("https://example.com/v.mp4",),
                       reference_audios=("https://example.com/a.mp3",))
    body = build_video_body(TWO_FIVE, "", media,
                            VideoOptions(duration=-1, omni_reference_task_type="extend", draft=True,
                                         resolution="480p", generate_audio=False))
    assert body == {
        "model": TWO_FIVE,
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,AAAA"}, "role": "reference_image"},
            {"type": "image_url", "image_url": {"url": "asset://asset-1"}, "role": "reference_image"},
            {"type": "video_url", "video_url": {"url": "https://example.com/v.mp4"}, "role": "reference_video"},
            {"type": "audio_url", "audio_url": {"url": "https://example.com/a.mp3"}, "role": "reference_audio"},
        ],
        "resolution": "480p",
        "ratio": "adaptive",
        "duration": -1,
        "watermark": False,
        "return_last_frame": False,
        "execution_expires_after": 172800,
        "output_format": "mp4",
        "generate_audio": False,
        "draft": True,
        "omni_reference_task_type": "extend",
    }


def test_draft_render_sends_only_the_fields_the_draft_rules_allow():
    body = build_video_body(TWO_FIVE, "", VideoMedia(draft_task_id="cgt-draft-1"),
                            VideoOptions(resolution="1080p", ratio="16:9", duration=8, seed=3,
                                         watermark=True, safety_identifier="user-hash"))
    assert body == {
        "model": TWO_FIVE,
        "content": [{"type": "draft_task", "draft_task": {"id": "cgt-draft-1"}}],
        "resolution": "1080p",
        "watermark": True,
        "return_last_frame": False,
        "execution_expires_after": 172800,
        "output_format": "mp4",
        "safety_identifier": "user-hash",
    }


@pytest.mark.parametrize("model, prompt, media, options, message", [
    (PRO, "x", VideoMedia(reference_images=(IMG_A,)), VideoOptions(),
     "seedance-1-0-pro-250528 does not take reference images, videos or audio. Use a Seedance 2.0 or 2.5 model."),
    (MINI, "x", VideoMedia(reference_images=(IMG_A,) * 10), VideoOptions(),
     "dreamina-seedance-2-0-mini-260615 takes at most 9 reference images, got 10."),
    (MINI, "x", VideoMedia(reference_audios=("https://example.com/a.mp3",)), VideoOptions(),
     "dreamina-seedance-2-0-mini-260615 needs a reference image or video alongside reference audio."),
    (PRO_FAST, "", VideoMedia(first_frame=IMG_A, last_frame=IMG_B), VideoOptions(),
     "seedance-1-0-pro-fast-251015 does not support a last frame; use a first frame only or pick another model."),
    (TWO_FIVE, "", VideoMedia(first_frame=IMG_A), VideoOptions(ratio="16:9"),
     "dreamina-seedance-2-5-260628 first-frame tasks accept only ratio adaptive, got 16:9."),
    (PRO, "x", VideoMedia(), VideoOptions(ratio="adaptive"),
     "seedance-1-0-pro-250528 cannot use ratio adaptive for text-to-video; pick a fixed ratio."),
    (MINI, "x", VideoMedia(), VideoOptions(service_tier="flex"),
     "dreamina-seedance-2-0-mini-260615 has no flex tier: ModelArk offers flex on Seedance 1.0 only."),
    (MINI, "x", VideoMedia(), VideoOptions(resolution="1080p"),
     "dreamina-seedance-2-0-mini-260615 renders 480p, 720p, not 1080p."),
    (MINI, "x", VideoMedia(), VideoOptions(output_format="mov"),
     "dreamina-seedance-2-0-mini-260615 outputs mp4 only, not mov."),
    (MINI, "x", VideoMedia(), VideoOptions(draft=True, resolution="480p"),
     "dreamina-seedance-2-0-mini-260615 has no draft mode; only Seedance 2.5 makes drafts."),
    (TWO_FIVE, "x", VideoMedia(), VideoOptions(draft=True, resolution="720p"),
     "A draft renders at 480p only, got 720p."),
    (MINI, "x", VideoMedia(), VideoOptions(duration=16),
     "dreamina-seedance-2-0-mini-260615 takes a duration of 4-15 s or -1, got 16."),
    (PRO, "x", VideoMedia(), VideoOptions(ratio="16:9", duration=-1),
     "seedance-1-0-pro-250528 cannot pick its own duration; set 2-12 s."),
    (PRO, "x", VideoMedia(), VideoOptions(ratio="16:9", frames=30),
     "frames must be 25 + 4n within 29-289, got 30."),
    (MINI, "x", VideoMedia(), VideoOptions(frames=29),
     "dreamina-seedance-2-0-mini-260615 takes no frames count; set frames to 0 and use duration."),
    (TWO_FIVE, "add a hat", VideoMedia(reference_videos=("https://example.com/v.mp4",)),
     VideoOptions(omni_reference_task_type="edit", duration=5),
     "A Seedance 2.5 video edit needs duration -1, got 5."),
    (TWO_FIVE, "prompt", VideoMedia(draft_task_id="cgt-1"), VideoOptions(resolution="1080p"),
     "A draft render reuses the draft's prompt; clear the prompt."),
    (TWO_FIVE, "", VideoMedia(draft_task_id="cgt-1"), VideoOptions(resolution="720p"),
     "A draft render needs resolution 1080p or 4k, got 720p."),
    (MINI, "", VideoMedia(first_frame=IMG_A, reference_images=(IMG_B,)), VideoOptions(),
     "First/last frames and reference inputs cannot be mixed in one Seedance request."),
    (MINI, "", VideoMedia(reference_videos=("/tmp/v.mp4",), reference_images=(IMG_A,)), VideoOptions(),
     "Reference video '/tmp/v.mp4' must start with one of https://, http://, asset://"),
    (MINI, "   ", VideoMedia(), VideoOptions(), "Text-to-video needs a prompt."),
    (MINI, "x", VideoMedia(), VideoOptions(camera_fixed=True),
     "dreamina-seedance-2-0-mini-260615 has no camera_fixed; it is on Seedance 1.0 only."),
    (TWO_FIVE, "", VideoMedia(draft_task_id="cgt-1"), VideoOptions(resolution="1080p", camera_fixed=True),
     "dreamina-seedance-2-5-260628 has no camera_fixed; it is on Seedance 1.0 only."),
])
def test_combinations_the_model_rejects_raise_before_any_call(model, prompt, media, options, message):
    with pytest.raises(ValueError) as excinfo:
        build_video_body(model, prompt, media, options)
    assert str(excinfo.value) == message


def test_cost_matches_the_dollar_figures_in_the_docs():
    # model-pricing billing examples, rounded as the docs print them.
    assert round(video_cost_usd("dreamina-seedance-2-0-260128", "480p", 50_220), 2) == 0.35
    assert round(video_cost_usd(TWO_FIVE, "4k", 972_000), 3) == 4.568
    assert round(video_cost_usd(PRO, "1080p", 244_800), 2) == 0.61
    assert round(video_cost_usd(PRO_FAST, "480p", 97_000), 2) == 0.10
    # Console resource pack: 10M Seedance 2.0 mini tokens for $21, priced at the with-video rate.
    assert round(video_cost_usd(MINI, "720p", 10_000_000, has_video_input=True), 2) == 21.00
    # create-video-generation-task-api: flex (offline) costs half of default.
    assert video_cost_usd(PRO, "1080p", 244_800, flex=True) * 2 == pytest.approx(
        video_cost_usd(PRO, "1080p", 244_800))
