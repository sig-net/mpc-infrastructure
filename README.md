# Multichain Infrastructure

This repository is the source of truth for partner-owned Multichain node infrastructure.

It now covers the current operator-based deployment contract:

- VM-based partner deployments on GCP for mainnet and testnet
- the signed manifest and operator bootstrap inputs those VMs consume
- the partner secret naming and Terraform inputs required to keep nodes aligned with the published release contract

This repository does not own the Kubernetes manifests used by SIG-managed clusters, but the same signed release model is intended to drive both VM-based and Kubernetes-based rollouts.

## Deployment Models

### VM-based partner deployment

The current partner target is a GCP VM deployment defined in:

- `terraform/partner-mainnet`
- `terraform/partner-testnet`

Each deployed node currently includes:

- one GCE VM created from a COS-backed instance template
- one `multichain` application container
- one `chain-signatures-operator` sidecar container running on the same VM
- local Redis state storage on the VM
- Secret Manager-backed runtime configuration
- a public global IP
- a Google Cloud HTTP(S) load balancer in front of the node
- managed TLS for mainnet partner domains
- project logging and a central logging sink

The operator is responsible for reading a signed release manifest, validating it against the trusted bootstrap public key, and keeping the application container aligned with the selected channel.

Detailed bootstrap guide:

- [Partner VM Bootstrap Guide](docs/partner-vm-bootstrap.md)

### Kubernetes deployment

Kubernetes is part of the overall release model, but not provisioned from this repository.

In practice:

- this repo defines the signed-manifest bootstrap contract and partner VM infrastructure
- `chain-signatures-publisher` publishes signed release manifests
- Kubernetes rollouts consume the same release artifacts through cluster-managed configuration in the Kubernetes repos

Overview:

- [Kubernetes Deployment Overview](docs/kubernetes-overview.md)

## What Gets Deployed

For the current partner VM path, Terraform provisions the following GCP resources and runtime components:

- a project service account for the node
- IAM roles for Secret Manager, Storage, IAM service-account admin, and logging
- a reserved global external IP per node
- a managed SSL certificate per mainnet node hostname
- an instance template and VM instance
- a backend service, health check, URL map, proxies, and forwarding rules
- firewall rules for health checks and SSH via IAP
- optional VPC, router, and NAT if the partner chooses `create_network = true`
- Secret Manager lookups for NEAR, Ethereum, Solana, and Hydration runtime inputs

At runtime, the startup script writes:

- `/var/lib/chain-signatures/bootstrap/bootstrap.env`
- `/var/lib/chain-signatures/bootstrap/manifest.pub`
- `/var/lib/chain-signatures/config/managed.env`
- `/var/lib/chain-signatures/config/app-container.json`

Then it starts:

- `multichain`
- `chain-signatures-operator`

## Bootstrap Requirements

Before a new partner deployment can be bootstrapped, you need:

- a GCP project where you can create compute, networking, IAM, logging, and Secret Manager resources
- permission equivalent to `Owner` on that project, or the practical ability to create the required resources and bindings
- a Cloud Storage bucket for Terraform state
- a domain or subdomain you control in DNS
- a local machine with `git`, `gcloud`, `terraform`, and `cargo`
- a NEAR account name reserved for the node
- generated node keys for NEAR, cipher, sign, Ethereum, and Solana
- the approved application image for the target environment
- the approved operator image for the target environment
- the manifest URL for the target environment
- the trusted manifest bootstrap public key for the target environment
- the complete Secret Manager secret set for the environment
- coordination with the chain-signatures team for any bootstrap values the partner cannot mint alone

### Required mainnet secrets

The current partner mainnet Terraform contract expects these Secret Manager secret IDs:

- `multichain-account-sk-mainnet-0`
- `multichain-cipher-sk-mainnet-0`
- `multichain-sign-sk-mainnet-0`
- `multichain-sk-share-mainnet-0`
- `multichain-eth-account-sk-mainnet-0`
- `multichain-eth-consensus-rpc-url-mainnet`
- `multichain-eth-execution-rpc-url-mainnet`
- `multichain-sol-account-sk-mainnet-0`
- `multichain-sol-rpc-ws-url-mainnet`
- `multichain-sol-rpc-http-url-mainnet`
- `multichain-hydration-rpc-ws-url-mainnet`
- `multichain-hydration-signer-uri-mainnet`

### Required testnet secrets

The current partner testnet Terraform contract expects these node-specific secret IDs plus the shared indexer credentials already referenced by Terraform:

- `multichain-account-sk-testnet-0`
- `multichain-cipher-sk-testnet-0`
- `multichain-sign-sk-testnet-0`
- `multichain-sk-share-testnet-0`
- `multichain-eth-account-sk-testnet-0`
- `multichain-eth-consensus-rpc-url-testnet`
- `multichain-eth-execution-rpc-url-testnet`
- `multichain-sol-account-sk-testnet-0`
- `multichain-sol-rpc-http-url-testnet`
- `multichain-sol-rpc-ws-url-testnet`

The current testnet module also depends on:

- `multichain-indexer-aws-access-key`
- `multichain-indexer-aws-secret-key`

Hydration values are currently passed directly in `terraform-testnet.auto.tfvars` rather than resolved from Secret Manager.

## Repo Layout

- `terraform/partner-mainnet` — current mainnet partner VM deployment
- `terraform/partner-testnet` — current testnet partner VM deployment
- `terraform/modules/instance-from-tpl` — VM instantiation helper
- `terraform/modules/mig_template` — COS instance-template helper
- `terraform/modules/multichain` — older Cloud Run deployment module
- `key_scripts/generate_keys` — helper for generating bootstrap keys

## Recommended Reading Order

If you are deploying a brand new partner node:

1. [Partner VM Bootstrap Guide](docs/partner-vm-bootstrap.md)
2. Review the appropriate example tfvars:
   - `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars`
   - `terraform/partner-testnet/terraform-testnet-example.auto.tfvars`
3. Populate Secret Manager with the expected secret names
4. Run Terraform
5. Complete DNS cutover and validation

If you already run an older partner deployment:

- [Migration Guide For Existing Partner Nodes](docs/migrating-existing-partner-node.md)

## Current State And Scope

This repository is primarily concerned with partner infrastructure bootstrapping and partner-facing runtime contracts.

It is not the full source of truth for:

- release manifest publishing logic
- Kubernetes environment overlays
- org-level GCP bootstrap and IAM outside the partner project

Those live in the adjacent repos used by the chain-signatures team.
