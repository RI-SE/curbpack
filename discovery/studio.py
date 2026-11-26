"""Studio settings. The user file holds installation values. The product file holds allowed overrides."""

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
        "api_key": "",
        "name": "qwen3-coder:30b",
        "temperature": 0.2,
    },
    "prompts": {"interpret": None, "discovery_hints": None},
    "paths": {
        "temp_dir": ".curbpack/tmp",
        "extract_work_dir": ".curbpack/extract",
        "keys_file": None,
    },
    "researcher_mode": False,
}


def studio_file(repo: Path) -> Path:
    return Path(repo) / STUDIO_NAME


def user_studio_dir(home: Path | None = None) -> Path:
    return (Path.home() if home is None else Path(home)) / ".curbpack"


def user_studio_file(home: Path | None = None) -> Path:
    return user_studio_dir(home) / STUDIO_NAME


def _env_file(home: Path | None = None) -> Path:
    return user_studio_dir(home) / _ENV_NAME


def created_studio_config() -> dict:
    return validate_studio_config(copy.deepcopy(CREATED_STUDIO))


def _api_key(value: object) -> str:
    if value == "":
        return ""
    if isinstance(value, str) and _env_placeholder(value.strip()):
        return value.strip()
    raise ModelError(STUDIO_NAME, "model.api_key", "empty or a $NAME placeholder")


def _env_placeholder(value: str) -> bool:
    return value.startswith("$") and len(value) > 1 and value[1:].replace("_", "").isalnum()


def validate_studio_config(obj: object) -> dict:
    if not isinstance(obj, dict):
        raise ModelError(STUDIO_NAME, "(root)", "object")
    unknown = sorted(set(obj) - set(_BLOCKS) - {"researcher_mode"})
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
    for key in ("endpoint", "name"):
        value = model[key]
        if not isinstance(value, str) or not value.strip():
            raise ModelError(STUDIO_NAME, f"model.{key}", "a string")
    api_key = _api_key(model["api_key"])
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
    mode = obj.get("researcher_mode", False)
    if not isinstance(mode, bool):
        raise ModelError(STUDIO_NAME, "researcher_mode", "true or false")
    return {
        "bind": {"host": host.strip(), "port": port},
        "model": {
            "endpoint": str(model["endpoint"]).strip(),
            "api_key": api_key,
            "name": str(model["name"]).strip(),
            "temperature": float(temperature),
        },
        "prompts": {key: None if prompts[key] is None else str(prompts[key]).strip() for key in _PROMPTS},
        "paths": {
            "temp_dir": str(paths["temp_dir"]).strip(),
            "extract_work_dir": str(paths["extract_work_dir"]).strip(),
            "keys_file": None if keys_file is None else str(keys_file).strip(),
        },
        "researcher_mode": mode,
    }


_PROJECT_TOP = {"model", "prompts", "paths", "researcher_mode"}
_PROJECT_MODEL = {"endpoint", "name", "temperature"}
_PROJECT_PROMPTS = {"interpret", "discovery_hints"}
_PROJECT_PATHS = {"extract_work_dir"}
_USER_FILE = "the user file ~/.curbpack/curbpack-studio.json"


def load_user_studio(home: Path | None = None) -> dict | None:
    path = user_studio_file(home)
    if not path.is_file():
        return None
    document = validate_studio_config(read_json(path))
    key = document["model"]["api_key"]
    if _env_placeholder(key):
        document["model"]["api_key"] = _read_env(_env_file(home)).get(key[1:], "")
    return document


def load_project_studio(repo: Path | None) -> dict | None:
    if repo is None:
        return None
    path = studio_file(repo)
    if not path.is_file():
        return None
    return validate_project_studio(read_json(path))


def validate_project_studio(obj: object) -> dict:
    if not isinstance(obj, dict):
        raise ModelError(STUDIO_NAME, "(root)", "object")
    disallowed = _disallowed_project_fields(obj)
    if disallowed:
        raise ModelError(STUDIO_NAME, ", ".join(disallowed), f"those fields in {_USER_FILE}")
    model = _partial_block(obj.get("model"), "model", _PROJECT_MODEL)
    if "endpoint" in model:
        _nonempty(model["endpoint"], "model.endpoint", "a string")
    if "name" in model:
        _nonempty(model["name"], "model.name", "a string")
    if "temperature" in model:
        temperature = model["temperature"]
        if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
            raise ModelError(STUDIO_NAME, "model.temperature", "a number")
        model["temperature"] = float(temperature)
    prompts = _partial_block(obj.get("prompts"), "prompts", _PROJECT_PROMPTS)
    for key in list(prompts):
        value = prompts[key]
        if value is None:
            continue
        if not _repo_relative(value):
            raise ModelError(STUDIO_NAME, f"prompts.{key}", "a repo-relative path or null")
        prompts[key] = str(value).strip()
    paths = _partial_block(obj.get("paths"), "paths", _PROJECT_PATHS)
    if "extract_work_dir" in paths and not _repo_relative(paths["extract_work_dir"]):
        raise ModelError(STUDIO_NAME, "paths.extract_work_dir", "a relative directory")
    if "extract_work_dir" in paths:
        paths["extract_work_dir"] = str(paths["extract_work_dir"]).strip()
    document: dict = {}
    if model:
        document["model"] = model
    if prompts:
        document["prompts"] = prompts
    if paths:
        document["paths"] = paths
    if "researcher_mode" in obj:
        if not isinstance(obj["researcher_mode"], bool):
            raise ModelError(STUDIO_NAME, "researcher_mode", "true or false")
        document["researcher_mode"] = obj["researcher_mode"]
    return document


