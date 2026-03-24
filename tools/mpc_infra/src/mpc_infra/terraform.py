import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .constants import TERRAFORM_DIRS
from .models import NetworkName

RESOURCE_START_RE = re.compile(r"^(?P<addr>[^:]+): (?P<action>Creating|Modifying|Destroying)\.\.\.$")
RESOURCE_DONE_RE = re.compile(
    r"^(?P<addr>[^:]+): (?P<action>Creation complete|Modifications complete|Destruction complete)"
)
IMAGE_RE = re.compile(r'"image"\s*:\s*"(?P<image>[^"]+)"')
MODULE_SEGMENT_RE = re.compile(r"^module\.([A-Za-z0-9_-]+)(?:\[.*\])?$")
RESOURCE_SEGMENT_RE = re.compile(r"^(data\.)?([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)(?:\[.*\])?$")


@dataclass
class PlanChange:
    address: str
    action: str
    source_hint: str | None = None


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


def _action_label(actions: list[str]) -> str:
    normalized = list(actions)
    if normalized == ["create"]:
        return "create"
    if normalized == ["update"]:
        return "update"
    if normalized == ["delete"]:
        return "delete"
    if normalized == ["create", "delete"] or normalized == ["delete", "create"]:
        return "replace"
    return "/".join(normalized) or "unknown"


def _find_block_line(path: Path, patterns: list[re.Pattern[str]]) -> str | None:
    if not path.exists():
        return None
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        for pattern in patterns:
            if pattern.search(line):
                return f"{path.name}:{line_no}"
    return None


def _module_source_dir(workdir: Path, module_name: str) -> Path | None:
    patterns = [re.compile(rf'^module\s+"{re.escape(module_name)}"\s*\{{')]
    for tf_file in sorted(workdir.glob("*.tf")):
        text = tf_file.read_text().splitlines()
        for idx, line in enumerate(text, start=1):
            if patterns[0].search(line):
                for inner in text[idx: min(len(text), idx + 12)]:
                    match = re.search(r'source\s*=\s*"([^"]+)"', inner)
                    if match:
                        return (workdir / match.group(1)).resolve()
                return None
    return None


def source_hint_for_address(workdir: Path, address: str) -> str | None:
    segments = address.split(".")
    if not segments:
        return None

    if segments[0] == "module" and len(segments) >= 2:
        module_segment = f"module.{segments[1]}"
        module_match = MODULE_SEGMENT_RE.match(module_segment)
        if not module_match:
            return None
        module_name = module_match.group(1)
        top_level_hint = _find_block_line(workdir / "main.tf", [re.compile(rf'^module\s+"{re.escape(module_name)}"\s*\{{')])
        source_dir = _module_source_dir(workdir, module_name)
        remainder = ".".join(segments[2:])
        if source_dir and remainder:
            resource_match = RESOURCE_SEGMENT_RE.match(remainder)
            if resource_match:
                resource_type = resource_match.group(2)
                resource_name = resource_match.group(3)
                patterns = [
                    re.compile(rf'^(resource|data)\s+"{re.escape(resource_type)}"\s+"{re.escape(resource_name)}"\s*\{{'),
                    re.compile(rf'^output\s+"{re.escape(resource_name)}"\s*\{{'),
                ]
                for tf_file in sorted(source_dir.glob("*.tf")):
                    hint = _find_block_line(tf_file, patterns)
                    if hint:
                        return f"{top_level_hint} -> {source_dir.name}/{hint}" if top_level_hint else f"{source_dir.name}/{hint}"
        return top_level_hint

    resource_match = RESOURCE_SEGMENT_RE.match(address)
    if resource_match:
        resource_type = resource_match.group(2)
        resource_name = resource_match.group(3)
        patterns = [
            re.compile(rf'^(resource|data)\s+"{re.escape(resource_type)}"\s+"{re.escape(resource_name)}"\s*\{{'),
            re.compile(rf'^output\s+"{re.escape(resource_name)}"\s*\{{'),
        ]
        for tf_file in sorted(workdir.glob("*.tf")):
            hint = _find_block_line(tf_file, patterns)
            if hint:
                return hint
    return None


def plan_changes_summary(workdir: Path, plan_json: dict) -> list[PlanChange]:
    changes: list[PlanChange] = []
    for rc in plan_json.get("resource_changes", []):
        actions = rc.get("change", {}).get("actions", [])
        if not any(action in {"create", "update", "delete", "replace"} for action in actions):
            continue
        address = rc["address"]
        changes.append(
            PlanChange(
                address=address,
                action=_action_label(actions),
                source_hint=source_hint_for_address(workdir, address),
            )
        )
    return changes


def plan_summary(network_name: NetworkName, var_file: Path) -> str:
    workdir = terraform_workdir(network_name)
    init_result = terraform_init(workdir)
    if init_result.returncode != 0:
        raise RuntimeError(init_result.stderr.strip() or init_result.stdout.strip() or "terraform init failed")
    result = terraform_plan(workdir, var_file)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "terraform plan failed")
    return summarize_plan(result.stdout)


def planned_resource_addresses(network_name: NetworkName, var_file: Path) -> tuple[str, Path, list[str], list[PlanChange]]:
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
    return summarize_plan(result.stdout), plan_path, existing_addresses, plan_changes_summary(workdir, plan_json)
