import re
import subprocess
from pathlib import Path

from .constants import TERRAFORM_DIRS
from .models import NetworkName


def terraform_workdir(network_name: NetworkName) -> Path:
    return TERRAFORM_DIRS[network_name]


def ensure_backend_bucket(workdir: Path, bucket: str) -> None:
    resources_tf = workdir / "resources.tf"
    text = resources_tf.read_text()
    updated = re.sub(r'bucket\s*=\s*"[^"]+"', f'bucket = "{bucket}"', text, count=1)
    resources_tf.write_text(updated)


def terraform_init(workdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["terraform", "init", "-input=false"], cwd=workdir, capture_output=True, text=True)


def terraform_plan(workdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["terraform", "plan", "-input=false", "-no-color"], cwd=workdir, capture_output=True, text=True)


def summarize_plan(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("Plan:") or line.startswith("No changes."):
            return line.strip()
    return "Terraform plan completed; summary line not found."


def plan_summary(network_name: NetworkName) -> str:
    workdir = terraform_workdir(network_name)
    init_result = terraform_init(workdir)
    if init_result.returncode != 0:
        raise RuntimeError(init_result.stderr.strip() or init_result.stdout.strip() or "terraform init failed")
    result = terraform_plan(workdir)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform plan failed")
    return summarize_plan(result.stdout)


def deploy_summary() -> str:
    return "Terraform deploy integration is not implemented yet."
