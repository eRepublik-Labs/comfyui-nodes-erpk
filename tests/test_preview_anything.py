# ABOUTME: Tests for the V3 PreviewAnything utility node.
# ABOUTME: Validates schema shape, content-type detection, and UI payload format.

"""
Tests for PreviewAnything.

The node should accept any input type and return a UI payload the frontend
can render (image / video / audio / gif / text / markdown). Server-side
content-type detection runs on strings via URL extension; binary tensors
and AUDIO dicts are saved to temp and served via ComfyUI's /view endpoint.
"""

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


@pytest.fixture
def node_class():
    from utils.preview_anything import PreviewAnything
    return PreviewAnything


@pytest.fixture
def schema(node_class):
    return node_class.define_schema()


class TestPreviewAnythingSchema:

    def test_inherits_comfy_node(self, node_class):
        assert issubclass(node_class, IO.ComfyNode)

    def test_node_id(self, schema):
        assert schema.node_id == "ERPK_PreviewAnything"

    def test_display_name(self, schema):
        assert schema.display_name == "Preview Anything"

    def test_category(self, schema):
        assert schema.category == "ERPK/utils"

    def test_is_output_node(self, schema):
        assert schema.is_output_node is True

    def test_has_value_input(self, schema):
        value_input = _find_input(schema, "value")
        assert value_input is not None
        assert value_input.io_type == "*"

    def test_has_display_type_combo(self, schema):
        dt = _find_input(schema, "display_type")
        assert dt is not None
        assert dt.io_type == "COMBO"
        assert dt.default == "auto"
        assert "auto" in dt.options
        for kind in ("text", "markdown", "image", "video", "audio", "gif"):
            assert kind in dt.options

    def test_display_type_is_optional(self, schema):
        dt = _find_input(schema, "display_type")
        assert dt.optional is True

    def test_has_filename_input(self, schema):
        fn = _find_input(schema, "filename")
        assert fn is not None
        assert fn.io_type == "STRING"
        assert fn.optional is True

    def test_has_strip_metadata_input(self, schema):
        sm = _find_input(schema, "strip_metadata")
        assert sm is not None
        assert sm.io_type == "BOOLEAN"
        assert sm.optional is True
        assert sm.default is False

    def test_no_outputs(self, schema):
        assert len(schema.outputs) == 0


