import json
from pathlib import Path

from .constants import GENERATED_TFVARS_FILENAME
from .models import PartnerDeploymentConfig


def render_partner_tfvars(config: PartnerDeploymentConfig) -> dict:
    node_configs = []
    for node in config.nodes:
        rendered_node = {
            "account": node.account_id,
            "account_sk_secret_id": node.secrets.account_sk,
            "cipher_sk_secret_id": node.secrets.cipher_sk,
            "sign_sk_secret_id": node.secrets.sign_sk,
            "sk_share_secret_id": node.secrets.sk_share,
            "eth_account_sk_secret_id": node.secrets.eth_account_sk,
            "eth_consensus_rpc_url_secret_id": node.secrets.eth_consensus_rpc,
            "eth_execution_rpc_url_secret_id": node.secrets.eth_execution_rpc,
            "eth_contract_address": config.eth_contract_address,
            "sol_account_sk_secret_id": node.secrets.sol_account_sk,
            "sol_program_address": config.sol_program_address,
            "sol_rpc_http_url_secret_id": node.secrets.sol_rpc_http,
            "sol_rpc_ws_url_secret_id": node.secrets.sol_rpc_ws,
        }
        if config.network_name == "mainnet" and node.domain:
            rendered_node["domain"] = node.domain
        if config.network_name == "testnet":
            rendered_node["hydration_rpc_ws_url"] = node.secrets.hydration_rpc_ws
            rendered_node["hydration_signer_uri"] = node.secrets.hydration_signer_uri
        node_configs.append(rendered_node)

    rendered = {
        "env": config.profile,
        "project_id": config.project_id,
        "network": config.network,
        "subnetwork": config.subnetwork,
        "region": config.region,
        "zone": config.zone,
        "node_configs": node_configs,
    }
    if config.image:
        rendered["image"] = config.image
    return rendered


def write_generated_tfvars(config: PartnerDeploymentConfig, destination_dir: Path) -> Path:
    destination = destination_dir / GENERATED_TFVARS_FILENAME
    rendered = render_partner_tfvars(config)
    destination.write_text(json.dumps(rendered, indent=2) + "\n")
    return destination
