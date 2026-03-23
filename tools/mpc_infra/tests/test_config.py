from pathlib import Path

from mpc_infra.config import load_config, write_starter_config


def test_write_and_load_starter_config(tmp_path: Path) -> None:
    path = tmp_path / "partner-mainnet.yaml"
    write_starter_config(path)
    config = load_config(path)
    assert config.profile == "mainnet"
    assert config.network == "default"
    assert len(config.nodes) == 1
