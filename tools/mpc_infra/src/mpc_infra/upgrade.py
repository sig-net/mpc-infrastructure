import re
import subprocess
from pathlib import Path

from .constants import EXAMPLE_TFVARS, MPC_RELEASE_REPO
from .models import ReleaseContract, ReleaseSecretRequirement, StatusReport
from .terraform import current_deployed_image, terraform_workdir

IMAGE_LINE_RE = re.compile(r'^image\s*=\s*"(?P<image>[^"]+)"', re.MULTILINE)


def resolve_target_tag(explicit_tag: str | None = None) -> str:
    if explicit_tag:
        return explicit_tag
    result = subprocess.run(
        ["gh", "release", "view", "--repo", MPC_RELEASE_REPO, "--json", "tagName", "--jq", ".tagName"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed to resolve latest release tag")
    return result.stdout.strip()


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


def expected_image_from_examples(network_name: str) -> str:
    path = EXAMPLE_TFVARS[network_name]
    text = path.read_text()
    match = IMAGE_LINE_RE.search(text)
    if not match:
        raise RuntimeError(f"Could not find image in {path}")
    return match.group("image")


def status_against_latest_release(network_name: str = "testnet") -> StatusReport:
    latest = resolve_release_contract()
    deployed_image = current_deployed_image(terraform_workdir(network_name))
    deployed_version = deployed_image.rsplit(":", 1)[-1] if deployed_image else "unknown"
    expected_image = expected_image_from_examples(network_name)
    expected_version = expected_image.rsplit(":", 1)[-1]
    missing = [secret.secret_name_suggestion for secret in latest.required_secrets]
    upgrade_available = deployed_image != expected_image
    return StatusReport(
        deployed_version=deployed_version,
        latest_version=expected_version,
        upgrade_available=upgrade_available,
        missing_secrets=missing,
        recommended_action="Run mpc-infra upgrade" if upgrade_available else "Up to date",
    )
