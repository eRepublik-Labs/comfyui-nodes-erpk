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

        The HyperFrames nodes (and any future node that returns a ComfyUI-temp-
        served URL) produce this shape: scheme is empty, path is /view, and the
        actual filename with extension lives in the filename= query parameter.
        """
        url = "/view?filename=hyperframes_abc123.mp4&type=temp&subfolder="
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


def _find_input(schema, input_id: str):
    for inp in schema.inputs:
        if inp.id == input_id:
            return inp
    return None