def save_user_studio(document: dict, home: Path | None = None) -> dict:
    written = validate_studio_config(document)
    path = user_studio_file(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, written)
    return written


def save_project_studio(repo: Path, document: dict) -> dict:
    written = validate_project_studio(document)
    write_json(studio_file(repo), written)
    return written


def effective_studio(repo: Path | None, home: Path | None = None) -> dict:
    """One value per field. A project key wins. The API key follows only a user endpoint."""
    user = load_user_studio(home)
    base = created_studio_config() if user is None else user
    origin = "built-in" if user is None else "user"
    project = load_project_studio(repo) or {}

    def pick(block: str, key: str) -> dict:
        current = project.get(block)
        if isinstance(current, dict) and key in current:
            return {"value": current[key], "source": "project"}
        return {"value": base[block][key], "source": origin}

    endpoint = pick("model", "endpoint")
    api_key = base["model"]["api_key"]
    send = endpoint["source"] == "user" and bool(api_key)
    if "researcher_mode" in project:
        mode = {"value": project["researcher_mode"], "source": "project"}
    else:
        mode = {"value": False, "source": "built-in"}
    return {
        "bind": {
            "host": {"value": base["bind"]["host"], "source": origin},
            "port": {"value": base["bind"]["port"], "source": origin},
        },
        "model": {
            "endpoint": endpoint,
            "name": pick("model", "name"),
            "temperature": pick("model", "temperature"),
            "api_key": {"value": api_key, "source": origin},
        },
        "prompts": {
            "interpret": pick("prompts", "interpret"),
            "discovery_hints": pick("prompts", "discovery_hints"),
        },
        "paths": {
            "temp_dir": {"value": base["paths"]["temp_dir"], "source": origin},
            "extract_work_dir": pick("paths", "extract_work_dir"),
            "keys_file": {"value": base["paths"]["keys_file"], "source": origin},
        },
        "researcher_mode": mode,
        "api_key_for_call": api_key if send else "",
    }


def listen_bind(cli_host: str | None, cli_port: int | None, *, home: Path | None = None) -> tuple[str, int]:
    chosen = effective_studio(None, home)["bind"]
    host = chosen["host"]["value"] if cli_host is None else cli_host
    port = chosen["port"]["value"] if cli_port is None else cli_port
    return host, port


def prompt_file(repo: Path, relative: str | None) -> Path | None:
    """A repo-relative prompt file. Null keeps the adapter prompt."""
    if relative is None:
        return None
    if not _repo_relative(relative):
        raise ModelError(STUDIO_NAME, "prompts", "a repo-relative path or null")
    path = (Path(repo) / relative).resolve()
    root = Path(repo).resolve()
    if path != root and root not in path.parents:
        raise ModelError(STUDIO_NAME, "prompts", "a file inside the repository")
    return path


def researcher_mode(repo: Path) -> bool:
    """True hides the Review column. Absent file or key keeps the column."""
    document = load_project_studio(repo)
    if document is None:
        return False
    return document.get("researcher_mode") is True


def user_from_form(form: dict) -> dict:
    def field(name: str) -> str:
        return _form_field(form, name)

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
            "researcher_mode": False,
        }
    )


def project_from_form(form: dict) -> dict:
    def field(name: str) -> str:
        return _form_field(form, name)

    def enabled(name: str) -> bool:
        return field(f"use_{name}") == "true"

    document: dict = {"researcher_mode": field("researcher_mode") == "true"}
    model = {}
    if enabled("model_endpoint"):
        model["endpoint"] = field("project_model_endpoint")
    if enabled("model_name"):
        model["name"] = field("project_model_name")
    if enabled("model_temperature"):
        try:
            model["temperature"] = float(field("project_model_temperature"))
        except ValueError:
            raise ModelError(STUDIO_NAME, "model.temperature", "a number")
    if model:
        document["model"] = model
    prompts = {}
    if enabled("prompt_interpret"):
        prompts["interpret"] = field("project_prompt_interpret") or None
    if enabled("prompt_discovery_hints"):
        prompts["discovery_hints"] = field("project_prompt_discovery_hints") or None
    if prompts:
        document["prompts"] = prompts
    if enabled("extract_work_dir"):
        document["paths"] = {"extract_work_dir": field("project_extract_work_dir")}
    return validate_project_studio(document)


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
        "researcher_mode": "true" if document.get("researcher_mode") is True else "",
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


def _form_field(form: dict, name: str) -> str:
    value = form.get(name)
    if isinstance(value, list):
        return (value or [""])[0].strip()
    return str(value or "").strip()


def _disallowed_project_fields(obj: dict) -> list[str]:
    names: list[str] = []
    for key in sorted(obj):
        if key == "bind":
            names.append("bind")
        elif key == "model" and isinstance(obj["model"], dict):
            names.extend(f"model.{field}" for field in sorted(obj["model"]) if field not in _PROJECT_MODEL)
        elif key == "prompts" and isinstance(obj["prompts"], dict):
            names.extend(
                f"prompts.{field}" for field in sorted(obj["prompts"]) if field not in _PROJECT_PROMPTS
            )
        elif key == "paths" and isinstance(obj["paths"], dict):
            names.extend(f"paths.{field}" for field in sorted(obj["paths"]) if field not in _PROJECT_PATHS)
        elif key not in _PROJECT_TOP:
            names.append(key)
        elif key in {"model", "prompts", "paths"} and not isinstance(obj[key], dict):
            names.append(key)
    return names


def _partial_block(value: object, name: str, allowed: set[str]) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ModelError(STUDIO_NAME, name, "object")
    return {key: value[key] for key in allowed if key in value}


def _nonempty(value: object, field: str, expected: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelError(STUDIO_NAME, field, expected)
