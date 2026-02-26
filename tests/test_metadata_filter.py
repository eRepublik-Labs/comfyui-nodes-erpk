# ABOUTME: Tests for the SaveImage metadata filter monkey-patch.
# ABOUTME: Validates that both prompt and extra_pnginfo are stripped when the per-node toggle is enabled.

"""
Tests for SaveImage metadata stripping.

Validates:
- Wrapper passes through all metadata when toggle is off (default)
- Wrapper strips both prompt and extra_pnginfo when toggle is on
- INPUT_TYPES patch adds the boolean toggle as optional input
"""

import pytest


class TestMetadataFilterWrapper:
    """The filtered save_images wrapper respects the strip_metadata toggle."""

    def _make_wrapper(self):
        """Create a filtered wrapper around a recording mock."""
        calls = []

        def mock_save(self_node, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
            calls.append({"prompt": prompt, "extra_pnginfo": extra_pnginfo})

        from metadata_filter import make_filtered_save_images
        wrapped = make_filtered_save_images(mock_save)
        return wrapped, calls

    def test_passes_through_when_toggle_off(self):
        wrapped, calls = self._make_wrapper()
        workflow = {"workflow": {"nodes": []}}
        prompt_data = {"1": {"class_type": "SaveImage"}}

        wrapped(None, "images", "prefix", prompt=prompt_data,
                extra_pnginfo=workflow, strip_metadata=False)

        assert len(calls) == 1
        assert calls[0]["prompt"] == prompt_data
        assert calls[0]["extra_pnginfo"] == workflow

    def test_strips_all_metadata_when_toggle_on(self):
        wrapped, calls = self._make_wrapper()
        workflow = {"workflow": {"nodes": []}}
        prompt_data = {"1": {"class_type": "SaveImage"}}

        wrapped(None, "images", "prefix", prompt=prompt_data,
                extra_pnginfo=workflow, strip_metadata=True)

        assert len(calls) == 1
        assert calls[0]["prompt"] is None
        assert calls[0]["extra_pnginfo"] is None

    def test_default_is_on(self):
        wrapped, calls = self._make_wrapper()
        workflow = {"workflow": {"nodes": []}}
        prompt_data = {"1": {"class_type": "SaveImage"}}

        wrapped(None, "images", "prefix", prompt=prompt_data, extra_pnginfo=workflow)

        assert calls[0]["prompt"] is None
        assert calls[0]["extra_pnginfo"] is None


class TestInputTypesPatch:
    """The INPUT_TYPES patch adds strip_metadata as optional boolean."""

    def test_adds_optional_toggle(self):
        from metadata_filter import make_patched_input_types

        original_called = []

        @classmethod
        def mock_input_types(s):
            original_called.append(True)
            return {
                "required": {
                    "images": ("IMAGE",),
                    "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
            }

        patched = make_patched_input_types(mock_input_types)
        result = patched.__func__(None)

        assert original_called
        assert "optional" in result
        assert "strip_metadata" in result["optional"]
        toggle_spec = result["optional"]["strip_metadata"]
        assert toggle_spec[0] == "BOOLEAN"
        assert toggle_spec[1]["default"] is True

    def test_preserves_existing_optional(self):
        from metadata_filter import make_patched_input_types

        @classmethod
        def mock_input_types(s):
            return {
                "required": {"images": ("IMAGE",)},
                "optional": {"existing": ("STRING",)},
            }

        patched = make_patched_input_types(mock_input_types)
        result = patched.__func__(None)

        assert "existing" in result["optional"]
        assert "strip_metadata" in result["optional"]
