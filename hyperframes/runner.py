# ABOUTME: Shared HyperFrames subprocess helpers: preflight, render, asset handling.
# ABOUTME: Abstracts Node/FFmpeg/hyperframes discovery from the node classes.

"""
Shared subprocess and asset helpers for the HyperFrames node family.

Responsibilities:
- preflight_check(): verify Node.js and FFmpeg are available, probe for
  the `hyperframes` npm package, and auto-install it on first use if it
  is missing but Node is present.
- render_html_to_mp4(): write an HTML composition (plus optional asset
  files) to a temp directory, invoke `npx hyperframes render`, and
  return the path of the resulting video in ComfyUI's temp folder.
- temp_view_url(): format a ComfyUI /view URL for a file in the temp dir.
- tensor_to_png_bytes(): encode a ComfyUI IMAGE tensor as PNG bytes for
  use as an asset file.
"""

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional


class HyperFramesError(RuntimeError):
    """Raised when HyperFrames preflight fails or a render errors out."""


def preflight_check() -> None:
    """Verify node, ffmpeg, and hyperframes are available.

    Auto-installs the hyperframes npm package via `npm install -g` if Node.js
    is present but hyperframes is not. Raises HyperFramesError with an
    actionable message on any failure.
    """
    if not shutil.which("node"):
        raise HyperFramesError(
            "HyperFrames requires Node.js >= 22. Install from "
            "https://nodejs.org/ and restart ComfyUI."
        )
    if not shutil.which("ffmpeg"):
        raise HyperFramesError(
            "HyperFrames requires FFmpeg. Install from https://ffmpeg.org/ "
            "and ensure it is on PATH."
        )

    # Probe hyperframes without triggering auto-install
    try:
        result = subprocess.run(
            ["npx", "--no-install", "hyperframes", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Missing hyperframes — auto-install
    print("[HyperFrames] 'hyperframes' npm package not found, installing...")
    install = subprocess.run(
        ["npm", "install", "-g", "hyperframes"],
        capture_output=True, text=True, timeout=300,
    )
    if install.returncode != 0:
        raise HyperFramesError(
            f"Failed to install hyperframes via npm: {install.stderr.strip()}\n"
            f"Try running manually: npm install -g hyperframes"
        )


def render_html_to_mp4(
    html_content: str,
    asset_files: Optional[dict] = None,
    output_format: str = "mp4",
    fps: int = 30,
    quality: str = "standard",
    timeout_seconds: int = 900,
) -> Path:
    """Render an HTML composition to a video file via `npx hyperframes render`.

    Args:
        html_content: Full HyperFrames-compliant HTML for the composition.
        asset_files: Optional dict mapping filename -> bytes. Each entry is
            written alongside index.html so relative paths resolve.
        output_format: 'mp4', 'mov', or 'webm'.
        fps: Frames per second (24, 30, 60 typical).
        quality: 'draft', 'standard', or 'high'.
        timeout_seconds: Max wall-clock time for the render.

    Returns:
        pathlib.Path pointing at the rendered video inside ComfyUI's temp dir.

    Raises:
        HyperFramesError: on preflight failure, subprocess failure, or
            missing output file.
    """
    import folder_paths  # ComfyUI

    preflight_check()

    render_dir = Path(tempfile.mkdtemp(prefix="erpk_hyperframes_"))
    try:
        (render_dir / "index.html").write_text(html_content, encoding="utf-8")
        if asset_files:
            for name, data in asset_files.items():
                (render_dir / name).write_bytes(data)

        output_filename = f"hyperframes_{uuid.uuid4().hex[:12]}.{output_format}"
        temp_dir = Path(folder_paths.get_temp_directory())
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / output_filename

        env = {**os.environ, "HYPERFRAMES_NO_UPDATE_CHECK": "1"}
        result = subprocess.run(
            [
                "npx", "hyperframes", "render",
                "--output", str(output_path),
                "--format", output_format,
                "--fps", str(fps),
                "--quality", quality,
                "--quiet",
            ],
            cwd=str(render_dir),
            capture_output=True, text=True, timeout=timeout_seconds,
            env=env,
        )
        if result.returncode != 0:
            raise HyperFramesError(
                f"hyperframes render failed (exit {result.returncode}):\n"
                f"stderr: {result.stderr.strip()}\n"
                f"stdout: {result.stdout.strip()}"
            )
        if not output_path.exists():
            raise HyperFramesError(
                f"hyperframes reported success but output file is missing: {output_path}"
            )
        return output_path
    finally:
        shutil.rmtree(render_dir, ignore_errors=True)


def temp_view_url(path: Path) -> str:
    """Return the /view URL ComfyUI serves for a file in its temp directory."""
    return f"/view?filename={path.name}&type=temp&subfolder="


def tensor_to_png_bytes(tensor) -> bytes:
    """Encode a ComfyUI IMAGE tensor as PNG bytes.

    Accepts tensors of shape [1, H, W, 3], [N, H, W, 3] (first frame used),
    or [H, W, 3]. Values are expected in the [0, 1] range.
    """
    from PIL import Image
    import io
    import numpy as np

    arr = tensor.detach().cpu().numpy() if hasattr(tensor, "detach") else np.asarray(tensor)
    if arr.ndim == 4:
        arr = arr[0]
    arr = (arr.clip(0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
