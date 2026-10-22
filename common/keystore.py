"""Local demo keys. An Ed25519 key bound to a display name, not an X.509 certificate."""

from __future__ import annotations

import base64
from pathlib import Path

from common.jsonio import read_json, write_json
from common.signing import generate_keypair


def _load(path: Path) -> dict:
    if not path.is_file():
        return {"keys": []}
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("keys"), list):
        raise ValueError(f"{path}: expected a keys list")
    return data


def load_or_create_key(directory: Path, name: str) -> tuple[bytes, bytes]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "keys.json"
    data = _load(path)
    for item in data["keys"]:
        if item.get("name") == name:
            return base64.b64decode(item["private"]), base64.b64decode(item["public"])
    private, public = generate_keypair()
    data["keys"].append(
        {
            "name": name,
            "private": base64.b64encode(private).decode("ascii"),
            "public": base64.b64encode(public).decode("ascii"),
        }
    )
    write_json(path, data)
    return private, public


def trust_store(directory: Path) -> dict[str, bytes]:
    data = _load(directory / "keys.json")
    trust = {}
    for item in data["keys"]:
        if isinstance(item.get("name"), str) and isinstance(item.get("public"), str):
            trust[item["name"]] = base64.b64decode(item["public"])
    return trust
