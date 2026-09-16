# ABOUTME: Tests encoding ComfyUI VIDEO and AUDIO objects into bytes for WaveSpeed uploads.
# ABOUTME: The API takes URLs only, so media has to become real files before a node can cite it.

"""
WaveSpeed's reference fields are `array<string>` of URLs. Images can also travel
as base64 data URIs (verified against minimax/h3/reference-to-video on
2026-09-16), but a 15-second video as a data URI would be tens of megabytes of
JSON, so video and audio go through the v3 media ticket flow instead.

These tests cover the encoding step only: turning a ComfyUI object into
(filename, content_type, bytes). The upload itself is the already-tested
`_upload_bytes_sync`.
"""

import io

import pytest

torch = pytest.importorskip("torch")
av = pytest.importorskip("av")

from wavespeed.wavespeed_api.media import audio_to_bytes, video_to_bytes


class _VideoFromPath:
    """Stands in for a VideoInput whose source is a file on disk."""

    def __init__(self, path):
        self._path = path

    def get_stream_source(self):
        return self._path


class _VideoFromBuffer:
    """Stands in for a VideoInput that can only offer an in-memory stream."""

    def __init__(self, data):
        self._data = data

    def get_stream_source(self):
        return io.BytesIO(self._data)


def _silence(seconds=1, sample_rate=44100, channels=2, batch=1):
    samples = int(seconds * sample_rate)
    return {
        "waveform": torch.zeros(batch, channels, samples),
        "sample_rate": sample_rate,
    }


# --- Video --------------------------------------------------------------------


def test_video_from_a_file_keeps_its_container(tmp_path):
    src = tmp_path / "clip.webm"
    src.write_bytes(b"\x1a\x45\xdf\xa3fake")

    filename, content_type, data = video_to_bytes(_VideoFromPath(str(src)))

    assert data == b"\x1a\x45\xdf\xa3fake"
    assert filename.endswith(".webm")
    assert content_type == "video/webm"


def test_video_from_an_unknown_extension_falls_back_to_mp4(tmp_path):
    src = tmp_path / "clip.bin"
    src.write_bytes(b"data")

    filename, content_type, _ = video_to_bytes(_VideoFromPath(str(src)))

    assert filename.endswith(".mp4")
    assert content_type == "video/mp4"


def test_video_from_a_buffer_is_read_whole_and_named_mp4():
    filename, content_type, data = video_to_bytes(_VideoFromBuffer(b"buffered bytes"))

    assert data == b"buffered bytes"
    assert (filename, content_type) == ("video.mp4", "video/mp4")


def test_video_buffer_is_rewound_before_reading():
    # get_stream_source may hand back a buffer left at EOF by save_to.
    buffer = io.BytesIO(b"payload")
    buffer.seek(len(b"payload"))

    class _AtEof:
        def get_stream_source(self):
            return buffer

    assert video_to_bytes(_AtEof())[2] == b"payload"


def test_empty_video_is_rejected_rather_than_uploaded():
    with pytest.raises(ValueError):
        video_to_bytes(_VideoFromBuffer(b""))


# --- Audio --------------------------------------------------------------------


def test_audio_encodes_to_a_real_mp3():
    filename, content_type, data = audio_to_bytes(_silence())

    assert (filename, content_type) == ("audio.mp3", "audio/mpeg")
    # Decodes as MP3, which a byte-count assertion would not prove. PyAV names
    # the decoder mp3float, so the container format is the stable check.
    with av.open(io.BytesIO(data)) as container:
        assert container.format.name == "mp3"
        assert container.streams.audio[0].codec_context.name.startswith("mp3")


def test_audio_keeps_its_sample_rate():
    data = audio_to_bytes(_silence(sample_rate=22050))[2]

    with av.open(io.BytesIO(data)) as container:
        assert container.streams.audio[0].codec_context.sample_rate == 22050


@pytest.mark.parametrize("channels,expected", [(1, 1), (2, 2)])
def test_audio_channel_layout_follows_the_waveform(channels, expected):
    data = audio_to_bytes(_silence(channels=channels))[2]

    with av.open(io.BytesIO(data)) as container:
        assert container.streams.audio[0].codec_context.channels == expected


def test_only_the_first_item_of_a_batch_is_sent():
    # The API takes one file per reference slot, so a batched AUDIO has to pick.
    one = audio_to_bytes(_silence(batch=1))[2]
    many = audio_to_bytes(_silence(batch=4))[2]

    assert len(many) == len(one)


def test_empty_audio_is_rejected_rather_than_uploaded():
    with pytest.raises(ValueError):
        audio_to_bytes({"waveform": torch.zeros(1, 2, 0), "sample_rate": 44100})


def test_audio_without_a_waveform_is_rejected():
    with pytest.raises(ValueError):
        audio_to_bytes({"sample_rate": 44100})