class TestContentTypeDetection:
    """Detection logic for strings: URL vs plain text, extension -> kind."""

    def test_string_without_url_is_text(self, node_class):
        result = node_class.execute(value="hello world", display_type="auto")
        assert result.ui["preview_anything"][0]["kind"] == "text"
        assert result.ui["preview_anything"][0]["text"] == "hello world"

    def test_markdown_content_detected_as_markdown(self, node_class):
        result = node_class.execute(
            value="# Heading\n\n**bold** text",
            display_type="auto",
        )
        assert result.ui["preview_anything"][0]["kind"] == "markdown"

    def test_image_url_by_extension(self, node_class):
        for ext in ("png", "jpg", "jpeg", "webp"):
            url = f"https://example.com/test.{ext}"
            result = node_class.execute(value=url, display_type="auto")
            payload = result.ui["preview_anything"][0]
            assert payload["kind"] == "image", f"{ext} should map to image"
            assert payload["url"] == url

    def test_gif_url_is_gif(self, node_class):
        result = node_class.execute(
            value="https://example.com/thing.gif",
            display_type="auto",
        )
        assert result.ui["preview_anything"][0]["kind"] == "gif"

    def test_video_url_by_extension(self, node_class):
        for ext in ("mp4", "webm", "mov"):
            url = f"https://example.com/v.{ext}"
            result = node_class.execute(value=url, display_type="auto")
            assert result.ui["preview_anything"][0]["kind"] == "video"

    def test_audio_url_by_extension(self, node_class):
        for ext in ("mp3", "wav", "ogg", "flac"):
            url = f"https://example.com/a.{ext}"
            result = node_class.execute(value=url, display_type="auto")
            assert result.ui["preview_anything"][0]["kind"] == "audio"

    def test_unknown_url_falls_back_to_text(self, node_class):
        """Unknown file extension on a URL — show the URL as text so user sees it."""
        result = node_class.execute(
            value="https://example.com/thing.xyz",
            display_type="auto",
        )
        kind = result.ui["preview_anything"][0]["kind"]
        assert kind in ("text", "markdown")

    def test_relative_view_url_with_video_filename_is_video(self, node_class):
        """ComfyUI /view?filename=X.mp4 URLs should auto-detect as video.

        Any node that returns a ComfyUI-temp-served URL produces this shape:
        scheme is empty, path is /view, and the actual filename with extension
        lives in the filename= query parameter.
        """
        url = "/view?filename=rendered_abc123.mp4&type=temp&subfolder="
        result = node_class.execute(value=url, display_type="auto")
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "video"
        assert payload["url"] == url

    def test_relative_view_url_with_image_filename_is_image(self, node_class):
        url = "/view?filename=preview_999.png&type=temp&subfolder="
        result = node_class.execute(value=url, display_type="auto")
        assert result.ui["preview_anything"][0]["kind"] == "image"

    def test_relative_view_url_with_audio_filename_is_audio(self, node_class):
        url = "/view?filename=preview_xyz.wav&type=temp&subfolder="
        result = node_class.execute(value=url, display_type="auto")
        assert result.ui["preview_anything"][0]["kind"] == "audio"

    def test_absolute_url_query_filename_also_detected(self, node_class):
        """The query-filename fallback should work on absolute URLs too,
        not just relative ones — in case a remote server uses the same pattern."""
        url = "https://example.com/view?filename=clip.webm"
        result = node_class.execute(value=url, display_type="auto")
        assert result.ui["preview_anything"][0]["kind"] == "video"

    def test_path_extension_wins_over_query_filename(self, node_class):
        """If path has a recognized extension, it takes priority over query filename."""
        url = "https://example.com/clip.mp4?filename=tracking.txt"
        result = node_class.execute(value=url, display_type="auto")
        # Path says .mp4 (video) — should win
        assert result.ui["preview_anything"][0]["kind"] == "video"

    def test_display_type_override(self, node_class):
        """Explicit display_type wins over auto-detection."""
        result = node_class.execute(
            value="https://example.com/real.png",
            display_type="text",
        )
        assert result.ui["preview_anything"][0]["kind"] == "text"


class TestExecuteReturns:

    def test_returns_node_output(self, node_class):
        result = node_class.execute(value="anything")
        assert isinstance(result, IO.NodeOutput)

    def test_ui_payload_is_list(self, node_class):
        result = node_class.execute(value="x")
        assert isinstance(result.ui["preview_anything"], list)
        assert len(result.ui["preview_anything"]) == 1

    def test_payload_includes_filename(self, node_class):
        result = node_class.execute(value="x", filename="myfile")
        payload = result.ui["preview_anything"][0]
        assert payload["filename"] == "myfile"

    def test_non_string_non_tensor_is_stringified(self, node_class):
        result = node_class.execute(value={"some": "dict"})
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "text"
        assert "some" in payload["text"]


class TestImageGalleryBatch:
    """Batched IMAGE tensors (N > 1) produce an image_gallery payload."""

    def _make_batched_tensor(self, n, h=4, w=4):
        import torch
        return torch.zeros((n, h, w, 3), dtype=torch.float32)

    def _install_folder_paths_stub(self, tmp_path):
        import os as _os, sys, types
        mod = types.ModuleType("folder_paths")
        temp_dir = str(tmp_path / "comfy_temp")
        _os.makedirs(temp_dir, exist_ok=True)
        mod.get_temp_directory = lambda: temp_dir
        sys.modules["folder_paths"] = mod
        return temp_dir

    def test_batched_tensor_produces_image_gallery_kind(self, node_class, tmp_path):
        try:
            import torch  # noqa: F401
        except ImportError:
            import pytest
            pytest.skip("torch not installed in test env")

        self._install_folder_paths_stub(tmp_path)
        tensor = self._make_batched_tensor(n=3)
        result = node_class.execute(value=tensor, display_type="auto")
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "image_gallery"
        assert isinstance(payload["urls"], list)
        assert len(payload["urls"]) == 3

        import sys
        sys.modules.pop("folder_paths", None)

    def test_batched_tensor_urls_are_distinct(self, node_class, tmp_path):
        try:
            import torch  # noqa: F401
        except ImportError:
            import pytest
            pytest.skip("torch not installed in test env")

        self._install_folder_paths_stub(tmp_path)
        tensor = self._make_batched_tensor(n=4)
        result = node_class.execute(value=tensor, display_type="auto")
        payload = result.ui["preview_anything"][0]
        assert len(set(payload["urls"])) == 4, "each gallery entry must have a distinct URL"

        import sys
        sys.modules.pop("folder_paths", None)

    def test_single_image_tensor_still_uses_image_kind(self, node_class, tmp_path):
        """Backwards compat: N=1 batched tensor (or 3D) uses singular image kind."""
        try:
            import torch
        except ImportError:
            import pytest
            pytest.skip("torch not installed in test env")

        self._install_folder_paths_stub(tmp_path)
        tensor = torch.zeros((1, 4, 4, 3), dtype=torch.float32)
        result = node_class.execute(value=tensor, display_type="auto")
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "image"
        assert "url" in payload
        assert "urls" not in payload

        import sys
        sys.modules.pop("folder_paths", None)


