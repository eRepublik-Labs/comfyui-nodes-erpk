# ABOUTME: Per-user API key store kept outside every directory a ComfyUI route serves.
# ABOUTME: One 0600 JSON file per user under erpk_keys/ (plus one for set-aside unusable values),
# ABOUTME: the move out of comfy.settings.json, the refusal of key writes back into it, and ApiKey.

import json
import os
import re
import tempfile
import threading
from urllib import parse

# Provider name -> the ComfyUI setting id the key used to live under.
PROVIDERS = {
    "anthropic": "ERPK.ANTHROPIC_API_KEY",
    "google": "ERPK.GOOGLE_API_KEY",
    "openai": "ERPK.OPENAI_API_KEY",
    "xai": "ERPK.XAI_API_KEY",
    "wavespeed": "ERPK.WAVESPEED_API_KEY",
    "byteplus": "ERPK.BYTEPLUS_API_KEY",
}
_KEY_SETTING_IDS = frozenset(PROVIDERS.values())

# ComfyUI's routes that write comfy.settings.json (app/app_settings.py and
# the raw file write in app/user_manager.py), each served with and without
# the /api prefix.
_SETTING_ROUTES = frozenset({"/settings/{id}", "/api/settings/{id}"})
_SETTINGS_ROUTES = frozenset({"/settings", "/api/settings"})
_USERDATA_ROUTES = frozenset({"/userdata/{file}", "/api/userdata/{file}"})
SETTINGS_WRITE_ROUTES = _SETTING_ROUTES | _SETTINGS_ROUTES | _USERDATA_ROUTES

KEY_SETTING_REFUSAL = "ERPK API keys are saved in Settings > ERPK > API Keys. Reload this page."

# ComfyUI's user ids (user_manager.add_user) are [a-zA-Z0-9_-] plus a uuid4.
# 250 leaves room for ".json" inside a 255-byte file name.
_USER_ID_RE = re.compile(r"[A-Za-z0-9_.-]{1,250}")
_REJECTED_SUFFIX = ".rejected"

# A key shorter than this would be mostly revealed by its last four characters.
_MIN_LENGTH_TO_SHOW_TAIL = 16

# One lock for every store in the process: callers build a store per lookup, so
# a per-instance lock would serialize nothing.
_write_lock = threading.Lock()


class ApiKey:
    """A resolved API key as it travels between nodes.

    A client node's output reaches any sink a user can wire it to: Preview
    nodes and failed-node errors store str() of it in the history every user
    can read. str() and repr() are masked and json.dumps raises TypeError, so
    a sink shows "ApiKey(set)". Only the API client constructors call reveal().
    """

    __slots__ = ("_key",)

    def __init__(self, key):
        if not isinstance(key, str):
            raise TypeError(f"API key must be a str, got {type(key).__name__}")
        if not key:
            raise ValueError("API key is empty")
        self._key = key

    def reveal(self):
        return self._key

    def __repr__(self):
        return "ApiKey(set)"

    __str__ = __repr__


def reveal_key(key):
    """An ApiKey's key; a str or None unchanged. For API client constructors,
    which take a key from a client node (ApiKey) or from a widget or config (str)."""
    return key.reveal() if isinstance(key, ApiKey) else key


def store_for(user_dir):
    """The store for a ComfyUI install: erpk_keys/ beside its user directory."""
    return KeyStore(os.path.join(os.path.dirname(os.path.normpath(user_dir)), "erpk_keys"))


