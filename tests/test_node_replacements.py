# ABOUTME: Tests for V1→V3 NodeReplace mappings registered in ERPKExtension.on_load().
# ABOUTME: Verifies that all 15 renamed nodes have correct replacement mappings.

import asyncio
import pytest

from tests.comfy_api_stub import ComfyAPI


# Complete mapping of all V1 node IDs that changed during V3 migration.
EXPECTED_REPLACEMENTS = {
    # WaveSpeed (15 nodes)
    "WaveSpeed Custom Client": "WaveSpeedAIAPIClient",
    "WaveSpeed Custom Preview Video": "PreviewVideo",
    "WaveSpeed Custom Save Audio": "SaveAudio",
    "WaveSpeed Custom Upload Image": "UploadImage",
    "WaveSpeed Custom SeedreamV4": "SeedreamV4Node",
    "WaveSpeed Custom SeedreamV4Edit": "SeedreamV4EditNode",
    "WaveSpeed Custom SeedreamV4Sequential": "SeedreamV4SequentialNode",
    "WaveSpeed Custom SeedreamV4EditSequential": "SeedreamV4EditSequentialNode",
    "WaveSpeed Custom SeedreamV4_5": "SeedreamV4_5Node",
    "WaveSpeed Custom SeedreamV4_5Edit": "SeedreamV4_5EditNode",
    "WaveSpeed Custom SeedreamV4_5Sequential": "SeedreamV4_5SequentialNode",
    "WaveSpeed Custom SeedreamV4_5EditSequential": "SeedreamV4_5EditSequentialNode",
    "WaveSpeed Custom QwenImageT2I": "QwenImageTextToImageNode",
    "WaveSpeed Custom QwenImageEdit": "QwenImageEditNode",
    "WaveSpeed Custom QwenImageEditPlus": "QwenImageEditPlusNode",
}


@pytest.fixture(autouse=True)
def reset_api():
    """Reset ComfyAPI singleton state between tests."""
    ComfyAPI._reset()
    yield
    ComfyAPI._reset()


def _run_on_load():
    """Import ERPKExtension and run on_load(), returning registered replacements."""
    from __init__ import ERPKExtension
    ext = ERPKExtension()
    asyncio.run(ext.on_load())
    return ComfyAPI().node_replacement.get_registered()


class TestNodeReplacements:
    """Tests for V1→V3 node replacement mappings."""

    def test_on_load_registers_replacements(self):
        """on_load() should register at least one replacement."""
        registered = _run_on_load()
        assert len(registered) > 0, "on_load() should register node replacements"

    def test_replacement_count(self):
        """Exactly 15 replacements should be registered."""
        registered = _run_on_load()
        assert len(registered) == 15, (
            f"Expected 15 replacements, got {len(registered)}"
        )

    def test_all_expected_old_ids_present(self):
        """Every expected V1 node ID should have a replacement registered."""
        registered = _run_on_load()
        registered_old_ids = {r.old_node_id for r in registered}
        for old_id in EXPECTED_REPLACEMENTS:
            assert old_id in registered_old_ids, (
                f"Missing replacement for V1 node: {old_id}"
            )

    def test_all_mappings_correct(self):
        """Each replacement should map old_node_id → new_node_id correctly."""
        registered = _run_on_load()
        mapping = {r.old_node_id: r.new_node_id for r in registered}
        for old_id, expected_new_id in EXPECTED_REPLACEMENTS.items():
            actual = mapping.get(old_id)
            assert actual == expected_new_id, (
                f"{old_id}: expected new_node_id={expected_new_id!r}, got {actual!r}"
            )

    def test_no_input_mapping_needed(self):
        """All replacements should be simple ID-only swaps (no input_mapping)."""
        registered = _run_on_load()
        for r in registered:
            assert r.input_mapping is None, (
                f"{r.old_node_id}: unexpected input_mapping={r.input_mapping}"
            )

    def test_no_output_mapping_needed(self):
        """All replacements should have no output_mapping."""
        registered = _run_on_load()
        for r in registered:
            assert r.output_mapping is None, (
                f"{r.old_node_id}: unexpected output_mapping={r.output_mapping}"
            )

    def test_no_duplicate_old_ids(self):
        """Each V1 node ID should only be registered once."""
        registered = _run_on_load()
        old_ids = [r.old_node_id for r in registered]
        assert len(old_ids) == len(set(old_ids)), (
            f"Duplicate old_node_ids found: "
            f"{[x for x in old_ids if old_ids.count(x) > 1]}"
        )

    def test_no_unexpected_replacements(self):
        """Only expected V1 node IDs should be registered."""
        registered = _run_on_load()
        registered_old_ids = {r.old_node_id for r in registered}
        unexpected = registered_old_ids - set(EXPECTED_REPLACEMENTS.keys())
        assert len(unexpected) == 0, (
            f"Unexpected replacement registrations: {unexpected}"
        )
