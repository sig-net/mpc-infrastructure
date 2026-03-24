from datetime import datetime
from pathlib import Path

import typer

from .config import build_interactive_starter, default_config_path, load_config, save_config, write_starter_config
from .constants import DEFAULT_NETWORK_NAME, TERRAFORM_DIRS
from .gcloud import create_secret_interactively
from .render import write_generated_tfvars
from .terraform import (
    RESOURCE_DONE_RE,
    RESOURCE_START_RE,
    ensure_backend_bucket,
    plan_summary,
    planned_resource_addresses,
    summarize_apply,
    terraform_apply_stream,
    terraform_output_json,
    terraform_workdir,
)
from .ui import banner, error, info, render_outputs_table, resource_progress, select, step, success, warn
from .upgrade import build_target_image, resolve_release_contract, resolve_target_tag, status_against_latest_release
from .validate import validate_config_and_environment

app = typer.Typer(help="Partner deployment wrapper for MPC infrastructure.")


def _prompt_for_network() -> str:
    return select(
        "Select deployment network",
        choices=["testnet", "mainnet"],
        default="testnet",
    )


def _write_deploy_log(workdir: Path, lines: list[str]) -> Path:
    log_dir = workdir / ".mpc-infra" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    path.write_text("\n".join(lines) + "\n")
    return path


def _mark_failed_resource(resources: dict[str, dict[str, str]], detail: str) -> str | None:
    running = [name for name, state in resources.items() if state["status"] == "running"]
    target = running[-1] if running else None
    if target is None:
        pending = [name for name, state in resources.items() if state["status"] == "pending"]
        target = pending[0] if pending else None
    if target is not None:
        resources[target]["status"] = "failed"
        resources[target]["detail"] = detail
    return target


@app.command()
def init(
    path: Path | None = None,
    network_name: str | None = typer.Option(None, "--network", help="Deployment network: mainnet or testnet."),
    force: bool = False,
) -> None:
    config_path = path or default_config_path()
    if config_path.exists() and not force:
        raise typer.BadParameter(f"Config already exists at {config_path}. Use --force to overwrite.")

    selected_network = network_name
    if selected_network is None:
        selected_network = _prompt_for_network()
    if selected_network not in TERRAFORM_DIRS:
        raise typer.BadParameter("--network must be one of: mainnet, testnet")

    banner("mpc-infra init", f"Preparing a {selected_network} deployment config")
    project_id = typer.prompt("GCP project ID")
    bucket_default = f"multichain-terraform-{project_id.replace('_', '-') }"
    state_bucket = typer.prompt("Terraform state bucket", default=bucket_default)
    account_placeholder = "company.near" if selected_network == "mainnet" else "company.testnet"
    account_id = typer.prompt("Node account ID", default=account_placeholder)
    domain = None
    if selected_network == "mainnet":
        domain = typer.prompt("Node domain (for example: mpc.company.com)")

    with step("Writing starter config"):
        starter = build_interactive_starter(
            network_name=selected_network,  # type: ignore[arg-type]
            project_id=project_id,
            state_bucket=state_bucket,
            account_id=account_id,
            domain=domain,
        )
        write_starter_config(config_path, network_name=selected_network, starter=starter)  # type: ignore[arg-type]

    success(f"Wrote starter config to {config_path}")
    info(f"Selected network: {selected_network}")
    warn("Review the generated secret names before running validate.")


@app.command()
def validate(path: Path | None = None) -> None:
    config_path = path or default_config_path()
    banner("mpc-infra validate", f"Checking {config_path}")
    with step("Loading deployment config"):
        config = load_config(config_path)
    with step("Running GCP, secret, and Terraform preflight checks"):
        report = validate_config_and_environment(config)

    info(f"Deployment network: {config.network_name}")
    for finding in report.findings:
        if finding.level == "info":
            info(finding.message)
        elif finding.level == "warning":
            warn(finding.message)
        else:
            error(finding.message)

    if report.ok:
        success("Validation passed")
    else:
        error("Validation failed")
        raise typer.Exit(code=1)


@app.command()
def plan(path: Path | None = None) -> None:
    config_path = path or default_config_path()
    banner("mpc-infra plan", f"Planning from {config_path}")
    with step("Loading deployment config"):
        config = load_config(config_path)
    workdir = terraform_workdir(config.network_name)
    with step("Rendering generated Terraform inputs"):
        generated = write_generated_tfvars(config, workdir)
    with step("Aligning Terraform backend bucket"):
        ensure_backend_bucket(workdir, config.state_bucket)
    info(f"Deployment network: {config.network_name}")
    info(f"Generated Terraform inputs: {generated}")
    with step("Running terraform plan"):
        summary = plan_summary(config.network_name, generated)
    success(summary)


