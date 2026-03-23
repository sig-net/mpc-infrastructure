from pathlib import Path

from .constants import TERRAFORM_PARTNER_MAINNET_DIR


def terraform_workdir() -> Path:
    return TERRAFORM_PARTNER_MAINNET_DIR


def plan_summary() -> str:
    return "Terraform plan integration is not implemented yet."


def deploy_summary() -> str:
    return "Terraform deploy integration is not implemented yet."
