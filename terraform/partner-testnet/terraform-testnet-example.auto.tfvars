env                     = "testnet"
project_id              = "near-cs-testnet"
network                 = "projects/sig-shared-network/global/networks/prod"
subnetwork              = "projects/sig-shared-network/regions/europe-west1/subnetworks/prod-europe-west1"
image                   = "europe-west1-docker.pkg.dev/near-cs-testnet/multichain-public/multichain-testnet:latest"
operator_image          = "europe-west1-docker.pkg.dev/near-cs-mainnet/multichain-public/chain-signatures-agent:0ce00ea"
manifest_url            = "https://storage.googleapis.com/chain-signatures-testnet/channels/stable/manifest.json"
trusted_manifest_pubkey = "KaVGVJVvFyYnTeDOcXjIY+IMXzCLXkElVjI8L0Aef9I="
region                  = "europe-west1"
zone                    = "europe-west1-b"

# The state bucket and manifest signing key still need to exist as prerequisites.
node_configs = [
  {
    node_id                         = 8
    account                         = "multichain-node-8.testnet"
    account_sk_secret_id            = "multichain-account-sk-testnet-8"
    cipher_sk_secret_id             = "multichain-cipher-sk-testnet-8"
    sign_sk_secret_id               = "multichain-sign-sk-testnet-8"
    sk_share_secret_id              = "multichain-sk-share-testnet-8"
    eth_account_sk_secret_id        = "multichain-eth-account-sk-testnet-8"
    eth_consensus_rpc_url_secret_id = "multichain-eth-consensus-rpc-url-testnet"
    eth_execution_rpc_url_secret_id = "multichain-eth-execution-rpc-url-testnet"
    eth_contract_address            = "83458E8Bf8206131Fe5c05127007FA164c0948A2"
    sol_account_sk_secret_id        = "multichain-sol-account-sk-testnet"
    sol_rpc_http_url_secret_id      = "multichain-sol-rpc-http-url-testnet"
    sol_rpc_ws_url_secret_id        = "multichain-sol-rpc-ws-url-testnet"
    sol_program_address             = "SigTVbfRK9LsXWpSv9KgpabrQcFKr5hDdUwMhYsXyKg"
    hydration_rpc_ws_url            = "wss://node.lark.hydration.cloud"
    hydration_signer_uri            = "//Bob"
  },
]
