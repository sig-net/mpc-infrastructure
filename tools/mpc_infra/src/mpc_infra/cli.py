from pathlib import Path

import typer

from .config import default_config_path, load_config, write_starter_config
from .constants import TERRAFORM_PARTNER_MAINNET_DIR
from .render import write_generated_tfvars
from .terraform import deploy_summary, plan_summary
from .upgrade import resolve_target_tag
from .validate import validate_config_and_environment

app = typer.Typer(help="Partner deployment wrapper for MPC infrastructure.")


@app.command()
def init(path: Path | None = None) -> None:
    """Write a starter partner config file."""
    config_path = path or default_config_path()
    write_starter_config(config_path)
    typer.echo(f"Wrote starter config to {config_path}")


@app.command()
def validate(path: Path | None = None) -> None:
    """Validate config and environment."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    report = validate_config_and_environment(config.project_id)
    typer.echo(f"Validation ok: {report.ok}")
    for finding in report.findings:
        typer.echo(f"[{finding.level}] {finding.message}")


@app.command()
def plan(path: Path | None = None) -> None:
    """Render generated tfvars and summarize the Terraform plan path."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    generated = write_generated_tfvars(config, TERRAFORM_PARTNER_MAINNET_DIR)
    typer.echo(f"Generated Terraform inputs: {generated}")
    typer.echo(plan_summary())


@app.command()
def deploy(path: Path | None = None) -> None:
    """Render generated tfvars and summarize the Terraform deploy path."""
    config_path = path or default_config_path()
    config = load_config(config_path)
    generated = write_generated_tfvars(config, TERRAFORM_PARTNER_MAINNET_DIR)
    typer.echo(f"Generated Terraform inputs: {generated}")
    typer.echo(deploy_summary())


@app.command()
def status() -> None:
    """Show the intended Terraform working directory for status inspection."""
    typer.echo(f"Terraform working directory: {TERRAFORM_PARTNER_MAINNET_DIR}")


@app.command()
def upgrade(tag: str | None = typer.Option(default=None, help="Explicit image tag override.")) -> None:
    """Resolve the target image tag for upgrades."""
    target = resolve_target_tag(tag)
    typer.echo(f"Target upgrade tag: {target}")


if __name__ == "__main__":
    app()
