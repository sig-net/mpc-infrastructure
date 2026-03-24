from pathlib import Path

from mpc_infra.terraform import deployed_instance_names
from mpc_infra.upgrade import status_against_latest_release


def test_status_report_has_recommended_action(monkeypatch) -> None:
    monkeypatch.setattr(
        "mpc_infra.upgrade.resolve_release_contract",
        lambda explicit_tag=None: type(
            "Contract",
            (),
            {
                "version": "v1.2.3",
                "image_tag": "deadbeef",
                "required_secrets": [type("Secret", (), {"secret_name_suggestion": "example-secret"})()],
            },
        )(),
    )
    monkeypatch.setattr("mpc_infra.upgrade.current_deployed_image", lambda workdir: "europe-west1-docker.pkg.dev/near-cs-testnet/multichain-public/multichain-testnet:oldtag")
    monkeypatch.setattr("mpc_infra.upgrade.terraform_workdir", lambda network_name: "/tmp/testnet")

    report = status_against_latest_release()
    assert report.latest_version == "v1.2.3"
    assert report.latest_github_version == "v1.2.3"
    assert report.target_image.endswith(":deadbeef")
    assert report.recommended_action


def test_deployed_instance_names_reads_outputs(monkeypatch) -> None:
    monkeypatch.setattr(
        "mpc_infra.terraform.terraform_output_json",
        lambda workdir: {"instance_names": ["instance-a", "instance-b"]},
    )
    names = deployed_instance_names(Path("/tmp/testnet"))
    assert names == ["instance-a", "instance-b"]
