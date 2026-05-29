# ABOUTME: Verifies /view?filename=&type=&subfolder= bytes are read from disk, not over HTTP.
# ABOUTME: Also guards against path traversal escaping the resolved type directory.

import importlib
import sys
import types

import pytest


def _load(monkeypatch, tmp_path):
    """Import preview_anything with a faked folder_paths pointing at tmp_path."""
    out = tmp_path / "output"; out.mkdir()
    tmp = tmp_path / "temp"; tmp.mkdir()
    inp = tmp_path / "input"; inp.mkdir()
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_output_directory = lambda: str(out)
    fake_fp.get_temp_directory = lambda: str(tmp)
    fake_fp.get_input_directory = lambda: str(inp)
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    mod = importlib.import_module("erpk.utils.preview_anything")
    return mod, {"output": out, "temp": tmp, "input": inp}


def test_view_url_reads_temp_file_from_disk(monkeypatch, tmp_path):
    mod, dirs = _load(monkeypatch, tmp_path)
    (dirs["temp"] / "clean.png").write_bytes(b"PNGDATA")
    data = mod._fetch_url_bytes("/view?filename=clean.png&type=temp&subfolder=")
    assert data == b"PNGDATA"


def test_view_url_honours_subfolder(monkeypatch, tmp_path):
    mod, dirs = _load(monkeypatch, tmp_path)
    sub = dirs["output"] / "batch1"; sub.mkdir()
    (sub / "img.png").write_bytes(b"OUT")
    data = mod._fetch_url_bytes("/view?filename=img.png&type=output&subfolder=batch1")
    assert data == b"OUT"


def test_view_url_rejects_path_traversal(monkeypatch, tmp_path):
    mod, _ = _load(monkeypatch, tmp_path)
    # secret.txt sits one level above the temp dir; ".." would reach it if the
    # containment guard were missing. The file EXISTS, so a None result proves
    # the guard rejected the out-of-bounds path rather than just failing to find it.
    secret = tmp_path / "secret.txt"; secret.write_bytes(b"TOPSECRET")
    data = mod._fetch_url_bytes("/view?filename=secret.txt&type=temp&subfolder=..")
    assert data is None


def test_view_url_unknown_type_returns_none(monkeypatch, tmp_path):
    mod, _ = _load(monkeypatch, tmp_path)
    assert mod._fetch_url_bytes("/view?filename=x.png&type=bogus&subfolder=") is None


def test_view_url_does_not_use_http(monkeypatch, tmp_path):
    """No network call: urllib.request.urlopen must not be invoked for /view paths."""
    mod, dirs = _load(monkeypatch, tmp_path)
    (dirs["temp"] / "f.png").write_bytes(b"X")
    import urllib.request

    def _boom(*a, **k):
        raise AssertionError("urlopen must not be called for /view paths")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    assert mod._fetch_url_bytes("/view?filename=f.png&type=temp&subfolder=") == b"X"
