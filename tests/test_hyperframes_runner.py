# ABOUTME: Tests for the shared HyperFrames runner module (preflight + subprocess render).
# ABOUTME: Covers node/ffmpeg/hyperframes discovery, auto-install behavior, and render flow.

"""
Tests for hyperframes.runner.

Validates that:
- preflight_check raises HyperFramesError with actionable messages when
  Node.js or FFmpeg are missing.
- preflight_check auto-installs the hyperframes npm package when Node is
  present but the package is not, via `npm install -g hyperframes`.
- render_html_to_mp4 writes HTML + assets to a temp dir, invokes
  `npx hyperframes render` with the correct flags, and returns a path
  inside ComfyUI's temp directory.
- Subprocess failures bubble up as HyperFramesError with stderr content.
- tensor_to_png_bytes round-trips a known tensor back to the same pixels.
"""

import os
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


def _install_folder_paths_stub(tmp_path):
    """Install a minimal folder_paths stub pointing at tmp_path."""
    mod = types.ModuleType("folder_paths")
    temp_dir = str(tmp_path / "comfy_temp")
    os.makedirs(temp_dir, exist_ok=True)
    mod.get_temp_directory = lambda: temp_dir
    sys.modules["folder_paths"] = mod
    return temp_dir


@pytest.fixture(autouse=True)
def _reset_folder_paths():
    yield
    sys.modules.pop("folder_paths", None)


class TestPreflightNodeMissing:
    def test_raises_with_install_url(self):
        from hyperframes.runner import HyperFramesError, preflight_check

        with patch("hyperframes.runner.shutil.which", side_effect=lambda name: None):
            with pytest.raises(HyperFramesError) as exc_info:
                preflight_check()
        assert "Node.js" in str(exc_info.value)
        assert "https://nodejs.org/" in str(exc_info.value)


class TestPreflightFFmpegMissing:
    def test_raises_with_install_url(self):
        from hyperframes.runner import HyperFramesError, preflight_check

        def which(name):
            return "/usr/bin/node" if name == "node" else None

        with patch("hyperframes.runner.shutil.which", side_effect=which):
            with pytest.raises(HyperFramesError) as exc_info:
                preflight_check()
        assert "FFmpeg" in str(exc_info.value)
        assert "https://ffmpeg.org/" in str(exc_info.value)


class TestPreflightAllPresent:
    def test_does_not_raise_when_hyperframes_probe_succeeds(self):
        from hyperframes.runner import preflight_check

        def which(name):
            return f"/usr/bin/{name}"

        probe = subprocess.CompletedProcess(
            args=["npx", "--no-install", "hyperframes", "--version"],
            returncode=0,
            stdout="0.5.0\n",
            stderr="",
        )
        with patch("hyperframes.runner.shutil.which", side_effect=which), \
             patch("hyperframes.runner.subprocess.run", return_value=probe) as run_mock:
            preflight_check()
            args = run_mock.call_args_list[0].args[0]
            assert args[:4] == ["npx", "--no-install", "hyperframes", "--version"]


class TestPreflightAutoInstall:
    def test_installs_hyperframes_when_probe_fails(self):
        from hyperframes.runner import preflight_check

        def which(name):
            return f"/usr/bin/{name}"

        probe = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="not found")
        install = subprocess.CompletedProcess(
            args=["npm", "install", "-g", "hyperframes"],
            returncode=0,
            stdout="added",
            stderr="",
        )
        calls = [probe, install]

        def fake_run(*args, **kwargs):
            return calls.pop(0)

        with patch("hyperframes.runner.shutil.which", side_effect=which), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run) as run_mock:
            preflight_check()

        invocations = [c.args[0] for c in run_mock.call_args_list]
        assert any(
            cmd[:3] == ["npm", "install", "-g"] and cmd[3] == "hyperframes"
            for cmd in invocations
        ), f"npm install -g hyperframes not invoked; got {invocations}"


class TestPreflightInstallFailure:
    def test_raises_when_install_fails(self):
        from hyperframes.runner import HyperFramesError, preflight_check

        def which(name):
            return f"/usr/bin/{name}"

        probe = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="missing")
        install = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="npm ERR! EACCES",
        )
        calls = [probe, install]

        def fake_run(*args, **kwargs):
            return calls.pop(0)

        with patch("hyperframes.runner.shutil.which", side_effect=which), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run):
            with pytest.raises(HyperFramesError) as exc_info:
                preflight_check()
        assert "EACCES" in str(exc_info.value) or "install" in str(exc_info.value).lower()


