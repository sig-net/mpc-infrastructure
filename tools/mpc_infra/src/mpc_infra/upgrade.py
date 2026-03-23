from .models import ReleaseContract, ReleaseSecretRequirement


def resolve_target_tag(explicit_tag: str | None = None) -> str:
    if explicit_tag:
        return explicit_tag
    return "latest-release-resolution-not-implemented"


def resolve_release_contract(explicit_tag: str | None = None) -> ReleaseContract:
    target = resolve_target_tag(explicit_tag)
    return ReleaseContract(
        version=target,
        image_tag=target,
        required_secrets=[
            ReleaseSecretRequirement(
                key="example_secret",
                secret_name_suggestion="example-secret-name",
                description="Example secret requirement placeholder",
            )
        ],
    )
