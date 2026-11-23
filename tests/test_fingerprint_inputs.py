# ABOUTME: Tests each node's cache fingerprint: seed-gated on API-calling nodes, per resolved
# ABOUTME: API key on nodes that output a key, and absent on every other config node.

"""
Validates that every node with not_idempotent=True has a seed input with
control_after_generate set. The seed widget replaces the old fingerprint_inputs
NaN hack — when set to "randomize" (default), the seed changes each queue,
busting the cache. When "fixed", the user gets cached/reproducible results.

A node that resolves an API key and outputs it is cached per resolved key
instead: the same key keeps the cached output, another key does not get it.
"""

import importlib
import json
import math
import sys
import types
from collections import OrderedDict

import pytest

IO = pytest.importorskip("comfy_api.latest").IO


# (module_path, class_name) for every node that makes API calls
API_NODES = [
    # Gemini
    ("erpk.gemini.nodes", "GeminiTextGeneration"),
    ("erpk.gemini.nodes", "GeminiChat"),
    ("erpk.gemini.nodes", "GeminiVision"),
    ("erpk.gemini.nodes", "GeminiDetect"),
    ("erpk.gemini.nodes", "GeminiImageGeneration"),
    ("erpk.gemini.nodes", "GeminiImageEdit"),
    ("erpk.gemini.omni_nodes", "GeminiOmniVideoGeneration"),
    ("erpk.gemini.omni_nodes", "GeminiOmniReferenceToVideo"),
    # OpenAI
    ("erpk.openai.nodes", "OpenAITextGeneration"),
    ("erpk.openai.nodes", "OpenAIChat"),
    ("erpk.openai.nodes", "OpenAIVision"),
    ("erpk.openai.image_nodes", "OpenAIImageGeneration"),
    ("erpk.openai.image_nodes", "OpenAIImageEdit"),
    ("erpk.openai.image_nodes", "OpenAIImageResponses"),
    ("erpk.openai.image_nodes", "OpenAISVGGeneration"),
    # Grok
    ("erpk.grok.nodes", "GrokTextGeneration"),
    ("erpk.grok.nodes", "GrokChat"),
    # BytePlus ModelArk. Seed is sent on Seedance 1.0 only; elsewhere it is cache-control only.
    ("erpk.byteplus.video_nodes", "BytePlusSeedanceTextToVideo"),
    ("erpk.byteplus.video_nodes", "BytePlusSeedanceImageToVideo"),
    ("erpk.byteplus.video_nodes", "BytePlusSeedanceReferenceToVideo"),
    # A free GET, but a task's status changes under the same ID, so the seed lets it re-read on demand.
    ("erpk.byteplus.video_nodes", "BytePlusSeedanceTaskResult"),
    ("erpk.byteplus.nodes", "BytePlusSeedreamTextToImage"),
    ("erpk.byteplus.nodes", "BytePlusSeedreamImageEdit"),
    # Claude
    ("claude.text_generation", "ClaudeTextGeneration"),
    ("claude.conversation", "ClaudeConversation"),
    ("claude.vision_analysis", "ClaudeVisionAnalysis"),
    ("claude.prompt_enhancer", "ClaudePromptEnhancer"),
    ("claude.structured_output", "ClaudeStructuredOutput"),
    # WaveSpeed
    ("erpk.wavespeed.dreamina_edit", "DreaminaEditNode"),
    ("erpk.wavespeed.dreamina_text_to_image", "DreaminaTextToImageNode"),
    ("erpk.wavespeed.jibmix_qwen_image", "JibMixQwenImageNode"),
    ("erpk.wavespeed.qwen_image_edit", "QwenImageEditNode"),
    ("erpk.wavespeed.qwen_image_edit_lora", "QwenImageEditLoraNode"),
    ("erpk.wavespeed.qwen_image_edit_plus", "QwenImageEditPlusNode"),
    ("erpk.wavespeed.qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode"),
    ("erpk.wavespeed.qwen_image_layered", "QwenImageLayeredNode"),
    ("erpk.wavespeed.qwen_image_lora", "QwenImageLoraNode"),
    ("erpk.wavespeed.qwen_image_max", "QwenImageMaxNode"),
    ("erpk.wavespeed.qwen_image_max_edit", "QwenImageMaxEditNode"),
    ("erpk.wavespeed.qwen_image_multiple_angles", "QwenImageMultipleAnglesNode"),
    ("erpk.wavespeed.qwen_image_multiple_angles_96", "QwenImageMultipleAngles96Node"),
    ("erpk.wavespeed.qwen_image_3_0_text_to_image", "QwenImage30TextToImageNode"),
    ("erpk.wavespeed.qwen_image_3_0_edit", "QwenImage30EditNode"),
    ("erpk.wavespeed.qwen_image_text_to_image", "QwenImageTextToImageNode"),
    ("erpk.wavespeed.minimax_h3_text_to_video", "MinimaxH3TextToVideoNode"),
    ("erpk.wavespeed.minimax_h3_image_to_video", "MinimaxH3ImageToVideoNode"),
    ("erpk.wavespeed.minimax_h3_reference_to_video", "MinimaxH3ReferenceToVideoNode"),
    ("erpk.wavespeed.minimax_h3_text_to_image", "MinimaxH3TextToImageNode"),
    ("erpk.wavespeed.minimax_h3_image_edit", "MinimaxH3ImageEditNode"),
    ("erpk.wavespeed.minimax_h3_video_edit", "MinimaxH3VideoEditNode"),
    ("erpk.wavespeed.minimax_h3_video_extend", "MinimaxH3VideoExtendNode"),
    ("erpk.wavespeed.seedance_2_5_text_to_video", "Seedance25TextToVideoNode"),
    ("erpk.wavespeed.seedance_2_5_image_to_video", "Seedance25ImageToVideoNode"),
    ("erpk.wavespeed.seedance_2_5_video_edit", "Seedance25VideoEditNode"),
    ("erpk.wavespeed.seedance_2_5_video_extend", "Seedance25VideoExtendNode"),
    ("erpk.wavespeed.seedream_v4", "SeedreamV4Node"),
    ("erpk.wavespeed.seedream_v4_edit", "SeedreamV4EditNode"),
    ("erpk.wavespeed.seedream_v4_sequential", "SeedreamV4SequentialNode"),
    ("erpk.wavespeed.seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode"),
    ("erpk.wavespeed.seedream_v4_5", "SeedreamV4_5Node"),
    ("erpk.wavespeed.seedream_v4_5_edit", "SeedreamV4_5EditNode"),
    ("erpk.wavespeed.seedream_v4_5_sequential", "SeedreamV4_5SequentialNode"),
    ("erpk.wavespeed.seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode"),
    ("erpk.wavespeed.seedream_v5_lite", "SeedreamV5LiteNode"),
    ("erpk.wavespeed.seedream_v5_lite_edit", "SeedreamV5LiteEditNode"),
    ("erpk.wavespeed.seedream_v5_pro", "SeedreamV5ProNode"),
    ("erpk.wavespeed.seedream_v5_pro_edit", "SeedreamV5ProEditNode"),
    ("erpk.wavespeed.seedream_v5_pro_layers", "SeedreamV5ProLayersNode"),
    ("erpk.wavespeed.seedream_v5_5", "SeedreamV5_5Node"),
    ("erpk.wavespeed.seedream_v5_5_edit", "SeedreamV5_5EditNode"),
    ("erpk.wavespeed.seedream_v5_5_layers", "SeedreamV5_5LayersNode"),
    ("erpk.wavespeed.seedream_v5_flash", "SeedreamV5FlashNode"),
    ("erpk.wavespeed.seedream_v5_flash_edit", "SeedreamV5FlashEditNode"),
    ("erpk.wavespeed.seedream_v5_flash_layers", "SeedreamV5FlashLayersNode"),
    ("erpk.wavespeed.flux_2_pro", "Flux2ProNode"),
    ("erpk.wavespeed.flux_2_pro_edit", "Flux2ProEditNode"),
    ("erpk.wavespeed.seedream_v5_lite_sequential", "SeedreamV5LiteSequentialNode"),
    ("erpk.wavespeed.seedream_v5_lite_edit_sequential", "SeedreamV5LiteEditSequentialNode"),
    # WaveSpeed video (Kling / LTX 2 Pro) — seed is cache-control only; these
    # endpoints have no API seed parameter, so a fixed seed reuses the cached
    # result rather than reproducing a deterministic generation.
    ("erpk.wavespeed.kling_elements", "KlingElementsNode"),
    ("erpk.wavespeed.kling_v2_5_turbo_text_to_video", "KlingV2_5TurboTextToVideoNode"),
    ("erpk.wavespeed.kling_v2_5_turbo_image_to_video", "KlingV2_5TurboImageToVideoNode"),
    ("erpk.wavespeed.kling_v2_6_text_to_video", "KlingV2_6TextToVideoNode"),
    ("erpk.wavespeed.kling_v2_6_image_to_video", "KlingV2_6ImageToVideoNode"),
    ("erpk.wavespeed.ltx_2_pro_text_to_video", "Ltx2ProTextToVideoNode"),
    ("erpk.wavespeed.ltx_2_pro_image_to_video", "Ltx2ProImageToVideoNode"),
]


