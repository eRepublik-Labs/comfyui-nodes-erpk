# ABOUTME: Tests for the HyperFramesSimpleComposer V3 node.
# ABOUTME: Validates schema, HTML generation, GSAP timeline, and runner invocation.

"""
Tests for HyperFramesSimpleComposer.

Validates that:
- The schema exposes the expected inputs with the right defaults.
- Executing requires an images tensor.
- Generated HTML uses the mandatory HyperFrames schema (root div with
  data-composition-id, class="clip" on scenes/captions, GSAP timeline
  registration whose key matches data-composition-id, and a timeline
  extension call so the composition runs for the full duration).
- Captions are emitted only when text is provided.
- An optional audio element is emitted when audio_url is given.
- Format/fps/quality are forwarded to the runner.
- The execute method returns an IO.NodeOutput whose first value is a
  /view URL string.
"""

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


@pytest.fixture
def node_class():
    from hyperframes.simple_composer import HyperFramesSimpleComposer
    return HyperFramesSimpleComposer


@pytest.fixture
def schema(node_class):
    return node_class.define_schema()


def _find_input(schema, input_id: str):
    for inp in schema.inputs:
        if inp.id == input_id:
            return inp
    return None


class _FakeImageTensor:
    """Minimal tensor-like object with the attributes the node relies on.

    Provides .ndim, .shape, slicing, and .detach().cpu().numpy() for the
    PNG encoder — avoids a torch dependency in tests.
    """

    def __init__(self, arr):
        import numpy as np
        self._arr = np.asarray(arr, dtype=np.float32)

    @property
    def ndim(self):
        return self._arr.ndim

    @property
    def shape(self):
        return self._arr.shape

    def __getitem__(self, key):
        return _FakeImageTensor(self._arr[key])

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self._arr

    def clip(self, lo, hi):
        return self._arr.clip(lo, hi)


def _make_image_tensor(n=1, h=4, w=4):
    import numpy as np
    arr = np.zeros((n, h, w, 3), dtype=np.float32)
    return _FakeImageTensor(arr)


class TestSchema:

    def test_inherits_comfy_node(self, node_class):
        assert issubclass(node_class, IO.ComfyNode)

    def test_node_id(self, schema):
        assert schema.node_id == "HyperFramesSimpleComposer"

    def test_display_name(self, schema):
        assert schema.display_name == "HyperFrames Simple Composer"

    def test_category(self, schema):
        assert schema.category == "ERPK/HyperFrames"

    def test_has_images_input(self, schema):
        inp = _find_input(schema, "images")
        assert inp is not None
        assert inp.io_type == "IMAGE"

    def test_has_captions_input(self, schema):
        inp = _find_input(schema, "captions")
        assert inp is not None
        assert inp.io_type == "STRING"

    def test_has_duration_per_scene(self, schema):
        inp = _find_input(schema, "duration_per_scene")
        assert inp is not None
        assert inp.io_type == "INT"
        assert inp.default == 3

    def test_has_stage_dimensions(self, schema):
        width = _find_input(schema, "stage_width")
        height = _find_input(schema, "stage_height")
        assert width is not None and width.io_type == "INT"
        assert height is not None and height.io_type == "INT"
        assert width.default == 1920
        assert height.default == 1080

    def test_has_audio_url(self, schema):
        inp = _find_input(schema, "audio_url")
        assert inp is not None
        assert inp.io_type == "STRING"
        assert inp.optional is True

    def test_has_transition_combo(self, schema):
        inp = _find_input(schema, "transition")
        assert inp is not None
        assert inp.io_type == "COMBO"
        assert inp.default == "fade"
        for t in ("cut", "fade", "crossfade"):
            assert t in inp.options

    def test_has_format_fps_quality(self, schema):
        fmt = _find_input(schema, "output_format")
        fps = _find_input(schema, "fps")
        q = _find_input(schema, "quality")
        assert fmt is not None and fmt.default == "mp4"
        assert fps is not None and fps.default == "30"
        assert q is not None and q.default == "standard"
        for f in ("mp4", "mov", "webm"):
            assert f in fmt.options
        for fpsv in ("24", "30", "60"):
            assert fpsv in fps.options
        for qv in ("draft", "standard", "high"):
            assert qv in q.options

    def test_not_idempotent(self, schema):
        assert schema.not_idempotent is True

    def test_has_string_output(self, schema):
        assert len(schema.outputs) == 1
        assert schema.outputs[0].io_type == "STRING"

    def test_fingerprint_inputs_is_nan(self, node_class):
        import math
        result = node_class.fingerprint_inputs()
        assert isinstance(result, float) and math.isnan(result)


