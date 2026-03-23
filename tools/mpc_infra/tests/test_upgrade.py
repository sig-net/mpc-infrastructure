from mpc_infra.upgrade import resolve_release_contract


def test_resolve_release_contract_contains_required_secrets() -> None:
    contract = resolve_release_contract()
    assert contract.required_secrets
    assert contract.required_secrets[0].secret_name_suggestion
