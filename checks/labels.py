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


_SHORT = {
    "exist": "Exists",
    "contents": "Contents",
    "text_forbid": "Forbidden text",
    "anti_placeholder": "Anti-placeholder",
    "fresh": "Fresh",
    "owned": "Owned",
    "dep_ban": "Banned",
}


def check_short_label(entry: dict) -> str:
    """Compact label for the same check `check_caption` describes."""
    caption = check_caption(entry)
    for key, sentence in CAPTIONS.items():
        if caption == sentence:
            return _SHORT[key]
    return str(entry.get("check") or "") or caption


def check_detail(entry: dict) -> dict:
    """Caption plus the arguments a person reads. File names are left out."""
    args = entry.get("args") if isinstance(entry.get("args"), dict) else {}
    fields: list[dict] = []
    for probe in args.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        kind = probe.get("kind")
        if kind == "size" and probe.get("bytes") is not None:
            fields.append({"label": "Min bytes", "value": str(probe["bytes"])})
        elif kind == "words" and probe.get("n") is not None:
            fields.append({"label": "Min words", "value": str(probe["n"])})
        elif kind == "headers":
            headers = [str(item) for item in probe.get("headers") or [] if str(item).strip()]
            if headers:
                fields.append({"label": "Require headers", "value": ", ".join(headers)})
        elif kind == "pattern":
            fields.append({"label": "Pattern", "value": str(probe.get("pattern") or "")})
        elif kind == "token":
            fields.append({"label": "Bind repo token", "value": "yes"})
    for key, label in (
        ("package", "Package"),
        ("banned_versions", "Banned versions"),
        ("max_age_days", "Max age days"),
        ("since_ref", "Since ref"),
        ("email", "Require git author email"),
        ("name", "Require git author name"),
    ):
        value = args.get(key)
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        fields.append({"label": label, "value": str(value)})
    if args.get("bind_repo_token") is True:
        fields.append({"label": "Bind repo token", "value": "yes"})
    return {"caption": check_caption(entry), "fields": fields}
