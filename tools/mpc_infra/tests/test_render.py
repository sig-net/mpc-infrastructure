from mpc_infra.models import NodeConfig, PartnerMainnetConfig, SecretRefs
from mpc_infra.render import render_partner_mainnet_tfvars


def test_render_partner_mainnet_tfvars() -> None:
    config = PartnerMainnetConfig(
        project_id="partner-project",
        state_bucket="multichain-terraform-partner",
        nodes=[
            NodeConfig(
                account_id="company.near",
                domain="company.example.com",
                secrets=SecretRefs(
                    account_sk="a",
                    cipher_sk="b",
                    sign_sk="c",
                    sk_share="d",
                    eth_account_sk="e",
                    eth_consensus_rpc="f",
                    eth_execution_rpc="g",
                    sol_account_sk="h",
                    sol_rpc_http="i",
                    sol_rpc_ws="j",
                    hydration_rpc_ws="k",
                    hydration_signer_uri="l",
                ),
            )
        ],
    )

    rendered = render_partner_mainnet_tfvars(config)
    assert rendered["project_id"] == "partner-project"
    assert rendered["node_configs"][0]["account"] == "company.near"
    assert rendered["node_configs"][0]["hydration_rpc_ws_url_secret_id"] == "k"
