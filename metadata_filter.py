# ABOUTME: Monkey-patches SaveImage to add a per-node toggle for metadata stripping.
# ABOUTME: Strips both prompt and extra_pnginfo (workflow JSON) from PNGs when the toggle is enabled.


def make_filtered_save_images(original_fn):
    """Wrap save_images to strip all metadata when strip_metadata is True."""

    def filtered_save_images(self, images, filename_prefix="ComfyUI",
                             prompt=None, extra_pnginfo=None,
                             strip_metadata=True):
        if strip_metadata:
            prompt = None
            extra_pnginfo = None
        return original_fn(self, images, filename_prefix, prompt, extra_pnginfo)

    return filtered_save_images


def make_patched_input_types(original_fn):
    """Wrap INPUT_TYPES to add strip_metadata boolean toggle."""

    @classmethod
    def patched_input_types(s):
        types = original_fn.__func__(s)
        types.setdefault("optional", {})
        types["optional"]["strip_metadata"] = (
            "BOOLEAN",
            {
                "default": True,
                "tooltip": "Strip all metadata (prompt and workflow) from saved PNG files",
            },
        )
        return types

    return patched_input_types


def install():
    """Apply the SaveImage monkey-patches. Call once at import time."""
    try:
        import nodes
        nodes.SaveImage.save_images = make_filtered_save_images(nodes.SaveImage.save_images)
        nodes.SaveImage.INPUT_TYPES = make_patched_input_types(nodes.SaveImage.INPUT_TYPES)
        print("[ERPK] Installed SaveImage metadata toggle")
    except ImportError:
        pass
    except Exception as e:
        print(f"[ERPK] Warning: Could not install SaveImage metadata toggle: {e}")
