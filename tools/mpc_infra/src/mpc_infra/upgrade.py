def resolve_target_tag(explicit_tag: str | None = None) -> str:
    if explicit_tag:
        return explicit_tag
    return "latest-release-resolution-not-implemented"
