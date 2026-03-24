from mpc_infra.upgrade import build_target_image, resolve_release_contract, resolve_target_tag


def test_resolve_release_contract_contains_required_secrets(monkeypatch) -> None:
    monkeypatch.setattr(
        "mpc_infra.upgrade.resolve_latest_release",
        lambda explicit_tag=None: type(
            "Release",
            (),
            {"version": explicit_tag or "v1.2.3", "commitish": "main", "commit_sha": "abc123"},
        )(),
    )
    contract = resolve_release_contract()
    assert contract.version == "v1.2.3"
    assert contract.image_tag == "abc123"
    assert contract.required_secrets
    assert contract.required_secrets[0].secret_name_suggestion


def test_resolve_target_tag_uses_release_commit_sha(monkeypatch) -> None:
    monkeypatch.setattr(
        "mpc_infra.upgrade.resolve_latest_release",
        lambda explicit_tag=None: type(
            "Release",
            (),
            {"version": explicit_tag or "v1.2.3", "commitish": "main", "commit_sha": "deadbeef"},
        )(),
    )
    assert resolve_target_tag() == "deadbeef"


def test_build_target_image_uses_network_repository() -> None:
    assert build_target_image("testnet", "deadbeef").endswith(":deadbeef")
