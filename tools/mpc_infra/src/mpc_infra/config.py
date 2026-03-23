from pathlib import Path

import yaml

from .constants import (
    CONFIG_FILENAME,
    DEFAULT_ETH_CONTRACT_ADDRESS,
    DEFAULT_IMAGE,
    DEFAULT_NETWORK,
    DEFAULT_PROFILE,
    DEFAULT_REGION,
    DEFAULT_SOL_PROGRAM_ADDRESS,
    DEFAULT_SUBNETWORK,
    DEFAULT_ZONE,
)
from .models import PartnerMainnetConfig


def default_config_path(cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    return root / CONFIG_FILENAME


def write_starter_config(path: Path) -> None:
    starter = {
        "version": 1,
        "profile": DEFAULT_PROFILE,
        "project_id": "<your-project-id>",
        "region": DEFAULT_REGION,
        "zone": DEFAULT_ZONE,
        "network": DEFAULT_NETWORK,
        "subnetwork": DEFAULT_SUBNETWORK,
        "state_bucket": "multichain-terraform-<your-entity-name>",
        "image": DEFAULT_IMAGE,
        "eth_contract_address": DEFAULT_ETH_CONTRACT_ADDRESS,
        "sol_program_address": DEFAULT_SOL_PROGRAM_ADDRESS,
        "nodes": [
            {
                "account_id": "company.near",
                "domain": "company.example.com",
                "secrets": {
                    "account_sk": "multichain-account-sk-mainnet-0",
                    "cipher_sk": "multichain-cipher-sk-mainnet-0",
                    "sign_sk": "multichain-sign-sk-mainnet-0",
                    "sk_share": "multichain-sk-share-mainnet-0",
                    "eth_account_sk": "multichain-eth-account-sk-mainnet-0",
                    "eth_consensus_rpc": "multichain-eth-consensus-rpc-url-mainnet",
                    "eth_execution_rpc": "multichain-eth-execution-rpc-url-mainnet",
                    "sol_account_sk": "multichain-sol-account-sk-mainnet-0",
                    "sol_rpc_http": "multichain-sol-rpc-http-url-mainnet",
                    "sol_rpc_ws": "multichain-sol-rpc-ws-url-mainnet",
                },
            }
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(starter, sort_keys=False))


def load_config(path: Path) -> PartnerMainnetConfig:
    data = yaml.safe_load(path.read_text())
    return PartnerMainnetConfig.model_validate(data)