class KeyStore:
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def get(self, user_id, provider):
        """The user's key for this provider, or None."""
        return self._read(self._path(user_id)).get(_check_provider(provider))

    def set(self, user_id, provider, key):
        provider = _check_provider(provider)
        _check_key(key)

        def put(keys):
            keys[provider] = key

        self._update(self._path(user_id), put)

    def clear(self, user_id, provider):
        provider = _check_provider(provider)
        self._update(self._path(user_id), lambda keys: keys.pop(provider, None))

    def status(self, user_id):
        """Which providers have a key, with the last four characters of each."""
        keys = self._read(self._path(user_id))
        return {provider: _describe(keys.get(provider)) for provider in PROVIDERS}

    def set_aside(self, user_id, values):
        """Keep {provider: value} settings values that are not usable keys in a
        file of their own, which get() never reads. A provider already set
        aside keeps its first value. Returns the providers already set aside."""
        already = []

        def merge(saved):
            for provider, value in values.items():
                if provider in saved:
                    already.append(provider)
                else:
                    saved[provider] = value

        self._update(self.set_aside_path(user_id), merge)
        return already

    def set_aside_path(self, user_id):
        return os.path.join(self.root_dir, _check_user_id(user_id) + _REJECTED_SUFFIX + ".json")

    def _path(self, user_id):
        return os.path.join(self.root_dir, _check_user_id(user_id) + ".json")

    def _read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                keys = json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # Raise below, outside this handler: the decode error carries the
            # file text, keys included, and would ride along as __context__.
            keys = None
        if not isinstance(keys, dict):
            raise RuntimeError(f"API key store file {path} is not a JSON object; fix or delete it")
        return keys

    def _update(self, path, change):
        with _write_lock:
            keys = self._read(path)
            change(keys)
            os.makedirs(self.root_dir, mode=0o700, exist_ok=True)
            _atomic_write(path, json.dumps(keys, indent=2))


def _check_user_id(user_id):
    # "<id>.rejected" would name another user's set-aside file as its key store
    # file; casefold covers case-insensitive file systems.
    if (
        not isinstance(user_id, str)
        or not _USER_ID_RE.fullmatch(user_id)
        or user_id in (".", "..")
        or user_id.casefold().endswith(_REJECTED_SUFFIX)
    ):
        raise ValueError(f"Invalid user id: {user_id!r}")
    return user_id


def _check_provider(provider):
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider!r}")
    return provider


def _check_key(key):
    """Raise ValueError for a key no provider would issue. The message never
    contains the key."""
    if not isinstance(key, str):
        raise ValueError(f"API key must be a string, got {type(key).__name__}")
    if not key:
        raise ValueError("API key is empty")
    if any(c.isspace() for c in key):
        raise ValueError("API key contains whitespace")
    if len(key) > 512:
        raise ValueError("API key is longer than 512 characters")


def _describe(key):
    if not key:
        return {"set": False, "last4": None}
    last4 = key[-4:] if len(key) >= _MIN_LENGTH_TO_SHOW_TAIL else None
    return {"set": True, "last4": last4}


