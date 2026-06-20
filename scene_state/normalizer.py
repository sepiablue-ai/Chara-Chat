import hashlib
import json
import os
import re
from copy import deepcopy


DEFAULT_REGISTRY = {"locations": {}, "clothing": {}}


def slugify_key(value, prefix):
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    if text:
        return text[:80]
    digest = hashlib.sha1(str(value or prefix).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def normalize_tags(value):
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    value = str(value or "")
    value = re.sub(r"\s+", " ", value).strip(" ,")
    return value[:500]


def normalize_confidence(value, default=0.0):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(1.0, confidence))


class DynamicSceneRegistry:
    def __init__(self, path):
        self.path = path
        self.data = deepcopy(DEFAULT_REGISTRY)
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data["locations"].update(loaded.get("locations", {}))
                self.data["clothing"].update(loaded.get("clothing", {}))
        except Exception as exc:
            print(f"[STATE] dynamic registry load failed: {exc}")

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_tags(self, kind, key):
        bucket = self.data.get(kind, {})
        item = bucket.get(str(key or ""))
        if not isinstance(item, dict):
            return ""
        return normalize_tags(item.get("image_tags", ""))

    def match_text(self, text):
        haystack = str(text or "").lower()
        matches = {"locations": [], "clothing": []}
        for kind in ("locations", "clothing"):
            for key, item in self.data.get(kind, {}).items():
                if not isinstance(item, dict):
                    continue
                probes = [key, item.get("label_ja", "")]
                probes.extend(item.get("aliases", []))
                best = 0
                for probe in probes:
                    probe = str(probe or "").strip().lower()
                    if len(probe) < 3:
                        continue
                    if probe in haystack:
                        best = max(best, len(probe))
                if best:
                    matches[kind].append((best, key, item))
        for kind in matches:
            matches[kind].sort(reverse=True, key=lambda row: row[0])
        return matches

    def register(self, kind, key, label_ja="", image_tags="", aliases=None):
        key = slugify_key(key, "location" if kind == "locations" else "clothing")
        image_tags = normalize_tags(image_tags)
        if not image_tags:
            return key
        bucket = self.data.setdefault(kind, {})
        existing = bucket.get(key, {})
        merged_aliases = list(existing.get("aliases", []))
        for alias in aliases or []:
            alias = str(alias).strip()
            if alias and alias not in merged_aliases:
                merged_aliases.append(alias)
        if existing:
            bucket[key] = {
                "label_ja": str(existing.get("label_ja") or label_ja).strip(),
                "image_tags": normalize_tags(existing.get("image_tags") or image_tags),
                "aliases": merged_aliases[:12],
            }
        else:
            bucket[key] = {
                "label_ja": str(label_ja or "").strip(),
                "image_tags": image_tags,
                "aliases": merged_aliases[:12],
            }
        self.save()
        return key


def normalize_dynamic_candidate(raw, current_state):
    if not isinstance(raw, dict):
        return None

    location = raw.get("location", {})
    clothing = raw.get("clothing", {})
    if not isinstance(location, dict):
        location = {}
    if not isinstance(clothing, dict):
        clothing = {}

    loc_key = slugify_key(location.get("key") or location.get("label_ja"), "location")
    clothing_key = slugify_key(
        clothing.get("key") or clothing.get("label_ja"), "clothing"
    )
    clothing_tags = normalize_tags(clothing.get("image_tags", "")).lower()
    negative_markers = {
        "gloves": ("no gloves", "without gloves"),
        "sleeve_covers": ("no sleeve cover", "without sleeve cover", "no arm cover"),
        "helmet": ("no helmet", "without helmet"),
        "mask": ("no mask", "without mask"),
        "poncho": ("no poncho", "without poncho"),
        "veil": ("no veil", "without veil"),
    }
    for marker, suffix in (
        ("gloves", "gloves"),
        ("sleeve cover", "sleeve_covers"),
        ("arm cover", "sleeve_covers"),
        ("helmet", "helmet"),
        ("mask", "mask"),
        ("poncho", "poncho"),
        ("veil", "veil"),
    ):
        if any(negative in clothing_tags for negative in negative_markers[suffix]):
            clothing_key = re.sub(rf"_{re.escape(suffix)}(?=_|$)", "", clothing_key)
            continue
        if marker in clothing_tags and suffix not in clothing_key:
            clothing_key = f"{clothing_key}_{suffix}"
    loc_conf = normalize_confidence(location.get("confidence"), 0.0)
    clothing_conf = normalize_confidence(clothing.get("confidence"), 0.0)
    loc_changed = bool(location.get("changed", False))
    clothing_changed = bool(clothing.get("changed", False))

    if loc_key == slugify_key(current_state.get("location"), "location"):
        loc_changed = False
    if clothing_key == slugify_key(current_state.get("clothing"), "clothing"):
        clothing_changed = False

    return {
        "location": loc_key if loc_changed and loc_conf >= 0.55 else None,
        "clothing": clothing_key if clothing_changed and clothing_conf >= 0.55 else None,
        "location_changed": loc_changed and loc_conf >= 0.55,
        "clothing_changed": clothing_changed and clothing_conf >= 0.55,
        "reason": str(raw.get("reason", "")).strip(),
        "tag_hint": normalize_tags(
            ", ".join(
                part
                for part in (
                    location.get("image_tags", ""),
                    clothing.get("image_tags", ""),
                    raw.get("additional_image_tags", ""),
                )
                if part
            )
        ),
        "location_confidence": loc_conf,
        "clothing_confidence": clothing_conf,
        "source": "dynamic",
        "registry": {
            "location": {
                "key": loc_key,
                "label_ja": location.get("label_ja", ""),
                "image_tags": normalize_tags(location.get("image_tags", "")),
                "aliases": location.get("aliases", []),
            },
            "clothing": {
                "key": clothing_key,
                "label_ja": clothing.get("label_ja", ""),
                "image_tags": normalize_tags(clothing.get("image_tags", "")),
                "aliases": clothing.get("aliases", []),
            },
        },
    }
