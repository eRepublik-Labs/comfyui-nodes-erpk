# ABOUTME: Tests the per-user API key store on real files in a tmp dir.
# ABOUTME: Covers key isolation, path safety, file permissions and the settings migration.

import pytest

from erpk.key_store import KeyStore


@pytest.fixture
def store(tmp_path):
    return KeyStore(str(tmp_path / "erpk_keys"))


def test_status_shows_only_the_last_four_characters(store):
    store.set("alice", "anthropic", "sk-ant-api03-abcdWXYZ")

    assert store.status("alice") == {
        "anthropic": {"set": True, "last4": "WXYZ"},
        "google": {"set": False, "last4": None},
        "openai": {"set": False, "last4": None},
        "xai": {"set": False, "last4": None},
        "wavespeed": {"set": False, "last4": None},
        "byteplus": {"set": False, "last4": None},
    }


def test_status_hides_the_tail_of_a_key_short_enough_to_reveal_it(store):
    store.set("alice", "openai", "abcd1234")

    assert store.status("alice")["openai"] == {"set": True, "last4": None}


@pytest.mark.parametrize("user_id", ["../x", "..", ".", "a/b", "a\\b", "", "x" * 251, "al ice", "alice\n", "alice.rejected", "alice.REJECTED"])
def test_a_user_id_that_could_leave_the_store_dir_never_reaches_the_filesystem(store, tmp_path, user_id):
    for call in (
        lambda: store.set(user_id, "anthropic", "sk-ant-api03-abcdWXYZ"),
        lambda: store.get(user_id, "anthropic"),
        lambda: store.status(user_id),
        lambda: store.clear(user_id, "anthropic"),
    ):
        with pytest.raises(ValueError) as raised:
            call()
        assert str(raised.value) == f"Invalid user id: {user_id!r}"
    assert sorted(p.name for p in tmp_path.iterdir()) == []


def test_every_user_id_comfyui_generates_is_accepted(store):
    # user_manager.add_user: the name with [^a-zA-Z0-9-_]+ replaced by "-",
    # then "_" and a uuid4.
    user_id = "Jane-Roe_" + "0f8fad5b-d9cb-469f-a165-70867728950e"
    store.set(user_id, "google", "AIzaSyA-0123456789abcdefWXYZ")

    assert store.get(user_id, "google") == "AIzaSyA-0123456789abcdefWXYZ"


def test_one_users_key_is_never_returned_for_another_user(store):
    store.set("alice", "google", "AIzaSyA-alice-0000000000WXYZ")

    assert store.get("bob", "google") is None
    assert store.status("bob")["google"] == {"set": False, "last4": None}


def test_clear_makes_the_key_unreadable_and_keeps_the_others(store):
    store.set("alice", "anthropic", "sk-ant-api03-abcdWXYZ")
    store.set("alice", "xai", "xai-0123456789abcdefQRST")

    store.clear("alice", "anthropic")

    assert store.get("alice", "anthropic") is None
    assert store.get("alice", "xai") == "xai-0123456789abcdefQRST"
    assert store.status("alice")["anthropic"] == {"set": False, "last4": None}


def test_store_dir_and_files_are_private_to_the_owner(store, tmp_path):
    import stat

    store.set("alice", "anthropic", "sk-ant-api03-abcdWXYZ")
    store.set("alice", "xai", "xai-0123456789abcdefQRST")

    root = tmp_path / "erpk_keys"
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert sorted(p.name for p in root.iterdir()) == ["alice.json"]
    assert stat.S_IMODE((root / "alice.json").stat().st_mode) == 0o600


def test_unknown_provider_is_rejected(store):
    with pytest.raises(ValueError) as raised:
        store.set("alice", "mistral", "sk-0123456789abcdefWXYZ")
    assert str(raised.value) == "Unknown provider: 'mistral'"


@pytest.mark.parametrize("key,message", [
    ("", "API key is empty"),
    ("sk-ant api03", "API key contains whitespace"),
    ("sk-ant-api03\n", "API key contains whitespace"),
    ("k" * 513, "API key is longer than 512 characters"),
    (None, "API key must be a string, got NoneType"),
])
def test_a_malformed_key_is_rejected_without_echoing_it(store, tmp_path, key, message):
    with pytest.raises(ValueError) as raised:
        store.set("alice", "anthropic", key)
    assert str(raised.value) == message
    assert not (tmp_path / "erpk_keys").exists()


def test_an_unreadable_store_file_fails_loudly_instead_of_reading_as_no_key(store, tmp_path):
    root = tmp_path / "erpk_keys"
    root.mkdir()
    (root / "alice.json").write_text('{"anthropic": "sk-ant-trunc', encoding="utf-8")

    with pytest.raises(RuntimeError) as raised:
        store.get("alice", "anthropic")
    assert str(raised.value) == f"API key store file {root / 'alice.json'} is not a JSON object; fix or delete it"


