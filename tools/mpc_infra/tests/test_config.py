from pathlib import Path

from mpc_infra.config import load_config, write_starter_config


def test_write_and_load_starter_config_mainnet(tmp_path: Path) -> None:
    path = tmp_path / "partner-deployment.yaml"
    write_starter_config(path, network_name="mainnet")
    config = load_config(path)
    assert config.network_name == "mainnet"
    assert config.nodes[0].domain == "company.example.com"


def test_write_and_load_starter_config_testnet(tmp_path: Path) -> None:
    path = tmp_path / "partner-deployment.yaml"
    write_starter_config(path, network_name="testnet")
    config = load_config(path)
    assert config.network_name == "testnet"
    assert config.nodes[0].local_address == "http://<node-public-ip>:3000"
    assert config.nodes[0].secrets.hydration_rpc_ws == "wss://node.lark.hydration.cloud"
