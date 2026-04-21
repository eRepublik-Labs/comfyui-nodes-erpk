# ABOUTME: Tests for the HyperFramesCustomTemplate V3 node.
# ABOUTME: Validates schema, image placeholder substitution, and runner invocation.

"""
Tests for HyperFramesCustomTemplate.

Validates that:
- The schema exposes html_template (required), optional images input,
  and format/fps/quality combo inputs.
- Executing with an empty template raises ValueError.
- Templates pass through unchanged when no images are provided.
- {{image_N}} placeholders (1-indexed) are substituted with local image
  filenames before being handed to the runner.
- Image assets are written to image_1.png, image_2.png, etc.
- Format/fps/quality are forwarded to the runner.
- The execute method returns an IO.NodeOutput with a /view URL string.
"""

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


@pytest.fixture
def node_class():
    from hyperframes.custom_template import HyperFramesCustomTemplate
    return HyperFramesCustomTemplate


@pytest.fixture
def schema(node_class):
    return node_class.define_schema()


def _find_input(schema, input_id: str):
    for inp in schema.inputs:
        if inp.id == input_id:
            return inp
    return None


class _FakeImageTensor:
    """Minimal tensor-like object with the attributes the node relies on."""

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
        assert schema.node_id == "HyperFramesCustomTemplate"

    def test_display_name(self, schema):
        assert schema.display_name == "HyperFrames Custom Template"

    def test_category(self, schema):
        assert schema.category == "ERPK/HyperFrames"

    def test_has_html_template_input(self, schema):
        inp = _find_input(schema, "html_template")
        assert inp is not None
        assert inp.io_type == "STRING"
        assert inp.multiline is True

    def test_has_images_input_optional(self, schema):
        inp = _find_input(schema, "images")
        assert inp is not None
        assert inp.io_type == "IMAGE"
        assert inp.optional is True

    def test_has_format_fps_quality(self, schema):
        fmt = _find_input(schema, "output_format")
        fps = _find_input(schema, "fps")
        q = _find_input(schema, "quality")
        assert fmt is not None and fmt.default == "mp4"
        assert fps is not None and fps.default == "30"
        assert q is not None and q.default == "standard"

    def test_not_idempotent(self, schema):
        assert schema.not_idempotent is True

    def test_has_string_output(self, schema):
        assert len(schema.outputs) == 1
        assert schema.outputs[0].io_type == "STRING"


class TestExecuteRequiresTemplate:
    def test_raises_value_error_for_empty_template(self, node_class):
        with pytest.raises(ValueError):
            node_class.execute(html_template="")

    def test_raises_value_error_for_whitespace_template(self, node_class):
        with pytest.raises(ValueError):
            node_class.execute(html_template="   \n   ")


class TestExecuteSubstitution:

    def _run_capture(self, node_class, **kwargs):
        import pathlib
        captured = {}

        def fake_render(html_content=None, asset_files=None, output_format="mp4",
                        fps=30, quality="standard", timeout_seconds=900):
            captured["html"] = html_content
            captured["assets"] = asset_files or {}
            captured["output_format"] = output_format
            captured["fps"] = fps
            captured["quality"] = quality
            return pathlib.Path("/tmp/erpk_out/hyperframes_custom.mp4")

        from hyperframes import runner as runner_module
        from hyperframes import custom_template as module
        from unittest.mock import patch

        with patch.object(module, "render_html_to_mp4", side_effect=fake_render, create=True), \
             patch.object(runner_module, "render_html_to_mp4", side_effect=fake_render):
            result = node_class.execute(**kwargs)
        return captured, result

    def test_template_unchanged_without_images(self, node_class):
        template = "<html><body>no images</body></html>"
        captured, _ = self._run_capture(node_class, html_template=template)
        assert captured["html"] == template
        assert captured["assets"] == {}

    def test_placeholders_are_1_indexed(self, node_class):
        template = '<img src="{{image_1}}"><img src="{{image_2}}">'
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(
            node_class, html_template=template, images=images,
        )
        html = captured["html"]
        assert "{{image_1}}" not in html
        assert "{{image_2}}" not in html
        assert "./image_1.png" in html
        assert "./image_2.png" in html

    def test_assets_named_1_indexed(self, node_class):
        template = '<img src="{{image_1}}"><img src="{{image_2}}">'
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(
            node_class, html_template=template, images=images,
        )
        assets = captured["assets"]
        assert "image_1.png" in assets
        assert "image_2.png" in assets
        assert assets["image_1.png"].startswith(b"\x89PNG")

    def test_untouched_placeholder_stays_when_images_missing(self, node_class):
        template = '<img src="{{image_5}}">'
        images = _make_image_tensor(n=2)
        captured, _ = self._run_capture(
            node_class, html_template=template, images=images,
        )
        assert "{{image_5}}" in captured["html"]

    def test_forwards_format_fps_quality(self, node_class):
        template = "<html></html>"
        captured, _ = self._run_capture(
            node_class,
            html_template=template,
            output_format="mov",
            fps="24",
            quality="draft",
        )
        assert captured["output_format"] == "mov"
        assert captured["fps"] == 24
        assert captured["quality"] == "draft"

    def test_returns_view_url_string(self, node_class):
        _, result = self._run_capture(
            node_class,
            html_template="<html></html>",
        )
        assert isinstance(result, IO.NodeOutput)
        assert isinstance(result[0], str)
        assert result[0].startswith("/view?")
        assert "type=temp" in result[0]
