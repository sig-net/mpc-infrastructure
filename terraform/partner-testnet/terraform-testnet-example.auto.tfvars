env                     = "testnet"
project_id              = "<your-project-id>" # <-- Change me
network                 = "default"
subnetwork              = "default"
image                   = "europe-west1-docker.pkg.dev/near-cs-testnet/multichain-public/multichain-testnet:<approved-tag>"
operator_image          = "europe-west1-docker.pkg.dev/near-cs-mainnet/multichain-public/chain-signatures-agent:<approved-tag>"
manifest_url            = "https://storage.googleapis.com/chain-signatures-testnet/channels/stable/manifest.json"
trusted_manifest_pubkey = "<ed25519-public-key>"
region                  = "europe-west1"
zone                    = "europe-west1-b"

# The state bucket and manifest signing key still need to exist as prerequisites.
node_configs = [
  {
    node_id                         = 0
    account                         = "company.testnet" # <-- Change me
    account_sk_secret_id            = "multichain-account-sk-testnet-0"
    cipher_sk_secret_id             = "multichain-cipher-sk-testnet-0"
    sign_sk_secret_id               = "multichain-sign-sk-testnet-0"
    sk_share_secret_id              = "multichain-sk-share-testnet-0"
    eth_account_sk_secret_id        = "multichain-eth-account-sk-testnet-0"
    eth_consensus_rpc_url_secret_id = "multichain-eth-consensus-rpc-url-testnet"
    eth_execution_rpc_url_secret_id = "multichain-eth-execution-rpc-url-testnet"
    eth_contract_address            = "83458E8Bf8206131Fe5c05127007FA164c0948A2"
    sol_account_sk_secret_id        = "multichain-sol-account-sk-testnet-0"
    sol_rpc_http_url_secret_id      = "multichain-sol-rpc-http-url-testnet"
    sol_rpc_ws_url_secret_id        = "multichain-sol-rpc-ws-url-testnet"
    sol_program_address             = "SigTVbfRK9LsXWpSv9KgpabrQcFKr5hDdUwMhYsXyKg"
    hydration_rpc_ws_url            = "<hydration-rpc-ws-url>" # <-- Change me
    hydration_signer_uri            = "<hydration-signer-uri>" # <-- Change me
  },
]
