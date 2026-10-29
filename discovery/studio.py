"""Product-repo curbpack-studio.json. Bind/model/prompt/temp live here, not in curbpack.json."""

from __future__ import annotations

import copy
from pathlib import Path

from common.errors import ModelError
from common.jsonio import read_json, write_json

STUDIO_NAME = "curbpack-studio.json"
_ENV_NAME = ".env"
_BLOCKS = ("bind", "model", "prompts", "paths")
_BIND = ("host", "port")
_MODEL = ("endpoint", "api_key", "name", "temperature")
_PROMPTS = ("interpret", "discovery_hints")
_PATHS = ("temp_dir", "extract_work_dir", "keys_file")

CREATED_STUDIO = {
    "bind": {"host": "127.0.0.1", "port": 8770},
    "model": {
        "endpoint": "http://127.0.0.1:11434",
        "api_key": "$CURBPACK_MODEL_API_KEY",
        "name": "qwen3-coder:30b",
        "temperature": 0.2,
    },
    "prompts": {"interpret": None, "discovery_hints": None},
    "paths": {
        "temp_dir": ".curbpack/tmp",
        "extract_work_dir": ".curbpack/extract",
        "keys_file": None,
    },
}


def studio_file(repo: Path) -> Path:
    return Path(repo) / STUDIO_NAME


def created_studio_config() -> dict:
    return validate_studio_config(copy.deepcopy(CREATED_STUDIO))


def validate_studio_config(obj: object) -> dict:
    if not isinstance(obj, dict):
        raise ModelError(STUDIO_NAME, "(root)", "object")
    unknown = sorted(set(obj) - set(_BLOCKS))
    if unknown:
        raise ModelError(STUDIO_NAME, unknown[0], f"one of {list(_BLOCKS)}")
    missing = [key for key in _BLOCKS if key not in obj]
    if missing:
        raise ModelError(STUDIO_NAME, missing[0], "a required block")
    bind = _object_block(obj["bind"], "bind", _BIND)
    host = bind["host"]
    if not isinstance(host, str) or not host.strip():
        raise ModelError(STUDIO_NAME, "bind.host", "a host string")
    port = bind["port"]
    if not isinstance(port, int) or isinstance(port, bool) or port < 1:
        raise ModelError(STUDIO_NAME, "bind.port", "a TCP port")
    model = _object_block(obj["model"], "model", _MODEL)
    for key in ("endpoint", "api_key", "name"):
        value = model[key]
        if not isinstance(value, str) or not value.strip():
            raise ModelError(STUDIO_NAME, f"model.{key}", "a string")
    temperature = model["temperature"]
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        raise ModelError(STUDIO_NAME, "model.temperature", "a number")
    prompts = _object_block(obj["prompts"], "prompts", _PROMPTS)
    for key in _PROMPTS:
        value = prompts[key]
        if value is None:
            continue
        if not _repo_relative(value):
            raise ModelError(STUDIO_NAME, f"prompts.{key}", "a repo-relative path or null")
    paths = _object_block(obj["paths"], "paths", _PATHS)
    for key in ("temp_dir", "extract_work_dir"):
        if not _repo_relative(paths[key]):
            raise ModelError(STUDIO_NAME, f"paths.{key}", "a relative directory")
    keys_file = paths["keys_file"]
    if keys_file is not None and not _repo_relative(keys_file):
        raise ModelError(STUDIO_NAME, "paths.keys_file", "a relative path or null")
    return {
        "bind": {"host": host.strip(), "port": port},
        "model": {
            "endpoint": str(model["endpoint"]).strip(),
            "api_key": str(model["api_key"]).strip(),
            "name": str(model["name"]).strip(),
            "temperature": float(temperature),
        },
        "prompts": {key: None if prompts[key] is None else str(prompts[key]).strip() for key in _PROMPTS},
        "paths": {
            "temp_dir": str(paths["temp_dir"]).strip(),
            "extract_work_dir": str(paths["extract_work_dir"]).strip(),
            "keys_file": None if keys_file is None else str(keys_file).strip(),
        },
    }