def _atomic_write(path, text, mode=None):
    """Replace path with text in one step. mkstemp creates the temp file 0600;
    mode, when given, is applied to the temp file before it takes path's place."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def migrate_settings(user_dir, store):
    """Move API keys out of every user's comfy.settings.json into store.

    A key already in the store wins over the one in settings. A value that is
    not a usable key goes to the user's set-aside file instead, where a value
    already set aside wins. Every key entry is deleted from settings;
    everything else in the file is kept, and the file is rewritten only when
    something was removed. Running it again changes nothing. Returns, per
    migrated user, the providers in each outcome. Prints counts and provider
    names, never keys or values.
    """
    report = {}
    if not os.path.isdir(user_dir):
        return report
    for name in sorted(os.listdir(user_dir)):
        folder = os.path.join(user_dir, name)
        settings_path = os.path.join(folder, "comfy.settings.json")
        if not os.path.isfile(settings_path):
            continue
        try:
            report[name] = _migrate_user(name, settings_path, store)
        except Exception as e:
            _warn_not_migrated(folder, str(e))
    return report


def _migrate_user(user_id, settings_path, store):
    _check_user_id(user_id)
    with open(settings_path, "r", encoding="utf-8") as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError:
            settings = None
    if not isinstance(settings, dict):
        raise ValueError("comfy.settings.json is not a JSON object")

    outcome = {"moved": [], "already_stored": [], "empty": [], "set_aside": []}
    unusable = {}
    for provider, setting_id in PROVIDERS.items():
        if setting_id not in settings:
            continue
        value = settings[setting_id]
        if value is None or (isinstance(value, str) and not value.strip()):
            outcome["empty"].append(provider)
        else:
            key = value.strip() if isinstance(value, str) else value
            try:
                _check_key(key)
            except ValueError as e:
                outcome["set_aside"].append(provider)
                unusable[provider] = (value, e)
            else:
                if store.get(user_id, provider) is None:
                    store.set(user_id, provider, key)
                    outcome["moved"].append(provider)
                else:
                    outcome["already_stored"].append(provider)
        del settings[setting_id]

    # Before the settings rewrite, so a crash between the two loses no value.
    already = store.set_aside(user_id, {p: value for p, (value, _) in unusable.items()}) if unusable else []

    removed = outcome["moved"] + outcome["already_stored"] + outcome["empty"] + outcome["set_aside"]
    if removed:
        mode = os.stat(settings_path).st_mode & 0o7777
        # The exact serialization of ComfyUI's app_settings.save_settings.
        _atomic_write(settings_path, json.dumps(settings, indent=4), mode=mode)
        for provider, (_, reason) in unusable.items():
            _warn_set_aside(PROVIDERS[provider], settings_path, reason, store.set_aside_path(user_id), provider in already)
        print(
            f"[ERPK] API keys for user {user_id}: "
            f"moved {len(outcome['moved'])} to the key store ({', '.join(outcome['moved'])}), "
            f"removed {len(outcome['already_stored'])} already stored ({', '.join(outcome['already_stored'])}), "
            f"removed {len(outcome['empty'])} empty ({', '.join(outcome['empty'])}), "
            f"set aside {len(outcome['set_aside'])} unusable values ({', '.join(outcome['set_aside'])})",
            flush=True,
        )
    return outcome


def _warn_set_aside(setting_id, settings_path, reason, set_aside_path, was_set_aside_earlier):
    where = (
        f"It was removed from that file; {set_aside_path} keeps the value set aside earlier."
        if was_set_aside_earlier
        else f"It was removed from that file and set aside in {set_aside_path}."
    )
    print(
        f"[ERPK] WARNING: {setting_id} in {settings_path} is not a usable API key: {reason}. "
        f"{where} Save a valid key in Settings > ERPK > API Keys.",
        flush=True,
    )


def _warn_not_migrated(folder, reason):
    print(
        f"[ERPK] WARNING: API keys NOT migrated for {folder}: {reason}. "
        "Any ERPK API keys in it stay readable by other users; fix the file and restart ComfyUI.",
        flush=True,
    )


def writes_key_setting(method, route, params, body):
    """Whether a request would save an ERPK API key into comfy.settings.json.

    A page loaded before the key store still has the old key settings and
    saves an edit through ComfyUI's settings routes. route is the aiohttp
    route pattern that matched, params its decoded parameters, body the raw
    request body.
    """
    if method != "POST":
        return False
    if route in _SETTING_ROUTES:
        return params.get("id") in _KEY_SETTING_IDS
    if route in _SETTINGS_ROUTES:
        try:
            settings = json.loads(body)
        except ValueError:
            return False
        return isinstance(settings, dict) and not _KEY_SETTING_IDS.isdisjoint(settings)
    if route in _USERDATA_ROUTES:
        return _names_settings_file(params.get("file", "")) and any(
            setting_id.encode() in body for setting_id in _KEY_SETTING_IDS
        )
    return False


def _names_settings_file(file):
    """Whether a /userdata file name can resolve to the user's comfy.settings.json.
    ComfyUI percent-decodes a name holding % once more, then joins it to the
    user's directory. A same-named file in a subfolder matches too, at no
    cost: only a body naming a key setting is refused. casefold covers
    case-insensitive file systems."""
    if "%" in file:
        file = parse.unquote(file)
    return os.path.basename(os.path.normpath(file)).casefold() == "comfy.settings.json"
