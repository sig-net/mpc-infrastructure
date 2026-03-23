import json
import shutil
import subprocess
from pathlib import Path

from .constants import REQUIRED_BINARIES, REQUIRED_GCP_APIS
from .models import PartnerMainnetConfig, ValidationFinding


class GCloudError(RuntimeError):
    pass


def _run_json(cmd: list[str]) -> object:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GCloudError(proc.stderr.strip() or proc.stdout.strip() or "command failed")
    return json.loads(proc.stdout or "null")


def _run_text(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GCloudError(proc.stderr.strip() or proc.stdout.strip() or "command failed")
    return proc.stdout.strip()


def _secret_names(config: PartnerMainnetConfig) -> list[str]:
    names: list[str] = []
    for node in config.nodes:
        names.extend(
            [
                node.secrets.account_sk,
                node.secrets.cipher_sk,
                node.secrets.sign_sk,
                node.secrets.sk_share,
                node.secrets.eth_account_sk,
                node.secrets.eth_consensus_rpc,
                node.secrets.eth_execution_rpc,
                node.secrets.sol_account_sk,
                node.secrets.sol_rpc_http,
                node.secrets.sol_rpc_ws,
            ]
        )
        if node.secrets.hydration_rpc_ws:
            names.append(node.secrets.hydration_rpc_ws)
        if node.secrets.hydration_signer_uri:
            names.append(node.secrets.hydration_signer_uri)
    return sorted(set(names))


def validate_gcloud_environment(config: PartnerMainnetConfig) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for binary in REQUIRED_BINARIES:
        if shutil.which(binary):
            findings.append(ValidationFinding(level="info", message=f"Found required binary: {binary}"))
        else:
            findings.append(ValidationFinding(level="error", message=f"Missing required binary: {binary}"))

    if any(f.level == "error" for f in findings):
        return findings

    try:
        account = _run_text(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
        findings.append(ValidationFinding(level="info", message=f"Active gcloud account: {account or 'none'}"))
    except GCloudError as exc:
        findings.append(ValidationFinding(level="error", message=f"Unable to determine active gcloud account: {exc}"))
        return findings

    try:
        project = _run_json(["gcloud", "projects", "describe", config.project_id, "--format=json"])
        findings.append(ValidationFinding(level="info", message=f"Found GCP project: {project['projectId']}"))
    except Exception as exc:
        findings.append(ValidationFinding(level="error", message=f"Unable to access GCP project {config.project_id}: {exc}"))
        return findings

    try:
        enabled_services = _run_json([
            "gcloud",
            "services",
            "list",
            "--enabled",
            "--project",
            config.project_id,
            "--format=json",
        ])
        enabled_names = {svc["config"]["name"] for svc in enabled_services}
        for api in REQUIRED_GCP_APIS:
            if api in enabled_names:
                findings.append(ValidationFinding(level="info", message=f"Required API enabled: {api}"))
            else:
                findings.append(ValidationFinding(level="error", message=f"Required API not enabled: {api}"))
    except Exception as exc:
        findings.append(ValidationFinding(level="error", message=f"Unable to list enabled APIs: {exc}"))

    try:
        _run_json([
            "gcloud",
            "storage",
            "buckets",
            "describe",
            f"gs://{config.state_bucket}",
            "--format=json",
        ])
        findings.append(ValidationFinding(level="info", message=f"Terraform state bucket found: gs://{config.state_bucket}"))
    except Exception as exc:
        findings.append(ValidationFinding(level="error", message=f"Terraform state bucket missing or inaccessible: gs://{config.state_bucket} ({exc})"))

    try:
        secret_list = _run_json([
            "gcloud",
            "secrets",
            "list",
            "--project",
            config.project_id,
            "--format=json",
        ])
        existing = {secret["name"].split("/")[-1] for secret in secret_list}
        for secret_name in _secret_names(config):
            if secret_name in existing:
                findings.append(ValidationFinding(level="info", message=f"Secret found: {secret_name}"))
            else:
                findings.append(ValidationFinding(level="error", message=f"Missing required secret: {secret_name}"))
    except Exception as exc:
        findings.append(ValidationFinding(level="error", message=f"Unable to list secrets in project {config.project_id}: {exc}"))

    return findings


def create_secret_interactively(project_id: str, secret_name: str, description: str) -> ValidationFinding:
    return ValidationFinding(
        level="info",
        message=(
            f"Secret creation flow for {secret_name} in project {project_id} is not implemented yet "
            f"({description})."
        ),
    )
