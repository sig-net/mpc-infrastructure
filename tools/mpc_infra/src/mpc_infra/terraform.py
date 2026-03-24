import json
import re
import subprocess
from pathlib import Path

from .constants import TERRAFORM_DIRS
from .models import NetworkName

RESOURCE_START_RE = re.compile(r"^(?P<addr>[^:]+): (?P<action>Creating|Modifying|Destroying)\.\.\.$")
RESOURCE_DONE_RE = re.compile(
    r"^(?P<addr>[^:]+): (?P<action>Creation complete|Modifications complete|Destruction complete)"
)
IMAGE_RE = re.compile(r'"image"\s*:\s*"(?P<image>[^"]+)"')


def terraform_workdir(network_name: NetworkName) -> Path:
    return TERRAFORM_DIRS[network_name]


def ensure_backend_bucket(workdir: Path, bucket: str) -> None:
    resources_tf = workdir / "resources.tf"
    text = resources_tf.read_text()
    updated = re.sub(r'bucket\s*=\s*"[^"]+"', f'bucket = "{bucket}"', text, count=1)
    resources_tf.write_text(updated)


def terraform_init(workdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["terraform", "init", "-input=false"], cwd=workdir, capture_output=True, text=True)


def terraform_plan(workdir: Path, var_file: Path, out_plan: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["terraform", "plan", "-input=false", "-no-color", f"-var-file={var_file.name}"]
    if out_plan is not None:
        cmd.append(f"-out={out_plan.name}")
    return subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)


def terraform_show_plan_json(workdir: Path, plan_file: Path) -> dict:
    result = subprocess.run(
        ["terraform", "show", "-json", plan_file.name], cwd=workdir, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform show failed")
    return json.loads(result.stdout)


def terraform_state_pull(workdir: Path) -> dict | None:
    result = subprocess.run(["terraform", "state", "pull"], cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def terraform_state_list(workdir: Path) -> list[str]:
    result = subprocess.run(["terraform", "state", "list"], cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _walk_resources(module: dict) -> list[dict]:
    resources = list(module.get("resources", []))
    for child in module.get("child_modules", []):
        resources.extend(_walk_resources(child))
    return resources


def current_deployed_image(workdir: Path) -> str | None:
    state = terraform_state_pull(workdir)
    if not state:
        return None
    values = state.get("values", {})
    root = values.get("root_module", {})
    for resource in _walk_resources(root):
        values = resource.get("values", {})
        metadata = values.get("metadata") or values.get("metadata_startup_script")
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata)
        else:
            metadata_str = str(metadata or "")
        match = IMAGE_RE.search(metadata_str)
        if match:
            return match.group("image")
    return None


def deployed_instance_names(workdir: Path) -> list[str]:
    try:
        outputs = terraform_output_json(workdir)
    except RuntimeError:
        return []
    raw = outputs.get("instance_names")
    if not isinstance(raw, list):
        return []
    return [name for name in raw if isinstance(name, str) and name]


def terraform_apply_stream(workdir: Path, plan_file: Path):
    proc = subprocess.Popen(
        ["terraform", "apply", "-input=false", "-no-color", "-auto-approve", plan_file.name],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        yield line.rstrip("\n")
    proc.wait()
    yield f"__EXIT_CODE__:{proc.returncode}"


def terraform_output_json(workdir: Path) -> dict[str, object]:
    result = subprocess.run(["terraform", "output", "-json"], cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform output failed")
    raw = json.loads(result.stdout)
    return {key: value.get("value") for key, value in raw.items()}


def summarize_plan(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("Plan:") or line.startswith("No changes."):
            return line.strip()
    return "Terraform plan completed; summary line not found."


def summarize_apply(stdout_lines: list[str]) -> str:
    for line in reversed(stdout_lines):
        if line.startswith("Apply complete!") or line.startswith("No changes."):
            return line.strip()
    return "Terraform apply completed; summary line not found."


def plan_summary(network_name: NetworkName, var_file: Path) -> str:
    workdir = terraform_workdir(network_name)
    init_result = terraform_init(workdir)
    if init_result.returncode != 0:
        raise RuntimeError(init_result.stderr.strip() or init_result.stdout.strip() or "terraform init failed")
    result = terraform_plan(workdir, var_file)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform plan failed")
    return summarize_plan(result.stdout)


def planned_resource_addresses(network_name: NetworkName, var_file: Path) -> tuple[str, Path, list[str], list[str]]:
    workdir = terraform_workdir(network_name)
    init_result = terraform_init(workdir)
    if init_result.returncode != 0:
        raise RuntimeError(init_result.stderr.strip() or init_result.stdout.strip() or "terraform init failed")
    existing_addresses = terraform_state_list(workdir)
    plan_path = workdir / "generated.tfplan"
    result = terraform_plan(workdir, var_file, out_plan=plan_path)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform plan failed")
    plan_json = terraform_show_plan_json(workdir, plan_path)
    addresses: list[str] = []
    for rc in plan_json.get("resource_changes", []):
        actions = rc.get("change", {}).get("actions", [])
        if any(action in {"create", "update", "delete", "replace"} for action in actions):
            addresses.append(rc["address"])
    return summarize_plan(result.stdout), plan_path, existing_addresses, addresses
