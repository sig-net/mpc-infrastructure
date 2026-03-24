from pathlib import Path

from mpc_infra.upgrade import (
    build_missing_secret_requirements,
    build_target_image,
    resolve_release_contract,
    resolve_target_tag,
    upgrade_readiness,
)


class Release:
    def __init__(self, version="v1.2.3", commit_sha="deadbeef", commitish="main"):
        self.version = version
        self.commit_sha = commit_sha
        self.commitish = commitish


class SecretRequirement:
    def __init__(self, key: str, secret_name_suggestion: str, description: str = "desc"):
        self.key = key
        self.secret_name_suggestion = secret_name_suggestion
        self.description = description


def test_resolve_release_contract_uses_release_commit_sha(monkeypatch) -> None:
    monkeypatch.setattr("mpc_infra.upgrade.resolve_latest_release", lambda explicit_tag=None: Release())
    contract = resolve_release_contract()
    assert contract.version == "v1.2.3"
    assert contract.image_tag == "deadbeef"
    assert contract.required_secrets == []


def test_resolve_target_tag_uses_release_commit_sha(monkeypatch) -> None:
    monkeypatch.setattr("mpc_infra.upgrade.resolve_latest_release", lambda explicit_tag=None: Release())
    assert resolve_target_tag() == "deadbeef"


def test_build_target_image_uses_network_repository() -> None:
    assert build_target_image("testnet", "deadbeef").endswith(":deadbeef")


def test_build_missing_secret_requirements_uses_configured_names(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "partner-deployment.yaml"
    config_path.write_text(
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
      hydration_rpc_ws: hydration-ws-secret
      hydration_signer_uri: hydration-signer-secret
""".strip()
    )
    from mpc_infra.config import load_config

    config = load_config(config_path)
    monkeypatch.setattr("mpc_infra.upgrade.list_secrets", lambda project_id: {"account-secret"})
    contract = type(
        "Contract",
        (),
        {
            "required_secrets": [
                SecretRequirement("account_sk", "unused-default"),
                SecretRequirement("hydration_rpc_ws", "unused-hydration"),
            ]
        },
    )()
    missing = build_missing_secret_requirements(config, contract)
    assert len(missing) == 1
    assert missing[0].key == "hydration_rpc_ws"
    assert missing[0].secret_name_suggestion == "hydration-ws-secret"


def test_upgrade_readiness_reports_missing_secrets(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "partner-deployment.yaml"
    config_path.write_text(
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
      hydration_rpc_ws: hydration-ws-secret
      hydration_signer_uri: hydration-signer-secret
""".strip()
    )
    from mpc_infra.config import load_config

    config = load_config(config_path)
    monkeypatch.setattr(
        "mpc_infra.upgrade.resolve_release_contract",
        lambda explicit_tag=None: type(
            "Contract",
            (),
            {
                "version": "v1.2.3",
                "image_tag": "deadbeef",
                "required_secrets": [SecretRequirement("cipher_sk", "cipher-secret")],
            },
        )(),
    )
    monkeypatch.setattr("mpc_infra.upgrade.list_secrets", lambda project_id: set())
    monkeypatch.setattr("mpc_infra.upgrade.current_deployed_image", lambda workdir: "repo:test")
    monkeypatch.setattr("mpc_infra.upgrade.terraform_workdir", lambda network_name: Path("/tmp/testnet"))
    readiness = upgrade_readiness(config)
    assert readiness.target_image.endswith(":deadbeef")
    assert readiness.current_image == "repo:test"
    assert not readiness.ready_for_upgrade
    assert readiness.missing_secret_requirements[0].secret_name_suggestion == "cipher-secret"
