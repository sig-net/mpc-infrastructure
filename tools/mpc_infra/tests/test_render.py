from mpc_infra.models import NodeConfig, PartnerDeploymentConfig, SecretRefs
from mpc_infra.render import render_partner_tfvars


def test_render_partner_mainnet_tfvars() -> None:
    config = PartnerDeploymentConfig(
        network_name="mainnet",
        profile="mainnet",
        project_id="partner-project",
        state_bucket="multichain-terraform-partner",
        eth_contract_address="D39b0aBc0acab7d48aC6DFC9612543f035233b68",
        sol_program_address="SigMcRMjKfnC7RDG5q4yUMZM1s5KJ9oYTPP4NmJRDRw",
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
                ),
            )
        ],
    )

    rendered = render_partner_tfvars(config)
    assert rendered["project_id"] == "partner-project"
    assert rendered["network"] == "default"
    assert rendered["node_configs"][0]["domain"] == "company.example.com"
    assert rendered["node_configs"][0]["sol_rpc_http_url_secret_id"] == "i"


def test_render_partner_testnet_tfvars() -> None:
    config = PartnerDeploymentConfig(
        network_name="testnet",
        profile="testnet",
        project_id="partner-project",
        state_bucket="multichain-terraform-partner",
        eth_contract_address="83458E8Bf8206131Fe5c05127007FA164c0948A2",
        sol_program_address="SigTVbfRK9LsXWpSv9KgpabrQcFKr5hDdUwMhYsXyKg",
        nodes=[
            NodeConfig(
                account_id="company.testnet",
                local_address="http://1.2.3.4:3000",
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

    rendered = render_partner_tfvars(config)
    assert rendered["node_configs"][0]["hydration_rpc_ws_url"] == "k"
    assert rendered["node_configs"][0]["hydration_signer_uri"] == "l"
    assert "domain" not in rendered["node_configs"][0]
