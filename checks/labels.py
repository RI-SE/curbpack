"""Words a reviewer reads. The stored check id stays the implementation name."""

from __future__ import annotations

CAPTIONS = {
    "exist": "File is present",
    "contents": "File has the expected content",
    "text_forbid": "File must not contain this text",
    "anti_placeholder": "File is not a placeholder",
    "fresh": "File is recent enough",
    "owned": "Written by the claimed author",
    "dep_ban": "Banned package version",
}


def check_caption(entry: dict) -> str:
    """Human label for one saved check. The `check` field is unchanged."""
    label = str(entry.get("label") or "")
    if label in CAPTIONS:
        return CAPTIONS[label]
    check = str(entry.get("check") or "")
    if check == "contents":
        probes = (entry.get("args") or {}).get("probes") or []
        kinds = {item.get("kind") for item in probes if isinstance(item, dict)}
        if kinds == {"pattern"}:
            return CAPTIONS["text_forbid"]
        if kinds == {"placeholder"}:
            return CAPTIONS["anti_placeholder"]
    return CAPTIONS.get(check, check)
