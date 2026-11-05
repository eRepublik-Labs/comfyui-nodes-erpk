# ABOUTME: Tests for the optional parallel prompt-worker patch.
# ABOUTME: Covers clamp logic, idempotence, and no-op behavior outside ComfyUI runtime.

import os
import sys
import threading
import types

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

from erpk.parallel_workers import _clamp_worker_count, cache_config, install, _DEFAULT_WORKERS, _MAX_WORKERS


class TestClampWorkerCount:
    """Setting values get coerced + clamped to a safe range."""

    def test_below_one_clamps_to_one(self):
        assert _clamp_worker_count(0) == 1
        assert _clamp_worker_count(-5) == 1

    def test_above_max_clamps_to_max(self):
        assert _clamp_worker_count(_MAX_WORKERS + 1) == _MAX_WORKERS
        assert _clamp_worker_count(9999) == _MAX_WORKERS

    def test_inside_range_passes_through(self):
        assert _clamp_worker_count(1) == 1
        assert _clamp_worker_count(2) == 2
        assert _clamp_worker_count(_MAX_WORKERS) == _MAX_WORKERS

    def test_string_input_coerced(self):
        assert _clamp_worker_count("3") == 3

    def test_garbage_input_returns_default(self):
        assert _clamp_worker_count(None) == _DEFAULT_WORKERS
        assert _clamp_worker_count("abc") == _DEFAULT_WORKERS
        assert _clamp_worker_count([]) == _DEFAULT_WORKERS


class _FakeQueue:
    """Stand-in for ComfyUI's PromptQueue. Exposes the sentinel surface."""
    pass


class _FakeServer:
    instance = None
    def __init__(self):
        self.prompt_queue = _FakeQueue()


def _install_fake_comfy(monkeypatch, n_workers):
    """Make `from server import PromptServer` resolve to our fake."""
    fake_server_module = types.ModuleType("server")
    fake_server_module.PromptServer = _FakeServer
    _FakeServer.instance = _FakeServer()
    monkeypatch.setitem(sys.modules, "server", fake_server_module)

    monkeypatch.setattr(
        "erpk.parallel_workers.get_comfy_setting",
        lambda key, default=None: n_workers if key == "ERPK.PARALLEL_WORKERS" else default,
    )

    spawned = []
    real_thread = threading.Thread

    def fake_thread(*args, **kwargs):
        spawned.append((args, kwargs))
        # Return a stub thread that doesn't actually start the loop.
        class _StubThread:
            def start(self_inner):
                pass
        return _StubThread()

    monkeypatch.setattr("erpk.parallel_workers.threading.Thread", fake_thread)
    return spawned


class TestInstall:
    """install() spawns the right number of extra threads with the right idempotence."""

    def test_n_equals_one_spawns_zero_extras(self, monkeypatch):
        spawned = _install_fake_comfy(monkeypatch, 1)
        install()
        assert len(spawned) == 0

    def test_n_equals_two_spawns_one_extra(self, monkeypatch):
        spawned = _install_fake_comfy(monkeypatch, 2)
        install()
        # Total workers = 2 (ComfyUI already has 1, we add 1)
        assert len(spawned) == 1

    def test_n_equals_four_spawns_three_extras(self, monkeypatch):
        spawned = _install_fake_comfy(monkeypatch, 4)
        install()
        assert len(spawned) == 3

    def test_install_is_idempotent(self, monkeypatch):
        spawned = _install_fake_comfy(monkeypatch, 3)
        install()
        install()
        install()
        # Three calls, but only the first should spawn threads.
        assert len(spawned) == 2  # 3 workers total → 2 extras spawned on first call only

    def test_no_server_module_is_silent(self, monkeypatch):
        # If `server` isn't importable, install() should no-op without raising.
        monkeypatch.setitem(sys.modules, "server", None)
        monkeypatch.setattr(
            "erpk.parallel_workers.get_comfy_setting",
            lambda key, default=None: 2,
        )
        # Should not raise.
        install()


class _Args:
    def __init__(self, cache_ram=(), cache_lru=0, cache_classic=False, cache_none=False):
        self.cache_ram = list(cache_ram)
        self.cache_lru = cache_lru
        self.cache_classic = cache_classic
        self.cache_none = cache_none


class _CacheTypes:
    CLASSIC, LRU, RAM_PRESSURE, NONE = "classic", "lru", "ram_pressure", "none"


RAM_64GB_MB = 64 * 1024


def test_cache_config_defaults_to_ram_pressure_with_derived_headroom():
    cache_type, cache_args = cache_config(_Args(), _CacheTypes, RAM_64GB_MB)
    assert cache_type == "ram_pressure"
    assert cache_args == {"lru": 0, "ram": 6.4, "ram_inactive": 64.0}


def test_cache_config_reads_active_and_inactive_gb_from_cache_ram_list():
    _, cache_args = cache_config(_Args(cache_ram=[3.0]), _CacheTypes, RAM_64GB_MB)
    assert cache_args == {"lru": 0, "ram": 3.0, "ram_inactive": 64.0}
    _, cache_args = cache_config(_Args(cache_ram=[3.0, 20.0]), _CacheTypes, RAM_64GB_MB)
    assert cache_args == {"lru": 0, "ram": 3.0, "ram_inactive": 20.0}


def test_cache_config_classic_lru_and_none_override_ram_pressure():
    assert cache_config(_Args(cache_classic=True), _CacheTypes, RAM_64GB_MB) == (
        "classic", {"lru": 0, "ram": 0, "ram_inactive": 0})
    assert cache_config(_Args(cache_lru=5), _CacheTypes, RAM_64GB_MB) == (
        "lru", {"lru": 5, "ram": 0, "ram_inactive": 0})
    assert cache_config(_Args(cache_none=True), _CacheTypes, RAM_64GB_MB) == (
        "none", {"lru": 0, "ram": 0, "ram_inactive": 0})
