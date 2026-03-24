from pathlib import Path

from mpc_infra.config import load_config
from mpc_infra.render import rendered_secret_names
from mpc_infra.upgrade import expected_secret_name


def _write_testnet_config(path: Path) -> None:
    path.write_text(
        """
version: 1
network_name: testnet
profile: testnet
project_id: demo-project
region: europe-west1
zone: europe-west1-b
network: default
subnetwork: default
state_bucket: demo-bucket
image: example:test
eth_contract_address: abc
sol_program_address: xyz
nodes:
  - account_id: company.testnet
    secrets:
      account_sk: account-secret
      cipher_sk: cipher-secret
      sign_sk: sign-secret
      sk_share: skshare-secret
      eth_account_sk: eth-account-secret
      eth_consensus_rpc: eth-consensus-secret
      eth_execution_rpc: eth-execution-secret
      sol_account_sk: sol-account-secret
      sol_rpc_http: sol-http-secret
      sol_rpc_ws: sol-ws-secret
      hydration_rpc_ws: wss://hydration.example/ws
      hydration_signer_uri: http://hydration.example/signer
""".strip()
    )


def test_rendered_secret_names_only_includes_secret_id_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "partner-deployment.yaml"
    _write_testnet_config(config_path)
    config = load_config(config_path)
    names = rendered_secret_names(config)
    assert "account-secret" in names
    assert "cipher-secret" in names
    assert "wss://hydration.example/ws" not in names
    assert "http://hydration.example/signer" not in names


def test_expected_secret_name_ignores_non_secret_literal_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "partner-deployment.yaml"
    _write_testnet_config(config_path)
    config = load_config(config_path)
    assert expected_secret_name(config, "account_sk") == "account-secret"
    assert expected_secret_name(config, "hydration_rpc_ws") is None
    assert expected_secret_name(config, "hydration_signer_uri") is None
