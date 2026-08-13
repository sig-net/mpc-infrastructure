# Partner VM Bootstrap Guide

This guide is for provisioning a new partner-owned Multichain node on GCP using the current operator-based VM deployment.

Use this guide when:

- you are creating a new partner deployment from scratch
- you want the node to follow the signed manifest release channel
- you need the Terraform inputs and secret names to match the current contract in this repository

Use the migration guide instead when the partner already has an older deployment:

- [Migration Guide For Existing Partner Nodes](migrating-existing-partner-node.md)

## What You Will Deploy

The current partner VM stack includes:

- one GCE VM running Container-Optimized OS
- one `multichain` container
- one `chain-signatures-operator` container
- local Redis state on the VM
- Secret Manager-backed runtime configuration
- a public IP and Google Cloud load balancer
- managed TLS for mainnet domains

The operator bootstraps from:

- `manifest_url`
- `manifest_channel`
- `trusted_manifest_pubkey`

and then reconciles the app container against the signed release manifest.

## Requirements

Before starting, make sure you have:

- access to create and administer a GCP project
- permissions equivalent to `Owner` on the target project
- a Cloud Storage bucket for Terraform state
- a domain or subdomain you can manage in DNS
- `git`, `gcloud`, `terraform`, and `cargo` on your local machine
- access to the chain-signatures team for bootstrap coordination
- an approved target image and operator image for the chosen environment

You will also need:

- a NEAR account name for the node
- a generated NEAR account secret/public key
- a generated cipher private/public key
- a generated sign private/public key
- a generated Ethereum account secret/public key
- a generated Solana account secret/public key

## 1. Create Or Select The GCP Project

Create a dedicated GCP project for the partner node.

Recommended naming style:

```text
partner-multichain
```

You will need the project ID later for:

- `project_id` in Terraform
- Secret Manager secret placement
- application-default credentials

## 2. Enable Required GCP Services

At minimum, enable:

- Secret Manager API
- Compute Engine API
- Cloud Logging API
- Cloud Storage API

If you are creating a new VPC with `create_network = true`, also ensure the network-related APIs normally used by Compute Engine are available in the project.

## 3. Create A Terraform State Bucket

Create a Cloud Storage bucket for Terraform state.

Recommended naming pattern:

```text
multichain-terraform-<your-entity-name>
```

Recommended bucket settings:

- region `europe-west1`
- storage class `Standard`
- public access prevention enabled
- uniform access enabled
- soft delete enabled

Use:

- `state/mainnet` for mainnet
- `state/testnet` for testnet

## 4. Generate Node Keys

Clone the repo and run the key generator:

```bash
git clone https://github.com/sig-net/mpc-infrastructure.git
cd mpc-infrastructure
git checkout main
git pull --ff-only
cd key_scripts/generate_keys
cargo run
```

Treat all generated secret material as production credentials.

## 5. Reserve The NEAR Account

Choose the account name the node will use.

Recommended mainnet pattern:

```text
<company-variation>.near
```

Recommended testnet pattern:

```text
<company-variation>.testnet
```

Coordinate with the chain-signatures team to create or fund the required account if the partner cannot do that independently.

## 6. Authenticate Local Tooling

Install and authenticate `gcloud` and make sure Terraform can use application-default credentials:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <your-project-id>
gcloud auth application-default set-quota-project <your-project-id>
```

## 7. Populate Secret Manager

### Mainnet secret IDs

Create these secrets in the target project:

```text
multichain-account-sk-mainnet-0
multichain-cipher-sk-mainnet-0
multichain-sign-sk-mainnet-0
multichain-sk-share-mainnet-0
multichain-eth-account-sk-mainnet-0
multichain-eth-consensus-rpc-url-mainnet
multichain-eth-execution-rpc-url-mainnet
multichain-sol-account-sk-mainnet-0
multichain-sol-rpc-ws-url-mainnet
multichain-sol-rpc-http-url-mainnet
multichain-hydration-rpc-ws-url-mainnet
multichain-hydration-signer-uri-mainnet
```

### Testnet secret IDs

Create these node-specific testnet secrets:

```text
multichain-account-sk-testnet-0
multichain-cipher-sk-testnet-0
multichain-sign-sk-testnet-0
multichain-sk-share-testnet-0
multichain-eth-account-sk-testnet-0
multichain-eth-consensus-rpc-url-testnet
multichain-eth-execution-rpc-url-testnet
multichain-sol-account-sk-testnet-0
multichain-sol-rpc-http-url-testnet
multichain-sol-rpc-ws-url-testnet
```

The current testnet Terraform also expects these shared indexer secrets to exist:

```text
multichain-indexer-aws-access-key
multichain-indexer-aws-secret-key
```

### Upload helper

The repository includes:

```text
terraform/partner-mainnet/scripts/upload_secrets.sh
```

You can use it with a local secrets file:

```bash
cd terraform/partner-mainnet/scripts
./upload_secrets.sh -d <gcp-project-id> -f secrets.txt
```

Do not commit `secrets.txt`.

## 8. Fill In Terraform Inputs

Start from the relevant example file:

- `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars`
- `terraform/partner-testnet/terraform-testnet-example.auto.tfvars`

Important current operator-era inputs are:

- `image`
- `operator_image`
- `manifest_url`
- `trusted_manifest_pubkey`
- `project_id`
- `network`
- `subnetwork`
- `region`
- `zone`
- `node_configs[*]`

For mainnet, `node_configs[0]` currently includes:

- account ID
- Secret Manager IDs for NEAR, cipher, sign, ETH, SOL, and Hydration
- external domain
- ETH contract address
- Solana program address

## 9. Initialize And Apply Terraform

For mainnet:

```bash
cd terraform/partner-mainnet
terraform init
terraform plan -var-file=terraform-mainnet.auto.tfvars
terraform apply -var-file=terraform-mainnet.auto.tfvars
```

For testnet:

```bash
cd terraform/partner-testnet
terraform init
terraform plan -var-file=terraform-testnet.auto.tfvars
terraform apply -var-file=terraform-testnet.auto.tfvars
```

## 10. Complete DNS Cutover

After apply completes, point the chosen hostname at the provisioned external IP.

Recommended mainnet hostname pattern:

```text
multichain-mainnet-0.<your-domain>
```

For mainnet, allow time for the managed SSL certificate to become active after DNS resolves correctly.

## 11. Validate The Node

After DNS and load balancer propagation, verify:

- the VM is healthy in Compute Engine
- the load balancer backend is healthy
- the application responds on the expected endpoint
- the operator container is running
- the application container is running
- startup logs do not show secret-resolution or manifest-verification failures

Useful checks:

```bash
gcloud compute instances list --project <your-project-id>
gcloud compute ssh <instance-name> --zone <zone> --project <your-project-id>
docker ps
docker logs chain-signatures-operator
docker logs multichain
```

## 12. Know The Runtime Contract

The startup script writes bootstrap files and launches both containers locally.

The operator consumes:

- bootstrap env
- trusted manifest public key
- managed env
- state files

The app container receives:

- NEAR credentials
- cipher/sign credentials
- ETH credentials and RPC endpoints
- SOL credentials and RPC endpoints
- Hydration connection values
- release bootstrap values such as account ID, environment, local address, and manifest metadata

If those values drift from the signed-manifest contract or Terraform naming contract, upgrades become harder to reason about. Keep Terraform, Secret Manager, and publisher-managed env names aligned.