def load_studio_config(repo: Path) -> dict | None:
    path = studio_file(repo)
    if not path.is_file():
        return None
    document = validate_studio_config(read_json(path))
    env = _read_env(repo / _ENV_NAME)
    return _substitute(document, env)


def save_studio_config(repo: Path, document: dict) -> dict:
    written = validate_studio_config(document)
    write_json(studio_file(repo), written)
    return written


def studio_from_form(form: dict) -> dict:
    def field(name: str) -> str:
        return (form.get(name) or [""])[0].strip() if isinstance(form.get(name), list) else str(form.get(name) or "").strip()

    port_text = field("bind_port")
    try:
        port = int(port_text)
    except ValueError:
        raise ModelError(STUDIO_NAME, "bind.port", "a TCP port")
    temperature_text = field("model_temperature")
    try:
        temperature = float(temperature_text)
    except ValueError:
        raise ModelError(STUDIO_NAME, "model.temperature", "a number")
    return validate_studio_config(
        {
            "bind": {"host": field("bind_host"), "port": port},
            "model": {
                "endpoint": field("model_endpoint"),
                "api_key": field("model_api_key"),
                "name": field("model_name"),
                "temperature": temperature,
            },
            "prompts": {
                "interpret": field("prompt_interpret") or None,
                "discovery_hints": field("prompt_discovery_hints") or None,
            },
            "paths": {
                "temp_dir": field("path_temp_dir"),
                "extract_work_dir": field("path_extract_work_dir"),
                "keys_file": field("path_keys_file") or None,
            },
        }
    )


def editor_values(document: dict) -> dict:
    bind = document.get("bind") if isinstance(document.get("bind"), dict) else {}
    model = document.get("model") if isinstance(document.get("model"), dict) else {}
    prompts = document.get("prompts") if isinstance(document.get("prompts"), dict) else {}
    paths = document.get("paths") if isinstance(document.get("paths"), dict) else {}
    return {
        "bind_host": str(bind.get("host") or ""),
        "bind_port": "" if bind.get("port") is None else str(bind.get("port")),
        "model_endpoint": str(model.get("endpoint") or ""),
        "model_api_key": str(model.get("api_key") or ""),
        "model_name": str(model.get("name") or ""),
        "model_temperature": "" if model.get("temperature") is None else str(model.get("temperature")),
        "prompt_interpret": "" if prompts.get("interpret") is None else str(prompts.get("interpret")),
        "prompt_discovery_hints": "" if prompts.get("discovery_hints") is None else str(prompts.get("discovery_hints")),
        "path_temp_dir": str(paths.get("temp_dir") or ""),
        "path_extract_work_dir": str(paths.get("extract_work_dir") or ""),
        "path_keys_file": "" if paths.get("keys_file") is None else str(paths.get("keys_file")),
    }


def _repo_relative(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = value.strip().replace("\\", "/")
    if path.startswith("/") or ".." in path.split("/"):
        return False
    return True


def _object_block(value: object, name: str, keys: tuple[str, ...]) -> dict:
    if not isinstance(value, dict):
        raise ModelError(STUDIO_NAME, name, "object")
    unknown = sorted(set(value) - set(keys))
    if unknown:
        raise ModelError(STUDIO_NAME, f"{name}.{unknown[0]}", f"one of {list(keys)}")
    missing = [key for key in keys if key not in value]
    if missing:
        raise ModelError(STUDIO_NAME, f"{name}.{missing[0]}", "a required field")
    return value


def _read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            values[key] = value.strip().strip("'\"")
    return values


def _substitute(value, env: dict[str, str], field: str = "(root)"):
    if isinstance(value, dict):
        return {key: _substitute(item, env, key if field == "(root)" else f"{field}.{key}") for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute(item, env, field) for item in value]
    if isinstance(value, str) and value.startswith("$") and len(value) > 1 and value[1:].replace("_", "").isalnum():
        name = value[1:]
        if name not in env:
            raise ModelError(STUDIO_NAME, field, f"${name} from .env")
        return env[name]
    return value
