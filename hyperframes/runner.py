# ABOUTME: Shared HyperFrames subprocess helpers: preflight, render, asset handling.
# ABOUTME: Abstracts Node/FFmpeg/hyperframes discovery from the node classes.

"""
Shared subprocess and asset helpers for the HyperFrames node family.

Responsibilities:
- preflight_check(): verify Node.js (with bundled npx) and FFmpeg are
  available. Uses `npx --yes` for hyperframes resolution, which installs
  the package into the per-user npx cache on first use without requiring
  `npm` to be on the subprocess PATH (common issue with NVM-managed
  Node installations where npm is only PATH-visible from shell rc files).
- render_html_to_mp4(): write an HTML composition (plus optional asset
  files) to a temp directory, invoke `npx --yes hyperframes render`, and
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
    """Verify node, npx, and ffmpeg are available.

    Uses npx's own pacote-based resolution (via `--yes`) to fetch the
    `hyperframes` package on first use, so the `npm` binary does not need
    to be separately on the subprocess PATH. Raises HyperFramesError with
    an actionable message on any failure.
    """
    if not shutil.which("node"):
        raise HyperFramesError(
            "HyperFrames requires Node.js >= 22. Install from "
            "https://nodejs.org/ and restart ComfyUI."
        )
    if not shutil.which("npx"):
        raise HyperFramesError(
            "HyperFrames requires npx (bundled with Node.js). Ensure your "
            "Node installation includes npx and that it is on PATH for the "
            "ComfyUI process. If you use NVM, the shell rc PATH additions "
            "do not propagate to subprocess invocations — symlink node and "
            "npx into /usr/local/bin or start ComfyUI from a shell where "
            "NVM has been sourced."
        )
    if not shutil.which("ffmpeg"):
        raise HyperFramesError(
            "HyperFrames requires FFmpeg. Install from https://ffmpeg.org/ "
            "and ensure it is on PATH."
        )

    # Resolve hyperframes via npx (auto-installs into user npx cache on first use).
    # First run may take up to ~2 minutes while the package downloads.
    try:
        result = subprocess.run(
            ["npx", "--yes", "hyperframes", "--version"],
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        raise HyperFramesError(
            "Timed out waiting for npx to resolve hyperframes. The first "
            "render can take up to 2 minutes while the package downloads. "
            "Retry, or pre-install manually: `npx --yes hyperframes --version`."
        )
    except FileNotFoundError as e:
        raise HyperFramesError(
            f"npx subprocess failed: {e}. Verify 'node' and 'npx' are on "
            f"the ComfyUI process PATH (not just your shell PATH)."
        )
    if result.returncode != 0:
        raise HyperFramesError(
            f"Failed to resolve hyperframes via npx:\n"
            f"stderr: {result.stderr.strip()}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"If your network restricts npm registry access, install "
            f"hyperframes manually: `npm install -g hyperframes`."
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
                "npx", "--yes", "hyperframes", "render",
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