@app.command()
def deploy(path: Path | None = None) -> None:
    config_path = path or default_config_path()
    banner("mpc-infra deploy", f"Deploying from {config_path}")
    with step("Loading deployment config"):
        config = load_config(config_path)
    with step("Validating config and environment"):
        report = validate_config_and_environment(config)
    if not report.ok:
        for finding in report.findings:
            if finding.level == "info":
                info(finding.message)
            elif finding.level == "warning":
                warn(finding.message)
            else:
                error(finding.message)
        error("Deployment blocked by validation errors")
        raise typer.Exit(code=1)

    workdir = terraform_workdir(config.network_name)
    with step("Rendering generated Terraform inputs"):
        generated = write_generated_tfvars(config, workdir)
    with step("Aligning Terraform backend bucket"):
        ensure_backend_bucket(workdir, config.state_bucket)
    with step("Preparing deployment plan"):
        plan_text, plan_file, existing_addresses, planned_addresses = planned_resource_addresses(config.network_name, generated)
    info(plan_text)

    resources: dict[str, dict[str, str]] = {
        address: {"status": "complete", "detail": "already exists"} for address in existing_addresses
    }
    for address in planned_addresses:
        resources[address] = {"status": "pending", "detail": "waiting"}

    apply_lines: list[str] = []
    exit_code = 0
    failed_resource: str | None = None
    with resource_progress(resources) as refresh:
        for line in terraform_apply_stream(workdir, plan_file):
            if line.startswith("__EXIT_CODE__:"):
                exit_code = int(line.split(":", 1)[1])
                continue
            apply_lines.append(line)
            start_match = RESOURCE_START_RE.match(line)
            if start_match:
                addr = start_match.group("addr")
                resources.setdefault(addr, {"status": "pending", "detail": "discovered during apply"})
                resources[addr]["status"] = "running"
                resources[addr]["detail"] = start_match.group("action").lower()
                refresh()
                continue
            done_match = RESOURCE_DONE_RE.match(line)
            if done_match:
                addr = done_match.group("addr")
                resources.setdefault(addr, {"status": "pending", "detail": "discovered during apply"})
                resources[addr]["status"] = "complete"
                resources[addr]["detail"] = done_match.group("action")
                refresh()
                continue
            if line.startswith("Error:"):
                failed_resource = _mark_failed_resource(resources, line)
                refresh()

    log_path = _write_deploy_log(workdir, apply_lines)

    if exit_code != 0:
        error("Terraform apply failed")
        if failed_resource:
            error(f"Failed resource: {failed_resource}")
        error(f"Terraform log: {log_path}")
        for line in apply_lines[-40:]:
            if line.startswith("Error:") or line.startswith("with ") or line.startswith("on ") or "error" in line.lower():
                error(line)
        raise typer.Exit(code=1)

    outputs = terraform_output_json(workdir)
    success(summarize_apply(apply_lines))
    info(f"Terraform log: {log_path}")
    render_outputs_table(outputs)
    if config.network_name == "testnet" and "node_public_ip" in outputs:
        info(f"Testnet node endpoint(s): {outputs['node_public_ip']}")


@app.command()
def status(path: Path | None = None) -> None:
    config_path = path or default_config_path()
    banner("mpc-infra status", "Checking deployment posture")
    with step("Loading deployment config"):
        config = load_config(config_path)
    with step("Resolving deployment posture"):
        report = status_against_latest_release(config.network_name)
    info(f"Deployment network: {config.network_name}")
    info(f"Current deployed image tag: {report.deployed_version}")
    info(f"Current GitHub version: {config.current_github_version or report.current_github_version}")
    info(f"Latest GitHub version: {report.latest_github_version}")
    info(f"Target image: {report.target_image}")
    info(f"Upgrade available: {report.upgrade_available}")
    if report.missing_secrets:
        warn("Missing required secrets:")
        for secret in report.missing_secrets:
            info(secret)
    success(f"Recommended action: {report.recommended_action}")


@app.command()
def upgrade(
    path: Path | None = None,
    tag: str | None = typer.Option(default=None, help="Explicit GitHub release tag override."),
    create_missing_secrets: bool = typer.Option(default=False, help="Guide the operator through creating missing secrets for the target release."),
) -> None:
    config_path = path or default_config_path()
    banner("mpc-infra upgrade", "Resolving target release")
    with step("Loading deployment config"):
        config = load_config(config_path)
    with step("Resolving target release metadata"):
        target = resolve_target_tag(tag)
        contract = resolve_release_contract(tag)
        report = status_against_latest_release(config.network_name)
        target_image = build_target_image(config.network_name, target)
    current_image_tag = report.deployed_version
    current_github_version = config.current_github_version or "unknown"
    info(f"Deployment network: {config.network_name}")
    info(f"Current deployed image tag: {current_image_tag}")
    info(f"Current GitHub version: {current_github_version}")
    info(f"Latest GitHub version: {contract.version}")
    info(f"Target image: {target_image}")
    if not report.upgrade_available:
        success("Already on the latest release image")
        return

    for secret in contract.required_secrets:
        info(f"Required secret: {secret.key} -> suggested name {secret.secret_name_suggestion}")
        if create_missing_secrets:
            with step(f"Handling secret {secret.secret_name_suggestion}"):
                finding = create_secret_interactively(project_id=config.project_id, secret_name=secret.secret_name_suggestion, description=secret.description)
            if finding.level == "info":
                info(finding.message)
            elif finding.level == "warning":
                warn(finding.message)
            else:
                error(finding.message)

    with step("Updating deployment image and release metadata in config"):
        config.image = target_image
        config.latest_github_version = contract.version
        save_config(config_path, config)
    success(f"Updated config image to {config.image}")
    info(f"Recorded latest GitHub version as {config.latest_github_version}")
    info("Run `mpc-infra plan` to review the upgrade, then `mpc-infra deploy` to apply it.")
