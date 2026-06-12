import re


GARMENT_PATTERN = re.compile(
    r"(^|[_\s])(shirt|coat|skirt|dress|pants|panties)($|[_\s])",
    re.IGNORECASE,
)
REDUNDANT_QUALITY_PATTERN = re.compile(
    r"^(1girl|solo|masterpiece|best[_\s]+quality|high[_\s]+quality|"
    r"good[_\s]+quality|quality)$",
    re.IGNORECASE,
)
BREAST_SIZE_PATTERN = re.compile(
    r"^(small|medium|large|huge|gigantic|heavy|average)([_\s]+"
    r"(small|medium|large|huge|gigantic|heavy|average))*[_\s]+breasts?$",
    re.IGNORECASE,
)


def sanitize_scene_tags(raw_tags):
    if isinstance(raw_tags, list):
        candidates = [str(tag) for tag in raw_tags]
    else:
        candidates = str(raw_tags).split(",")

    sanitized = []
    seen = set()
    breast_size_added = False
    for candidate in candidates:
        tag = candidate.strip()
        if not tag or GARMENT_PATTERN.search(tag):
            continue
        if REDUNDANT_QUALITY_PATTERN.fullmatch(tag):
            continue
        if BREAST_SIZE_PATTERN.fullmatch(tag):
            if not breast_size_added:
                sanitized.append("small medium breasts")
                breast_size_added = True
            continue
        tag = re.sub(r"\s+", "_", tag)
        normalized = tag.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        sanitized.append(tag)
    return ", ".join(sanitized)


def merge_prompt_tags(*tag_groups):
    merged = []
    seen = set()
    for group in tag_groups:
        for candidate in str(group).split(","):
            tag = candidate.strip()
            if not tag:
                continue
            normalized = re.sub(r"[\s_]+", "_", tag).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(tag)
    return ", ".join(merged)


def build_scene_context(user_action, scene_tags, location, clothing, max_tags=20):
    tags = [
        tag.strip()
        for tag in sanitize_scene_tags(scene_tags).split(",")
        if tag.strip()
    ][:max_tags]
    action = re.sub(r"\s+", " ", str(user_action)).strip()[:100]
    parts = [
        f"location={str(location).strip() or 'unknown'}",
        f"clothing={str(clothing).strip() or 'unknown'}",
    ]
    if action:
        parts.append(f"previous_user_action={action}")
    if tags:
        parts.append(f"scene_tags={','.join(tags)}")
    return "; ".join(parts)