# --- migrate_settings ---------------------------------------------------------

import json
import os
import stat

from erpk.key_store import migrate_settings


def write_comfy_settings(user_dir, user_id, settings, mode=0o644):
    """Write settings the way ComfyUI's app_settings.save_settings does."""
    folder = user_dir / user_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "comfy.settings.json"
    path.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    os.chmod(path, mode)
    return path


@pytest.fixture
def user_dir(tmp_path):
    folder = tmp_path / "user"
    folder.mkdir()
    return folder


def test_migration_moves_every_key_and_leaves_every_other_entry_byte_for_byte(user_dir, store, console):
    path = write_comfy_settings(user_dir, "alice", {
        "Comfy.Locale": "ro",
        "ERPK.ANTHROPIC_API_KEY": "sk-ant-api03-abcdWXYZ",
        "Comfy.UserName": "Zoë",
        "ERPK.GOOGLE_API_KEY": "  AIzaSyA-0123456789abcdefWXYZ\n",
        "ERPK.OPENAI_API_KEY": "",
        "ERPK.AUTO_CLEAR_HISTORY": True,
        "ERPK.PARALLEL_WORKERS": 2,
    })

    report = migrate_settings(str(user_dir), store)

    assert path.read_bytes() == json.dumps({
        "Comfy.Locale": "ro",
        "Comfy.UserName": "Zoë",
        "ERPK.AUTO_CLEAR_HISTORY": True,
        "ERPK.PARALLEL_WORKERS": 2,
    }, indent=4).encode("utf-8")
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert store.get("alice", "anthropic") == "sk-ant-api03-abcdWXYZ"
    assert store.get("alice", "google") == "AIzaSyA-0123456789abcdefWXYZ"
    assert store.get("alice", "openai") is None
    assert report == {"alice": {"moved": ["anthropic", "google"], "already_stored": [], "empty": ["openai"], "set_aside": []}}
    assert console() == (
        "[ERPK] API keys for user alice: moved 2 to the key store (anthropic, google), "
        "removed 0 already stored (), removed 1 empty (openai), set aside 0 unusable values ()\n"
    )


def test_migration_never_overwrites_a_key_already_in_the_store(user_dir, store, console):
    store.set("alice", "anthropic", "sk-ant-api03-fromSTORE")
    path = write_comfy_settings(user_dir, "alice", {"ERPK.ANTHROPIC_API_KEY": "sk-ant-api03-fromSETTINGS"})

    report = migrate_settings(str(user_dir), store)

    assert store.get("alice", "anthropic") == "sk-ant-api03-fromSTORE"
    assert json.loads(path.read_text(encoding="utf-8")) == {}
    assert report == {"alice": {"moved": [], "already_stored": ["anthropic"], "empty": [], "set_aside": []}}
    assert console() == (
        "[ERPK] API keys for user alice: moved 0 to the key store (), "
        "removed 1 already stored (anthropic), removed 0 empty (), set aside 0 unusable values ()\n"
    )


def test_a_second_migration_changes_nothing(user_dir, store, console):
    path = write_comfy_settings(user_dir, "alice", {
        "Comfy.Locale": "ro",
        "ERPK.XAI_API_KEY": "xai-0123456789abcdefQRST",
        "ERPK.OPENAI_API_KEY": "two words",
    })
    migrate_settings(str(user_dir), store)
    console()
    files = [path, user_dir.parent / "erpk_keys" / "alice.json", user_dir.parent / "erpk_keys" / "alice.rejected.json"]
    before = [(f.read_bytes(), f.stat().st_mtime_ns) for f in files]

    report = migrate_settings(str(user_dir), store)

    after = [(f.read_bytes(), f.stat().st_mtime_ns) for f in files]
    assert after == before
    assert report == {"alice": {"moved": [], "already_stored": [], "empty": [], "set_aside": []}}
    assert console() == ""


def test_malformed_settings_json_is_left_untouched_with_a_loud_warning(user_dir, store, console):
    folder = user_dir / "alice"
    folder.mkdir()
    path = folder / "comfy.settings.json"
    path.write_text('{"ERPK.ANTHROPIC_API_KEY": "sk-ant-api03-abcdWXYZ",', encoding="utf-8")

    report = migrate_settings(str(user_dir), store)

    assert path.read_text(encoding="utf-8") == '{"ERPK.ANTHROPIC_API_KEY": "sk-ant-api03-abcdWXYZ",'
    assert store.get("alice", "anthropic") is None
    assert report == {}
    assert console() == (
        f"[ERPK] WARNING: API keys NOT migrated for {folder}: comfy.settings.json is not a JSON object. "
        "Any ERPK API keys in it stay readable by other users; fix the file and restart ComfyUI.\n"
    )