class TestStripMetadata:
    """strip_metadata re-encodes image URLs to drop EXIF / ICC / XMP."""

    def test_default_off_passes_url_through(self, node_class):
        url = "https://example.com/photo.jpg"
        result = node_class.execute(value=url, display_type="auto", strip_metadata=False)
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "image"
        assert payload["url"] == url

    def test_off_by_default_when_not_specified(self, node_class):
        url = "https://example.com/photo.jpg"
        result = node_class.execute(value=url, display_type="auto")
        payload = result.ui["preview_anything"][0]
        assert payload["url"] == url

    def test_ignored_for_non_image_urls(self, node_class):
        """Video / audio / text URLs must pass through untouched regardless."""
        video = "https://example.com/clip.mp4"
        result = node_class.execute(value=video, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "video"
        assert payload["url"] == video

        audio = "https://example.com/music.mp3"
        result = node_class.execute(value=audio, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "audio"
        assert payload["url"] == audio

    def test_on_image_url_rewrites_to_view_url(self, node_class, monkeypatch, tmp_path):
        """Image URL + strip_metadata=True should rewrite to /view? URL
        serving a re-encoded copy from ComfyUI's temp dir."""
        from PIL import Image
        import io
        import sys
        import types

        # Stub folder_paths to point at tmp_path
        folder_paths = types.ModuleType("folder_paths")
        temp_dir = tmp_path / "comfy_temp"
        folder_paths.get_temp_directory = lambda: str(temp_dir)
        sys.modules["folder_paths"] = folder_paths

        # Build a PNG with a known-good EXIF hint in memory (tiny placeholder)
        original = Image.new("RGB", (8, 8), color=(128, 64, 255))
        buf = io.BytesIO()
        original.save(buf, format="PNG")
        fake_bytes = buf.getvalue()

        import utils.preview_anything as mod
        monkeypatch.setattr(mod, "_fetch_url_bytes", lambda url, timeout_seconds=30: fake_bytes)

        url = "https://example.com/original.png"
        result = node_class.execute(value=url, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "image"
        assert payload["url"].startswith("/view?"), f"Expected /view? URL, got {payload['url']!r}"
        assert "_stripped_" in payload["url"]

        sys.modules.pop("folder_paths", None)

    def test_on_image_url_produces_clean_pixel_match(self, node_class, monkeypatch, tmp_path):
        """Verify the re-encoded image has no EXIF — PIL should report no exif."""
        from PIL import Image
        import io
        import sys
        import types
        import os
        from urllib.parse import urlparse, parse_qs

        folder_paths = types.ModuleType("folder_paths")
        temp_dir = tmp_path / "comfy_temp"
        folder_paths.get_temp_directory = lambda: str(temp_dir)
        sys.modules["folder_paths"] = folder_paths

        # Build a JPEG with EXIF payload
        original = Image.new("RGB", (16, 16), color=(200, 100, 50))
        # PIL does not easily synthesize EXIF without piexif; instead we'll
        # confirm the re-encoded output has no exif metadata attribute.
        buf = io.BytesIO()
        original.save(buf, format="JPEG", quality=90)
        fake_bytes = buf.getvalue()

        import utils.preview_anything as mod
        monkeypatch.setattr(mod, "_fetch_url_bytes", lambda url, timeout_seconds=30: fake_bytes)

        url = "https://example.com/photo.jpg"
        result = node_class.execute(value=url, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]

        # Locate the written file on disk and verify it's clean
        params = parse_qs(urlparse(payload["url"]).query)
        filename_on_disk = params["filename"][0]
        written_path = os.path.join(str(temp_dir), filename_on_disk)
        assert os.path.exists(written_path), f"Re-encoded file missing at {written_path}"

        reloaded = Image.open(written_path)
        reloaded.load()
        # A freshly-pasted image should carry no EXIF dict
        exif_bytes = reloaded.info.get("exif", b"")
        assert exif_bytes in (b"", None), (
            f"Expected no EXIF after strip, got {len(exif_bytes)} bytes"
        )
        # ICC profile should also be absent
        assert reloaded.info.get("icc_profile") in (None, b""), \
            "ICC profile leaked through the metadata strip"

        sys.modules.pop("folder_paths", None)

    def test_fetch_failure_falls_back_to_original_url(self, node_class, monkeypatch):
        """If fetch fails, the payload passes through the original URL so the
        preview still works — we don't break the node over a strip failure."""
        import utils.preview_anything as mod
        monkeypatch.setattr(mod, "_fetch_url_bytes", lambda url, timeout_seconds=30: None)

        url = "https://example.com/unreachable.png"
        result = node_class.execute(value=url, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]
        assert payload["url"] == url, "Original URL must survive strip failure"

    def test_gif_url_also_stripped(self, node_class, monkeypatch, tmp_path):
        """GIFs are grouped with images for metadata-stripping purposes."""
        from PIL import Image
        import io
        import sys
        import types

        folder_paths = types.ModuleType("folder_paths")
        temp_dir = tmp_path / "comfy_temp"
        folder_paths.get_temp_directory = lambda: str(temp_dir)
        sys.modules["folder_paths"] = folder_paths

        original = Image.new("RGB", (4, 4), color=(50, 200, 50))
        buf = io.BytesIO()
        original.save(buf, format="GIF")
        fake_bytes = buf.getvalue()

        import utils.preview_anything as mod
        monkeypatch.setattr(mod, "_fetch_url_bytes", lambda url, timeout_seconds=30: fake_bytes)

        url = "https://example.com/animated.gif"
        result = node_class.execute(value=url, display_type="auto", strip_metadata=True)
        payload = result.ui["preview_anything"][0]
        assert payload["kind"] == "gif"
        assert payload["url"].startswith("/view?")

        sys.modules.pop("folder_paths", None)


class TestSaveAudioFallback:
    """torchaudio 2.x delegates `save` to torchcodec. If torchcodec is missing
    (common in many ComfyUI environments), save raises ImportError mid-call.
    The audio path must fall back to a stdlib WAV writer instead of propagating."""

    def test_writes_wav_when_torchaudio_save_raises_importerror(self, tmp_path, monkeypatch):
        torch = pytest.importorskip("torch")

        import sys
        import types
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_temp_directory = lambda: str(tmp_path)
        sys.modules["folder_paths"] = folder_paths

        torchaudio_stub = types.ModuleType("torchaudio")
        def raise_missing_codec(*args, **kwargs):
            raise ImportError(
                "TorchCodec is required for save_with_torchcodec. "
                "Please install torchcodec to use this function."
            )
        torchaudio_stub.save = raise_missing_codec
        monkeypatch.setitem(sys.modules, "torchaudio", torchaudio_stub)

        import utils.preview_anything as mod
        sample_rate = 16000
        waveform = torch.zeros(1, 1, sample_rate)  # 1s of silence, 1 channel, [B, C, T] like ComfyUI emits
        url = mod._save_audio_dict({"waveform": waveform, "sample_rate": sample_rate}, "test")

        assert url is not None
        assert url.startswith("/view?")
        wav_files = list(tmp_path.glob("*.wav"))
        assert len(wav_files) == 1
        # Smoke-check the WAV header
        with open(wav_files[0], "rb") as fh:
            header = fh.read(12)
        assert header[:4] == b"RIFF"
        assert header[8:12] == b"WAVE"

        sys.modules.pop("folder_paths", None)


def _find_input(schema, input_id: str):
    for inp in schema.inputs:
        if inp.id == input_id:
            return inp
    return None
