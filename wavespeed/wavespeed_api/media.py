# ABOUTME: Turns ComfyUI VIDEO and AUDIO objects into uploadable (filename, content type, bytes).
# ABOUTME: WaveSpeed reference fields take URLs, so media must become a real file before a node cites it.

import io
import os

# Containers WaveSpeed accepts, mapped from the extension a VideoInput reports.
# Anything else is relabelled mp4, which is what an in-memory VideoInput writes.
_VIDEO_CONTENT_TYPES = {
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "mkv": "video/x-matroska",
    "avi": "video/x-msvideo",
    "m4v": "video/x-m4v",
}

_DEFAULT_VIDEO_EXTENSION = "mp4"

# MP3 over FLAC: reference audio is a guide track, not a master, and every
# service accepts it. 192k is transparent enough for that job at a third of
# FLAC's size, which matters because the bytes cross the wire twice.
_AUDIO_BIT_RATE = 192_000


def video_to_bytes(video):
    """Return (filename, content_type, data) for a ComfyUI VIDEO input.

    Reads the video's own stream source rather than re-encoding it, so a clip
    that arrived as MP4 is uploaded as the same MP4. Re-encoding would cost a
    generation's worth of time and lose quality for no gain.

    Args:
        video: A VideoInput, or anything exposing get_stream_source()

    Returns:
        tuple: (filename, content_type, data)

    Raises:
        ValueError: If the video yields no bytes
    """
    source = video.get_stream_source()

    if isinstance(source, str):
        extension = os.path.splitext(source)[1].lstrip(".").lower()
        with open(source, "rb") as handle:
            data = handle.read()
    else:
        extension = ""
        source.seek(0)
        data = source.read()

    if extension not in _VIDEO_CONTENT_TYPES:
        extension = _DEFAULT_VIDEO_EXTENSION

    if not data:
        raise ValueError("The connected video is empty, so there is nothing to upload")

    return f"video.{extension}", _VIDEO_CONTENT_TYPES[extension], data


def audio_to_bytes(audio):
    """Return (filename, content_type, data) for a ComfyUI AUDIO input.

    ComfyUI carries audio as a waveform tensor plus a sample rate, which no API
    accepts directly, so it is encoded to MP3 at the waveform's own sample rate.
    A batched waveform contributes its first item only: each reference slot on
    the WaveSpeed side holds one file.

    Args:
        audio: dict with "waveform" (B, C, S) and "sample_rate"

    Returns:
        tuple: (filename, content_type, data)

    Raises:
        ValueError: If the waveform is missing or empty
    """
    import av

    waveform = audio.get("waveform") if isinstance(audio, dict) else None
    if waveform is None:
        raise ValueError("The connected audio has no waveform")

    sample_rate = audio.get("sample_rate")
    if not sample_rate:
        raise ValueError("The connected audio has no sample rate")

    waveform = waveform.cpu()
    if waveform.ndim == 3:
        waveform = waveform[0]
    if waveform.numel() == 0:
        raise ValueError("The connected audio is empty, so there is nothing to upload")

    layout = "mono" if waveform.shape[0] == 1 else "stereo"

    buffer = io.BytesIO()
    container = av.open(buffer, mode="w", format="mp3")
    try:
        stream = container.add_stream("libmp3lame", rate=sample_rate, layout=layout)
        stream.bit_rate = _AUDIO_BIT_RATE

        frame = av.AudioFrame.from_ndarray(
            waveform.movedim(0, 1).reshape(1, -1).float().numpy(),
            format="flt",
            layout=layout,
        )
        frame.sample_rate = sample_rate
        frame.pts = 0

        container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    finally:
        container.close()

    return "audio.mp3", "audio/mpeg", buffer.getvalue()
