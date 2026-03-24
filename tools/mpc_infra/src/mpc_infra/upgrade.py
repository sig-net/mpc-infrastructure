import json
import subprocess
from dataclasses import dataclass

from .constants import MPC_RELEASE_REPO, PROFILE_DEFAULTS
from .models import ReleaseContract, ReleaseSecretRequirement, StatusReport
from .terraform import current_deployed_image, terraform_workdir


@dataclass
class GitHubReleaseInfo:
    version: str
    commitish: str
    commit_sha: str


def _run_gh_json(args: list[str]) -> dict:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh command failed")
    return json.loads(result.stdout)


def resolve_commit_sha(ref: str) -> str:
    ref_data = _run_gh_json(["api", f"repos/{MPC_RELEASE_REPO}/git/ref/{ref}"])
    obj = ref_data["object"]
    if obj["type"] == "commit":
        return obj["sha"]
    if obj["type"] == "tag":
        tag_data = _run_gh_json(["api", f"repos/{MPC_RELEASE_REPO}/git/tags/{obj['sha']}"])
        tagged = tag_data["object"]
        if tagged["type"] != "commit":
            raise RuntimeError(f"Unsupported annotated tag target type: {tagged['type']}")
        return tagged["sha"]
    raise RuntimeError(f"Unsupported ref target type: {obj['type']}")


def resolve_latest_release(explicit_tag: str | None = None) -> GitHubReleaseInfo:
    if explicit_tag:
        release = _run_gh_json(["api", f"repos/{MPC_RELEASE_REPO}/releases/tags/{explicit_tag}"])
    else:
        release = _run_gh_json(["api", f"repos/{MPC_RELEASE_REPO}/releases/latest"])

    version = release["tag_name"]
    commit_sha = resolve_commit_sha(f"tags/{version}")
    return GitHubReleaseInfo(
        version=version,
        commitish=release.get("target_commitish") or commit_sha,
        commit_sha=commit_sha,
    )


def resolve_target_tag(explicit_tag: str | None = None) -> str:
    return resolve_latest_release(explicit_tag).commit_sha


def resolve_release_contract(explicit_tag: str | None = None) -> ReleaseContract:
    release = resolve_latest_release(explicit_tag)
    return ReleaseContract(
        version=release.version,
        image_tag=release.commit_sha,
        required_secrets=[
            ReleaseSecretRequirement(
                key="example_secret",
                secret_name_suggestion="example-secret-name",
                description="Example secret requirement placeholder",
            )
        ],
    )


def build_target_image(network_name: str, image_tag: str) -> str:
    repository = PROFILE_DEFAULTS[network_name]["image_repository"]
    return f"{repository}:{image_tag}"


def deployed_image_tag(image: str | None) -> str:
    if not image or ":" not in image:
        return "unknown"
    return image.rsplit(":", 1)[-1]


def status_against_latest_release(network_name: str = "testnet") -> StatusReport:
    latest = resolve_release_contract()
    deployed_image = current_deployed_image(terraform_workdir(network_name))
    target_image = build_target_image(network_name, latest.image_tag)
    missing = [secret.secret_name_suggestion for secret in latest.required_secrets]
    upgrade_available = deployed_image != target_image
    return StatusReport(
        deployed_version=deployed_image_tag(deployed_image),
        latest_version=latest.version,
        current_github_version="unknown",
        latest_github_version=latest.version,
        target_image=target_image,
        upgrade_available=upgrade_available,
        missing_secrets=missing,
        recommended_action="Run mpc-infra upgrade" if upgrade_available else "Up to date",
    )