class TestRenderRunsHyperFramesCLI:
    def test_invokes_expected_flags(self, tmp_path):
        _install_folder_paths_stub(tmp_path)
        from hyperframes.runner import render_html_to_mp4

        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["cwd"] = kwargs.get("cwd")
            captured["env"] = kwargs.get("env")
            # Produce the output file the caller expects
            out_flag_idx = cmd.index("--output")
            output_path = Path(cmd[out_flag_idx + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake-mp4-bytes")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch("hyperframes.runner.preflight_check"), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run):
            path = render_html_to_mp4(
                html_content="<html></html>",
                output_format="mp4",
                fps=30,
                quality="standard",
            )

        cmd = captured["cmd"]
        assert cmd[:3] == ["npx", "hyperframes", "render"]
        assert "--output" in cmd
        assert "--format" in cmd and cmd[cmd.index("--format") + 1] == "mp4"
        assert "--fps" in cmd and cmd[cmd.index("--fps") + 1] == "30"
        assert "--quality" in cmd and cmd[cmd.index("--quality") + 1] == "standard"
        assert "--quiet" in cmd
        assert path.exists()
        # Env contains no-update flag
        assert captured["env"] is not None
        assert captured["env"].get("HYPERFRAMES_NO_UPDATE_CHECK") == "1"


class TestRenderReturnsPathInComfyUITempDir:
    def test_output_inside_temp(self, tmp_path):
        temp_dir = _install_folder_paths_stub(tmp_path)
        from hyperframes.runner import render_html_to_mp4

        def fake_run(cmd, **kwargs):
            out_flag_idx = cmd.index("--output")
            output_path = Path(cmd[out_flag_idx + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"ok")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch("hyperframes.runner.preflight_check"), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run):
            path = render_html_to_mp4(
                html_content="<html></html>",
                output_format="mp4",
            )

        assert str(path).startswith(temp_dir)
        assert path.suffix == ".mp4"


class TestRenderWritesHtmlAndAssets:
    def test_files_written_to_render_dir(self, tmp_path, monkeypatch):
        _install_folder_paths_stub(tmp_path)
        from hyperframes import runner

        # Disable cleanup by monkeypatching shutil.rmtree inside the module
        monkeypatch.setattr(runner.shutil, "rmtree", lambda *a, **kw: None)

        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cwd"] = kwargs.get("cwd")
            out_flag_idx = cmd.index("--output")
            output_path = Path(cmd[out_flag_idx + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"ok")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch("hyperframes.runner.preflight_check"), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run):
            runner.render_html_to_mp4(
                html_content="<html>MARKER</html>",
                asset_files={"scene_0.png": b"PNGBYTES", "music.mp3": b"MP3DATA"},
            )

        render_dir = Path(captured["cwd"])
        assert (render_dir / "index.html").read_text(encoding="utf-8") == "<html>MARKER</html>"
        assert (render_dir / "scene_0.png").read_bytes() == b"PNGBYTES"
        assert (render_dir / "music.mp3").read_bytes() == b"MP3DATA"


class TestRenderRaisesOnSubprocessFailure:
    def test_raises_hyperframes_error_with_stderr(self, tmp_path):
        _install_folder_paths_stub(tmp_path)
        from hyperframes.runner import HyperFramesError, render_html_to_mp4

        failure = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout="rendering...",
            stderr="bad HTML schema",
        )
        with patch("hyperframes.runner.preflight_check"), \
             patch("hyperframes.runner.subprocess.run", return_value=failure):
            with pytest.raises(HyperFramesError) as exc_info:
                render_html_to_mp4(html_content="<html></html>")
        msg = str(exc_info.value)
        assert "bad HTML schema" in msg
        assert "exit 2" in msg or "returncode" in msg.lower() or "2" in msg


class TestRenderRaisesWhenOutputMissing:
    def test_raises_when_cli_reports_success_but_file_absent(self, tmp_path):
        _install_folder_paths_stub(tmp_path)
        from hyperframes.runner import HyperFramesError, render_html_to_mp4

        def fake_run(cmd, **kwargs):
            # Success exit but do NOT create the output file
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch("hyperframes.runner.preflight_check"), \
             patch("hyperframes.runner.subprocess.run", side_effect=fake_run):
            with pytest.raises(HyperFramesError) as exc_info:
                render_html_to_mp4(html_content="<html></html>")
        assert "missing" in str(exc_info.value).lower() or "not" in str(exc_info.value).lower()


class TestTempViewURL:
    def test_format(self):
        from hyperframes.runner import temp_view_url

        path = Path("/tmp/whatever/hyperframes_abc123.mp4")
        url = temp_view_url(path)
        assert url == "/view?filename=hyperframes_abc123.mp4&type=temp&subfolder="


class _FakeImageTensor:
    """Minimal tensor-like object for PNG encoder tests."""

    def __init__(self, arr):
        import numpy as np
        self._arr = np.asarray(arr, dtype=np.float32)

    @property
    def ndim(self):
        return self._arr.ndim

    @property
    def shape(self):
        return self._arr.shape

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class TestTensorToPngBytes:
    def test_round_trip_decodable(self):
        from PIL import Image
        import io
        import numpy as np

        from hyperframes.runner import tensor_to_png_bytes

        # Build an 8x8 gradient tensor in [0,1] with known values
        arr = np.zeros((1, 8, 8, 3), dtype=np.float32)
        for y in range(8):
            for x in range(8):
                arr[0, y, x] = [x / 7.0, y / 7.0, 0.5]
        tensor = _FakeImageTensor(arr)

        png_bytes = tensor_to_png_bytes(tensor)
        assert png_bytes.startswith(b"\x89PNG")

        img = Image.open(io.BytesIO(png_bytes))
        decoded = np.array(img).astype(np.float32) / 255.0
        assert decoded.shape == (8, 8, 3)
        # Corners match original values within quantization tolerance
        assert abs(decoded[0, 0, 0] - 0.0) < 0.01
        assert abs(decoded[0, 7, 0] - 1.0) < 0.01
        assert abs(decoded[7, 0, 1] - 1.0) < 0.01

    def test_numpy_array_direct(self):
        """The helper should also accept a plain numpy array without tensor methods."""
        import numpy as np
        from hyperframes.runner import tensor_to_png_bytes

        arr = np.zeros((4, 4, 3), dtype=np.float32)
        arr[0, 0] = [1.0, 0.0, 0.0]
        png_bytes = tensor_to_png_bytes(arr)
        assert png_bytes.startswith(b"\x89PNG")