class TestExecuteRequiresImages:
    def test_raises_value_error_without_images(self, node_class):
        with pytest.raises(ValueError):
            node_class.execute(images=None)


class TestExecuteHTMLGeneration:

    def _run_capture(self, node_class, **kwargs):
        """Invoke execute with render_html_to_mp4 mocked so we can inspect the HTML."""
        import pathlib
        captured = {}

        def fake_render(html_content=None, asset_files=None, output_format="mp4",
                         fps=30, quality="standard", timeout_seconds=900):
            captured["html"] = html_content
            captured["assets"] = asset_files or {}
            captured["output_format"] = output_format
            captured["fps"] = fps
            captured["quality"] = quality
            return pathlib.Path("/tmp/erpk_out/hyperframes_fake.mp4")

        from hyperframes import runner as runner_module
        from hyperframes import simple_composer as module
        from unittest.mock import patch

        with patch.object(module, "render_html_to_mp4", side_effect=fake_render, create=True), \
             patch.object(runner_module, "render_html_to_mp4", side_effect=fake_render):
            result = node_class.execute(**kwargs)
        return captured, result

    def test_html_has_root_div_with_composition_id(self, node_class):
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(node_class, images=images)
        html = captured["html"]
        assert 'id="root"' in html
        assert 'data-composition-id="erpk_simple"' in html
        assert 'data-start="0"' in html
        assert 'data-width=' in html
        assert 'data-height=' in html

    def test_one_img_per_scene(self, node_class):
        images = _make_image_tensor(n=3)
        captured, _ = self._run_capture(node_class, images=images)
        html = captured["html"]
        count = html.count('class="clip scene"')
        assert count == 3

    def test_caption_only_when_provided(self, node_class):
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(
            node_class,
            images=images,
            captions="first caption\nsecond caption",
        )
        html = captured["html"]
        assert html.count('class="clip caption"') == 2
        assert "first caption" in html
        assert "second caption" in html

    def test_no_caption_divs_when_blank(self, node_class):
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(node_class, images=images, captions="")
        html = captured["html"]
        assert 'class="clip caption"' not in html

    def test_audio_element_when_url_given(self, node_class):
        images = _make_image_tensor(n=1)
        captured, _ = self._run_capture(
            node_class,
            images=images,
            audio_url="https://example.com/music.mp3",
        )
        html = captured["html"]
        assert "<audio" in html
        assert "https://example.com/music.mp3" in html

    def test_no_audio_element_when_url_blank(self, node_class):
        images = _make_image_tensor(n=1)
        captured, _ = self._run_capture(node_class, images=images, audio_url="")
        html = captured["html"]
        assert "<audio" not in html

    def test_timeline_extension_tl_set(self, node_class):
        images = _make_image_tensor(n=3)
        captured, _ = self._run_capture(
            node_class, images=images, duration_per_scene=4,
        )
        html = captured["html"]
        # 3 scenes * 4s = 12s total
        assert "tl.set({}, {}, 12)" in html

    def test_timeline_registered_under_composition_id(self, node_class):
        images = _make_image_tensor(n=1)
        captured, _ = self._run_capture(node_class, images=images)
        html = captured["html"]
        assert 'window.__timelines["erpk_simple"]' in html

    def test_gsap_cdn_present(self, node_class):
        images = _make_image_tensor(n=1)
        captured, _ = self._run_capture(node_class, images=images)
        html = captured["html"]
        assert "cdn.jsdelivr.net/npm/gsap" in html

    def test_forwards_format_fps_quality_to_runner(self, node_class):
        images = _make_image_tensor(n=1)
        captured, _ = self._run_capture(
            node_class,
            images=images,
            output_format="webm",
            fps="60",
            quality="high",
        )
        assert captured["output_format"] == "webm"
        assert captured["fps"] == 60
        assert captured["quality"] == "high"

    def test_returns_view_url_string(self, node_class):
        images = _make_image_tensor(n=1)
        _, result = self._run_capture(node_class, images=images)
        assert isinstance(result, IO.NodeOutput)
        assert isinstance(result[0], str)
        assert result[0].startswith("/view?")
        assert "type=temp" in result[0]

    def test_scene_image_assets_written(self, node_class):
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(node_class, images=images)
        assets = captured["assets"]
        assert "scene_0.png" in assets
        assert "scene_1.png" in assets
        assert assets["scene_0.png"].startswith(b"\x89PNG")