def _load_class(module_path, class_name):
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


@pytest.mark.parametrize("module_path,class_name", API_NODES,
                         ids=[f"{m}.{c}" for m, c in API_NODES])
class TestCacheBusting:
    """Every API-calling node must bypass ComfyUI's execution cache via seed."""

    def test_not_idempotent_is_true(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        assert schema.not_idempotent is True, (
            f"{class_name} makes API calls but not_idempotent is not True"
        )

    def test_has_seed_input(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        seed_inputs = [i for i in schema.inputs if i.id == "seed"]
        assert len(seed_inputs) == 1, (
            f"{class_name} must have a 'seed' input for cache-busting"
        )

    def test_seed_has_control_after_generate(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        seed_input = next(i for i in schema.inputs if i.id == "seed")
        assert seed_input.control_after_generate is not None, (
            f"{class_name} seed input must have control_after_generate set"
        )

    def test_fingerprint_returns_nan_for_random_seed(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        assert hasattr(cls, "fingerprint_inputs"), (
            f"{class_name} must define fingerprint_inputs for cache control"
        )
        import math
        result = cls.fingerprint_inputs(seed=-1)
        assert isinstance(result, float) and math.isnan(result), (
            f"{class_name}.fingerprint_inputs(seed=-1) should return NaN, got {result!r}"
        )


# Seeded nodes whose output carries the API key they resolved: a Gemini chat
# session holds the client that started it. Their fixed-seed fingerprint is
# the seed and the resolved key's cache token.
SEEDED_KEY_NODES = [
    ("erpk.gemini.nodes", "GeminiChat", "google"),
]
SEED_ONLY_NODES = [node for node in API_NODES if node not in [(m, c) for m, c, _ in SEEDED_KEY_NODES]]


@pytest.mark.parametrize("module_path,class_name", SEED_ONLY_NODES,
                         ids=[f"{m}.{c}" for m, c in SEED_ONLY_NODES])
class TestFixedSeedIsTheFingerprint:

    def test_fingerprint_returns_seed_for_fixed_seed(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        result = cls.fingerprint_inputs(seed=42)
        assert result == 42, (
            f"{class_name}.fingerprint_inputs(seed=42) should return 42, got {result!r}"
        )


# Config / passthrough nodes: no API call, no seed input, no API key resolved.
# They must NOT define fingerprint_inputs — a seedless node copies the NaN branch
# unconditionally (kwargs.get("seed", -1) is always -1), marking itself dirty
# every queue. As a root, that cascades cache invalidation into every downstream
# node, re-billing the whole graph. These rely on ComfyUI's default input-based
# caching instead.
CONFIG_NODES = [
    ("erpk.gemini.nodes", "GeminiSystemInstruction"),
    ("erpk.gemini.nodes", "GeminiSafetySettings"),
    ("utils.regional_prompt", "RegionalPromptBuilder"),
    ("utils.image_grid_loader", "ImageGridLoader"),
    ("erpk.openai.nodes", "OpenAISystemInstruction"),
    ("erpk.wavespeed.minimax_h3_lora_stack", "MinimaxH3LoraStackNode"),
]


@pytest.mark.parametrize("module_path,class_name", CONFIG_NODES,
                         ids=[f"{m}.{c}" for m, c in CONFIG_NODES])
class TestConfigNodesAreCacheable:
    """Non-API config/passthrough nodes must not force re-execution every queue."""

    def test_no_seed_input(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        schema = cls.define_schema()
        assert not [i for i in schema.inputs if i.id == "seed"], (
            f"{class_name} is treated as a config node but declares a seed input"
        )

    def test_does_not_declare_fingerprint_inputs(self, module_path, class_name):
        cls = _load_class(module_path, class_name)
        assert "fingerprint_inputs" not in cls.__dict__, (
            f"{class_name} has no seed input, so its fingerprint_inputs always "
            f"returns NaN — marking it dirty every queue and cascading cache "
            f"invalidation downstream. Remove the method; rely on default caching."
        )


# (module_path, class_name, key store provider, has an api_key widget) for every
# node that resolves the queuing user's API key and outputs a client carrying it.
KEY_NODES = [
    ("erpk.claude.nodes", "ClaudeAPIClient", "anthropic", True),
    ("erpk.openai.nodes", "OpenAIAPIConfig", "openai", False),
    ("erpk.gemini.nodes", "GeminiAPIConfig", "google", False),
    ("erpk.grok.nodes", "GrokAPIClient", "xai", True),
    ("erpk.byteplus.nodes", "BytePlusAPIClient", "byteplus", True),
    ("erpk.wavespeed.nodes", "WaveSpeedAIAPIClient", "wavespeed", True),
]

# No character of these keys is a hex digit, so a hex fingerprint can only
# share a substring with one by containing part of it.
ALICE_KEY = "sk-KLMNOPQRSTUVWXYZ-ghijklmnopqrstuvwxyz"
BOB_KEY = "sk-ZYXWVUTSRQPONMLK-zyxwvutsrqponmlkjihg"
ROTATED_KEY = "sk-GHIJKLMNOPQRSTUV-mnopqrstuvwxyzghijkl"


class Users:
    """A ComfyUI user directory with a key store, and the user whose prompt is running."""

    def __init__(self, tmp_path, monkeypatch):
        from erpk import settings

        self._settings = settings
        self._keys_dir = tmp_path / "erpk_keys"
        self._keys_dir.mkdir()
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_user_directory = lambda: str(user_dir)
        self._prompt_server = types.SimpleNamespace(client_id=None)
        server = types.ModuleType("server")
        server.PromptServer = types.SimpleNamespace(instance=self._prompt_server)
        monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)
        monkeypatch.setitem(sys.modules, "server", server)
        monkeypatch.setattr(settings, "_client_user_map", OrderedDict())

    def store_key(self, user_id, provider, key):
        (self._keys_dir / f"{user_id}.json").write_text(json.dumps({provider: key}), encoding="utf-8")

    def queue_as(self, user_id):
        client_id = f"client-of-{user_id}"
        assert self._settings.register_client_user(client_id, user_id)
        self._prompt_server.client_id = client_id


@pytest.fixture
def users(tmp_path, monkeypatch):
    return Users(tmp_path, monkeypatch)


def _shared_runs(key, text):
    return [key[i:i + 4] for i in range(len(key) - 3) if key[i:i + 4] in text]


@pytest.mark.parametrize("module_path,class_name,provider,has_key_widget", KEY_NODES,
                         ids=[c for _, c, _, _ in KEY_NODES])
class TestKeyNodesAreCachedPerResolvedKey:
    """A node that outputs a resolved API key is reused only for the same key."""

    def test_no_seed_input(self, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        assert not [i for i in cls.define_schema().inputs if i.id == "seed"]

    def test_same_key_keeps_the_same_fingerprint(self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        first = cls.fingerprint_inputs()
        second = cls.fingerprint_inputs()

        assert isinstance(first, str)
        assert first == second

    def test_users_with_different_keys_get_different_fingerprints(
            self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.store_key("bob", provider, BOB_KEY)

        users.queue_as("alice")
        alice = cls.fingerprint_inputs()
        users.queue_as("bob")
        bob = cls.fingerprint_inputs()
        users.queue_as("alice")

        assert alice != bob
        assert cls.fingerprint_inputs() == alice

    def test_a_changed_key_changes_the_fingerprint(self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.queue_as("alice")
        users.store_key("alice", provider, ALICE_KEY)
        before = cls.fingerprint_inputs()

        users.store_key("alice", provider, ROTATED_KEY)

        assert cls.fingerprint_inputs() != before

    def test_fingerprint_shares_no_four_characters_with_the_key(
            self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        assert _shared_runs(ALICE_KEY, cls.fingerprint_inputs()) == []

KEY_WIDGET_NODES = [node for node in KEY_NODES if node[3]]


@pytest.mark.parametrize("module_path,class_name,provider,has_key_widget", KEY_WIDGET_NODES,
                         ids=[c for _, c, _, _ in KEY_WIDGET_NODES])
class TestKeyWidgetSetsTheFingerprint:
    """The api_key widget is where execute looks when the user has stored no key."""

    def test_a_key_typed_in_the_widget_sets_the_fingerprint_when_none_is_stored(
            self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.queue_as("alice")

        typed = cls.fingerprint_inputs(api_key=ALICE_KEY)

        assert typed == cls.fingerprint_inputs(api_key=f"  {ALICE_KEY}  ")
        assert typed != cls.fingerprint_inputs(api_key=BOB_KEY)
        assert _shared_runs(ALICE_KEY, typed) == []

    def test_a_stored_key_wins_over_the_widget(self, users, module_path, class_name, provider, has_key_widget):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        assert cls.fingerprint_inputs(api_key=BOB_KEY) == cls.fingerprint_inputs(api_key="")

    def test_a_linked_key_widget_does_not_raise(self, users, module_path, class_name, provider, has_key_widget):
        """ComfyUI passes None for an input fed by a link, and turns an exception
        here into a fingerprint that never matches."""
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        assert cls.fingerprint_inputs(api_key=None) == cls.fingerprint_inputs(api_key="")


@pytest.mark.parametrize("module_path,class_name,provider", SEEDED_KEY_NODES,
                         ids=[c for _, c, _ in SEEDED_KEY_NODES])
class TestSeededKeyNodesAreCachedPerSeedAndKey:
    """A fixed seed reuses the cached output only for a prompt that resolves the same key."""

    def test_fixed_seed_and_same_key_keep_the_same_fingerprint(self, users, module_path, class_name, provider):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        first = cls.fingerprint_inputs(seed=42)

        assert isinstance(first, str)
        assert first == cls.fingerprint_inputs(seed=42)
        assert first != cls.fingerprint_inputs(seed=43)

    def test_users_with_different_keys_get_different_fingerprints(self, users, module_path, class_name, provider):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.store_key("bob", provider, BOB_KEY)

        users.queue_as("alice")
        alice = cls.fingerprint_inputs(seed=42)
        users.queue_as("bob")

        assert cls.fingerprint_inputs(seed=42) != alice

    def test_fingerprint_shares_no_four_characters_with_the_key(self, users, module_path, class_name, provider):
        cls = _load_class(module_path, class_name)
        users.store_key("alice", provider, ALICE_KEY)
        users.queue_as("alice")

        assert _shared_runs(ALICE_KEY, cls.fingerprint_inputs(seed=42)) == []
