from pathlib import Path

import yaml

from .constants import (
    CONFIG_FILENAME,
    DEFAULT_NETWORK,
    DEFAULT_NETWORK_NAME,
    DEFAULT_REGION,
    DEFAULT_SUBNETWORK,
    DEFAULT_ZONE,
    PROFILE_DEFAULTS,
)
from .models import NetworkName, PartnerDeploymentConfig


def default_config_path(cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    return root / CONFIG_FILENAME


def _starter_for(network_name: NetworkName) -> dict:
    defaults = PROFILE_DEFAULTS[network_name]
    node = {
        "account_id": "company.near" if network_name == "mainnet" else "company.testnet",
        "secrets": {
            "account_sk": f"multichain-account-sk-{network_name}-0",
            "cipher_sk": f"multichain-cipher-sk-{network_name}-0",
            "sign_sk": f"multichain-sign-sk-{network_name}-0",
            "sk_share": f"multichain-sk-share-{network_name}-0",
            "eth_account_sk": f"multichain-eth-account-sk-{network_name}-0",
            "eth_consensus_rpc": f"multichain-eth-consensus-rpc-url-{network_name}",
            "eth_execution_rpc": f"multichain-eth-execution-rpc-url-{network_name}",
            "sol_account_sk": "multichain-sol-account-sk-testnet" if network_name == "testnet" else "multichain-sol-account-sk-mainnet-0",
            "sol_rpc_http": f"multichain-sol-rpc-http-url-{network_name}",
            "sol_rpc_ws": f"multichain-sol-rpc-ws-url-{network_name}",
        },
    }
    if defaults["supports_domain"]:
        node["domain"] = "company.example.com"
    if defaults["supports_hydration"]:
        node["secrets"]["hydration_rpc_ws"] = "wss://node.lark.hydration.cloud"
        node["secrets"]["hydration_signer_uri"] = "//Bob"

    return {
        "version": 1,
        "network_name": network_name,
        "profile": defaults["profile"],
        "project_id": "<your-project-id>",
        "region": DEFAULT_REGION,
        "zone": DEFAULT_ZONE,
        "network": DEFAULT_NETWORK,
        "subnetwork": DEFAULT_SUBNETWORK,
        "state_bucket": "multichain-terraform-<your-entity-name>",
        "image": defaults["image"],
        "eth_contract_address": defaults["eth_contract_address"],
        "sol_program_address": defaults["sol_program_address"],
        "nodes": [node],
    }


def build_interactive_starter(
    network_name: NetworkName,
    project_id: str,
    state_bucket: str,
    account_id: str,
    domain: str | None = None,
) -> dict:
    starter = _starter_for(network_name)
    starter["project_id"] = project_id
    starter["state_bucket"] = state_bucket
    starter["nodes"][0]["account_id"] = account_id
    if network_name == "mainnet" and domain:
        starter["nodes"][0]["domain"] = domain
    return starter


def write_starter_config(path: Path, network_name: NetworkName = DEFAULT_NETWORK_NAME, starter: dict | None = None) -> None:
    content = starter or _starter_for(network_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(content, sort_keys=False))


def load_config(path: Path) -> PartnerDeploymentConfig:
    data = yaml.safe_load(path.read_text())
    return PartnerDeploymentConfig.model_validate(data)


def save_config(path: Path, config: PartnerDeploymentConfig) -> None:
    path.write_text(yaml.safe_dump(config.model_dump(exclude_none=True), sort_keys=False))