def test_a_user_dir_whose_name_is_not_a_valid_user_id_is_left_untouched(user_dir, store, console):
    path = write_comfy_settings(user_dir, "al ice", {"ERPK.ANTHROPIC_API_KEY": "sk-ant-api03-abcdWXYZ"})
    original = path.read_bytes()

    report = migrate_settings(str(user_dir), store)

    assert path.read_bytes() == original
    assert report == {}
    assert console() == (
        f"[ERPK] WARNING: API keys NOT migrated for {user_dir / 'al ice'}: Invalid user id: 'al ice'. "
        "Any ERPK API keys in it stay readable by other users; fix the file and restart ComfyUI.\n"
    )


def test_a_value_the_store_rejects_leaves_settings_for_a_private_set_aside_file(user_dir, store, console):
    path = write_comfy_settings(user_dir, "alice", {
        "Comfy.Locale": "ro",
        "ERPK.ANTHROPIC_API_KEY": 12345,
        "ERPK.GOOGLE_API_KEY": "k" * 513,
        "ERPK.WAVESPEED_API_KEY": "  two words\n",
    })

    report = migrate_settings(str(user_dir), store)

    root = user_dir.parent / "erpk_keys"
    rejected = root / "alice.rejected.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {"Comfy.Locale": "ro"}
    assert json.loads(rejected.read_text(encoding="utf-8")) == {
        "anthropic": 12345,
        "google": "k" * 513,
        "wavespeed": "  two words\n",
    }
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE(rejected.stat().st_mode) == 0o600
    assert sorted(p.name for p in root.iterdir()) == ["alice.rejected.json"]
    assert store.get("alice", "anthropic") is None
    assert report == {"alice": {"moved": [], "already_stored": [], "empty": [], "set_aside": ["anthropic", "google", "wavespeed"]}}
    assert console() == (
        f"[ERPK] WARNING: ERPK.ANTHROPIC_API_KEY in {path} is not a usable API key: API key must be a string, got int. "
        f"It was removed from that file and set aside in {rejected}. Save a valid key in Settings > ERPK > API Keys.\n"
        f"[ERPK] WARNING: ERPK.GOOGLE_API_KEY in {path} is not a usable API key: API key is longer than 512 characters. "
        f"It was removed from that file and set aside in {rejected}. Save a valid key in Settings > ERPK > API Keys.\n"
        f"[ERPK] WARNING: ERPK.WAVESPEED_API_KEY in {path} is not a usable API key: API key contains whitespace. "
        f"It was removed from that file and set aside in {rejected}. Save a valid key in Settings > ERPK > API Keys.\n"
        "[ERPK] API keys for user alice: moved 0 to the key store (), removed 0 already stored (), "
        "removed 0 empty (), set aside 3 unusable values (anthropic, google, wavespeed)\n"
    )


def test_a_value_already_set_aside_is_kept_and_the_settings_entry_still_goes(user_dir, store, console):
    write_comfy_settings(user_dir, "alice", {"ERPK.WAVESPEED_API_KEY": "two words"})
    migrate_settings(str(user_dir), store)
    console()
    path = write_comfy_settings(user_dir, "alice", {
        "ERPK.WAVESPEED_API_KEY": "three more words",
        "ERPK.BYTEPLUS_API_KEY": "ark-0123456789abcdefQRST",
    })

    report = migrate_settings(str(user_dir), store)

    rejected = user_dir.parent / "erpk_keys" / "alice.rejected.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {}
    assert json.loads(rejected.read_text(encoding="utf-8")) == {"wavespeed": "two words"}
    assert json.loads((user_dir.parent / "erpk_keys" / "alice.json").read_text(encoding="utf-8")) == {
        "byteplus": "ark-0123456789abcdefQRST",
    }
    assert report == {"alice": {"moved": ["byteplus"], "already_stored": [], "empty": [], "set_aside": ["wavespeed"]}}
    assert console() == (
        f"[ERPK] WARNING: ERPK.WAVESPEED_API_KEY in {path} is not a usable API key: API key contains whitespace. "
        f"It was removed from that file; {rejected} keeps the value set aside earlier. "
        "Save a valid key in Settings > ERPK > API Keys.\n"
        "[ERPK] API keys for user alice: moved 1 to the key store (byteplus), removed 0 already stored (), "
        "removed 0 empty (), set aside 1 unusable values (wavespeed)\n"
    )


def test_users_without_a_settings_file_are_skipped_quietly(user_dir, store, console):
    (user_dir / "__manager").mkdir()
    (user_dir / "users.json").write_text("{}", encoding="utf-8")

    assert migrate_settings(str(user_dir), store) == {}
    assert console() == ""
    assert not (user_dir.parent / "erpk_keys").exists()


def test_a_missing_user_dir_has_nothing_to_migrate(tmp_path, store, console):
    assert migrate_settings(str(tmp_path / "user"), store) == {}
    assert console() == ""
