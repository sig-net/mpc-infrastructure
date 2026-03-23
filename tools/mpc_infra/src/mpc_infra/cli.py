from pathlib import Path

import typer

from .config import default_config_path, load_config, write_starter_config
from .constants import DEFAULT_NETWORK_NAME, TERRAFORM_DIRS
from .gcloud import create_secret_interactively
from .render import write_generated_tfvars
from .terraform import ensure_backend_bucket, plan_summary, terraform_workdir
from .upgrade import resolve_release_contract, resolve_target_tag, status_against_latest_release
from .validate import validate_config_and_environment

app = typer.Typer(help="Partner deployment wrapper for MPC infrastructure.")


@app.command()
def init(
    path: Path | None = None,
    network_name: str = typer.Option(DEFAULT_NETWORK_NAME, "--network", help="Deployment network: mainnet or testnet."),
    force: bool = False,
) -> None:
    """Write a starter partner config file."""
    config_path = path or default_config_path()
    if config_path.exists() and not force:
        raise typer.BadParameter(f"Config already exists at {config_path}. Use --force to overwrite.")
    if network_name not in TERRAFORM_DIRS:
        raise typer.BadParameter("--network must be one of: mainnet, testnet")
    write_starter_config(config_path, network_name=network_name)  # type: ignore[arg-type]
    typer.echo(f"Wrote starter config to {config_path}")
    typer.echo(f"Selected network: {network_name}")


@app.command()
def validate(path: Path | None = None) -> None:
    """Validate config and environment."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    report = validate_config_and_environment(config)
    typer.echo(f"Validation ok: {report.ok}")
    typer.echo(f"Deployment network: {config.network_name}")
    for finding in report.findings:
        typer.echo(f"[{finding.level}] {finding.message}")
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def plan(path: Path | None = None) -> None:
    """Render generated tfvars, align backend bucket, and run terraform plan."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    workdir = terraform_workdir(config.network_name)
    generated = write_generated_tfvars(config, workdir)
    ensure_backend_bucket(workdir, config.state_bucket)
    typer.echo(f"Deployment network: {config.network_name}")
    typer.echo(f"Generated Terraform inputs: {generated}")
    summary = plan_summary(config.network_name)
    typer.echo(summary)


@app.command()
def deploy(path: Path | None = None) -> None:
    """Render generated tfvars and summarize the Terraform deploy path."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    workdir = terraform_workdir(config.network_name)
    generated = write_generated_tfvars(config, workdir)
    typer.echo(f"Generated Terraform inputs: {generated}")
    typer.echo("Terraform deploy integration is not implemented yet.")


@app.command()
def status() -> None:
    """Show deployment/version posture against the latest release."""
    report = status_against_latest_release()
    typer.echo(f"Deployed version: {report.deployed_version}")
    typer.echo(f"Latest release: {report.latest_version}")
    typer.echo(f"Upgrade available: {report.upgrade_available}")
    if report.missing_secrets:
        typer.echo("Missing required secrets:")
        for secret in report.missing_secrets:
            typer.echo(f"- {secret}")
    typer.echo(f"Recommended action: {report.recommended_action}")


@app.command()
def upgrade(
    tag: str | None = typer.Option(default=None, help="Explicit image tag override."),
    create_missing_secrets: bool = typer.Option(default=False, help="Guide the operator through creating missing secrets for the target release."),
) -> None:
    """Resolve the target image tag and release contract for upgrades."""
    target = resolve_target_tag(tag)
    contract = resolve_release_contract(tag)
    typer.echo(f"Target upgrade tag: {target}")
    typer.echo(f"Target release contract version: {contract.version}")
    for secret in contract.required_secrets:
        typer.echo(f"Required secret: {secret.key} -> suggested name {secret.secret_name_suggestion}")
        if create_missing_secrets:
            finding = create_secret_interactively(project_id="<project-from-config>", secret_name=secret.secret_name_suggestion, description=secret.description)
            typer.echo(f"[{finding.level}] {finding.message}")


if __name__ == "__main__":
    app()
