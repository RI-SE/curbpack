"""Args schemas from available_checks.json. This build runs exist and contents."""

from __future__ import annotations

import json
from pathlib import Path

from common.errors import CheckError, ModelError

IMPLEMENTED = {"exist", "contents"}
OPS = {">", ">=", "<", "<="}
PROBE_KINDS = {"size", "words", "headers", "token", "pattern", "placeholder"}
_REGISTRY_PATH = Path(__file__).with_name("available_checks.json")


def load_registry() -> dict:
    """The Check registry: id, command, and args JSON Schema."""
    document = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("checks"), list):
        raise CheckError("available_checks.json has no checks list")
    return document


def registry_entry(check: str) -> dict | None:
    for item in load_registry()["checks"]:
        if isinstance(item, dict) and item.get("id") == check:
            return item
    return None


def check_ids() -> list[str]:
    return [item["id"] for item in load_registry()["checks"] if isinstance(item, dict) and isinstance(item.get("id"), str)]


def validate_check_args(check: str, args: object) -> None:
    entry = registry_entry(check)
    if entry is None:
        raise CheckError(f"unknown check type {check!r}")
    schema = entry.get("args_schema")
    if not isinstance(schema, dict):
        raise CheckError(f"check {check!r} has no args schema")
    _validate_json_schema(args, schema, f"check {check}")
    if isinstance(args, dict):
        _safe_paths(args, check)
    if check == "contents":
        for index, probe in enumerate(args["probes"]):
            _validate_probe(probe, index)


def _reject_extra(args: dict, allowed: set[str], where: str) -> None:
    extra = sorted(set(args) - allowed)
    if extra:
        raise ModelError(where, extra[0], f"one of {sorted(allowed)}")


def _safe_rel(value: str, where: str, field: str) -> None:
    if value.startswith("/") or ".." in value.split("/"):
        raise ModelError(where, field, "a relative path inside the repository")


def _validate_json_schema(value: object, schema: dict, where: str) -> None:
    if "oneOf" in schema:
        matched = 0
        first_error: ModelError | None = None
        for option in schema["oneOf"]:
            try:
                _validate_json_schema(value, option, where)
            except ModelError as exc:
                if first_error is None:
                    first_error = exc
            else:
                matched += 1
        if matched != 1:
            if matched == 0 and first_error is not None:
                raise first_error
            raise ModelError(where, "args", "exactly one registered args shape")
        return
    if "const" in schema and "type" not in schema:
        if value != schema["const"]:
            raise ModelError(where, "value", repr(schema["const"]))
        return
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise ModelError(where, "args", "object")
        properties = schema.get("properties") or {}
        for field in schema.get("required") or []:
            if field not in value:
                raise ModelError(where, field, "present")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ModelError(where, extra[0], f"one of {sorted(properties)}")
        for key, item in value.items():
            if key in properties:
                _validate_json_schema(item, properties[key], f"{where}.{key}")
        return
    if expected == "array":
        if not isinstance(value, list):
            raise ModelError(where, "value", "list")
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ModelError(where, "value", f"at least {minimum} item")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_json_schema(item, item_schema, f"{where}[{index}]")
        return
    if expected == "string":
        if not isinstance(value, str):
            raise ModelError(where, "value", "string")
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ModelError(where, "value", "non-empty string")
        return
    if expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ModelError(where, "value", "integer")
        return
    if expected == "boolean":
        if not isinstance(value, bool):
            raise ModelError(where, "value", "boolean")
    if "const" in schema and value != schema["const"]:
        raise ModelError(where, "value", repr(schema["const"]))


def _safe_paths(args: dict, check: str) -> None:
    if isinstance(args.get("path"), str):
        _safe_rel(args["path"], check, "path")
    paths = args.get("paths")
    if isinstance(paths, list):
        for index, item in enumerate(paths):
            if isinstance(item, str):
                _safe_rel(item, check, f"paths[{index}]")


def _validate_probe(probe: object, index: int) -> None:
    where = f"contents.probes[{index}]"
    if not isinstance(probe, dict):
        raise ModelError("contents", f"probes[{index}]", "object")
    kind = probe.get("kind")
    if kind not in PROBE_KINDS:
        raise ModelError("contents", f"probes[{index}].kind", "size, words, headers, token, pattern, or placeholder")
    allowed = {
        "size": {"kind", "bytes", "op"},
        "words": {"kind", "n", "op"},
        "headers": {"kind", "headers"},
        "token": {"kind"},
        "pattern": {"kind", "pattern"},
        "placeholder": {"kind"},
    }[kind]
    _reject_extra(probe, allowed, where)
    if kind == "size":
        if not isinstance(probe.get("bytes"), int) or isinstance(probe.get("bytes"), bool):
            raise ModelError(where, "bytes", "integer")
        if probe.get("op") not in OPS:
            raise ModelError(where, "op", "> >= < or <=")
    elif kind == "words":
        if not isinstance(probe.get("n"), int) or isinstance(probe.get("n"), bool):
            raise ModelError(where, "n", "integer")
        if probe.get("op") not in OPS:
            raise ModelError(where, "op", "> >= < or <=")
    elif kind == "headers":
        headers = probe.get("headers")
        if not isinstance(headers, list) or not headers:
            raise ModelError(where, "headers", "non-empty list of strings")
        for header_index, header in enumerate(headers):
            if not isinstance(header, str) or not header:
                raise ModelError(where, f"headers[{header_index}]", "string")
    elif kind == "pattern":
        if not isinstance(probe.get("pattern"), str) or not probe["pattern"]:
            raise ModelError(where, "pattern", "regular expression string")
