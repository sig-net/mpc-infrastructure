from .models import ReleaseContract, ReleaseSecretRequirement, StatusReport


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


def status_against_latest_release() -> StatusReport:
    latest = resolve_release_contract()
    deployed_version = "deployed-version-not-implemented"
    missing = [secret.secret_name_suggestion for secret in latest.required_secrets]
    return StatusReport(
        deployed_version=deployed_version,
        latest_version=latest.version,
        upgrade_available=deployed_version != latest.version,
        missing_secrets=missing,
        recommended_action="Run mpc-infra upgrade" if deployed_version != latest.version else "Up to date",
    )
