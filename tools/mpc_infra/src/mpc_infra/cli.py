from pathlib import Path

import typer

from .config import build_interactive_starter, default_config_path, load_config, write_starter_config
from .constants import DEFAULT_NETWORK_NAME, TERRAFORM_DIRS
from .gcloud import create_secret_interactively
from .render import write_generated_tfvars
from .terraform import ensure_backend_bucket, plan_summary, terraform_workdir
from .ui import banner, error, info, select, step, success, warn
from .upgrade import resolve_release_contract, resolve_target_tag, status_against_latest_release
from .validate import validate_config_and_environment

app = typer.Typer(help="Partner deployment wrapper for MPC infrastructure.")


def _prompt_for_network() -> str:
    return select(
        "Select deployment network",
        choices=["testnet", "mainnet"],
        default="testnet",
    )


@app.command()
def init(
    path: Path | None = None,
    network_name: str | None = typer.Option(None, "--network", help="Deployment network: mainnet or testnet."),
    force: bool = False,
) -> None:
    """Write a starter partner config file."""
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
    bucket_default = f"multichain-terraform-{project_id.replace('_', '-')}"
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
    """Validate config and environment."""
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
    """Render generated tfvars, align backend bucket, and run terraform plan."""
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
    """Render generated tfvars and summarize the Terraform deploy path."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    workdir = terraform_workdir(config.network_name)
    generated = write_generated_tfvars(config, workdir)
    info(f"Generated Terraform inputs: {generated}")
    warn("Terraform deploy integration is not implemented yet.")


@app.command()
def status() -> None:
    """Show deployment/version posture against the latest release."""
    banner("mpc-infra status", "Checking deployment posture")
    with step("Resolving deployment posture"):
        report = status_against_latest_release()
    info(f"Deployed version: {report.deployed_version}")
    info(f"Latest release: {report.latest_version}")
    info(f"Upgrade available: {report.upgrade_available}")
    if report.missing_secrets:
        warn("Missing required secrets:")
        for secret in report.missing_secrets:
            info(secret)
    success(f"Recommended action: {report.recommended_action}")


@app.command()
def upgrade(
    tag: str | None = typer.Option(default=None, help="Explicit image tag override."),
    create_missing_secrets: bool = typer.Option(default=False, help="Guide the operator through creating missing secrets for the target release."),
) -> None:
    """Resolve the target image tag and release contract for upgrades."""
    banner("mpc-infra upgrade", "Resolving target release")
    with step("Resolving target release metadata"):
        target = resolve_target_tag(tag)
        contract = resolve_release_contract(tag)
    info(f"Target upgrade tag: {target}")
    info(f"Target release contract version: {contract.version}")
    for secret in contract.required_secrets:
        info(f"Required secret: {secret.key} -> suggested name {secret.secret_name_suggestion}")
        if create_missing_secrets:
            with step(f"Handling secret {secret.secret_name_suggestion}"):
                finding = create_secret_interactively(project_id="<project-from-config>", secret_name=secret.secret_name_suggestion, description=secret.description)
            if finding.level == "info":
                info(finding.message)
            elif finding.level == "warning":
                warn(finding.message)
            else:
                error(finding.message)
